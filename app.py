import streamlit as st
import requests
import json
import re

# --- КОНФІГУРАЦІЯ ---
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

st.set_page_config(page_title="AI Chef DEBUG", page_icon="🧪", layout="wide")

st.title("🧪 AI Chef: Debug Mode ON")
st.write("Всі дані, що приходять від ШІ, тепер логуються внизу.")

# --- UI ---
source_input = st.text_area("Вставте текст зі сторінки:", height=200)

def fetch_calories(simple_name):
    """Пошук у базі OpenFoodFacts"""
    clean_query = re.sub(r'[^а-яА-Яa-zA-Z\s]', '', simple_name.lower()).strip()
    if not clean_query: return 0
    url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={clean_query}&search_simple=1&action=process&json=1&page_size=1"
    try:
        r = requests.get(url, timeout=5).json()
        if 'products' in r and len(r['products']) > 0:
            nutri = r['products'][0].get('nutriments', {})
            cal = nutri.get('energy-kcal_100g') or nutri.get('energy-kcal') or 0
            return float(cal)
    except: pass
    return 0

def ask_ai_debug(content):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    prompt = f"""
    You are a Recipe Parser. Extract data from this messy text: "{content}"
    
    Rules:
    1. Steps: word-for-word instructions.
    2. API Data: [{{ "n": "product in Ukrainian", "w": weight_in_grams }}]
    
    Return ONLY JSON.
    """
    
    payload = {
        "model": "llama-3.1-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0
    }
    
    try:
        response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=30)
        return response
    except Exception as e:
        st.error(f"Network Error: {e}")
        return None

if st.button("🚀 Аналізувати з логуванням"):
    if source_input:
        with st.spinner('AI працює...'):
            response = ask_ai_debug(source_input)
            
            if response and response.status_code == 200:
                raw_text = response.json()['choices'][0]['message']['content']
                
                # --- ВИВОДИМО ЛОГ ---
                with st.expander("🛠️ DEBUG: RAW RESPONSE", expanded=True):
                    st.code(raw_text)
                
                try:
                    # Очищення JSON
                    start = raw_text.find('{')
                    end = raw_text.rfind('}') + 1
                    data = json.loads(raw_text[start:end])
                    
                    col1, col2 = st.columns([1.5, 1])
                    
                    with col1:
                        st.subheader("📖 Інструкція")
                        st.write(data.get('steps', 'Не знайдено'))
                        
                    with col2:
                        st.subheader("📊 Калорійність")
                        total = 0
                        # Шукаємо дані в різних можливих ключах
                        items = data.get('api_data', data.get('items', []))
                        for item in items:
                            c_100 = fetch_calories(item['n'])
                            w = item.get('w', 0)
                            c_final = (c_100 * w) / 100
                            total += c_final
                            st.write(f"🔹 {item['n']} ({w}г) — {int(c_final)} ккал")
                        
                        st.divider()
                        st.metric("УСЬОГО", f"{int(total)} ккал")
                except Exception as e:
                    st.error(f"Помилка парсингу: {e}")
            else:
                st.error("ШІ не відповів або помилка API.")
                if response: st.write(response.text)
    else:
        st.warning("Вставте текст.")

st.divider()
st.caption("Логи автоматично з'являються після натискання кнопки.")
