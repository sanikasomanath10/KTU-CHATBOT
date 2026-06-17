from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vector_store = FAISS.load_local(
    "vector_db",
    embeddings,
    allow_dangerous_deserialization=True
)

question = input("Ask a question: ")

results = vector_store.similarity_search(question, k=3)

print("\nTop Relevant Chunks:\n")

for i, doc in enumerate(results, start=1):
    print(f"\n----- Result {i} -----\n")
    print(doc.page_content)
