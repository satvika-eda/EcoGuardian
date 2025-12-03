"""
EcoGuardian - Streamlit App
Same UI, cleaned backend (ADK + async + caching fixed)
"""

from pathlib import Path
import streamlit as st
import asyncio
import time
from datetime import datetime
from typing import Dict
from google.genai import types

# ============================================================================
# CONFIGURATION
# ============================================================================
APP_NAME = "EcoGuardian"
DB_FILE = "/tmp/ecoguardian_sessions.db"
DB_URL = f"sqlite+aiosqlite:///{DB_FILE}"

# ============================================================================
# GLOBAL EVENT LOOP (no asyncio.run anywhere)
# ============================================================================
try:
    GLOBAL_LOOP = asyncio.get_running_loop()
except RuntimeError:
    GLOBAL_LOOP = asyncio.new_event_loop()
    asyncio.set_event_loop(GLOBAL_LOOP)


def run_in_loop(coro):
    """Run any coroutine on a single global event loop."""
    return GLOBAL_LOOP.run_until_complete(coro)

# ============================================================================
# RUNNER INITIALIZATION
# ============================================================================
@st.cache_resource
def initialize_runner():

    from google.adk.runners import Runner
    from google.adk.memory import InMemoryMemoryService
    from google.adk.plugins.logging_plugin import LoggingPlugin
    from google.adk.sessions import DatabaseSessionService

    from agent import root_agent

    session_service = DatabaseSessionService(db_url=DB_URL)
    memory_service = InMemoryMemoryService()
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
        memory_service=memory_service,
        plugins=[LoggingPlugin()],
    )
    return runner, session_service, memory_service


def get_adk():
    if "adk_runner" not in st.session_state:
        st.session_state.adk_runner, st.session_state.session_service, st.session_state.memory_service = initialize_runner()
    return (
        st.session_state.adk_runner,
        st.session_state.session_service,
        st.session_state.memory_service
    )


# ============================================================================
# SESSION & AGENT HELPERS
# ============================================================================
def ensure_session_exists(user_id: str, session_id: str):
    # sourcery skip: use-contextlib-suppress
    """Ensure session exists in database for this user/session."""
    runner, session_service, memory_service = get_adk()


    async def _create():
        try:
            await session_service.create_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=session_id,
            )
        except Exception:
            # Already exists or benign error
            pass

    return run_in_loop(_create())


async def ask_agent_async(query: str, user_id: str, session_id: str) -> str:
    """Send query to agent through Runner and return final text."""
    query_content = types.Content(role="user", parts=[types.Part(text=query)])
    runner, session_service, memory_service = get_adk()

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=query_content,
        state_delta={"city": st.session_state.selected_city},
    ):
        if event.is_final_response() and event.content:
            return event.content.parts[0].text

    return ""


def agent_call(query: str) -> str:
    """Synchronous wrapper - reuses user's ADK session."""
    user_id = st.session_state.user_id
    session_id = st.session_state.adk_session_id

    runner, session_service, memory_service = get_adk()

    ensure_session_exists(user_id, session_id)
    return run_in_loop(ask_agent_async(query, user_id, session_id))


def card(title: str, body: str, icon: str, color: str):
    """Render a styled info card (your original gradient style)."""
    st.markdown(
        f"""
        <div style="
            padding: 20px;
            border-radius: 15px;
            background: linear-gradient(135deg, {color} 0%, {color}dd 100%);
            color: white;
            margin-bottom: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            ">
            <div style="font-size: 26px; font-weight: 700; margin-bottom: 10px;">
                {icon} {title}
            </div>
            <div style="font-size: 16px; line-height: 1.6; opacity: 0.95;">
                {body}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="EcoGuardian - Environmental Intelligence",
    layout="wide",
    page_icon="🌿",
    initial_sidebar_state="expanded",
)

# Custom CSS – same visuals as your original
st.markdown(
    """
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    div[data-testid="stChatMessage"],
    div[data-testid="stChatMessageContent"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    /* Fixed chat input at bottom */
    div[data-testid="stChatInput"] {
        position: fixed !important;
        bottom: 20px !important;
        left: 260px !important;
        right: 20px !important;
        z-index: 9999 !important;
        background: white !important;
        padding: 10px !important;
        border-radius: 10px !important;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1) !important;
    }
    
    [data-testid="stVerticalBlock"] > div:nth-child(3) .block-container {
        padding-bottom: 120px !important;
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    .stButton button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
    }
    
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
if "user_id" not in st.session_state:
    st.session_state.user_id = f"user_{int(time.time())}"

if "adk_session_id" not in st.session_state:
    st.session_state.adk_session_id = f"session_{int(time.time())}"

if "messages" not in st.session_state:
    st.session_state.messages = []

if "selected_city" not in st.session_state:
    st.session_state.selected_city = "Select a city"

if "env_data" not in st.session_state:
    st.session_state.env_data = {}

# ============================================================================
# SIDEBAR - SAME LAYOUT
# ============================================================================
with st.sidebar:
    st.markdown(
        """
        <div style="text-align: center; padding: 20px 0;">
            <h1 style="font-size: 2.5rem; margin: 0;">🌍</h1>
            <h2 style="margin: 10px 0;">EcoGuardian</h2>
            <p style="opacity: 0.8; font-size: 0.9rem;">AI-Powered Environmental Intelligence</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    st.divider()

    # City Selection
    st.subheader("📍 Location")
    cities = [
        "Select a city",
        "New York",
        "Boston",
        "Miami",
        "San Francisco",
        "Los Angeles",
        "Chicago",
        "Houston",
        "Seattle",
        "Dallas",
        "Austin",
        "Portland",
        "Denver",
    ]

    city = st.selectbox(
        "Choose a city",
        cities,
        key="city_selector",
        help="Select a city to view environmental data",
    )

    if city != st.session_state.selected_city:
        st.session_state.selected_city = city

    st.divider()

    # Session Management
    st.subheader("💬 Session")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 New", use_container_width=True):
            st.session_state.adk_session_id = f"session_{int(time.time())}"
            st.session_state.messages = []
            st.session_state.env_data = {}
            st.rerun()

    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    st.caption(f"Session: ...{st.session_state.adk_session_id[-8:]}")

    st.divider()

    # Stats
    st.subheader("📊 Stats")
    st.metric("Messages", len(st.session_state.messages))
    st.metric(
        "Session Time",
        f"{(time.time() - int(st.session_state.adk_session_id.split('_')[1]))//60:.0f}m",
    )

# ============================================================================
# MAIN HEADER
# ============================================================================
col1, col2 = st.columns([4, 1])
with col1:
    st.title("🌿 EcoGuardian")
    st.caption("Environmental Intelligence powered by AI")
with col2:
    st.markdown(
        f"""
        <div style="text-align: right; padding-top: 10px;">
            <div style="font-size: 0.8rem; opacity: 0.7;">
                {datetime.now().strftime('%b %d, %Y')}
            </div>
            <div style="font-size: 0.9rem; font-weight: 600;">
                {datetime.now().strftime('%I:%M %p')}
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

st.divider()

# ============================================================================
# WELCOME SCREEN
# ============================================================================
if city == "Select a city":
    st.markdown(
        """
        <div style="text-align: center; padding: 50px 0;">
            <h2 style="color: #667eea;">👋 Welcome to EcoGuardian</h2>
            <p style="font-size: 1.2rem; margin: 20px 0; opacity: 0.8;">
                Your AI-powered environmental and health intelligence platform
            </p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div style="padding: 30px; text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; color: white; margin: 10px;">
                <div style="font-size: 3rem;">🌤️</div>
                <h3>Environment</h3>
                <p>Real-time air quality, weather, pollen, and UV data</p>
            </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div style="padding: 30px; text-align: center; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 15px; color: white; margin: 10px;">
                <div style="font-size: 3rem;">🏥</div>
                <h3>Health</h3>
                <p>Disease outbreak tracking and symptom analysis</p>
            </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div style="padding: 30px; text-align: center; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 15px; color: white; margin: 10px;">
                <div style="font-size: 3rem;">🌱</div>
                <h3>Events</h3>
                <p>Discover local eco-friendly activities</p>
            </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div style="text-align: center; margin-top: 50px;">
            <h3 style="color: #667eea;">👈 Select a city from the sidebar to get started</h3>
        </div>
    """,
        unsafe_allow_html=True,
    )

    st.stop()

# ============================================================================
# ENVIRONMENT DATA LOADING (SYNC, CACHED, NO ASYNCIO.RUN)
# ============================================================================
@st.cache_data(show_spinner=False, ttl=3600)
def load_environment_data(city_name: str, user_id: str, session_id: str) -> Dict[str, str]:
    """Fetch environment data using the user's ADK session (sync via run_in_loop)."""
    queries = {
        "air": f"Summarize air quality in {city_name} in 3-4 concise lines.",
        "weather": f"Summarize current weather in {city_name}. Be concise.",
        "pollen": f"What is the pollen level in {city_name}? Keep it short.",
        "uv": f"What is the UV index in {city_name}? Explain briefly.",
        "events": f"List 3-5 upcoming environmental or sustainability events in {city_name}. Be specific with dates if available.",
    }

    results: Dict[str, str] = {
        key: run_in_loop(ask_agent_async(q, user_id, session_id))
        for key, q in queries.items()
    }
    return results


# Ensure main session exists once before loading env data
ensure_session_exists(st.session_state.user_id, st.session_state.adk_session_id)

with st.spinner(f"🔄 Loading environment data for {city}..."):
    env_data = load_environment_data(
        city,
        st.session_state.user_id,
        st.session_state.adk_session_id,
    )
    st.session_state.env_data = env_data

# ============================================================================
# TABS
# ============================================================================
tab_env, tab_events, tab_health, tab_chat = st.tabs(
    ["🌦️ Environment", "🌱 Events", "🏥 Health", "💬 Chat"]
)

# ============================================================================
# TAB 1: ENVIRONMENT DASHBOARD
# ============================================================================
with tab_env:
    st.subheader(f"🌎 {city} — Environment Overview")
    st.markdown("---")

    # Metrics Row (same as original)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Data Source", "Real-time")
    with col2:
        st.metric("🔄 Updated", "Now")
    with col3:
        st.metric("📍 Location", city)
    with col4:
        st.metric("✅ Status", "Active")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        card("Air Quality", env_data["air"], "🌫️", "#6a8caf")
        card("Pollen Level", env_data["pollen"], "🌻", "#d4a700")
    with col2:
        card("Weather", env_data["weather"], "🌦️", "#4b8bbe")
        card("UV Index", env_data["uv"], "☀️", "#d9534f")

    st.markdown("---")
    if st.button("🔄 Refresh Data", use_container_width=False):
        st.cache_data.clear()
        st.session_state.env_data = {}
        st.rerun()

# ============================================================================
# TAB 2: LOCAL EVENTS
# ============================================================================
with tab_events:
    st.subheader(f"🌱 {city} — Environmental Events")
    st.markdown("---")

    st.markdown(
        f"""
        <div style="
            padding: 25px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            color: white;
            line-height: 1.8;">
            {env_data["events"]}
        </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    custom_event_query = st.text_input(
        "🔍 Search for specific events",
        placeholder="e.g., tree planting, sustainability workshops...",
    )

    if st.button("Search Events", use_container_width=False) and custom_event_query:
        with st.spinner("Searching..."):
            result = agent_call(
                f"Find {custom_event_query} events in {city}"
            )
            st.markdown(result)

# ============================================================================
# TAB 3: HEALTH INSIGHTS
# ============================================================================
with tab_health:
    st.subheader(f"🏥 {city} — Health Insights")
    st.markdown("---")

    health_option = st.radio(
        "What would you like to check?",
        [
            "🦠 Disease Outbreaks",
            "🤧 Symptom Analysis",
            "🏥 Find Hospitals",
        ],
        horizontal=True,
    )

    if health_option == "🦠 Disease Outbreaks":
        if st.button("Check Current Outbreaks", use_container_width=False):
            with st.spinner("Checking WHO/CDC data..."):
                result = agent_call(
                    f"Are there any disease outbreaks in {city}? Check WHO and CDC sources."
                )
                st.info(result)

    elif health_option == "🤧 Symptom Analysis":
        symptoms = st.text_area(
            "Describe your symptoms",
            placeholder="e.g., fever, cough, headache...",
        )
        if st.button("Analyze Symptoms", use_container_width=False) and symptoms:
            with st.spinner("Analyzing..."):
                result = agent_call(
                    f"I'm in {city} and have these symptoms: {symptoms}. "
                    "What should I do? Provide disease possibilities and recommendations."
                )
            st.warning(result)
            st.caption("⚠️ This is not medical advice. Consult a healthcare professional.")

    elif health_option == "🏥 Find Hospitals":
        if st.button("Find Nearest Hospitals", use_container_width=False):
            with st.spinner("Searching..."):
                result = agent_call(
                    f"Find the nearest hospitals in {city} with emergency services."
                )
                st.success(result)


# ============================================================================
# TAB 4: CHAT
# ============================================================================
with tab_chat:
    st.subheader(f"💬 Chat with EcoGuardian — {city}")
    st.markdown("---")

    if not st.session_state.messages:
        st.info(
            f"""
            👋 Hello! I'm EcoGuardian, your environmental and health intelligence assistant.
            
            Ask me about:
            - 🌤️ Air quality and weather in {city}
            - 🤧 Pollen levels and UV index
            - 🦠 Disease outbreaks and health alerts
            - 🏥 Symptom analysis and hospital locations
            - 🌱 Eco-friendly events and activities
            
            What would you like to know?
        """
        )

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if "quick_query" in st.session_state:
        user_msg = st.session_state.quick_query
        del st.session_state.quick_query
    else:
        user_msg = st.chat_input(f"Ask about {city}...")

    if user_msg:
        st.session_state.messages.append({"role": "user", "content": user_msg})
        with st.chat_message("user"):
            st.markdown(user_msg)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    reply = agent_call(user_msg)
                    st.markdown(reply)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": reply}
                    )
                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": error_msg}
                    )

# ============================================================================
# FOOTER - SAME AS ORIGINAL
# ============================================================================
st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.caption("🌍 EcoGuardian © 2025")
with footer_col2:
    st.caption(f"💬 Session: ...{st.session_state.adk_session_id[-8:]}")
with footer_col3:
    st.caption(f"⏰ {datetime.now().strftime('%I:%M %p')}")
