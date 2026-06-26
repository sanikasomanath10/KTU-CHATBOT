from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

print("Initializing Gemini Client...")
if not os.environ.get("GEMINI_API_KEY"):
    print("WARNING: GEMINI_API_KEY environment variable is not set! Please configure it in a .env file.")
try:
    client = genai.Client()
    print("Gemini client initialized successfully.")
except Exception as e:
    print(f"Error initializing Gemini client: {e}")
    client = None

# ==========================
# LOAD EMBEDDING MODEL
# ==========================
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# ==========================
# LOAD VECTOR DATABASE
# ==========================
vector_store = FAISS.load_local(
    "vector_db",
    embeddings,
    allow_dangerous_deserialization=True
)

print("\nIndustrial Safety RAG Chatbot Started!")
print("Type 'exit' to quit.\n")

while True:

    question = input("You: ")

    if question.lower() == "exit":
        print("Goodbye!")
        break

    # Retrieve relevant chunks
    docs = vector_store.similarity_search(
        question,
        k=5
    )

    # Combine retrieved text
    context = "\n\n".join(
        doc.page_content for doc in docs
    )

    # Debug (optional)
    print("\nRetrieved Documents:", len(docs))

    prompt = f"""
You are an Industrial Safety Engineering Assistant.

Use the provided notes to answer the user's question.

NOTES:
{context}

QUESTION:
{question}

RULES:
1. Answer the question strictly based on the provided NOTES. Do not assume, extrapolate, or use outside knowledge.
2. If the answer is not found in the NOTES, you MUST say exactly "not found in the textbook." and nothing else.
3. Keep the answer clear, concise, and direct.

ANSWER:
"""

    try:
        if not client:
            raise Exception("Gemini client is not initialized.")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"System: You are a helpful academic assistant.\nUser: {prompt}"
        )
        response_text = response.text.strip()

        print("\nBot:")
        print(response_text)
        print()

    except Exception as e:

        print("\nError:")
        print(e)
        print()