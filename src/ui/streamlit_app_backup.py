import streamlit as st
import os
import sys

# Menambahkan direktori proyek ke PATH agar modul lokal dapat diimpor
# Ini penting karena streamlit akan menjalankan skrip ini dari direktori yang berbeda
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

st.set_page_config(page_title="QA Bot Internal", page_icon="🤖")

try:
    # Mengimpor fungsi initialize_qa_system dan get_qa_response dari qa_bot.py
    # Ini adalah fungsi yang kita modifikasi di qa_bot.py sebelumnya.
    from src.qa_bot.qa_bot import initialize_qa_system, get_qa_response
    # --- Inisialisasi Model dan Vector DB di awal (PENTING untuk performa) ---
    # Memuat model dan vector_db bisa memakan waktu, jadi lakukan HANYA SEKALI
    # saat aplikasi Streamlit dimulai.
    # Ini akan mencegah model dimuat ulang setiap kali ada interaksi.
    
    # qa_model_initialized akan menjadi flag yang menyimpan state apakah model sudah dimuat atau belum
    if 'qa_model_initialized' not in st.session_state:
        st.session_state['qa_model_initialized'] = False
        # st.session_state['qa_bot_instance'] tidak lagi diperlukan karena kita akan memanggil fungsi langsung
        # dan inisialisasi dikelola di dalam qa_bot.py dengan variabel global.

    if not st.session_state['qa_model_initialized']:
        with st.spinner("Memuat basis pengetahuan dan model QA (ini mungkin butuh waktu pertama kali)..."):
            try:
                # --- PERUBAHAN DI SINI: Panggil initialize_qa_system() dari qa_bot.py ---
                # Fungsi ini akan menginisialisasi semua komponen bot (Vector DB, LLM, Chains)
                # dan menyimpannya di variabel global di dalam modul qa_bot.py.
                initialize_qa_system() 
                st.session_state['qa_model_initialized'] = True
                
                st.success("Basis pengetahuan dan model QA berhasil dimuat!")
            except Exception as e:
                st.error(f"Gagal memuat basis pengetahuan dan model QA: {e}")
                st.session_state['qa_model_initialized'] = False
                # Optionally, sys.exit() if you want the app to stop on initialization failure
                
except ImportError as ie:
    st.error(f"Error impor: {ie}. Pastikan file 'qa_bot.py' ada dan tidak ada kesalahan sintaks. "
             f"Pastikan juga semua dependensi LangChain sudah terinstal.")
    st.info("Coba jalankan `pip install -r requirements.txt` dan pastikan 'qa_bot.py' ada di direktori root.")
except Exception as e:
    st.error(f"Terjadi kesalahan tak terduga saat inisialisasi: {e}")
    st.info("Periksa log di terminal untuk detail lebih lanjut.")


st.title("🤖 QA Bot Internal")
st.caption("Asisten cerdas untuk tim QA Anda.")

# --- Inisialisasi Riwayat Chat ---
# Jika 'messages' belum ada di session_state, buat list kosong
if "messages" not in st.session_state:
    st.session_state.messages = []

# Menampilkan pesan sebelumnya dari riwayat chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Input Chat Pengguna ---
if prompt := st.chat_input("Tanyakan sesuatu tentang dokumen QA..."):
    # Tambahkan pesan pengguna ke riwayat chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Dapatkan respons dari bot QA
    with st.chat_message("assistant"):
        with st.spinner("Bot sedang berpikir..."):
            if st.session_state['qa_model_initialized']:
                try:
                    # --- PERUBAHAN DI SINI: Panggil get_qa_response() dari qa_bot.py ---
                    # Fungsi ini akan langsung memproses query menggunakan instance bot yang sudah diinisialisasi
                    response = get_qa_response(prompt) 
                    st.markdown(response)
                except Exception as e:
                    st.error(f"Terjadi kesalahan saat mendapatkan respons: {e}")
                    response = "Maaf, terjadi kesalahan saat memproses permintaan Anda. " \
                               "Mohon periksa log di terminal untuk detail lebih lanjut."
                    st.markdown(response)
            else:
                response = "Bot belum berhasil diinisialisasi. Mohon coba lagi atau periksa log error."
                st.markdown(response)
        
        # Tambahkan respons bot ke riwayat chat
        st.session_state.messages.append({"role": "assistant", "content": response})

