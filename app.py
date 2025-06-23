import streamlit as st
import requests
import json

# --- Configuration ---
# Set the Production URL as the only base URL
# Replace this with your actual deployed backend URL
FASTAPI_BASE_URL = "https://xv2cgtswgvavjpk5majlqxur5m.srv.us" 
CHAT_ENDPOINT = f"{FASTAPI_BASE_URL}/api/v1/chatlegis/chat"

# The categories for our new production feature
DOCUMENT_CATEGORIES = ["General", "Statutes", "Judgements", "Contracts", "Suits"]

# --- Page Setup ---
st.set_page_config(
    page_title="ChatLegis",
    page_icon="⚖️",
    layout="centered" # Centered layout is often cleaner for chat apps
)

# --- App Header ---
st.title("⚖️ ChatLegis")
st.caption("Your AI Assistant for Pakistani Law")

# --- Initialize Session State ---
# We need to store messages, conversation_id, and the selected category
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "document_category" not in st.session_state:
    st.session_state.document_category = "General" # Default to General focus

# --- Sidebar for Scope Selection ---
st.sidebar.title("Research Focus")
st.sidebar.info(
    "Select a specific legal category to focus the AI's research, or use 'General' "
    "to allow the AI to search across all available knowledge bases."
)

# The selectbox now directly controls the session state for the category
st.sidebar.selectbox(
    "Select Document Category:",
    options=DOCUMENT_CATEGORIES,
    key="document_category", # This key maps directly to st.session_state.document_category
)

st.sidebar.markdown("---")
# You can add more info or links in the sidebar later
# st.sidebar.write("About ChatLegis...")


# --- Display Chat History ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Chat Input Logic ---
# Construct a dynamic placeholder for the chat input
chat_input_placeholder = "Ask about Pakistani Law..."
if st.session_state.document_category != "General":
    chat_input_placeholder += f" (Focus: {st.session_state.document_category})"

# The main chat input field
if prompt := st.chat_input(chat_input_placeholder):
    # Display user message immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare data for the API request
    # This now correctly includes the selected document_category
    scope_to_send = st.session_state.document_category if st.session_state.document_category != "General" else None
    
    request_data = {
        "prompt": prompt,
        "role": "user",
        "conversation_id": st.session_state.conversation_id,
        "document_category": scope_to_send
    }

    # Show a spinner while waiting for the backend response
    with st.chat_message("assistant"):
        with st.spinner("ChatLegis is thinking..."):
            try:
                response = requests.post(CHAT_ENDPOINT, json=request_data, timeout=120)
                response.raise_for_status() # Raise an error for bad status codes (4xx or 5xx)
                response_data = response.json()

                # Parse the response from the backend
                assistant_reply = response_data.get("ai_response", "Sorry, I could not get a reply.")
                # IMPORTANT: Update the conversation_id for the next request
                st.session_state.conversation_id = response_data.get("conversation_id")

            except requests.exceptions.RequestException as e:
                st.error(f"Connection Error: Could not connect to the ChatLegis service. Please check if the backend is running.")
                assistant_reply = "Error: Could not connect to the backend."
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
                assistant_reply = "An unexpected error occurred."

        st.markdown(assistant_reply)

    # Add the AI's response to the message history for display
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})