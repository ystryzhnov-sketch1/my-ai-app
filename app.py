import streamlit as st
import requests
import json

# Конфігурація - ВИПРАВЛЕНО: Стабільний URL для Gemini 1.5 Flash
GEMINI_API_KEY = "AIzaSyDDaPe3W_cS6qaUxX6uY0XcZrzEfxN83lE"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

st.set_page_config(page_title="AI Recipe Scanner", page_icon="🥗", layout="centered")

st.title("🥗 AI Scanner: Від рецепта до калорій")
st.write("Аналіз посилань та тексту за допомогою Gemini 1.5 Flash")

source_input = st.text_input("Вставте посилання на відео/сайт або текст рецепта:", placeholder="https://...")

def get_nutrition(item_name):
    # Пошук в Open Food Facts (Безкоштовна база)
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
    # Промпт з подвійними дужками {{ }} для уникнення ValueError
    prompt_text = f"""
    Ти — кулінарний аналітик. Твоє завдання: витягни інгредієнти з джерела: "{input_data}".
    Поверни відповідь ВИКЛЮЧНО у форматі JSON списку:
    [
      {{"name": "назва продукту", "weight": вага_в_грамах}}
    ]
    Якщо вага не вказана, припусти логічну середню порцію. Не пиши нічого, крім JSON.
    """
    
    # Структура запиту згідно з документацією Google
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt_text
            }]
        }]
    }
    
    headers = {'Content-Type': 'application/json'}
    
    with st.expander("🛠️ Технічні логи (Debug)"):
        try:
            st.write(f"Відправка запиту на: {GEMINI_URL.split('?')[0]}")
            response = requests.post(GEMINI_URL, json=payload, headers=headers, timeout=15)
            
            st.write(f"Статус відповіді: {response.status_code}")
            
            resp_json = response.json()
            
            if response.status_code == 200:
                if 'candidates' in resp_json:
                    raw_text = resp_json['candidates'][0]['content']['parts'][0]['text']
                    st.code(raw_text, language="json")
                    
                    # Чистимо текст від можливого сміття (markdown)
                    clean_text = raw_text.replace("```json", "").replace("```", "").strip()
                    start = clean_text.find('[')
                    end = clean_text.rfind(']') + 1
                    
                    if start != -1 and end != 0:
                        return json.loads(clean_text[start:end])
                else:
                    st.error("Поле 'candidates' відсутнє. Можливо, контент заблоковано.")
            else:
                st.error(f"Помилка API: {resp_json}")
                
        except Exception as e:
            st.error(f"Помилка: {str(e)}")
    return []

if st.button("🚀 Розпізнати та порахувати"):
    if source_input:
        ingredients = ask_gemini_about_link(source_input)
        
        if ingredients:
            st.subheader("📊 Аналіз складу:")
            total_cal = 0
            chart_data = {}
            
            for item in ingredients:
                nutri = get_nutrition(item['name'])
                item_cal = (nutri['cal'] * item['weight']) / 100
                total_cal += item_cal
                chart_data[nutri['name']] = item_cal
                st.write(f"✅ **{nutri['name']}** ({item['weight']}г) — **{int(item_cal)} ккал**")
            
            st.divider()
            st.metric("ЗАГАЛЬНА КАЛОРІЙНІСТЬ", f"{int(total_cal)} ккал")
            st.bar_chart(chart_data)
        else:
            st.info("Не вдалося отримати інгредієнти. Спробуйте вставити назву страви або опис текстом.")
    else:
        st.warning("Введіть посилання або текст.")
