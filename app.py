import streamlit as st
import requests
import json

# Конфігурація
GEMINI_API_KEY = "AIzaSyDDaPe3W_cS6qaUxX6uY0XcZrzEfxN83lE"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

st.set_page_config(page_title="AI Scanner Debug Mode", page_icon="🛠️")

st.title("🛠️ AI Scanner + Debug Logs")
st.write("Аналіз посилань з детальним логуванням помилок.")

source_input = st.text_input("Вставте URL або текст:", placeholder="https://...")

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

def ask_gemini_about_link(input_data):
    prompt = f"""
    Ти — кулінарний експерт. Проаналізуй вміст: "{input_data}".
    Витягни список інгредієнтів та їх вагу.
    Відповідь надай ВИКЛЮЧНО у форматі JSON списку:
    [
      {{"name": "назва продукту українською", "weight": 100}}
    ]
    Не пиши ніякого тексту, крім JSON.
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    # Створюємо контейнер для логів
    with st.expander("📝 Технічні логи (Debug Info)"):
        try:
            st.write("--- Запит до Gemini API ---")
            response = requests.post(GEMINI_URL, json=payload, timeout=15)
            
            # Логуємо статус код
            st.write(f"Статус відповіді: {response.status_code}")
            
            resp_json = response.json()
            st.write("--- Повна відповідь API ---")
            st.json(resp_json) # Виводимо весь JSON від Google
            
            if 'candidates' in resp_json:
                raw_text = resp_json['candidates'][0]['content']['parts'][0]['text']
                st.write("--- Сирий текст від ШІ ---")
                st.code(raw_text)
                
                clean_text = raw_text.replace("```json", "").replace("```", "").strip()
                start = clean_text.find('[')
                end = clean_text.rfind(']') + 1
                
                if start != -1 and end != 0:
                    return json.loads(clean_text[start:end])
                else:
                    st.error("JSON не знайдено у тексті відповіді.")
            else:
                # Перевіряємо причину відмови (Finish Reason)
                if 'promptFeedback' in resp_json:
                    st.warning(f"Запит відхилено фільтрами безпеки: {resp_json['promptFeedback']}")
                st.error("Поле 'candidates' відсутнє у відповіді.")
                
        except Exception as e:
            st.error(f"Критична помилка виконання: {str(e)}")
    return []

if st.button("🚀 Розпізнати"):
    if source_input:
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
