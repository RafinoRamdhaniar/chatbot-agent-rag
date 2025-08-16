# file_handler.py (Diperbaiki)
import pandas as pd
from pypdf import PdfReader
from io import BytesIO
import os # Tambahkan import os

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceBgeEmbeddings

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
    
    # --- PERBAIKAN DI SINI ---
    # Mengosongkan token Hugging Face untuk menghindari error 401 pada model publik.
    # Ini mencegah pengiriman kredensial yang mungkin tidak valid.
    os.environ['HUGGING_FACE_HUB_TOKEN'] = ''
    
    # Menggunakan model embedding open-source yang efisien
    model_name = "BAAI/bge-small-en-v1.5"
    encode_kwargs = {'normalize_embeddings': True} 
    embeddings = HuggingFaceBgeEmbeddings(
        model_name=model_name,
        model_kwargs={'device': 'cpu'}, # Gunakan CPU
        encode_kwargs=encode_kwargs
    )
    
    vector_store = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vector_store
