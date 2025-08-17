import streamlit as st
import re
import os
from agent_core import create_charting_agent, create_rag_chain # Ganti create_db_agent
from file_handler import get_text_from_files, get_text_chunks, get_vector_store

# --- Konfigurasi Halaman ---
st.set_page_config(page_title="🤖 Agent AI Perusahaan", layout="wide")

# --- Judul dan Deskripsi ---
st.title("🤖 Agent AI Cerdas untuk Perusahaan Anda")
st.markdown("Pilih mode di sidebar untuk berinteraksi dengan data penjualan atau menganalisis dokumen Anda.")

# --- Sidebar untuk Pilihan Mode ---
with st.sidebar:
    st.header("Mode Agent")
    agent_mode = st.radio(
        "Pilih jenis tugas yang ingin Anda lakukan:",
        ("Analisis Data & Visualisasi", "Analisis Dokumen (PDF, Excel, dll.)")
    )
    st.info("Didukung oleh Gemini dari Google AI.")

# --- Inisialisasi State ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "rag_chain" not in st.session_state:
    st.session_state.rag_chain = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# --- Fungsi utama untuk menampilkan chat ---
def run_chat_interface():
    # Tampilkan riwayat chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # Jika ada path gambar di pesan, tampilkan
            if "image_path" in message:
                st.image(message["image_path"])
    
    # Terima input dari pengguna
    if prompt := st.chat_input("Tanyakan sesuatu..."):
        # Tambahkan pesan pengguna ke riwayat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Tampilkan pesan dari asisten
        with st.chat_message("assistant"):
            with st.spinner("Memproses..."):
                if agent_mode == "Analisis Data & Visualisasi":
                    # Gunakan agent baru yang bisa membuat grafik
                    db_agent = create_charting_agent() 
                    if db_agent:
                        try:
                            # Sertakan riwayat chat untuk konteks
                            result = db_agent.invoke({
                                "input": prompt,
                                "chat_history": st.session_state.chat_history
                            })
                            response = result["output"]
                            
                            # Update riwayat chat untuk agent
                            st.session_state.chat_history.extend([
                                {"role": "user", "content": prompt},
                                {"role": "assistant", "content": response}
                            ])

                        except Exception as e:
                            response = f"Terjadi kesalahan saat memproses permintaan Anda: {e}"
                    else:
                        response = "Gagal terhubung ke database. Mohon periksa konfigurasi."
                else: # Mode Analisis Dokumen
                    if st.session_state.rag_chain:
                        response_chain = st.session_state.rag_chain.invoke({"input": prompt})
                        response = response_chain["answer"]
                    else:
                        response = "Silakan unggah dokumen terlebih dahulu untuk dianalisis."
                
                # --- Logika untuk menampilkan grafik ---
                image_path = None
                final_response_text = response # Gunakan variabel baru untuk teks
                
                match = re.search(r"PLOT_GENERATED:(.*)", final_response_text)
                
                if match:
                    image_filename = match.group(1).strip()
                    # Hapus penanda dari teks respons
                    final_response_text = re.sub(r"PLOT_GENERATED:.*", "", final_response_text).strip()
                    
                    if os.path.exists(image_filename):
                        st.image(image_filename)
                        image_path = image_filename
                        # PERBAIKAN: Jika teks kosong, berikan pesan default
                        if not final_response_text:
                            final_response_text = "Berikut adalah grafik yang Anda minta."
                    else:
                        final_response_text += "\n\n(Gagal menemukan file grafik yang dibuat.)"

                st.markdown(final_response_text)
        
        # Tambahkan respons asisten ke riwayat
        assistant_message = {"role": "assistant", "content": final_response_text}
        if image_path:
            assistant_message["image_path"] = image_path
        st.session_state.messages.append(assistant_message)

# --- Logika Tampilan Berdasarkan Mode ---
if agent_mode == "Analisis Data & Visualisasi":
    st.subheader("🔍 Analis Data & Visualisasi")
    st.write(
        "Anda bisa bertanya atau meminta visualisasi data. "
        "Contoh: 'Berapa sisa stok untuk Buku Tulis?', 'Buatkan pie chart yang menunjukkan distribusi penjualan per pelanggan', "
        "atau 'Tampilkan 5 produk dengan penjualan terbanyak dalam bentuk bar chart'."
    )
    if st.session_state.get("current_mode") != "db_chart":
        st.session_state.messages = []
        st.session_state.chat_history = []
        st.session_state.current_mode = "db_chart"
    
    run_chat_interface()

else: # Mode Analisis Dokumen
    st.subheader("📄 Analisis Dokumen")
    
    if st.session_state.get("current_mode") != "rag":
        st.session_state.messages = []
        st.session_state.rag_chain = None
        st.session_state.current_mode = "rag"
        
    uploaded_files = st.file_uploader(
        "Unggah file Anda (PDF, XLSX, CSV, TXT)", 
        accept_multiple_files=True,
        type=['pdf', 'xlsx', 'xls', 'csv', 'txt']
    )
    
    if uploaded_files:
        with st.spinner("Membaca dan memproses file... Ini mungkin memakan waktu beberapa saat."):
            if not st.session_state.rag_chain:
                raw_text = get_text_from_files(uploaded_files)
                text_chunks = get_text_chunks(raw_text)
                vector_store = get_vector_store(text_chunks)
                st.session_state.rag_chain = create_rag_chain(vector_store)
                st.success("Dokumen berhasil diproses! Sekarang Anda bisa mulai bertanya.")
    
    if st.session_state.rag_chain:
        run_chat_interface()
    else:
        st.warning("Mohon unggah satu atau lebih dokumen untuk memulai analisis.")
