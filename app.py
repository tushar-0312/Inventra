"""
============================================================================
INVENTRA - Streamlit Web Application
============================================================================

This is the main entry point for the Inventra web interface.
It provides a conversational chat UI for interacting with the multi-agent
inventory management system.

FEATURES:
---------
- Chat interface for natural language queries
- Region selection for weather forecasts
- Conversation history display
- Real-time agent activity indicators

USAGE:
------
    streamlit run app.py

============================================================================
"""

import os
import sys
from pathlib import Path

import streamlit as st

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="Inventra - Smart Inventory Management",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =============================================================================
# CUSTOM STYLING
# =============================================================================

st.markdown("""
<style>
    /* Main container styling */
    .main {
        background-color: #0E1117;
    }
    
    /* Chat message styling */
    .stChatMessage {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 0.5rem;
    }
    
    /* Agent tag styling */
    .agent-tag {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: bold;
        margin-right: 8px;
    }
    
    .agent-data {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
    }
    
    .agent-weather {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
    }
    
    .agent-decision {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #1E1E1E;
    }
    
    /* Header styling */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    .header-title {
        color: white;
        font-size: 2rem;
        font-weight: bold;
        margin: 0;
    }
    
    .header-subtitle {
        color: rgba(255,255,255,0.8);
        font-size: 1rem;
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# INITIALIZATION
# =============================================================================

def initialize_session():
    """Initialize session state variables."""
    
    # Chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Graph instance
    if "graph" not in st.session_state:
        try:
            from agents.graph import build_graph
            st.session_state.graph = build_graph(use_memory=False)
            st.session_state.graph_ready = True
        except Exception as e:
            st.session_state.graph = None
            st.session_state.graph_ready = False
            st.session_state.graph_error = str(e)
    
    # Thread ID for conversation memory
    if "thread_id" not in st.session_state:
        import uuid
        st.session_state.thread_id = str(uuid.uuid4())[:8]
    
    # Selected region
    if "region" not in st.session_state:
        st.session_state.region = "mumbai"


def check_api_key():
    """Check if Google API key is configured."""
    api_key = os.getenv("GOOGLE_API_KEY")
    return api_key and api_key != "your_google_api_key_here"


# =============================================================================
# SIDEBAR
# =============================================================================

def render_sidebar():
    """Render the sidebar with settings and info."""
    
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        
        # Region selection
        st.session_state.region = st.selectbox(
            "📍 Default Region",
            ["mumbai", "delhi", "bengaluru"],
            index=0,
            help="Select region for weather forecasts"
        )
        
        st.divider()
        
        # Quick actions
        st.markdown("## 🚀 Quick Actions")
        
        if st.button("📊 Check Low Stock", use_container_width=True):
            add_query("What items are low on stock?")
        
        if st.button("🌧️ Weather Impact", use_container_width=True):
            add_query(f"How will weather affect sales in {st.session_state.region}?")
        
        if st.button("📦 Reorder Recommendations", use_container_width=True):
            add_query("Generate reorder recommendations for next week")
        
        st.divider()
        
        # Info panel
        st.markdown("## ℹ️ About")
        st.markdown("""
        **Inventra** is an AI-powered inventory 
        management system that uses multiple 
        agents to:
        
        - 📊 Analyze inventory levels
        - 🌤️ Forecast weather impact
        - 🎯 Make smart decisions
        - 🎫 Generate action tickets
        """)
        
        st.divider()
        
        # Clear chat button
        if st.button("🗑️ Clear Chat", use_container_width=True, type="secondary"):
            st.session_state.messages = []
            st.rerun()


def add_query(query: str):
    """Add a query to the chat."""
    st.session_state.pending_query = query


# =============================================================================
# CHAT INTERFACE
# =============================================================================

def render_header():
    """Render the application header."""
    
    st.markdown("""
    <div class="header-container">
        <p class="header-title">📦 Inventra</p>
        <p class="header-subtitle">AI-Powered Smart Inventory Management System</p>
    </div>
    """, unsafe_allow_html=True)


def format_agent_response(content: str) -> str:
    """
    Format agent response with proper styling.
    
    Extracts agent name and applies appropriate tag.
    """
    # Check if response has agent prefix
    if content.startswith("[Data Agent]"):
        tag = '<span class="agent-tag agent-data">DATA AGENT</span>'
        content = content.replace("[Data Agent]", "", 1).strip()
    elif content.startswith("[Weather Agent]"):
        tag = '<span class="agent-tag agent-weather">WEATHER AGENT</span>'
        content = content.replace("[Weather Agent]", "", 1).strip()
    elif content.startswith("[Decision Agent]"):
        tag = '<span class="agent-tag agent-decision">DECISION AGENT</span>'
        content = content.replace("[Decision Agent]", "", 1).strip()
    else:
        tag = ""
    
    return f"{tag}\n\n{content}"


def process_query(query: str):
    """
    Process a user query through the multi-agent system.
    
    Args:
        query: User's natural language query
    """
    from agents.graph import run_query, get_final_response
    from langchain_core.messages import HumanMessage, AIMessage
    
    # Run the query
    result = run_query(
        st.session_state.graph,
        query,
        thread_id=st.session_state.thread_id,
        region=st.session_state.region
    )
    
    # Extract and return the response
    if result.get("error"):
        return f"❌ Error: {result['error']}"
    
    # Compile all agent responses
    response_parts = []
    messages = result.get("messages", [])
    
    for msg in messages:
        if hasattr(msg, "content") and msg.content:
            if isinstance(msg, AIMessage):
                response_parts.append(msg.content)
    
    return "\n\n---\n\n".join(response_parts) if response_parts else "No response generated."


def render_chat():
    """Render the main chat interface."""
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                # Format agent responses
                formatted = format_agent_response(message["content"])
                st.markdown(formatted, unsafe_allow_html=True)
            else:
                st.markdown(message["content"])
    
    # Check for pending query from sidebar
    if hasattr(st.session_state, "pending_query") and st.session_state.pending_query:
        query = st.session_state.pending_query
        st.session_state.pending_query = None
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": query})
        
        # Process and add response
        with st.spinner("🤖 Agents analyzing your query..."):
            response = process_query(query)
            st.session_state.messages.append({"role": "assistant", "content": response})
        
        st.rerun()
    
    # Chat input
    if query := st.chat_input("Ask about your inventory, weather impact, or recommendations..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": query})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(query)
        
        # Process query
        with st.chat_message("assistant"):
            with st.spinner("🤖 Agents analyzing your query..."):
                response = process_query(query)
                formatted = format_agent_response(response)
                st.markdown(formatted, unsafe_allow_html=True)
                
                # Add to history
                st.session_state.messages.append({"role": "assistant", "content": response})


# =============================================================================
# MAIN APP
# =============================================================================

def main():
    """Main application entry point."""
    
    # Initialize session
    initialize_session()
    
    # Render sidebar
    render_sidebar()
    
    # Render header
    render_header()
    
    # Check API key
    if not check_api_key():
        st.error("""
        ⚠️ **Google API Key Not Configured**
        
        Please create a `.env` file in the project root with:
        ```
        GOOGLE_API_KEY=your_actual_api_key
        ```
        
        Get your API key from: https://aistudio.google.com/apikey
        """)
        return
    
    # Check graph status
    if not st.session_state.graph_ready:
        st.error(f"""
        ⚠️ **Graph Build Error**
        
        Error: {st.session_state.get('graph_error', 'Unknown error')}
        
        Please check the console for details.
        """)
        return
    
    # Render chat interface
    render_chat()


if __name__ == "__main__":
    main()
