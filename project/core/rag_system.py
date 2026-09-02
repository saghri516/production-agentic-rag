import uuid
# from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import InMemorySaver
import os

import config
from db.vector_db_manager import VectorDbManager
from db.parent_store_manager import ParentStoreManager
from document_chunker import DocumentChunker
from rag_agent.tools import ToolFactory
from rag_agent.graph import create_agent_graph
from core.observability import Observability
from core.logger import get_logger

logger = get_logger(__name__)

class RAGSystem:

    def __init__(self, collection_name=config.CHILD_COLLECTION):
        self.collection_name = collection_name
        self.vector_db = VectorDbManager()
        self.parent_store = ParentStoreManager()
        self.chunker = DocumentChunker()
        self.observability = Observability()
        self.agent_graph = None
        self.checkpointer = InMemorySaver()
        self._postgres_context = None
        self.recursion_limit = config.GRAPH_RECURSION_LIMIT

    def initialize(self):
        self._configure_checkpointer()
        self.vector_db.create_collection(self.collection_name)
        collection = self.vector_db.get_collection(self.collection_name)

        # llm = ChatOllama(
        #     model=config.LLM_MODEL,
        #     temperature=config.LLM_TEMPERATURE,
        #     seed=config.LLM_SEED,)
        llm = ChatGroq(model=config.LLM_MODEL, temperature=config.LLM_TEMPERATURE, api_key=os.getenv("GROQ_API_KEY"))
        
        tools = ToolFactory(collection).create_tools()
        self.agent_graph = create_agent_graph(llm, tools, self.checkpointer)

    def _configure_checkpointer(self):
        if not config.DATABASE_URL:
            logger.warning("Warning: DATABASE_URL is not set; using InMemorySaver. Conversation history will not persist across restarts.")
            return

        try:
            from langgraph.checkpoint.postgres import PostgresSaver

            self._postgres_context = PostgresSaver.from_conn_string(config.DATABASE_URL)
            self.checkpointer = self._postgres_context.__enter__()
            self.checkpointer.setup()
            logger.info("Postgres checkpointer initialized.")
        except Exception as exc:
            if self._postgres_context is not None:
                self._postgres_context.__exit__(type(exc), exc, exc.__traceback__)
                self._postgres_context = None
            self.checkpointer = InMemorySaver()
            logger.warning(f"Warning: Could not initialize PostgresSaver ({exc}); using InMemorySaver.")

    def get_config(self, thread_id):
        cfg = {"configurable": {"thread_id": thread_id}, "recursion_limit": self.recursion_limit}
        handler = self.observability.get_handler()
        if handler:
            cfg["callbacks"] = [handler]
        return cfg

    def reset_thread(self, thread_id):
        try:
            self.agent_graph.checkpointer.delete_thread(thread_id)
        except Exception as e:
            logger.warning(f"Warning: Could not delete thread {thread_id}: {e}")
        return str(uuid.uuid4())

    def shutdown(self):
        if self._postgres_context is not None:
            self._postgres_context.__exit__(None, None, None)
            self._postgres_context = None
