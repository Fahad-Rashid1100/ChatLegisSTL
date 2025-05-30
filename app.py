import streamlit as st
import requests # To call the FastAPI backend
import json

# --- Configuration ---
FASTAPI_BASE_URL = "https://qbkvnx6f75rram62xlxegiuv5q.srv.us"  # Your FastAPI backend URL
CHAT_ENDPOINT = f"{FASTAPI_BASE_URL}/api/v1/chatlegis/chat"

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="ChatLegis Demo",
    page_icon="⚖️",
    layout="wide"
)

# --- App Header ---
st.title("⚖️ ChatLegis Demo")
st.caption("AI Assistant for Pakistani Law - Powered by Gemini with Google Search Grounding")

# --- Initialize chat history in session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "fastapi_history" not in st.session_state: # Separate history for FastAPI format
    st.session_state.fastapi_history = []


# --- Display existing messages ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Handle user input ---
if prompt := st.chat_input("Ask ChatLegis about Pakistani Law..."):
    # Add user message to Streamlit chat display
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare data for FastAPI request
    request_data = {
        "message": prompt,
        "history": st.session_state.fastapi_history # Send history in FastAPI format
    }

    # Display a thinking indicator
    with st.chat_message("assistant"):
        with st.spinner("ChatLegis is thinking..."):
            try:
                response = requests.post(CHAT_ENDPOINT, json=request_data, timeout=120) # Increased timeout
                response.raise_for_status()  # Raise an exception for bad status codes
                
                response_data = response.json()
                assistant_reply = response_data.get("reply", "Sorry, I couldn't get a reply.")

            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to backend: {e}")
                assistant_reply = "Error: Could not connect to the ChatLegis service."
            except json.JSONDecodeError:
                st.error("Error: Invalid response from backend.")
                assistant_reply = "Error: Received an invalid response from the service."
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
                assistant_reply = "An unexpected error occurred."
        
        st.markdown(assistant_reply)

    # Add assistant reply to Streamlit chat display
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
    
    # Update FastAPI history (important for context in subsequent calls)
    st.session_state.fastapi_history.append({"role": "user", "text": prompt})
    st.session_state.fastapi_history.append({"role": "model", "text": assistant_reply})

    # Keep history to a reasonable length (e.g., last 10 messages for FastAPI context)
    MAX_HISTORY_LEN = 10 # 5 pairs of user/model messages
    if len(st.session_state.fastapi_history) > MAX_HISTORY_LEN:
        st.session_state.fastapi_history = st.session_state.fastapi_history[-MAX_HISTORY_LEN:]