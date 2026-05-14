import streamlit as st
import requests
import json

# Налаштування Gemini API
GEMINI_API_KEY = "AIzaSyDDaPe3W_cS6qaUxX6uY0XcZrzEfxN83lE"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

st.set_page_config(page_title="AI Nutri-Scanner", page_icon="🥗")

st.title("🥗 Справжній AI Nutri-Scanner")
st.write("Тепер працює на базі Gemini 1.5 Flash")

# Поле для введення
recipe_text = st.text_area("Вставте опис рецепта (наприклад: 'я зробив салат з 200г курки та 2 помідорів'):", height=150)

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

def ask_gemini(text):
    prompt = f"""
    Ти дієтолог-аналітик. Проаналізуй цей текст рецепта: "{text}".
    Витягни всі інгредієнти та їх вагу в грамах (якщо вага не вказана, припусти логічну середню порцію).
    Поверни відповідь ТІЛЬКИ у форматі чистого JSON списку об'єктів, без зайвих слів.
    Приклад: [{"name": "курка", "weight": 200}, {"name": "огірок", "weight": 50}]
    """
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(GEMINI_URL, json=payload)
    
    try:
        raw_text = response.json()['candidates'][0]['content']['parts'][0]['text']
        # Очищення від можливих Markdown лапок
        clean_json = raw_text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except Exception as e:
        st.error(f"ШІ не зміг розпарсити текст: {e}")
        return []

if st.button("🚀 Розрахувати БЖВ"):
    if recipe_text:
        with st.spinner('Gemini аналізує склад...'):
            ingredients = ask_gemini(recipe_text)
            
            if ingredients:
                st.subheader("📋 Розпізнані інгредієнти:")
                total_cal = 0
                chart_data = {}

                for item in ingredients:
                    data = get_nutrition(item['name'])
                    item_cal = (data['cal'] * item['weight']) / 100
                    total_cal += item_cal
                    chart_data[data['name']] = item_cal
                    
                    st.write(f"🔸 **{data['name']}**: {item['weight']}г — ~{int(item_cal)} ккал")

                st.divider()
                st.metric("Загальна енергетична цінність", f"{int(total_cal)} ккал")
                st.bar_chart(chart_data)
            else:
                st.error("ШІ не знайшов інгредієнтів у тексті.")
    else:
        st.warning("Будь ласка, введіть текст рецепта.")
