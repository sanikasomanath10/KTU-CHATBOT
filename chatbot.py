from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import google.generativeai as genai
import os
# ==========================
# GEMINI API KEY
# ==========================
genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

# Gemini Model
model = genai.GenerativeModel("gemini-2.5-flash")

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
1. Answer only from the notes.
2. If related information exists, use it to form the answer.
3. Keep the answer clear and concise.
4. Only say "I could not find the answer in the notes" if absolutely nothing relevant is present.

ANSWER:
"""

    try:

        response = model.generate_content(prompt)

        print("\nBot:")
        print(response.text)
        print()

    except Exception as e:

        print("\nError:")
        print(e)
        print()