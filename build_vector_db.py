from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

import os



pdf_files = [
    "data/industry_module1.pdf",
    "data/industry_module2.pdf"
]

all_text = ""

for pdf in pdf_files:
    reader = PdfReader(pdf)

    for page in reader.pages:
        text = page.extract_text()

        if text:
            all_text += text

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

chunks = text_splitter.split_text(all_text)

print("Total Chunks:", len(chunks))

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vector_store = FAISS.from_texts(
    chunks,
    embedding=embeddings
)

vector_store.save_local("vector_db")

print("Vector Database Created Successfully!")