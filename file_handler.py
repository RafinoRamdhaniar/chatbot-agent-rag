import pandas as pd
from pypdf import PdfReader
from io import BytesIO
import os
import nest_asyncio # Tambahkan import ini

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# --- PERBAIKAN UTAMA: Terapkan patch asyncio ---
# Ini memungkinkan event loop berjalan di dalam thread Streamlit
nest_asyncio.apply()

def get_text_from_files(uploaded_files):
    """Mengekstrak teks dari berbagai jenis file yang diunggah."""
    text = ""
    for file in uploaded_files:
        if file.name.endswith(".pdf"):
            pdf_reader = PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text()
        elif file.name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file)
            text += df.to_string()
        elif file.name.endswith(".csv"):
            df = pd.read_csv(file)
            text += df.to_string()
        elif file.name.endswith((".txt", ".md")):
            stringio = BytesIO(file.getvalue())
            text += stringio.read().decode("utf-8")
    return text

def get_text_chunks(text):
    """Memecah teks menjadi potongan-potongan yang lebih kecil (chunks)."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(text_chunks):
    """Membuat vector store dari potongan teks menggunakan embeddings."""
    
    # Menggunakan GoogleGenerativeAIEmbeddings untuk konsistensi dan menghindari
    # masalah otentikasi dengan Hugging Face.
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    
    vector_store = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vector_store
