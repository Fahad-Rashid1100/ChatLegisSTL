import streamlit as st
import requests
import json
import io
from st_audiorec import st_audiorec

# --- Configuration ---
FASTAPI_BASE_URL = "https://xv2cgtswgvavjpk5majlqxur5m.srv.us" # Using dev port for testing
CHAT_ENDPOINT = f"{FASTAPI_BASE_URL}/api/v1/chatlegis/chat"
DOCUMENT_CATEGORIES = ["General", "Statutes", "Judgements", "Contracts", "Suits"]

st.set_page_config(page_title="ChatLegis", page_icon="⚖️", layout="centered")
st.title("⚖️ ChatLegis")
st.caption("Your AI Assistant for Pakistani Law")

# --- Initialize Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "document_category" not in st.session_state:
    st.session_state.document_category = "General"
if "audio_data" not in st.session_state:
    st.session_state.audio_data = None

# --- Central function for backend communication ---
def send_chat_request(prompt_text, file_data=None, file_name=None):
    with st.chat_message("assistant"):
        with st.spinner("ChatLegis is thinking..."):
            try:
                scope_to_send = st.session_state.document_category if st.session_state.document_category != "General" else None
                data = {
                    "prompt": prompt_text,
                    "role": "user",
                    "conversation_id": st.session_state.conversation_id,
                    "document_category": scope_to_send
                }
                files = {'file': (file_name, file_data, 'application/octet-stream')} if file_data else None

                response = requests.post(CHAT_ENDPOINT, data=data, files=files, timeout=180)
                response.raise_for_status()
                response_data = response.json()

                assistant_reply = response_data.get("ai_response", "Sorry, I couldn't get a reply.")
                st.session_state.conversation_id = response_data.get("conversation_id")
            except requests.exceptions.RequestException as e:
                st.error(f"Connection Error: Could not connect to the backend.")
                assistant_reply = "Error: Could not connect to the ChatLegis service."
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
                assistant_reply = "An unexpected error occurred."
        st.markdown(assistant_reply)
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

# --- Sidebar UI ---
with st.sidebar:
    st.title("Research Focus")
    st.sidebar.selectbox("Select Document Category:", options=DOCUMENT_CATEGORIES, key="document_category")
    st.markdown("---")
    st.header("Upload a Document")
    uploaded_file = st.file_uploader(
        "Upload a document to ask questions about it",
        type=['pdf', 'png', 'jpg', 'jpeg', 'wav'],
        key="file_upload_widget"
    )
    st.markdown("---")
    st.header("Record Audio")
    wav_audio_data = st_audiorec()

    # Check for a new, valid audio recording
    if wav_audio_data is not None and len(wav_audio_data) > 1000:
        # If there's a new recording, save it to the session state
        st.session_state.audio_data = wav_audio_data
        # DO NOT call st.rerun() here, as it will cause a loop.
        # The script will continue and render the buttons below naturally.

# --- Main Chat Interface ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Audio Handling Logic ---
if st.session_state.audio_data is not None:
    st.info("You have a recorded audio clip. You can send it or clear it.")
    st.audio(st.session_state.audio_data, format='audio/wav')

    col1, col2, _ = st.columns([1, 1, 2])

    with col1:
        if st.button("▶️ Send Audio"):
            st.session_state.messages.append({"role": "user", "content": "[User sent an audio recording]"})
            with st.chat_message("user"):
                st.audio(st.session_state.audio_data, format='audio/wav')

            with st.spinner("Transcribing and sending audio... Please wait."):
                send_chat_request(
                    prompt_text="Please transcribe the following audio and provide a detailed answer to the user's question.",
                    file_data=st.session_state.audio_data,
                    file_name="user_audio.wav"
                )

            st.session_state.audio_data = None
            st.rerun()

    with col2:
        if st.button("🗑️ Clear Recording"):
            st.session_state.audio_data = None
            st.rerun()

# --- Chat Input for Text ---
chat_input_placeholder = "Ask about Pakistani Law..."
if st.session_state.document_category != "General":
    chat_input_placeholder += f" (Focus: {st.session_state.document_category})"

if prompt := st.chat_input(chat_input_placeholder, disabled=(st.session_state.audio_data is not None)):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    file_to_send = None
    file_name_to_send = None
    if uploaded_file is not None:
        file_to_send = uploaded_file.getvalue()
        file_name_to_send = uploaded_file.name
        st.info(f"Attaching file: `{file_name_to_send}`")

    send_chat_request(
        prompt_text=prompt,
        file_data=file_to_send,
        file_name=file_name_to_send
    )