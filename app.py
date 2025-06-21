import streamlit as st
import requests
import json

# --- Configuration ---
PROD_FASTAPI_BASE_URL = "https://xv2cgtswgvavjpk5majlqxur5m.srv.us"
DEV_FASTAPI_BASE_URL = "http://localhost:8000" # Standard local development port

# The actual FASTAPI_BASE_URL will be set dynamically based on the environment selection later in the script,
# after st.session_state.environment is confirmed.
FASTAPI_BASE_URL = "" # Initialize, will be overwritten
CHAT_ENDPOINT = "" # Initialize, will be overwritten


st.set_page_config(page_title="ChatLegis Demo", page_icon="⚖️", layout="wide")

# --- Environment Selector ---
st.sidebar.title("Environment")
current_environment = st.sidebar.selectbox(
    "Choose an environment:",
    ("Production", "Development"),
    key="environment_selection" # Using a key to ensure it's treated distinctly
)

if "environment" not in st.session_state:
    st.session_state.environment = "Production" # Default

# Update session state if selection changes
if st.session_state.environment_selection: # Check if the selectbox has a value
    st.session_state.environment = st.session_state.environment_selection

# --- Dynamically set API endpoints based on environment ---
if st.session_state.environment == "Development":
    FASTAPI_BASE_URL = DEV_FASTAPI_BASE_URL
else: # Default to Production
    FASTAPI_BASE_URL = PROD_FASTAPI_BASE_URL

CHAT_ENDPOINT = f"{FASTAPI_BASE_URL}/api/v1/chatlegis/chat"


st.title("⚖️ ChatLegis Demo")
st.caption(f"AI Assistant for Pakistani Law (Environment: {st.session_state.environment}, API: {FASTAPI_BASE_URL})")


# --- Function to display production chat interface ---
def show_production_chat():
    # --- Initialize session state ---
    # We only need to store the conversation_id and the display messages
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = None

    # --- Display existing messages ---
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # --- Handle user input ---
    if prompt := st.chat_input("Ask ChatLegis about Pakistani Law..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Prepare data for FastAPI request - NO MORE HISTORY
        request_data = {
            "prompt": prompt,
            "role": "user", # The Streamlit app is always the user
            "conversation_id": st.session_state.conversation_id
        }

        with st.chat_message("assistant"):
            with st.spinner("ChatLegis is thinking..."):
                try:
                    response = requests.post(CHAT_ENDPOINT, json=request_data, timeout=120)
                    response.raise_for_status()
                    response_data = response.json()

                    # Get the reply and the conversation_id from the response
                    assistant_reply = response_data.get("ai_response", "Sorry, I couldn't get a reply.")
                    # Store the conversation_id for the next request
                    st.session_state.conversation_id = response_data.get("conversation_id")

                except requests.exceptions.RequestException as e:
                    st.error(f"Error connecting to backend: {e}")
                    assistant_reply = "Error: Could not connect to the ChatLegis service."
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")
                    assistant_reply = "An unexpected error occurred."

            st.markdown(assistant_reply)

        # Add assistant reply to the display history
        st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

# --- Main App Logic ---
show_production_chat()


# --- Development Features Placeholder ---
if st.session_state.environment == "Development":
    st.sidebar.markdown("---") # Separator in sidebar
    st.sidebar.header("🚧 Development Features 🚧")
    st.sidebar.info("New features like Multichat will appear here once implemented.")

    # You could also add placeholders in the main app area if needed
    # st.markdown("---")
    # st.header("🚧 Development Area 🚧")
    # st.info("This section is visible only in the Development environment.")