import streamlit as st
import requests
import json
import re

# --- КОНФІГУРАЦІЯ ---
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

st.set_page_config(page_title="AI Recipe Intelligence", page_icon="🧠", layout="wide")

st.title("🧠 Розумний Екстрактор Рецептів")
st.write("Ця версія автоматично відділяє рецепт від реклами та зайвого тексту з будь-якого сайту.")

# --- UI ---
source_input = st.text_area("Вставте текст зі сторінки (можна копіювати все підряд):", 
                            placeholder="Просто виділіть все на сторінці (Ctrl+A), скопіюйте і вставте сюди...",
                            height=250)

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

def ask_ai_smart(content):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    # Промпт тепер містить інструкцію з фільтрації сміття
    prompt = f"""
    You are a Recipe Data Expert. I will give you a messy text from a website. 
    Your tasks:
    1. FILTER: Ignore ads, menus, comments, and footer text.
    2. EXTRACT: Find the actual cooking steps and ingredients.
    3. FORMAT: Return ONLY a JSON object:
    {{
      "recipe_title": "Title of the dish",
      "steps": "Full instructions verbatim, structured with numbers",
      "ingredients_list": ["Original ingredient lines"],
      "api_data": [{{"n": "clean product name in Ukrainian", "w": weight_in_grams}}]
    }}

    If the text contains no recipe, return {{"error": "No recipe found"}}.
    TEXT: "{content}"
    """
    
    payload = {
        "model": "llama-3.1-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 3000
    }
    
    try:
        response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            res_text = response.json()['choices'][0]['message']['content']
            start = res_text.find('{')
            end = res_text.rfind('}') + 1
            return res_text[start:end]
        return None
    except:
        return None

if st.button("🚀 Витягнути рецепт та порахувати"):
    if source_input:
        with st.spinner('ШІ відфільтровує сміття та аналізує склад...'):
            raw_json = ask_ai_smart(source_input)
            if raw_json:
                try:
                    data = json.loads(raw_json)
                    
                    if "error" in data:
                        st.error("ШІ не знайшов рецепт у цьому тексті. Спробуйте скопіювати іншу частину сторінки.")
                    else:
                        st.header(f"🍴 {data.get('recipe_title', 'Рецепт')}")
                        
                        col1, col2 = st.columns([1.5, 1])
                        
                        with col1:
                            st.subheader("📖 Покрокове приготування")
                            st.write(data.get('steps'))
                            
                            st.subheader("🛒 Оригінальні інгредієнти")
                            for ing in data.get('ingredients_list', []):
                                st.write(f"• {ing}")
                                
                        with col2:
                            st.subheader("📊 Розрахунок Ккал")
                            total = 0
                            for item in data.get('api_data', []):
                                c_100 = fetch_calories(item['n'])
                                w = item.get('w', 0)
                                c_final = (c_100 * w) / 100
                                total += c_final
                                st.success(f"**{item['n']}** ({w}г) — {int(c_final)} ккал")
                            
                            st.divider()
                            st.metric("ЗАГАЛЬНА ЕНЕРГІЯ", f"{int(total)} ккал")
                except Exception as e:
                    st.error("Помилка обробки. Можливо, текст занадто великий.")
                    with st.expander("Показати сиру відповідь"):
                        st.code(raw_json)
            else:
                st.error("Сервер ШІ не відповів.")
    else:
        st.warning("Вставте текст.")
