from flask import Flask, render_template, request, jsonify
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import google.generativeai as genai
import os
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

def load_vector_db():
    print("Loading vector database...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    vector_store = FAISS.load_local(
        "vector_db",
        embeddings,
        allow_dangerous_deserialization=True
    )
    return vector_store

try:
    vector_store = load_vector_db()
    print("Vector database loaded successfully.")
except Exception as e:
    print(f"Error loading vector DB: {e}")
    vector_store = None

@app.route("/upload", methods=["POST"])
def upload_files():
    global vector_store
    
    if 'files' not in request.files:
        return jsonify({"response": "No file part"}), 400
        
    files = request.files.getlist('files')
    
    if not files or files[0].filename == '':
        return jsonify({"response": "No selected file"}), 400
        
    all_text = ""
    
    try:
        for file in files:
            if file and file.filename.endswith('.pdf'):
                reader = PdfReader(file)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        all_text += text
                        
        if not all_text:
            return jsonify({"response": "Could not extract text from the provided PDFs."}), 400
            
        # Larger chunk size for faster processing
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=200
        )
        
        chunks = text_splitter.split_text(all_text)
        
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Replace global vector store with the new one
        vector_store = FAISS.from_texts(
            chunks,
            embedding=embeddings
        )
        
        # Optionally save to disk to persist
        vector_store.save_local("vector_db")
        
        return jsonify({"response": f"Successfully processed {len(files)} files and built knowledge base."}), 200
        
    except Exception as e:
        return jsonify({"response": f"Error processing PDFs: {str(e)}"}), 500

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    if not vector_store:
        return jsonify({"response": "Error: Vector database not loaded."}), 500

    data = request.get_json()
    question = data.get("message")

    if not question:
        return jsonify({"response": "Error: No message provided."}), 400

    try:
        docs = vector_store.similarity_search(question, k=5)
        context = "\n\n".join(doc.page_content for doc in docs)

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
        return jsonify({"response": response.text})
    except Exception as e:
        return jsonify({"response": f"Error generating response: {e}"}), 500

if __name__ == "__main__":
    app.run(debug=True)