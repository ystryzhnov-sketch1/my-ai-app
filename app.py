import streamlit as st
import requests
import json
import re

# --- КОНФІГУРАЦІЯ ---
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

st.set_page_config(page_title="Debug Mode: AI Chef", page_icon="🛠️", layout="wide")

st.title("🛠️ AI Chef: Debug & Trace Mode")
st.write("Кожний крок запиту тепер логується нижче.")

# --- UI ДЛЯ ВВОДУ ---
source_input = st.text_area("Вставте рецепт:", height=150, help="Сюди можна кидати посилання або текст")

# --- СИСТЕМА ЛОГУВАННЯ ---
def log_debug(title, content):
    with st.expander(f"🔍 LOG: {title}", expanded=False):
        if isinstance(content, dict) or isinstance(content, list):
            st.json(content)
        else:
            st.code(content)

# --- ФУНКЦІЇ ОБРОБКИ ---

def try_repair_json(broken_json):
    """Спроба закрити обірваний JSON масив або об'єкт"""
    if not broken_json: return None
    # Видаляємо все після останньої коми, якщо JSON обірвався
    last_comma = broken_json.rfind(',')
    if last_comma != -1:
        attempt = broken_json[:last_comma] + "]}"
        try: return json.loads(attempt)
        except: pass
    return None

def fetch_calories(simple_name):
    """Шукає калорії з логуванням запиту"""
    clean_query = re.sub(r'[^а-яА-Яa-zA-Z\s]', '', simple_name.lower()).strip()
    url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={clean_query}&search_simple=1&action=process&json=1&page_size=1"
    try:
        r = requests.get(url, timeout=5).json()
        if 'products' in r and len(r['products']) > 0:
            nutri = r['products'][0].get('nutriments', {})
            cal = nutri.get('energy-kcal_100g') or nutri.get('energy-kcal') or (nutri.get('energy_100g', 0) / 4.184)
            return round(float(cal), 1)
    except Exception as e:
        log_debug(f"OpenFoodFacts Error ({clean_query})", str(e))
    return 0

def ask_ai_debug(content):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Спрощуємо промпт, щоб зменшити кількість токенів на виході
    prompt = f"""
    Analyze this recipe: "{content}".
    Return ONLY a JSON object:
    {{
      "steps": "Original instructions word-for-word.",
      "items": [{{"n": "product name", "w": weight_in_grams}}]
    }}
    Rules: If weight unknown, use average (egg=50, onion=100). No talk, just JSON.
    """
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 2048, # Зменшили, щоб ШІ не розганявся на гігантські тексти
        "response_format": {"type": "json_object"}
    }
    
    try:
        log_debug("API Payload", payload)
        response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=30)
        
        log_debug(f"API Response Status: {response.status_code}", response.text)
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            st.error(f"Groq API Error {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Connection Error: {str(e)}")
        return None

# --- ГОЛОВНИЙ ЦИКЛ ---

if st.button("🚀 Запустити аналіз з логами"):
    if source_input:
        with st.spinner('AI працює...'):
            raw_res = ask_ai_debug(source_input)
            
            if raw_res:
                try:
                    data = json.loads(raw_res)
                    log_debug("Parsed Data", data)
                    
                    c1, c2 = st.columns([1.5, 1])
                    
                    with c1:
                        st.subheader("📝 Кроки")
                        st.info(data.get('steps', 'Немає даних'))
                    
                    with c2:
                        st.subheader("📊 Калорії")
                        total = 0
                        for item in data.get('items', []):
                            c_100 = fetch_calories(item['n'])
                            weight = item['w']
                            res_cal = (c_100 * weight) / 100
                            total += res_cal
                            st.write(f"🔹 {item['n']} ({weight}г): {int(res_cal)} ккал")
                        
                        st.divider()
                        st.metric("РАЗОМ", f"{int(total)} ккал")
                        
                except Exception as parse_err:
                    st.error(f"Помилка парсингу JSON: {parse_err}")
                    repaired = try_repair_json(raw_res)
                    if repaired:
                        st.warning("Спроба відновити дані з пошкодженого JSON...")
                        st.json(repaired)
            else:
                st.error("ШІ не повернув результат. Перевірте LOG нижче.")
    else:
        st.warning("Введіть текст.")

st.divider()
st.caption("Режим налагодження активовано. Всі відповіді Groq доступні в блоках Expanders.")
