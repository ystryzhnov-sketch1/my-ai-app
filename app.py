import streamlit as st
import requests
import json
import re

# --- КОНФІГУРАЦІЯ ---
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

st.set_page_config(page_title="AI Smart Chef Pro", page_icon="⚖️", layout="wide")

st.title("⚖️ Розумний Аналізатор Рецептів")
st.write("Стійка версія: розпізнає довгі рецепти та виправляє помилки ШІ.")

source_input = st.text_area("Вставте текст рецепта або посилання:", height=150)

# --- РОБОТА З БАЗОЮ ДАНИХ ---

def fetch_calories(simple_name):
    """Шукає калорії в Open Food Facts"""
    clean_query = re.sub(r'[^а-яА-Яa-zA-Z\s]', '', simple_name.lower()).strip()
    url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={clean_query}&search_simple=1&action=process&json=1&page_size=1"
    
    try:
        r = requests.get(url, timeout=5).json()
        if 'products' in r and len(r['products']) > 0:
            nutri = r['products'][0].get('nutriments', {})
            cal = nutri.get('energy-kcal_100g') or nutri.get('energy-kcal') or (nutri.get('energy_100g', 0) / 4.184)
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
    
    prompt = f"""
    Ти — кулінарний дата-інженер. Твоє завдання — перетворити текст на структурований JSON.
    ДЖЕРЕЛО: "{content}"
    
    СТРУКТУРА ВІДПОВІДІ:
    {{
      "original_steps": "копія кроків СЛОВО В СЛОВО без змін",
      "list_for_user": ["інгредієнт 1 як у тексті", "інгредієнт 2..."],
      "list_for_api": [
        {{"search_name": "назва для бази (напр. 'курка')", "weight": вага_в_грамах}}
      ]
    }}
    ПРАВИЛА:
    1. Якщо вага не вказана, постав логічну (яйце=50, цибуля=100, вода=200).
    2. Поверни ТІЛЬКИ JSON. Не пиши нічого до або після нього.
    """
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 3000, # Достатньо для довгих інструкцій
        "response_format": {"type": "json_object"}
    }
    
    try:
        response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=25)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            st.error(f"Помилка API Groq: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Помилка з'єднання: {str(e)}")
        return None

# --- ВІДОБРАЖЕННЯ ---

if st.button("🚀 Аналізувати"):
    if source_input:
        with st.spinner('ШІ аналізує текст...'):
            raw_res = ask_ai(source_input)
            
            if raw_res:
                try:
                    # На випадок, якщо ШІ додав Markdown розмітку ```json ... ```
                    clean_res = raw_res.strip()
                    if clean_res.startswith("```"):
                        clean_res = re.sub(r'^```json\s*|\s*```$', '', clean_res)
                    
                    data = json.loads(clean_res)
                    
                    col1, col2 = st.columns([1.5, 1])
                    
                    with col1:
                        st.subheader("📝 Приготування (Оригінал)")
                        steps = data.get('original_steps', "Кроки не знайдені")
                        st.info(steps)
                        
                        st.subheader("🛒 Список продуктів")
                        for ing in data.get('list_for_user', []):
                            st.write(f"• {ing}")
                    
                    with col2:
                        st.subheader("📊 Розрахунок Ккал")
                        total_cal = 0
                        
                        for item in data.get('list_for_api', []):
                            cals_per_100 = fetch_calories(item['search_name'])
                            item_cal = (cals_per_100 * item['weight']) / 100
                            total_cal += item_cal
                            
                            icon = "✅" if item_cal > 0 else "⚪"
                            st.write(f"{icon} **{item['search_name']}** ({item['weight']}г) — {int(item_cal)} ккал")
                        
                        st.divider()
                        st.metric("ЗАГАЛЬНА ЕНЕРГІЯ", f"{int(total_cal)} ккал")
                        
                except Exception as e:
                    st.error(f"Помилка парсингу JSON: {str(e)}")
                    st.code(raw_res) # Показуємо, що саме повернув ШІ для відладки
            else:
                st.error("ШІ повернув порожню відповідь.")
    else:
        st.warning("Вставте рецепт.")
