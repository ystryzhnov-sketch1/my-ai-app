import streamlit as st
import requests
import json

# Конфігурація
GEMINI_API_KEY = "AIzaSyDDaPe3W_cS6qaUxX6uY0XcZrzEfxN83lE"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

st.set_page_config(page_title="AI Video Recipe Scanner", page_icon="🎥")

st.title("🎥 AI Scanner: Рецепти з посилань")
st.write("Прототип для розпізнавання інгредієнтів з сайтів та відео.")

source_input = st.text_input("Вставте URL або текст:", placeholder="https://...")

def get_nutrition(item_name):
    # Пошук в Open Food Facts
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

def ask_gemini_about_link(input_data):
    # Використовуємо подвійні дужки {{ }} щоб уникнути ValueError
    prompt = f"""
    Ти — кулінарний експерт. Проаналізуй вміст: "{input_data}".
    Витягни список інгредієнтів та їх вагу.
    Відповідь надай ВИКЛЮЧНО у форматі JSON списку:
    [
      {{"name": "назва продукту українською", "weight": 100}}
    ]
    Якщо вага не вказана, вкажи середню вагу для цього інгредієнта в цій страві.
    Не пиши ніякого тексту, крім JSON.
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        response = requests.post(GEMINI_URL, json=payload, timeout=15)
        resp_json = response.json()
        
        if 'candidates' in resp_json:
            raw_text = resp_json['candidates'][0]['content']['parts'][0]['text']
            # Очищення тексту від Markdown-розмітки
            clean_text = raw_text.replace("```json", "").replace("```", "").strip()
            
            # Знаходимо початок і кінець масиву JSON
            start = clean_text.find('[')
            end = clean_text.rfind(']') + 1
            if start != -1 and end != 0:
                return json.loads(clean_text[start:end])
        else:
            st.error("ШІ не зміг отримати дані. Можливо, посилання заблоковане.")
            return []
    except Exception as e:
        st.error(f"Помилка: {e}")
        return []
    return []

if st.button("🚀 Розпізнати"):
    if source_input:
        with st.spinner('Gemini аналізує посилання...'):
            ingredients = ask_gemini_about_link(source_input)
            
            if ingredients:
                total_cal = 0
                chart_data = {}
                
                st.subheader("📋 Результат:")
                for item in ingredients:
                    nutri = get_nutrition(item['name'])
                    item_cal = (nutri['cal'] * item['weight']) / 100
                    total_cal += item_cal
                    chart_data[nutri['name']] = item_cal
                    
                    st.write(f"**{nutri['name']}** — {item['weight']}г (~{int(item_cal)} ккал)")
                
                st.divider()
                st.metric("Загальна калорійність", f"{int(total_cal)} ккал")
                st.bar_chart(chart_data)
    else:
        st.warning("Введіть дані.")
