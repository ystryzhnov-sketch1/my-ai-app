import streamlit as st
import requests
import json

# --- КОНФІГУРАЦІЯ ---
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

st.set_page_config(page_title="AI Chef Verbatim", page_icon="👨‍🍳", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .recipe-box { background-color: #ffffff; padding: 20px; border-radius: 15px; border-left: 5px solid #ff4b4b; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("👨‍🍳 AI Екстрактор: Рецепти Клопотенка та інших")
st.write("Копіює рецепт слово в слово та рахує калорії.")

# --- ВВІД ДАНИХ ---
source_input = st.text_area("Вставте посилання або скопійований текст із сайту:", 
                            placeholder="Вставте посилання на рецепт...",
                            height=100)

# --- ФУНКЦІЇ ---

def get_nutrition(item_name):
    """Покращений пошук калорійності"""
    # Очищуємо назву від зайвих слів для кращого пошуку
    search_query = item_name.split(',')[0].split('(')[0].replace("червоний", "").strip()
    url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={search_query}&search_simple=1&action=process&json=1&page_size=1"
    try:
        r = requests.get(url, timeout=5).json()
        if 'products' in r and len(r['products']) > 0:
            p = r['products'][0]
            nutri = p.get('nutriments', {})
            cal = nutri.get('energy-kcal_100g') or nutri.get('energy-kcal') or 0
            return {
                "name": p.get('product_name_uk', p.get('product_name', item_name)),
                "cal": cal
            }
    except:
        pass
    return {"name": item_name, "cal": 0}

def ask_ai(input_data):
    """Запит до ШІ для точного копіювання тексту"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""
    Ти — асистент-архіваріус. Твоє завдання: максимально точно витягнути дані з джерела: "{input_data}".
    
    Поверни відповідь ТІЛЬКИ у форматі JSON:
    {{
      "original_ingredients": ["список інгредієнтів точно як у тексті"],
      "clean_ingredients": [
        {{"name": "чиста назва продукту для пошуку в базі", "weight": вага_цифрою}}
      ],
      "original_instructions": "Покрокові кроки приготування СЛОВО В СЛОВО як в оригіналі."
    }}
    
    ВАЖЛИВО: 
    1. Поле original_instructions має містити пряме цитування тексту приготування.
    2. Якщо це посилання на відомий сайт (наприклад Klopotenko), згадай цей рецепт і витягни його кроки.
    """
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "response_format": {"type": "json_object"}
    }
    
    try:
        response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=20)
        return response.json()['choices'][0]['message']['content'] if response.status_code == 200 else None
    except:
        return None

# --- ЛОГІКА ДОДАТКА ---

if st.button("🚀 Розпізнати рецепт"):
    if source_input:
        with st.spinner('Синхронізація з оригіналом...'):
            raw_response = ask_ai(source_input)
            
            if raw_response:
                data = json.loads(raw_response)
                orig_ing = data.get('original_ingredients', [])
                clean_ing = data.get('clean_ingredients', [])
                instructions = data.get('original_instructions', "")

                col1, col2 = st.columns([1.5, 1])

                with col1:
                    st.subheader("📖 Оригінальний рецепт")
                    st.markdown(f"<div class='recipe-box'>{instructions}</div>", unsafe_allow_html=True)
                    
                    st.subheader("🛒 Список продуктів (як на сайті)")
                    for ing in orig_ing:
                        st.write(f"▪️ {ing}")
                    
                with col2:
                    st.subheader("📊 Розрахунок Ккал")
                    total_cal = 0
                    
                    for item in clean_ing:
                        nutri = get_nutrition(item['name'])
                        # Якщо база видала 0, спробуємо підставити середнє значення (опціонально)
                        cals_per_100g = nutri['cal'] if nutri['cal'] > 0 else 0
                        
                        item_cal = (cals_per_100g * item['weight']) / 100
                        total_cal += item_cal
                        
                        status_icon = "🟢" if item_cal > 0 else "⚪"
                        st.write(f"{status_icon} **{item['name']}** ({item['weight']}г): {int(item_cal)} ккал")
                    
                    st.divider()
                    st.metric("ЗАГАЛЬНА ЕНЕРГІЯ", f"{int(total_cal)} ккал")
                    if total_cal == 0:
                        st.warning("База даних Open Food Facts не знайшла калорійність для деяких назв. Спробуйте змінити назву інгредієнта на більш просту.")
            else:
                st.error("ШІ не зміг отримати доступ до даних за посиланням.")
    else:
        st.warning("Вставте посилання.")
