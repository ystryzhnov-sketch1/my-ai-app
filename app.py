import streamlit as st
import requests
import json

GEMINI_API_KEY = "AIzaSyDDaPe3W_cS6qaUxX6uY0XcZrzEfxN83lE"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

st.set_page_config(page_title="AI Video Recipe Scanner", page_icon="🎥")

st.title("🎥 AI Scanner: Рецепти з відео")
st.write("Вставте посилання на відео (YouTube, TikTok) або текст рецепта.")

# Поле для посилання
source_input = st.text_input("URL відео або текст:", placeholder="https://www.youtube.com/watch?v=...")

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
    # Додаємо налаштування, щоб ШІ не блокував запити через фільтри безпеки
    prompt = f"""
    Ти — кулінарний аналітик. Твоє завдання: витягни список інгредієнтів з цього джерела: "{input_data}".
    
    Якщо це посилання на сайт чи відео, використай свої знання про цей рецепт або проаналізуй доступний текст.
    Якщо ти не можеш відкрити посилання, спробуй здогадатися про склад страви за назвою в URL.
    
    Відповідь надай ВИКЛЮЧНО у форматі JSON списку:
    [{"name": "назва продукту", "weight": вага_в_грамах}]
    
    Не пиши ніяких пояснень, тільки JSON. Якщо інгредієнтів немає, поверни [].
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    try:
        response = requests.post(GEMINI_URL, json=payload, timeout=15)
        resp_json = response.json()
        
        # Перевірка, чи є відповідь у списку candidates
        if 'candidates' in resp_json and resp_json['candidates'][0]['content']['parts']:
            raw_text = resp_json['candidates'][0]['content']['parts'][0]['text']
            # Витягуємо тільки частину з JSON (якщо ШІ додав зайвий текст)
            start_index = raw_text.find('[')
            end_index = raw_text.rfind(']') + 1
            if start_index != -1 and end_index != 0:
                clean_json = raw_text[start_index:end_index]
                return json.loads(clean_json)
        else:
            # Вивід помилки від самого Google API для діагностики
            st.error(f"Помилка API: {resp_json.get('error', {}).get('message', 'Невідома помилка')}")
            return []
            
    except Exception as e:
        st.error(f"Помилка обробки: {str(e)}")
        return []
    return []
if st.button("🔍 Розпізнати рецепт"):
    if source_input:
        with st.spinner('ШІ "дивиться" відео та шукає інгредієнти...'):
            ingredients = ask_gemini_about_link(source_input)
            
            if ingredients:
                st.success(f"Знайдено інгредієнтів: {len(ingredients)}")
                
                total_cal = 0
                chart_data = {}

                for item in ingredients:
                    with st.expander(f"🍎 {item['name']} ({item['weight']}г)"):
                        data = get_nutrition(item['name'])
                        item_cal = (data['cal'] * item['weight']) / 100
                        total_cal += item_cal
                        chart_data[item['name']] = item_cal
                        st.write(f"Калорійність на 100г: {data['cal']} ккал")
                        st.write(f"У цій порції: **{int(item_cal)} ккал**")

                st.divider()
                st.sidebar.metric("ЗАГАЛЬНА СУМА", f"{int(total_cal)} ккал")
                st.bar_chart(chart_data)
            else:
                st.error("Не вдалося витягнути дані. Спробуйте вставити опис відео текстом.")
    else:
        st.warning("Вставте посилання або текст.")
