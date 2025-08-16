# agent_core.py (dengan Kemampuan Grafik dan Impor yang Diperbaiki)

import os
from dotenv import load_dotenv

from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# --- Import baru untuk Agent yang lebih canggih ---
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_experimental.tools import PythonREPLTool
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage

# Muat variabel lingkungan dari file .env
load_dotenv()

def get_db_connection_string():
    """Membentuk string koneksi database dari variabel lingkungan."""
    return (
        f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )

def create_charting_agent():
    """
    Membuat agent canggih yang bisa menjalankan SQL dan kode Python untuk membuat grafik.
    """
    try:
        db = SQLDatabase.from_uri(get_db_connection_string())
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro-latest",
            temperature=0,
        )
        
        # Definisikan alat-alat yang bisa digunakan agent
        sql_toolkit = SQLDatabaseToolkit(db=db, llm=llm)
        sql_tools = sql_toolkit.get_tools()
        python_tool = PythonREPLTool() # Alat untuk eksekusi kode Python
        
        tools = sql_tools + [python_tool]
        
        # --- PERUBAHAN UTAMA DI SINI: Menambahkan Konteks Bisnis pada Prompt ---
        prompt_template = """
        Anda adalah seorang analis data ahli yang bekerja dengan database MySQL dan Python.
        Anda memiliki akses ke seperangkat alat untuk melakukan query database dan mengeksekusi kode Python.

        --- Konteks Database Penting ---
        - Tabel `produk` berisi informasi produk seperti `nama_produk` dan `harga_jual`.
        - Tabel `penjualan` berisi header transaksi dengan `nama_pelanggan` dan `tanggal_transaksi`.
        - Tabel `detail_penjualan` menghubungkan `penjualan` dan `produk`, dan berisi `jumlah` (kuantitas) barang yang terjual.
        - Untuk menghitung **total pendapatan (revenue)**, Anda HARUS menggabungkan `detail_penjualan` dengan `produk` dan mengalikan `jumlah` dengan `harga_jual`.
        - Jika pengguna bertanya tentang "bulan ini" atau tidak menyebutkan periode waktu, asumsikan itu adalah **Agustus 2025**, karena data sampel di database berasal dari bulan tersebut.
        ---

        Untuk menjawab pertanyaan pengguna, ikuti langkah-langkah berikut:
        1. Gunakan konteks di atas untuk memahami pertanyaan pengguna tanpa perlu bertanya balik.
        2. Gunakan alat SQL untuk mengambil data yang relevan dari database.
        3. Jika pengguna meminta visualisasi atau grafik (seperti bar chart, line chart, pie chart, dll.):
           a. Gunakan alat Python REPL untuk memproses data (jika perlu) menggunakan pandas.
           b. Tulis kode Python menggunakan matplotlib untuk membuat grafik.
           c. **SANGAT PENTING**: Simpan grafik yang Anda buat ke file bernama `chart.png`. Pastikan untuk menutup plot dengan `plt.close()` setelah menyimpannya agar file ditulis dengan benar ke disk.
           d. Setelah menyimpan grafik, dalam jawaban akhir Anda, sertakan penanda khusus: `PLOT_GENERATED:chart.png`.
        4. Jika tidak ada permintaan grafik, cukup jawab pertanyaan pengguna berdasarkan data yang Anda ambil.
        
        Mulai!
        
        Pertanyaan: {input}
        {agent_scratchpad}
        """
        
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", prompt_template),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )
        
        agent = create_openai_tools_agent(llm, tools, prompt)
        
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            memory=None 
        )
        
        return agent_executor
        
    except Exception as e:
        print(f"Error creating charting agent: {e}")
        return None

def create_rag_chain(vector_store):
    """Membuat RAG chain untuk menjawab pertanyaan berdasarkan dokumen."""
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash-latest",
        temperature=0.2,
        max_output_tokens=3000,
        top_p=0.8,
    )
    
    retriever = vector_store.as_retriever()
    
    prompt = ChatPromptTemplate.from_template("""
    Anda adalah asisten AI yang ahli dalam menganalisis dokumen.
    Jawab pertanyaan pengguna hanya berdasarkan konteks yang diberikan di bawah ini.
    Jika informasi tidak ada dalam konteks, katakan Anda tidak tahu.

    Konteks:
    {context}

    Pertanyaan:
    {input}
    """)
    
    document_chain = create_stuff_documents_chain(llm, prompt)
    retrieval_chain = create_retrieval_chain(retriever, document_chain)
    
    return retrieval_chain
