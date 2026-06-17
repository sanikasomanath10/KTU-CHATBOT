# KTU Industrial Safety Chatbot

## Overview

KTU Industrial Safety Chatbot is an AI-powered question-answering system designed to help students learn Industrial Safety concepts efficiently from their study materials.

The chatbot uses Retrieval-Augmented Generation (RAG) to retrieve relevant content from Industrial Safety notes and generate accurate answers using Google's Gemini model.

The application provides a user-friendly web interface built with Streamlit.

---

## Features

* Ask questions in natural language
* Retrieval-Augmented Generation (RAG)
* FAISS vector database for semantic search
* Gemini 2.5 Flash for answer generation
* Streamlit-based chat interface
* Chat history support
* Clear chat functionality
* Fast and lightweight deployment

---

## Technology Stack

* Python
* Streamlit
* Google Gemini API
* LangChain
* FAISS
* Sentence Transformers
* PyPDF

---

## Approach

This chatbot follows a Retrieval-Augmented Generation (RAG) architecture.

### Workflow

1. Industrial Safety PDF notes are loaded.
2. Text is extracted and divided into chunks.
3. Chunks are converted into embeddings using the Sentence Transformers model:

   * all-MiniLM-L6-v2
4. Embeddings are stored inside a FAISS vector database.
5. When a user asks a question:

   * Relevant chunks are retrieved using semantic similarity search.
   * Retrieved context is sent to Gemini.
   * Gemini generates a context-aware answer.

### What Makes This Chatbot Unique

* Answers are grounded in the provided Industrial Safety notes.
* Reduces hallucination by supplying relevant context.
* Specifically designed for KTU Industrial Safety syllabus.
* Lightweight and deployable with minimal resources.

---

## Project Structure

```text
ktu-industrial-safety-chatbot/
│
├── app.py
├── chatbot.py
├── requirements.txt
├── README.md
├── data/
│   └── industry_module1.pdf
│
└── vector_db/
```

## Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/ktu-industrial-safety-chatbot.git

cd ktu-industrial-safety-chatbot
```

Create virtual environment:

```bash
python -m venv venv
```

Activate virtual environment:

Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Running the Chatbot

Run the Streamlit application:

```bash
streamlit run app.py
```

Open:

```text
http://localhost:8501
```

---

## Challenges Faced

### 1. Poor Answer Retrieval

Initially the chatbot failed to answer certain questions even though the information existed in the notes.

Solution:

* Increased retrieved chunks.
* Improved prompt design.
* Added context-based answering instructions.

### 2. Streamlit Blank Page Issue

The first Streamlit version displayed a blank page because the file contained only backend code and lacked Streamlit UI components.

Solution:

* Rebuilt the interface using Streamlit widgets and chat components.

### 3. Dependency Issues

Several package compatibility issues occurred while installing sentence-transformers, torch, and torchvision.

Solution:

* Installed compatible versions of the required libraries.
* Verified environment setup using a dedicated virtual environment.

---

## Future Improvements

* Multi-PDF support
* Voice-based interaction
* Module-wise filtering
* PDF upload through UI
* Support for multiple KTU subjects

---

## Author

Alka A.S.

B.Tech Computer Science and Engineering

Government Engineering College Sreekrishnapuram
