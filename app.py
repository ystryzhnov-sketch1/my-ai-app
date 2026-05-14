import streamlit as st
import requests
import json

# --- КОНФІГУРАЦІЯ ---
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

st.set_page_config(page_title="AI Chef & Nutri-Scanner", page_icon="👨‍🍳", layout="wide")

# Стилізація інтерфейсу
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_index=True)

st.title("👨‍🍳 AI Chef: Рецепти та Калорії")
st.write("Вставте посилання на відео або опис страви — я розрахую нутрієнти та навчу готувати.")

# --- ВВІД ДАНИХ ---
source_input = st.text_area("Посилання на відео/сайт або назва страви:", 
                            placeholder="Наприклад: https://youtube.com/... або 'дієтична лазанья з кабачків'",
                            height=100)

# --- ФУНКЦІЇ ---

def get_nutrition(item_name):
    """Шукає калорійність у базі Open Food Facts"""
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

def ask_ai(input_data):
    """Запит до Llama 3.1 для створення рецепта та списку продуктів"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""
    Ти — шеф-кухар та дієтолог. Проаналізуй: "{input_data}".
    
    Поверни відповідь ВИКЛЮЧНО у форматі JSON:
    {{
      "ingredients": [
        {{"name": "назва продукту", "weight": вага_в_грамах}}
      ],
      "instructions": "Покроковий рецепт приготування українською мовою."
    }}
    
    ПРАВИЛА:
    1. Не повторюй інгредієнти.
    2. Якщо ваги немає в джерелі, припусти логічну вагу.
    3. Інструкція має бути чіткою та структурованою.
    4. ТІЛЬКИ JSON, жодного зайвого тексту.
    """
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "response_format": {"type": "json_object"}
    }
    
    try:
        response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=20)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            st.error(f"Помилка API: {response.text}")
            return None
    except Exception as e:
        st.error(f"Помилка зв'язку: {e}")
        return None

# --- ЛОГІКА ДОДАТКА ---

if st.button("🚀 Отримати повний рецепт"):
    if source_input:
        with st.spinner('ШІ аналізує страву та пише інструкції...'):
            raw_response = ask_ai(source_input)
            
            if raw_response:
                data = json.loads(raw_response)
                ingredients = data.get('ingredients', [])
                instructions = data.get('instructions', "")

                # Створюємо дві колонки: зліва інструкції, справа калорії
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.subheader("📖 Покрокове приготування")
                    st.info(instructions)
                    
                with col2:
                    st.subheader("📊 Харчова цінність")
                    total_cal = 0
                    chart_data = {}
                    
                    for item in ingredients:
                        nutri = get_nutrition(item['name'])
                        item_cal = (nutri['cal'] * item['weight']) / 100
                        total_cal += item_cal
                        chart_data[nutri['name']] = item_cal
                        st.write(f"🔹 {nutri['name']} ({item['weight']}г): **{int(item_cal)} ккал**")
                    
                    st.divider()
                    st.metric("ЗАГАЛЬНА ЕНЕРГІЯ", f"{int(total_cal)} ккал")
                    if chart_data:
                        st.bar_chart(chart_data)
                
                # Додатково: Логи для перевірки (можна приховати)
                with st.expander("📝 Технічні дані"):
                    st.json(data)
            else:
                st.error("Не вдалося отримати дані від ШІ.")
    else:
        st.warning("Будь ласка, вставте посилання або опис.")
