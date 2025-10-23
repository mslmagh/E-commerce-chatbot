import google.generativeai as genai
import streamlit as st  # Yeni eklediğimiz kütüphane
import sys
import json
import os

# --- AYARLAR ---
# Bu dosya, kalıcı hafıza için KULLANILMAYACAK (Streamlit'in kendi hafızası var)
# HISTORY_FILE = "chat_history.json" 
KNOWLEDGE_FILE = "products.txt"  # Bilgi bankası dosyanız

# --- Anahtar Kontrolü ---
if "..." in API_KEY or API_KEY == "" or not API_KEY.startswith("AIza"):
    st.error("Lütfen API anahtarınızı kodun içine yapıştırın.")
    st.stop() # Hata varsa uygulamayı durdur

# --- Kurumsal Hafıza Fonksiyonu (RAG) ---
# Bu fonksiyon 'cache'lenir, yani sadece 1 kere çalıştırılır,
# her seferinde dosyayı okumamak için sonucu hafızada tutar.
@st.cache_data
def load_knowledge_base():
    """
    Bilgi bankası dosyasını ('products.txt') okur.
    """
    if not os.path.exists(KNOWLEDGE_FILE):
        st.error(f"'{KNOWLEDGE_FILE}' dosyası bulunamadı. Lütfen oluşturun.")
        return ""
    
    with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
        knowledge = f.read()
        print(f"[Sistem: '{KNOWLEDGE_FILE}' bilgi bankası başarıyla yüklendi.]")
        return knowledge

# --- Model ve Sohbet Başlatma Fonksiyonu ---
# Bu da 'cache'lenir, yani model her etkileşimde yeniden kurulmaz.
@st.cache_resource
def initialize_model():
    """
    Gemini modelini ve sohbet oturumunu başlatır.
    """
    genai.configure(api_key=API_KEY)
    
    # 1. Bilgi Bankasını (Ürünleri) yükle
    knowledge_base = load_knowledge_base()

    # 2. Bota "Karakter" ve "Bilgi" ver (System Prompt)
    system_instruction = (
        "Sen, bir e-ticaret sitesi için Müşteri Destek Asistanısın.\n"
        "Görevin, müşterilere nazik, kısa ve net cevaplar vermek.\n"
        "Sadece ve sadece sana aşağıda '--- BİLGİ BANKASI ---' başlığı altında verilen bilgileri kullanarak cevap ver.\n"
        "Eğer sorulan soru bu bilgilerin dışındaysa, 'Bu konuda bilgim yok, lütfen mesai saatleri içinde (09:00-17:00) canlı desteğe bağlanın.' de.\n"
        "Asla fiyat uydurma veya stokta olmayan bir ürün için 'var' deme.\n\n"
        "--- BİLGİ BANKASI ---\n"
        f"{knowledge_base}"
        "--- BİLGİ BANKASI SONU ---"
    )

    # 3. Modeli başlat (system_instruction ile)
    model = genai.GenerativeModel(
        model_name='gemini-pro-latest',
        system_instruction=system_instruction
    )

    # 4. Sohbeti başlat (Boş geçmişle)
    chat = model.start_chat(history=[])
    return chat

# --- Ana Uygulama Arayüzü ---

# Sayfa başlığını ayarla
st.set_page_config(page_title="E-Ticaret Destek Botu", page_icon="🤖")
st.title("🤖 E-Ticaret Destek Botu")
st.caption(f"Şu an '{KNOWLEDGE_FILE}' dosyasındaki bilgilere göre cevap veriyorum.")


# 1. Modeli ve sohbet oturumunu başlat
# Streamlit'in kendi hafızası olan 'session_state' kullanılır.
# Bu sayede 'chat' nesnesi, sayfa yenilense bile kaybolmaz.
if "chat" not in st.session_state:
    st.session_state.chat = initialize_model()

# 2. "Hafızayı Temizle" butonu
if st.sidebar.button("Sohbeti Temizle"):
    # Modeli yeniden, boş hafızayla başlat
    st.session_state.chat = initialize_model()
    st.sidebar.success("Sohbet hafızası temizlendi.")

# 3. Eski Sohbet Mesajlarını Göster
# 'st.session_state.chat.history' içindeki tüm mesajları döngüye al
for message in st.session_state.chat.history:
    # Gemini 'model' rolünü kullanır, Streamlit 'assistant' bekler
    role = "assistant" if message.role == "model" else message.role
    
    with st.chat_message(role):
        st.markdown(message.parts[0].text)

# 4. Kullanıcıdan Yeni Mesaj Al (Sayfanın en altındaki giriş kutusu)
if prompt := st.chat_input("Deri ayakkabı var mı?"):
    
    # Kullanıcının mesajını hemen arayüze ekle
    with st.chat_message("user"):
        st.markdown(prompt)

    # Botun cevabını al
    try:
        with st.spinner("Bot düşünüyor..."): # "Bot düşünüyor..." yazısı yerine dönen ikon
            response = st.session_state.chat.send_message(prompt)
        
        # Botun cevabını arayüze ekle
        with st.chat_message("assistant"):
            st.markdown(response.text.strip())
            
    except Exception as e:
        st.error(f"Bir hata oluştu: {e}") 