from flask import Flask, render_template, request, jsonify, send_file
import io
import re
from fpdf import FPDF
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

@app.route("/generate_key", methods=["POST"])
def generate_key():
    global vector_store
    if not vector_store:
        return jsonify({"response": "Error: Vector database is empty. Please upload a textbook first!"}), 400

    if 'file' not in request.files:
        return jsonify({"response": "No file part"}), 400
        
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({"response": "No selected file"}), 400

    try:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t: text += t

        # Use LLM to extract questions from the text
        extraction_prompt = f"""
You are an assistant that extracts questions from a test paper.
Extract all the distinct questions from the following text. 
If a question has sub-parts (like a, b, c), keep them together as a single question.
Do not include general instructions like "Answer all questions", section headers, or marks.
Return each distinct question separated by "|||".
If there are no questions, return "NO_QUESTIONS_FOUND".

TEXT:
{text}
"""
        try:
            extraction_response = model.generate_content(extraction_prompt)
            extracted_text = extraction_response.text.strip()
            
            if "NO_QUESTIONS_FOUND" in extracted_text or not extracted_text:
                return jsonify({"response": "Could not automatically detect questions. Please ensure the file contains clear questions."}), 400
                
            questions = [q.strip() for q in extracted_text.split("|||") if len(q.strip()) > 5]
            
            if not questions:
                return jsonify({"response": "Could not automatically detect questions. Please ensure the file contains clear questions."}), 400
                
        except Exception as e:
            return jsonify({"response": f"Error extracting questions from file: {str(e)}"}), 500

        # Limit to first 20 questions to prevent extreme generation times
        questions = questions[:20]
        
        final_answer_key = "## Generated Answer Key\n\n"
        
        # Gather contexts for all questions to answer them in a single batch
        # This prevents hitting the 5 RPM free tier rate limit
        combined_contexts = ""
        questions_text = ""
        
        for i, q in enumerate(questions, 1):
            docs = vector_store.similarity_search(q, k=3)
            context = "\n".join(doc.page_content for doc in docs)
            combined_contexts += f"--- CONTEXT FOR Q{i} ---\n{context}\n\n"
            questions_text += f"Q{i}: {q}\n"
            
        prompt = f"""
You are an expert academic assistant.
Use ONLY the provided notes to answer the specific questions from a test paper.
If the notes do not contain the answer for a particular question, say "Information not found in the textbook."

NOTES:
{combined_contexts}

QUESTIONS TO ANSWER:
{questions_text}

Please provide the answers for all questions. Format your output exactly like this for each question:
**Q[Number]: [Question text]**

[Your answer]

---

"""
        try:
            response = model.generate_content(prompt)
            final_answer_key += response.text.strip()
        except Exception as e:
            return jsonify({"response": f"Error generating answers: {str(e)}"}), 500

        return jsonify({"response": final_answer_key}), 200

    except Exception as e:
        return jsonify({"response": f"Error generating answer key: {str(e)}"}), 500

@app.route("/download_pdf", methods=["POST"])
def download_pdf():
    try:
        data = request.get_json()
        content = data.get("content", "No content provided")

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=11)
        
        # Clean up markdown somewhat for standard PDF
        content = content.replace("**", "").replace("## ", "").replace("---", "_"*40)
        
        # fpdf doesn't handle unicode well by default with basic fonts, so encode/decode to ignore errors
        safe_content = content.encode('latin-1', 'replace').decode('latin-1')
        
        pdf.multi_cell(0, 7, txt=safe_content)
        
        # Output to bytes
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name='Answer_Key.pdf'
        )
    except Exception as e:
        return jsonify({"response": f"Error creating PDF: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)