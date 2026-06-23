from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from transformers import pipeline
import torch

print("Loading Hugging Face model (Qwen2.5-1.5B-Instruct)...")
try:
    device_id = 0 if torch.cuda.is_available() else -1
    hf_pipeline = pipeline(
        "text-generation",
        model="Qwen/Qwen2.5-1.5B-Instruct",
        device=device_id,
        torch_dtype=torch.float32 if device_id == -1 else torch.bfloat16
    )
    print("Hugging Face model loaded successfully.")
except Exception as e:
    print(f"Error loading Hugging Face model: {e}")
    hf_pipeline = None

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
        messages = [
            {"role": "system", "content": "You are a helpful academic assistant."},
            {"role": "user", "content": prompt}
        ]
        response = hf_pipeline(messages, max_new_tokens=1024)
        response_text = response[0]["generated_text"][-1]["content"].strip()

        print("\nBot:")
        print(response_text)
        print()

    except Exception as e:

        print("\nError:")
        print(e)
        print()