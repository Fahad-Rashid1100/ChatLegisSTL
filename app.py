import streamlit as st
import requests

# --- Configuration ---
FASTAPI_BASE_URL = "https://xv2cgtswgvavjpk5majlqxur5m.srv.us"
API_V1_STR = "/api/v1"
CHAT_ENDPOINT = f"{FASTAPI_BASE_URL}{API_V1_STR}/chatlegis/chat"
CONVERSATIONS_ENDPOINT = f"{FASTAPI_BASE_URL}{API_V1_STR}/chatlegis/conversations"
HISTORY_ENDPOINT = f"{FASTAPI_BASE_URL}{API_V1_STR}/chatlegis/history"
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
if "jwt_token" not in st.session_state:
    st.session_state.jwt_token = None
if "conversation_list" not in st.session_state:
    st.session_state.conversation_list = []

# --- Helper Functions ---
def get_auth_header():
    if not st.session_state.jwt_token:
        st.error("Authentication token not set. Please add your token in the sidebar.")
        return None
    return {"Authorization": f"Bearer {st.session_state.jwt_token}"}

def clear_chat():
    st.session_state.messages = []
    st.session_state.conversation_id = None

def load_conversation(convo_id):
    headers = get_auth_header()
    if not headers: return
    try:
        response = requests.get(f"{HISTORY_ENDPOINT}/{convo_id}", headers=headers)
        response.raise_for_status()
        # The history from backend doesn't have the streamlit 'content' key
        # We need to remap 'parts' to 'content' for display
        messages = []
        for msg in response.json():
            content = msg.get("parts", [{}])[0].get("text", "[message not found]")
            messages.append({"role": msg["role"], "content": content})
        st.session_state.messages = messages
        st.session_state.conversation_id = convo_id
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to load conversation: {e}")

# --- Sidebar UI ---
with st.sidebar:
    st.title("User Settings")
    
    st.header("Authentication")
    jwt_input = st.text_input("Enter your JWT Token", type="password", value=st.session_state.jwt_token or "")
    if jwt_input:
        st.session_state.jwt_token = jwt_input

    st.markdown("---")
    
    if st.session_state.jwt_token:
        st.header("Conversation History")
        if st.button("New Chat"):
            clear_chat()
            st.rerun()

        try:
            conv_response = requests.get(CONVERSATIONS_ENDPOINT, headers=get_auth_header())
            if conv_response.status_code == 200:
                st.session_state.conversation_list = conv_response.json()
        except requests.exceptions.RequestException:
            st.error("Could not fetch history.")

        for convo in st.session_state.conversation_list:
            if st.button(convo['title'], key=convo['id'], use_container_width=True):
                load_conversation(convo['id'])
                st.rerun()
                
    st.markdown("---")
    st.title("Research Focus")
    st.selectbox("Select Document Category:", options=DOCUMENT_CATEGORIES, key="document_category")
    st.markdown("---")
    st.header("Upload a Document")
    uploaded_file = st.file_uploader("Upload a document", type=['pdf', 'png', 'jpg', 'jpeg'])

# --- Main Chat Interface ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def send_chat_request(prompt_text, file_data=None, file_name=None):
    headers = get_auth_header()
    if not headers: return

    with st.chat_message("assistant"):
        with st.spinner("ChatLegis is thinking..."):
            scope_to_send = st.session_state.document_category if st.session_state.document_category != "General" else None
            data = {
                "prompt": prompt_text,
                "conversation_id": st.session_state.conversation_id,
                "document_category": scope_to_send
            }
            files = {'file': (file_name, file_data, 'application/octet-stream')} if file_data else None

            try:
                response = requests.post(CHAT_ENDPOINT, data=data, files=files, headers=headers, timeout=180)
                response.raise_for_status()
                response_data = response.json()
                assistant_reply = response_data.get("ai_response", "Sorry, I couldn't get a reply.")
                st.session_state.conversation_id = response_data.get("conversation_id")
            except requests.exceptions.HTTPError as e:
                st.error(f"Error from server: {e.response.status_code} - {e.response.text}")
                assistant_reply = "An error occurred while communicating with the service."
            except requests.exceptions.RequestException as e:
                st.error(f"Connection Error: Could not connect to the backend: {e}")
                assistant_reply = "Error: Could not connect to the ChatLegis service."
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
                assistant_reply = "An unexpected error occurred."
        
        st.markdown(assistant_reply)
        st.session_state.messages.append({"role": "assistant", "content": assistant_reply})


# --- Chat Input ---
if prompt := st.chat_input("Ask about Pakistani Law..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    file_to_send, file_name_to_send = (None, None)
    if uploaded_file is not None:
        file_to_send = uploaded_file.getvalue()
        file_name_to_send = uploaded_file.name
        st.info(f"Attaching file: `{file_name_to_send}`")

    send_chat_request(
        prompt_text=prompt,
        file_data=file_to_send,
        file_name=file_name_to_send
    )
    # Clear the uploader after sending
    # This is a bit of a hack for Streamlit's file uploader state
    if uploaded_file:
        st.rerun()