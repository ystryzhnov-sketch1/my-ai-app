import streamlit as st
import requests
import json
import re
from bs4 import BeautifulSoup

# --- КОНФІГУРАЦІЯ ---
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

st.set_page_config(page_title="AI Chef Pro (Web Reader)", page_icon="🌐", layout="wide")

st.title("🌐 AI Chef: Авто-рецепт за посиланням")
st.write("Вставте посилання на рецепт, і ШІ сам витягне дані та порахує БЖВ.")

# --- ФУНКЦІЇ ---

def get_text_from_url(url):
    """Функція для витягування тексту з веб-сторінки"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Використовуємо BeautifulSoup для очищення HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Видаляємо непотрібні елементи (скрипти, стилі, навігацію)
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.extract()
            
        # Отримуємо чистий текст
        text = soup.get_text(separator=' ', strip=True)
        return text
    except Exception as e:
        return f"Помилка при читанні сайту: {e}"

def fetch_nutrition(simple_name):
    """Пошук нутрієнтів у базі OpenFoodFacts"""
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
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    # Промпт із жорсткими обмеженнями (пункти 1 та 2)
    prompt = f"""
    Analyze this text and extract the recipe: "{content[:15000]}"
    
    RULES:
    1. Extract only the recipe that is present in the text.
    2. If there is NO recipe, return {{"error": "No recipe found in the provided text"}}.
    3. DO NOT invent, hallucinate, or use external knowledge. 
    4. "steps" must be word-for-word instructions from the text.
    5. "api_data" names must be in UKRAINIAN for database search.
    
    Return ONLY JSON:
    {{
      "steps": ["step 1", "step 2"],
      "api_data": [{{ "n": "product name", "w": weight_in_grams }}]
    }}
    """
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0
    }
    
    try:
        response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=30)
        return response
    except Exception as e:
        st.error(f"Network Error: {e}")
        return None

# --- UI ---
source_input = st.text_input("Вставте посилання на рецепт (або текст):", placeholder="https://klopotenko.com/...")

if st.button("🚀 Обробити"):
    if source_input:
        final_text = source_input
        
        # Перевірка: якщо це URL, зчитуємо сторінку
        if source_input.strip().startswith("http"):
            with st.spinner('Завантажую вміст сторінки...'):
                final_text = get_text_from_url(source_input)
                if "Помилка при читанні" in final_text:
                    st.error(final_text)
                    st.stop()

        with st.spinner('AI аналізує текст сторінки...'):
            response = ask_ai_debug(final_text)
            
            # Логи виводяться ЗАВЖДИ
            if response is not None:
                with st.expander("🛠️ DEBUG: FULL API RESPONSE", expanded=True):
                    st.write(f"Status Code: {response.status_code}")
                    try:
                        st.json(response.json())
                    except:
                        st.text(response.text)
            
            if response and response.status_code == 200:
                raw_text = response.json()['choices'][0]['message']['content']
                
                try:
                    # Чистимо JSON від можливих маркерів ```json
                    json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
                    data = json.loads(json_match.group()) if json_match else json.loads(raw_text)
                    
                    if "error" in data:
                        st.warning(f"⚠️ AI: {data['error']}")
                    else:
                        col1, col2 = st.columns([1.5, 1])
                        
                        with col1:
                            st.subheader("📖 Інструкція з сайту")
                            steps = data.get('steps', [])
                            if isinstance(steps, list):
                                for i, s in enumerate(steps, 1): st.write(f"{i}. {s}")
                            else:
                                st.write(steps)
                            
                        with col2:
                            st.subheader("📊 Розрахунок БЖВ")
                            totals = {"cal": 0, "p": 0, "f": 0, "c": 0}
                            
                            for item in data.get('api_data', []):
                                n = fetch_nutrition(item['n'])
                                w = item.get('w', 0)
                                
                                c_item = (n['cal'] * w) / 100
                                totals["cal"] += c_item
                                totals["p"] += (n['p'] * w) / 100
                                totals["f"] += (n['f'] * w) / 100
                                totals["c"] += (n['c'] * w) / 100
                                
                                st.write(f"🔹 **{item['n']}** ({w}г) — {int(c_item)} ккал")
                            
                            st.divider()
                            st.metric("ЗАГАЛЬНА ЕНЕРГІЯ", f"{int(totals['cal'])} ккал")
                            
                            st.write("**Співвідношення БЖВ (г):**")
                            st.bar_chart({"Б": totals['p'], "Ж": totals['f'], "В": totals['c']})
                            
                except Exception as e:
                    st.error(f"Помилка розбору даних: {e}")
            else:
                st.error("Помилка API Groq")
    else:
        st.warning("Введіть посилання або текст.")
