import streamlit as st
import requests
import json

# Конфігурація - ВИПРАВЛЕНО: Використовуємо -latest версію моделі
GEMINI_API_KEY = "AIzaSyDDaPe3W_cS6qaUxX6uY0XcZrzEfxN83lE"
# Спробуємо найбільш універсальний шлях v1beta
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}"

st.set_page_config(page_title="AI Recipe Scanner", page_icon="🥗")

st.title("🥗 AI Scanner: Виправлена версія")
st.write("Якщо ви бачите це, додаток готовий до тесту.")

source_input = st.text_input("Вставте посилання або текст:", placeholder="Приклад: салат з 200г курки")

def get_nutrition(item_name):
    url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={item_name}&search_simple=1&action=process&json=1&page_size=1"
    try:
        r = requests.get(url, timeout=5).json()
        if 'products' in r and len(r['products']) > 0:
            p = r['products'][0]
            nutri = p.get('nutriments', {})
            return {
                "name": p.get('product_name_uk', p.get('product_name', item_name)),
                "cal": nutri.get('energy-kcal_100g', 0)
            }
    except:
        pass
    return {"name": item_name, "cal": 0}

def ask_gemini(input_data):
    # Промпт з подвійними дужками
    prompt_text = f"""
    Ти — дієтолог. Витягни інгредієнти з цього тексту/посилання: "{input_data}".
    Поверни JSON список об'єктів: [{{"name": "назва", "weight": вага_в_грамах}}].
    Тільки JSON, без тексту.
    """
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt_text}]
        }]
    }
    
    with st.expander("🛠️ Логи розробника"):
        try:
            response = requests.post(GEMINI_URL, json=payload, timeout=15)
            st.write(f"Статус: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                raw_content = result['candidates'][0]['content']['parts'][0]['text']
                st.code(raw_content)
                
                # Чистимо JSON
                clean_json = raw_content.replace("```json", "").replace("```", "").strip()
                start = clean_json.find('[')
                end = clean_json.rfind(']') + 1
                return json.loads(clean_json[start:end])
            else:
                st.error(f"Помилка API: {response.text}")
                # Якщо flash не знайдено, спробуємо дати пораду
                if "not found" in response.text.lower():
                    st.info("Порада: Спробуйте змінити модель на 'gemini-pro' у коді.")
        except Exception as e:
            st.error(f"Помилка: {e}")
    return []

if st.button("🚀 Аналіз"):
    if source_input:
        ingredients = ask_gemini(source_input)
        if ingredients:
            total_cal = 0
            for item in ingredients:
                data = get_nutrition(item['name'])
                item_cal = (data['cal'] * item['weight']) / 100
                total_cal += item_cal
                st.write(f"✅ {data['name']} ({item['weight']}г) — {int(item_cal)} ккал")
            st.divider()
            st.metric("Разом", f"{int(total_cal)} ккал")
    else:
        st.warning("Введіть дані.")
