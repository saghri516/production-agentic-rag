custom_css = """
    /* ============================================
       MAIN CONTAINER
       ============================================ */
    .progress-text { 
        display: none !important;
    }
    
    .gradio-container { 
        max-width: 1000px !important;
        width: 100% !important;
        margin: 0 auto !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        background: radial-gradient(circle at 30% 0%, #2a1f5e 0%, #14102e 45%, #0a081c 100%) !important;
    }

    /* ============================================
       APP HEADER
       ============================================ */
    #app-header {
        text-align: center !important;
        padding: 24px 10px 16px 10px !important;
    }

    #app-header h1 {
        font-size: 2.1rem !important;
        font-weight: 800 !important;
        color: #ffffff !important;
        margin-bottom: 6px !important;
        letter-spacing: -0.02em !important;
    }

    #app-header p {
        color: #a9a3d4 !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
    }
    
    /* ============================================
       TABS
       ============================================ */
    button[role="tab"] {
        color: #9d97c7 !important;
        border-bottom: 2px solid transparent !important;
        border-radius: 0 !important;
        transition: all 0.2s ease !important;
        background: transparent !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
    }
    
    button[role="tab"]:hover {
        color: #c4bdff !important;
    }
    
    button[role="tab"][aria-selected="true"] {
        color: #ffffff !important;
        border-bottom: 2px solid #7c5cff !important;
        border-radius: 0 !important;
        background: transparent !important;
    }
    
    .tabs {
        border-bottom: none !important;
        border-radius: 0 !important;
    }
    
    .tab-nav {
        border-bottom: 1px solid #2e2760 !important;
        border-radius: 0 !important;
    }
    
    button[role="tab"]::before,
    button[role="tab"]::after,
    .tabs::before,
    .tabs::after,
    .tab-nav::before,
    .tab-nav::after {
        display: none !important;
        content: none !important;
        border-radius: 0 !important;
    }
    
    #doc-management-tab {
        max-width: 550px !important;
        margin: 0 auto !important;
    }
    
    /* ============================================
       BUTTONS
       ============================================ */
    button {
        border-radius: 10px !important;
        border: none !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        transition: all 0.2s ease !important;
        box-shadow: none !important;
    }
    
    .primary {
        background: #7c5cff !important;
        color: white !important;
        box-shadow: 0 4px 16px rgba(124, 92, 255, 0.35) !important;
    }
    
    .primary:hover {
        background: #8f72ff !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(124, 92, 255, 0.45) !important;
    }
    
    .stop {
        background: #e5484d !important;
        color: white !important;
        box-shadow: 0 4px 14px rgba(229, 72, 77, 0.35) !important;
    }
    
    .stop:hover {
        background: #f2585d !important;
        transform: translateY(-1px) !important;
    }

    button:not(.primary):not(.stop) {
        background: #1e1a45 !important;
        color: #d4d0f5 !important;
        border: 1px solid #322b6b !important;
    }

    button:not(.primary):not(.stop):hover {
        background: #272060 !important;
        border-color: #7c5cff !important;
    }
    
    /* ============================================
       CHAT INPUT BOX
       ============================================ */
    textarea[placeholder="Type a message..."],
    textarea[data-testid*="textbox"]:not(#file-list-box textarea) {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: #111111 !important;
        font-weight: 500 !important;
        font-size: 1rem !important;
    }

    textarea[placeholder="Type a message..."]::placeholder,
    textarea[data-testid*="textbox"]::placeholder {
        color: #737373 !important;
    }
    
    textarea[placeholder="Type a message..."]:focus {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: #111111 !important;
    }
    
    .gr-text-input:has(textarea[placeholder="Type a message..."]),
    [class*="chatbot"] + * [data-testid="textbox"],
    form:has(textarea[placeholder="Type a message..."]) > div {
        background: transparent !important;
        border: none !important;
        gap: 12px !important;
    }
    
    form:has(textarea[placeholder="Type a message..."]) button,
    [class*="chatbot"] ~ * button[type="submit"] {
        background: #7c5cff !important;
        border: none !important;
        padding: 10px !important;
        border-radius: 10px !important;
    }
    
    form:has(textarea[placeholder="Type a message..."]) button:hover {
        background: #8f72ff !important;
    }
    
    form:has(textarea[placeholder="Type a message..."]) {
        gap: 12px !important;
        display: flex !important;
    }
    
    /* ============================================
       FILE UPLOAD
       ============================================ */
    .file-preview, 
    [data-testid="file-upload"] {
        background: #171340 !important;
        border: 1.5px dashed #4a3f9e !important;
        border-radius: 14px !important;
        color: #ffffff !important;
        min-height: 200px !important;
    }
    
    .file-preview:hover, 
    [data-testid="file-upload"]:hover {
        border-color: #7c5cff !important;
        background: #1c1850 !important;
    }
    
    .file-preview *,
    [data-testid="file-upload"] * {
        color: #ffffff !important;
        font-weight: 500 !important;
    }
    
    .file-preview .label,
    [data-testid="file-upload"] .label {
        display: none !important;
    }
    
    /* ============================================
       INPUTS & TEXTAREAS
       ============================================ */
    input, 
    textarea {
        background: #171340 !important;
        border: 1px solid #322b6b !important;
        border-radius: 12px !important;
        color: #ede9ff !important;
        font-weight: 500 !important;
        transition: border-color 0.2s ease !important;
    }
    
    input:focus, 
    textarea:focus {
        border-color: #7c5cff !important;
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(124, 92, 255, 0.2) !important;
    }
    
    textarea[readonly] {
        background: #171340 !important;
        color: #b8b2e6 !important;
    }
    
    /* ============================================
       FILE LIST BOX
       ============================================ */
    #file-list-box {
        background: #171340 !important;
        border: 1px solid #322b6b !important;
        border-radius: 12px !important;
        padding: 10px !important;
    }
    
    #file-list-box textarea {
        background: transparent !important;
        border: none !important;
        color: #ede9ff !important;
        font-weight: 600 !important;
        padding: 0 !important;
    }
    
    /* ============================================
       CHATBOT CONTAINER
       ============================================ */
    .chatbot {
        border-radius: 18px !important;
        background: #120e30 !important;
        border: 1px solid #2e2760 !important;
    }

    .chatbot .message-wrap,
    .chatbot > div {
        gap: 10px !important;
        padding: 16px !important;
    }

    /* ============================================
       MESSAGE BUBBLES
       ============================================ */
    .message {
        border-radius: 14px !important;
        font-weight: 500 !important;
        font-size: 1rem !important;
    }

    .message.user {
        background: #7c5cff !important;
        color: #ffffff !important;
        box-shadow: 0 3px 12px rgba(124, 92, 255, 0.3) !important;
    }
    
    .message.bot {
        background: #1c1850 !important;
        color: #ede9ff !important;
        border: 1px solid #322b6b !important;
        width: fit-content !important;
        max-width: 90% !important;
    }
    
    .message-row img {
        margin: 0px !important;
    }

    .avatar-container img {
        padding: 0px !important;
    }

    /* ============================================
       TOOL CALL / THOUGHT CONTENT
       ============================================ */
    .message.bot *,
    .message.bot p,
    .message.bot li,
    .message.bot span,
    .message.bot div {
        color: #ede9ff !important;
        opacity: 1 !important;
        font-weight: 500 !important;
    }

    .message.bot code,
    .message.bot pre {
        color: #9d8cff !important;
        background: #0e0b28 !important;
        opacity: 1 !important;
        font-weight: 500 !important;
        border: 1px solid #322b6b !important;
        border-radius: 8px !important;
    }

    .thought-content,
    .tool-details,
    [class*="thought"],
    [class*="tool-call"],
    details,
    summary {
        color: #ede9ff !important;
        opacity: 1 !important;
        background: #1c1850 !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
    }

    details summary {
        color: #a78bfa !important;
        font-weight: 700 !important;
    }

    .chatbot [style*="opacity"] {
        opacity: 1 !important;
    }

    /* ============================================
       INTRO / DESCRIPTION TEXT
       ============================================ */
    .prose,
    .prose *,
    .markdown-body,
    .markdown-body *,
    #component-0 .prose,
    [class*="description"] {
        color: #ede9ff !important;
        font-weight: 500 !important;
    }

    .prose strong,
    .markdown-body strong {
        color: #a78bfa !important;
        font-weight: 700 !important;
    }

    .prose em,
    .markdown-body em {
        color: #c4bdff !important;
        font-weight: 500 !important;
    }
    
    /* ============================================
       PROGRESS BAR
       ============================================ */
    .progress-bar-wrap {
        border-radius: 10px !important;
        overflow: hidden !important;
        background: #171340 !important;
    }

    .progress-bar {
        border-radius: 10px !important;
        background: #7c5cff !important;
    }
    
    /* ============================================
       TYPOGRAPHY
       ============================================ */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 700 !important;
    }
    
    /* ============================================
       GLOBAL OVERRIDES
       ============================================ */
    * {
        box-shadow: none !important;
    }
    
    footer {
        visibility: hidden;
    }
"""