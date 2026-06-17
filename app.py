import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import google.generativeai as genai
import os
# ==========================
# PAGE SETTINGS
# ==========================
st.set_page_config(
    page_title="KTU Assistant",
    page_icon="🎓",
    layout="wide"
)

# ==========================
# GEMINI API KEY
# ==========================
genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
) 

model = genai.GenerativeModel("gemini-2.5-flash")

# ==========================
# LOAD EMBEDDINGS
# ==========================
@st.cache_resource
def load_vector_db():

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vector_store = FAISS.load_local(
        "vector_db",
        embeddings,
        allow_dangerous_deserialization=True
    )

    return vector_store

vector_store = load_vector_db()

# ==========================
# UI
# ==========================
st.title("🎓 KTU Assistant")
st.markdown("Ask questions from your PDF notes")

# Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display old messages
for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
question = st.chat_input("Ask a question...")

if question:

    # Show user message
    st.session_state.messages.append(
        {"role": "user", "content": question}
    )

    with st.chat_message("user"):
        st.markdown(question)

    with st.spinner("Searching notes..."):

        try:

            docs = vector_store.similarity_search(
                question,
                k=5
            )

            context = "\n\n".join(
                doc.page_content for doc in docs
            )

            prompt = f"""
You are an Industrial Safety Engineering Assistant.

Use the provided notes to answer the user's question.

NOTES:
{context}

QUESTION:
{question}

RULES:
1. Answer only from the notes.
2. If related information exists, use it to form the answer.
3. Keep the answer clear and concise.
4. Only say "I could not find the answer in the notes" if absolutely nothing relevant is present.

ANSWER:
"""

            response = model.generate_content(prompt)

            answer = response.text

        except Exception as e:

            answer = f"Error: {e}"

    with st.chat_message("assistant"):
        st.markdown(answer)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )

# Sidebar
with st.sidebar:

    st.header("KTU Assistant")

    if st.button("Clear Chat"):

        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.write("Industrial Safety Notes Chatbot")