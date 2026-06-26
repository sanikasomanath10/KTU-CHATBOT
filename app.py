from flask import Flask, render_template, request, jsonify, send_file
import io
import re
from fpdf import FPDF
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import requests
import os
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from google import genai
import concurrent.futures

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

print("Initializing Gemini Client...")
if not os.environ.get("GEMINI_API_KEY"):
    print("WARNING: GEMINI_API_KEY environment variable is not set! Please configure it in a .env file.")
try:
    client = genai.Client()
    print("Gemini client initialized successfully.")
except Exception as e:
    print(f"Error initializing Gemini client: {e}")
    client = None

def generate_with_local_model(prompt, model_name="gemini-2.5-flash", temperature=0.1):
    if not client:
        raise Exception("Gemini client is not initialized.")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=f"System: You are a strict and precise academic evaluator.\nUser: {prompt}",
            config={"temperature": temperature}
        )
        return response.text.strip()
    except Exception as e:
        print(f"Model generation error: {e}")
        raise Exception(f"Failed to generate text: {e}")

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
1. Answer the question strictly based on the provided NOTES. Do not assume, extrapolate, or use outside knowledge.
2. If the answer is not found in the NOTES, you MUST say exactly "not found in the textbook." and nothing else.
3. Keep the answer clear, concise, and direct.

ANSWER:
"""
        response_text = generate_with_local_model(prompt)
        return jsonify({"response": response_text})
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
Extract all the distinct questions from the following text ALONG WITH THEIR MARKS. 
Carefully read the document to understand the marks allocation. Marks may be explicitly stated next to each question, or they may be defined in section headers (e.g., "Section A: Answer all questions. Each carries 3 marks").

IMPORTANT CONTEXT ON EXAM STRUCTURE:
The standard format of this question paper is typically out of 170 marks total:
- The first 10 questions are 3 marks each.
- The next 10 questions are 14 marks each (which may be split into subquestions).
This is the standard format but it may vary. Use this context to help infer marks if they are missing or unclear, but always prefer explicitly stated marks or section instructions if present.

Determine the marks for EVERY question based on these instructions.
If a question has sub-parts (like a, b, c), keep them together as a single question but specify the marks for each part if available.
Do not include general instructions like "Answer all questions" or section headers in your final output, but USE them to determine the marks.
Format each extracted question exactly like this: [Marks] Question text. (For example: [5 Marks] What is ...?)
Return each distinct formatted question separated by "|||".
If there are no questions, return "NO_QUESTIONS_FOUND".

TEXT:
{text}
"""
        try:
            extracted_text = generate_with_local_model(extraction_prompt).strip()
            
            if "NO_QUESTIONS_FOUND" in extracted_text or not extracted_text:
                return jsonify({"response": "Could not automatically detect questions. Please ensure the file contains clear questions."}), 400
                
            questions = [q.strip() for q in extracted_text.split("|||") if len(q.strip()) > 5]
            
            if not questions:
                return jsonify({"response": "Could not automatically detect questions. Please ensure the file contains clear questions."}), 400
                
        except Exception as e:
            return jsonify({"response": f"Error extracting questions from file: {str(e)}"}), 500

        # Chunk questions to stay within daily rate limits (e.g. 20 requests per day limit)
        chunk_size = 10
        chunks = [questions[i:i + chunk_size] for i in range(0, len(questions), chunk_size)]
        
        final_answer_key = "## Generated Answer Key\n\n"

        for chunk_idx, chunk in enumerate(chunks):
            if chunk_idx > 0:
                import time
                time.sleep(5.0)  # Stay below RPM rate limit
                
            combined_contexts = ""
            questions_text = ""
            
            for i, q in enumerate(chunk, start=chunk_idx * chunk_size + 1):
                # Clean the question text to remove marks prefix before searching (e.g. "[5 Marks] ...")
                q_clean = re.sub(r"^\[[^\]]+\]\s*", "", q).strip()
                docs = vector_store.similarity_search(q_clean, k=4)
                context = "\n".join(doc.page_content for doc in docs)
                combined_contexts += f"=== NOTES CONTEXT FOR Q{i} ===\n{context}\n\n"
                questions_text += f"Q{i}: {q}\n"
            
            prompt = f"""
You are an expert academic assistant.
Use ONLY the provided notes context to answer the specific questions from a test paper.
For each question, look strictly at its corresponding NOTES CONTEXT. Do not mix context between questions.

CRITICAL RULES:
1. You MUST answer every single question listed in the QUESTIONS TO ANSWER section.
2. If the answer to a particular question is not found in its corresponding NOTES CONTEXT, you MUST write exactly:
**Q[Number]: [Question text including marks]**
not found in the textbook.
---
Do not include any rubric or marks breakdown or other text for that question.

Pay close attention to the MARKS allocated for each question (e.g., [5 Marks]).
- For 1-2 marks questions, provide a brief, concise answer (1-2 sentences).
- For 3-5 marks questions, provide a detailed paragraph or a few bullet points.
- For 6+ marks questions, provide a comprehensive answer with headings, subheadings, and a clear structure.
Include a brief suggested marking rubric or marks allocation for each answer.

NOTES CONTEXTS:
{combined_contexts}

QUESTIONS TO ANSWER:
{questions_text}

Format your output exactly like this for each question:
**Q[Number]: [Question text including marks]**

[Your answer matching the depth required by the marks]

*Suggested Rubric:*
- [Rubric point 1]: [Marks]
- [Rubric point 2]: [Marks]

**Total Marks for this Question**: [Total Marks]
---
"""
            try:
                res = generate_with_local_model(prompt)
                final_answer_key += res.strip() + "\n\n"
            except Exception as e:
                # Fallback for the chunk if error occurs
                for i, q in enumerate(chunk, start=chunk_idx * chunk_size + 1):
                    final_answer_key += f"**Q{i}: {q}**\nnot found in the textbook.\n---\n\n"

        return jsonify({"response": final_answer_key}), 200

    except Exception as e:
        return jsonify({"response": f"Error generating answer key: {str(e)}"}), 500

@app.route("/evaluate_sheet", methods=["POST"])
def evaluate_sheet():
    if 'file' not in request.files:
        return jsonify({"response": "No file part"}), 400
        
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({"response": "No selected file"}), 400

    answer_key = request.form.get("answer_key")
    strictness = request.form.get("strictness", "Medium")

    if not answer_key:
        return jsonify({"response": "No answer key provided. Please generate an answer key first."}), 400

    try:
        reader = PdfReader(file)
        student_text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t: student_text += t

        # Split answer key by "**Q" to isolate questions
        parts = answer_key.split("**Q")
        if len(parts) > 1:
            questions_rubrics = ["**Q" + p for p in parts[1:]]
        else:
            questions_rubrics = [answer_key]
            
        chunk_size = 10 # Increased to 10 to stay within daily rate limits
        chunks = [questions_rubrics[i:i + chunk_size] for i in range(0, len(questions_rubrics), chunk_size)]
        
        def evaluate_chunk(chunk):
            chunk_text = "\n".join(chunk)
            prompt = f"""
You are an expert academic evaluator. 
You are tasked with evaluating a student's answer sheet ONLY for the specific questions provided in the chunk below.

QUESTIONS & RUBRICS TO EVALUATE:
{chunk_text}

STUDENT'S ENTIRE ANSWER SHEET:
{student_text}

EVALUATION STRICTNESS LEVEL: {strictness}
- If strictness is "Hard": Be very strict. Require exact terminology and all points from the rubric to award full marks. Deduct marks for missing details.
- If strictness is "Medium": Standard grading. Balance terminology and conceptual understanding. Award partial marks reasonably.
- If strictness is "Liberal": Give the benefit of the doubt. Award partial marks if the core concept or related keywords are present, even if poorly phrased.

GRADING RULE:
1. You MUST evaluate EVERY SINGLE question provided in the QUESTIONS & RUBRICS section above. Do not skip any question.
2. If the student did not answer a question, award 0 marks and state "Not answered".
3. CRITICAL: You MUST strictly adhere to the total marks specified in the question text or rubric (e.g., [5 Marks] or similar). Do NOT invent or change the total marks.
4. The marks awarded CANNOT exceed the total marks allocated for that question.
5. If the answer key says "not found in the textbook." for a question, check if the student has answered it. If the student's answer is academically correct and accurate, award marks accordingly. If the student's answer is incorrect, partial, or missing, award 0 or partial marks.

OUTPUT FORMAT:
Generate a markdown formatted evaluation report.
For EACH question, you MUST output EXACTLY this format (do not deviate):
**Q[Number]**: 
- **Marks Awarded**: [Awarded Marks] / [Total Marks]
- **Feedback**: [Detailed feedback explaining why marks were awarded or deducted.]

DO NOT provide a Total Score at the end. Only evaluate the questions provided in this specific chunk.
"""
            import time
            for attempt in range(3):
                try:
                    return generate_with_local_model(prompt)
                except Exception as e:
                    if attempt == 2:
                        return f"**Q[Unknown]**:\n- **Marks Awarded**: 0 / 0\n- **Feedback**: Error evaluating this chunk: {str(e)}\n\n"
                    time.sleep(5)

        results = []
        for i, chunk in enumerate(chunks):
            if i > 0:
                import time
                time.sleep(4.5)  # Stay below 15 RPM rate limit
            try:
                res = evaluate_chunk(chunk)
                results.append(res)
            except Exception as e:
                results.append(f"Error evaluating some questions: {e}\n\n")
                    
        full_evaluation_report = "## Evaluation Report\n\n"
        for res in results:
            full_evaluation_report += res.strip() + "\n\n"
            
        # Programmatically calculate total score
        total_awarded = 0.0
        total_possible = 0.0
        
        # Extremely robust regex to catch variations in bolding, brackets, spaces, and case
        matches = re.findall(r"\*?\*?Marks Awarded\*?\*?\s*:\s*\*?\[?([\d\.]+)\]?\*?\s*(?:/|out of)\s*\*?\[?([\d\.]+)\]?\*?", full_evaluation_report, re.IGNORECASE)
        
        # Fallback line-by-line parsing if regex fails to find any matches
        if not matches:
            for line in full_evaluation_report.splitlines():
                if "marks awarded" in line.lower():
                    nums = re.findall(r"([\d\.]+)", line)
                    if len(nums) >= 2:
                        matches.append((nums[0], nums[1]))
        
        for awarded, possible in matches:
            try:
                total_awarded += float(awarded)
                total_possible += float(possible)
            except ValueError:
                pass
                
        if total_possible == 0:
            full_evaluation_report += "\n\n### Final Total Score\n*(Could not automatically calculate score, please check the formatting above)*\n"
        else:
            total_awarded = round(total_awarded, 2)
            total_possible = round(total_possible, 2)
            percentage = round((total_awarded / total_possible) * 100, 2) if total_possible > 0 else 0
            
            full_evaluation_report += f"\n\n### Final Evaluation Score\n"
            full_evaluation_report += f"- **Total Marks Awarded**: {total_awarded}\n"
            full_evaluation_report += f"- **Full Marks Possible**: {total_possible}\n"
            full_evaluation_report += f"\n**Final Score**: {total_awarded} out of {total_possible} ({percentage}%)\n\n"
            full_evaluation_report += f"*Overall Comment*: Evaluation complete. Evaluated {len(matches)} questions."

        return jsonify({"response": full_evaluation_report}), 200

    except Exception as e:
        return jsonify({"response": f"Error evaluating sheet: {str(e)}"}), 500

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
    app.run(debug=False, use_reloader=False)