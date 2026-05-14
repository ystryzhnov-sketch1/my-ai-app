import streamlit as st
import requests
import json
import re

# --- КОНФІГУРАЦІЯ ---
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

st.set_page_config(page_title="AI Smart Chef", page_icon="⚖️", layout="wide")

st.markdown("""
    <style>
    .stAlert { padding: 10px; border-radius: 5px; }
    .main { background-color: #fcfcfc; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚖️ Розумний Аналізатор Рецептів")
st.write("ШІ автоматично адаптує назви продуктів під вимоги глобальних баз даних.")

source_input = st.text_area("Вставте рецепт (текст або посилання):", height=150)

# --- РОБОТА З БАЗОЮ ДАНИХ ---

def fetch_calories(simple_name):
    """Шукає калорії за максимально спрощеною назвою"""
    # Очищуємо від зайвих символів
    clean_query = re.sub(r'[^а-яА-Яa-zA-Z\s]', '', simple_name).strip()
    url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={clean_query}&search_simple=1&action=process&json=1&page_size=1"
    
    try:
        r = requests.get(url, timeout=5).json()
        if 'products' in r and len(r['products']) > 0:
            nutri = r['products'][0].get('nutriments', {})
            # Шукаємо ккал у різних полях бази
            cal = nutri.get('energy-kcal_100g') or nutri.get('energy-kcal') or nutri.get('energy_100g', 0) / 4.184
            return round(float(cal), 1)
    except:
        pass
    return 0

# --- РОБОТА З ШІ ---

def ask_ai(content):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Промпт тепер вимагає "search_name" - ідеальну назву для пошуковика
    prompt = f"""
    Ти — кулінарний дата-інженер. Розклади рецепт: "{content}".
    
    ПРАВИЛА:
    1. original_steps: копіюй кроки СЛОВО В СЛОВО.
    2. list_for_user: список інгредієнтів як в оригіналі.
    3. list_for_api: список об'єктів {{
        "original": "як у тексті (напр. 'дві великі морквини')",
        "search_name": "ІДЕАЛЬНЕ слово для пошуку (напр. 'морква')",
        "weight": вага в грамах (число)
    }}
    
    Якщо вага не вказана, вирахуй середню (цибуля=100г, олія=15г, яйце=50г).
    ПОВЕРНИ ТІЛЬКИ JSON.
    """
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }
    
    try:
        response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=20)
        return response.json()['choices'][0]['message']['content']
    except:
        return None

# --- ІНТЕРФЕЙС ---

if st.button("🚀 Аналізувати"):
    if source_input:
        with st.spinner('ШІ оптимізує запити до бази даних...'):
            res = ask_ai(source_input)
            if res:
                data = json.loads(res)
                
                col1, col2 = st.columns([1.5, 1])
                
                with col1:
                    st.subheader("📝 Оригінальна інструкція")
                    st.info(data.get('original_steps'))
                    
                    st.subheader("🛒 Інгредієнти")
                    for ing in data.get('list_for_user', []):
                        st.write(f"• {ing}")
                
                with col2:
                    st.subheader("📊 Розрахунок енергії")
                    total_cal = 0
                    
                    for item in data.get('list_for_api', []):
                        # Використовуємо саме search_name для бази
                        cals_per_100 = fetch_calories(item['search_name'])
                        
                        # Якщо база нічого не дала, ШІ пробує вгадати (fallback)
                        item_cal = (cals_per_100 * item['weight']) / 100
                        total_cal += item_cal
                        
                        if item_cal > 0:
                            st.success(f"✅ **{item['search_name']}** ({item['weight']}г) — {int(item_cal)} ккал")
                        else:
                            st.warning(f"⚠️ **{item['search_name']}** ({item['weight']}г) — база не відповіла")
                    
                    st.divider()
                    st.metric("ЗАГАЛЬНА КАЛОРІЙНІСТЬ", f"{int(total_cal)} ккал")
            else:
                st.error("Помилка обробки тексту.")
    else:
        st.warning("Будь ласка, вставте текст рецепта.")
