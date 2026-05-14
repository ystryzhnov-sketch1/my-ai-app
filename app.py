import streamlit as st
import requests
import json
import re
from bs4 import BeautifulSoup

# --- КОНФІГУРАЦІЯ ---
# Переконайся, що ці рядки точно такі, як тут
GROQ_API_KEY = "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"
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

st.set_page_config(page_title="AI Chef Pro (Fixed)", page_icon="🛡️", layout="wide")

st.title("🛡️ AI Chef: Фінальна версія")

# --- ФУНКЦІЇ ---

def get_text_from_url(url):
    try:
        url = url.strip() # Прибираємо зайві пробіли
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for el in soup(["script", "style", "nav", "footer", "header", "aside"]):
            el.extract()
        return soup.get_text(separator=' ', strip=True)
    except Exception as e:
        return f"Помилка при читанні сайту: {e}"

def fetch_nutrition(simple_name):
    clean_query = re.sub(r'[^а-яА-Яa-zA-Z\s]', '', simple_name.lower()).strip()
    if not clean_query: return {"cal": 0, "p": 0, "f": 0, "c": 0}
    
    url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={clean_query}&search_simple=1&action=process&json=1&page_size=1"
    try:
        r = requests.get(url, timeout=5).json()
        if 'products' in r and len(r['products']) > 0:
            nutri = r['products'][0].get('nutriments', {})
            return {
                "cal": float(nutri.get('energy-kcal_100g', 0)),
                "p": float(nutri.get('proteins_100g', 0)),
                "f": float(nutri.get('fat_100g', 0)),
                "c": float(nutri.get('carbohydrates_100g', 0))
            }
    except: pass
    return {"cal": 0, "p": 0, "f": 0, "c": 0}

def ask_ai_debug(content):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""
    Analyze text: "{content[:12000]}"
    Extract ONLY the recipe. 
    JSON keys MUST be "steps" and "api_data" (with "n" and "w").
    Return VALID JSON ONLY.
    """
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0
    }
    
    # Використовуємо прямий URL, щоб уникнути помилки InvalidSchema
    return requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=30)

# --- UI ---
source_input = st.text_input("Вставте посилання або текст рецепта:")

if st.button("🚀 Запустити аналіз"):
    if source_input:
        source_input = source_input.strip()
        final_text = source_input
        
        if source_input.startswith("http"):
            with st.spinner('Зчитую сайт...'):
                final_text = get_text_from_url(source_input)
                if "Помилка" in final_text:
                    st.error(final_text)
                    st.stop()

        with st.spinner('AI обробляє дані...'):
            response = ask_ai_debug(final_text)
            
            if response is not None and response.status_code == 200:
                with st.expander("🛠️ DEBUG LOG", expanded=False):
                    st.json(response.json())
                
                raw_content = response.json()['choices'][0]['message']['content']
                
                try:
                    json_match = re.search(r'\{.*\}', raw_content, re.DOTALL)
                    data = json.loads(json_match.group())
                    
                    col1, col2 = st.columns([1.5, 1])
                    with col1:
                        st.subheader("📖 Інструкція")
                        for i, s in enumerate(data.get('steps', []), 1): st.write(f"{i}. {s}")
                        
                    with col2:
                        st.subheader("📊 Розрахунок БЖВ")
                        totals = {"cal": 0, "p": 0, "f": 0, "c": 0}
                        items = data.get('api_data', [])
                        
                        for item in items:
                            # Універсальний пошук ключів (захист від ШІ)
                            name = item.get('n') or item.get('н') or item.get('name')
                            weight = item.get('w') or item.get('в') or item.get('weight') or 0
                            
                            if name:
                                n = fetch_nutrition(name)
                                c_item = (n['cal'] * weight) / 100
                                totals["cal"] += c_item
                                totals["p"] += (n['p'] * weight) / 100
                                totals["f"] += (n['f'] * weight) / 100
                                totals["c"] += (n['c'] * weight) / 100
                                st.write(f"🔹 **{name}** ({weight}г) — {int(c_item)} ккал")
                        
                        st.divider()
                        st.metric("УСЬОГО", f"{int(totals['cal'])} ккал")
                        st.bar_chart({"Б": totals['p'], "Ж": totals['f'], "В": totals['c']})
                        
                except Exception as e:
                    st.error(f"Помилка розбору: {e}")
            else:
                st.error(f"Помилка API Groq. Статус: {response.status_code if response else 'Немає відповіді'}")
    else:
        st.warning("Введіть дані.")
