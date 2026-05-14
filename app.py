import streamlit as st
import requests
import json
import re

# --- КОНФІГУРАЦІЯ ---
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

st.set_page_config(page_title="AI Chef Pro (BZhV)", page_icon="🧬", layout="wide")

st.title("🧬 AI Chef: Рецепт + БЖВ")
st.write("Аналіз калорій, білків, жирів та вуглеводів на основі тексту рецепта.")

# --- UI ---
source_input = st.text_area("Вставте текст рецепта (не посилання!):", height=200, placeholder="Скопіюйте сюди інгредієнти та кроки приготування з сайту...")

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
    
    # Оновлений промпт за твоїм погодженням (пункти 1 та 2)
    prompt = f"""
    Analyze this text: "{content}"
    If there is no recipe content, return {{"error": "No recipe found"}}.
    Do not invent or imagine information. Extract only what is present.
    
    Format as JSON:
    1. "steps": full instructions verbatim.
    2. "api_data": [{{ "n": "product name in UKRAINIAN", "w": weight_in_grams }}]
    
    Return ONLY JSON.
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

if st.button("🚀 Виконати повний аналіз"):
    if source_input:
        with st.spinner('AI аналізує реальний текст...'):
            response = ask_ai_debug(source_input)
            
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
                    # Покращений парсинг JSON (пункт 3)
                    json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
                    if json_match:
                        data = json.loads(json_match.group())
                    else:
                        data = json.loads(raw_text)
                    
                    if "error" in data:
                        st.warning("⚠️ AI каже: " + data["error"])
                    else:
                        col1, col2 = st.columns([1.5, 1])
                        
                        with col1:
                            st.subheader("📖 Інструкція")
                            steps = data.get('steps', [])
                            if isinstance(steps, list):
                                for s in steps: st.write(f"• {s}")
                            else:
                                st.write(steps)
                            
                        with col2:
                            st.subheader("📊 Нутрієнти (БЖВ)")
                            totals = {"cal": 0, "p": 0, "f": 0, "c": 0}
                            
                            items = data.get('api_data', [])
                            for item in items:
                                n = fetch_nutrition(item['n'])
                                w = item.get('w', 0)
                                
                                c_item = (n['cal'] * w) / 100
                                p_item = (n['p'] * w) / 100
                                f_item = (n['f'] * w) / 100
                                carb_item = (n['c'] * w) / 100
                                
                                totals["cal"] += c_item
                                totals["p"] += p_item
                                totals["f"] += f_item
                                totals["c"] += carb_item
                                
                                st.write(f"🔹 **{item['n']}** ({w}г)")
                                st.caption(f"Ккал: {int(c_item)} | Б: {round(p_item,1)}г | Ж: {round(f_item,1)}г | В: {round(carb_item,1)}г")
                            
                            st.divider()
                            st.metric("ЗАГАЛЬНА ЕНЕРГІЯ", f"{int(totals['cal'])} ккал")
                            
                            st.write("**Співвідношення БЖВ (грами):**")
                            b_data = {"Білки": totals['p'], "Жири": totals['f'], "Вуглеводи": totals['c']}
                            st.bar_chart(b_data)
                        
                except Exception as e:
                    st.error(f"Помилка розбору даних: {e}")
            else:
                st.error("Помилка API Groq")
    else:
        st.warning("Вставте текст рецепта.")

st.divider()
st.caption("Логи залишаються на екрані.")
