import streamlit as st
from dotenv import load_dotenv
from backend.qa_chain import get_answer

# Load environment variables
load_dotenv()

# --- Page Configuration ---
st.set_page_config(page_title="MeitY Chatbot", layout="wide")
st.title("🤖 MeitY Knowledge Base Chatbot")
st.info("Ask a question about the documents provided in the knowledge base.")

# --- Session State Initialization ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Chat Interface ---
query = st.chat_input("Ask a question...")

if query:
    st.session_state.chat_history.append({"role": "user", "content": query})
    with st.spinner("Thinking..."):
        answer = get_answer(query)
        st.session_state.chat_history.append({"role": "assistant", "content": answer})

# --- Display Chat History ---
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])