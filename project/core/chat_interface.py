import json
import re
import threading
import time
from collections import deque
from langchain_core.messages import HumanMessage, AIMessageChunk, ToolMessage
from core.execution_logger import log_chat_end, log_chat_start, log_error

SYSTEM_NODES = {"summarize_history", "rewrite_query"}
FINAL_RESPONSE_NODES = {"aggregate_answers"}

SYSTEM_NODE_CONFIG = {
    "rewrite_query":     {"title": "🔍 Query Analysis & Rewriting"},
    "summarize_history": {"title": "📋 Chat History Summary"},
}

# --- Helpers ---

def make_message(content, *, title=None, node=None):
    msg = {"role": "assistant", "content": content}
    if title or node:
        msg["metadata"] = {k: v for k, v in {"title": title, "node": node}.items() if v}
    return msg


def find_msg_idx(messages, node):
    return next(
        (i for i, m in enumerate(messages) if m.get("metadata", {}).get("node") == node),
        None,
    )


def parse_rewrite_json(buffer):
    match = re.search(r"\{.*\}", buffer, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except Exception:
        return None


def format_rewrite_content(buffer):
    data = parse_rewrite_json(buffer)
    if not data:
        return "⏳ Analyzing query..."
    if data.get("is_clear"):
        lines = ["✅ **Query is clear**"]
        if data.get("questions"):
            lines += ["\n**Rewritten queries:**"] + [f"- {q}" for q in data["questions"]]
    else:
        lines = ["❓ **Query is unclear**"]
        clarification = data.get("clarification_needed", "")
        if clarification and clarification.strip().lower() != "no":
            lines.append(f"\nClarification needed: *{clarification}*")
    return "\n".join(lines)


def extract_system_node_text(chunk):
    """Get the textual payload of a system-node chunk.

    Structured-output models (e.g. via with_structured_output) often stream
    their JSON as a tool call rather than plain .content. This pulls text
    from whichever channel actually has it, so system nodes are handled
    consistently regardless of how the underlying model streams structured
    output.
    """
    if getattr(chunk, "content", None):
        return chunk.content
    tool_call_chunks = getattr(chunk, "tool_call_chunks", None)
    if tool_call_chunks:
        return "".join(tcc.get("args") or "" for tcc in tool_call_chunks)
    return ""

# --- End of Helpers ---

class ChatInterface:

    _rate_limit_lock = threading.Lock()
    _message_timestamps = {}
    _rate_limit_max_messages = 10
    _rate_limit_window_seconds = 60

    def __init__(self, rag_system):
        self.rag_system = rag_system

    @classmethod
    def _is_rate_limited(cls, thread_id):
        now = time.monotonic()
        cutoff = now - cls._rate_limit_window_seconds

        with cls._rate_limit_lock:
            timestamps = cls._message_timestamps.setdefault(thread_id, deque())
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()

            if len(timestamps) >= cls._rate_limit_max_messages:
                return True

            timestamps.append(now)
            return False

    def _handle_system_node(self, text, node, response_messages, system_node_buffer):
        """Update (or create) the collapsible system-node message and surface any clarification."""
        system_node_buffer[node] = system_node_buffer.get(node, "") + text
        buffer = system_node_buffer[node]
        title  = SYSTEM_NODE_CONFIG[node]["title"]
        content = format_rewrite_content(buffer) if node == "rewrite_query" else buffer

        idx = find_msg_idx(response_messages, node)
        if idx is None:
            response_messages.append(make_message(content, title=title, node=node))
        else:
            response_messages[idx]["content"] = content

        if node == "rewrite_query":
            self._surface_clarification(buffer, response_messages)

    def _surface_clarification(self, buffer, response_messages):
        """If the query is unclear, add/update a plain clarification message."""
        data          = parse_rewrite_json(buffer) or {}
        clarification = data.get("clarification_needed", "")
        if not data.get("is_clear") and clarification.strip().lower() not in ("", "no"):
            cidx = find_msg_idx(response_messages, "clarification")
            if cidx is None:
                response_messages.append(make_message(clarification, node="clarification"))
            else:
                response_messages[cidx]["content"] = clarification

    def _handle_tool_call(self, chunk, response_messages, active_tool_calls):
        """Register new tool calls as collapsible messages."""
        for tc in chunk.tool_calls:
            if tc.get("id") and tc["id"] not in active_tool_calls:
                response_messages.append(
                    make_message(f"Running `{tc['name']}`...", title=f"🛠️ {tc['name']}")
                )
                active_tool_calls[tc["id"]] = len(response_messages) - 1

    def _handle_tool_result(self, chunk, response_messages, active_tool_calls):
        """Fill in the tool result inside the matching collapsible message."""
        idx = active_tool_calls.get(chunk.tool_call_id)
        if idx is not None:
            preview = str(chunk.content)[:300]
            suffix  = "\n..." if len(str(chunk.content)) > 300 else ""
            response_messages[idx]["content"] = f"```\n{preview}{suffix}\n```"

    def _handle_llm_token(self, chunk, node, response_messages):
        """Append streaming LLM tokens to the last plain assistant message."""
        last = response_messages[-1] if response_messages else None
        if not (last and last.get("role") == "assistant" and "metadata" not in last):
            response_messages.append(make_message(""))
        response_messages[-1]["content"] += chunk.content

    def chat(self, message, history, thread_id):
        """Generator that streams Gradio chat message dicts."""
        if not self.rag_system.agent_graph:
            yield "⚠️ System not initialized!"
            return

        if self._is_rate_limited(thread_id):
            yield "Rate limit reached: maximum 10 messages per minute. Please try again later."
            return

        config        = self.rag_system.get_config(thread_id)
        current_state = self.rag_system.agent_graph.get_state(config)
        log_chat_start(message.strip(), thread_id, bool(current_state.next))

        try:
            if current_state.next:
                self.rag_system.agent_graph.update_state(config, {"messages": [HumanMessage(content=message.strip())]})
                stream_input = None
            else:
                stream_input = {"messages": [HumanMessage(content=message.strip())]}

            response_messages  = []
            active_tool_calls  = {}
            system_node_buffer = {}

            for chunk, metadata in self.rag_system.agent_graph.stream(stream_input, config=config, stream_mode="messages"):
                node = metadata.get("langgraph_node", "")

                # IMPORTANT: system nodes (rewrite_query, summarize_history) must be
                # checked FIRST and independently of chunk shape. Structured-output
                # models often stream their JSON as a tool call (tool_call_chunks)
                # rather than plain .content — if this check doesn't run before the
                # generic tool-call handler below, that structured-output tool call
                # gets misrendered as a real, never-completing tool invocation
                # (e.g. a permanently "Running QueryAnalysis..." box), and the
                # clarification message never surfaces to the user.
                if node in SYSTEM_NODES and isinstance(chunk, AIMessageChunk):
                    text = extract_system_node_text(chunk)
                    if text:
                        self._handle_system_node(text, node, response_messages, system_node_buffer)
                    else:
                        continue

                elif hasattr(chunk, "tool_calls") and chunk.tool_calls:
                    self._handle_tool_call(chunk, response_messages, active_tool_calls)

                elif isinstance(chunk, ToolMessage):
                    self._handle_tool_result(chunk, response_messages, active_tool_calls)

                elif isinstance(chunk, AIMessageChunk) and chunk.content and node in FINAL_RESPONSE_NODES:
                    self._handle_llm_token(chunk, node, response_messages)

                else:
                    continue

                yield response_messages

            final_state = self.rag_system.agent_graph.get_state(config)
            log_chat_end(getattr(final_state, "values", final_state))

        except Exception as e:
            log_error("chat", e)
            yield f"❌ Error: {str(e)}"

    def clear_session(self, thread_id):
        new_thread_id = self.rag_system.reset_thread(thread_id)
        self.rag_system.observability.flush()
        return new_thread_id