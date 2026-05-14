import streamlit as st
import requests
import json

# КОНФІГУРАЦІЯ GROQ
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

st.set_page_config(page_title="AI Recipe Scanner", page_icon="🥗")

st.title("🥗 AI Scanner: Перевірена версія (2026)")
st.write("Аналіз інгредієнтів через Llama 3.1")

source_input = st.text_input("Вставте текст або посилання:", placeholder="Наприклад: 2 яйця та 100г бекону")

def get_nutrition(item_name):
    """Шукає дані про калорійність у відкритій базі"""
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
    """Запит до ШІ для розпізнавання інгредієнтів"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""
    Ти — професійний дієтолог. Твоє завдання: витягни інгредієнти та їх вагу з тексту або опису відео за посиланням: "{input_data}".
    Поверни відповідь ТІЛЬКИ у форматі JSON масиву:
    [
      {{"name": "назва продукту українською", "weight": вага_в_грамах}}
    ]
    Якщо вага не вказана, припусти середню порцію. Не пиши жодного тексту, крім JSON.
    """
    
    payload = {
        "model": "llama-3.1-8b-instant",  # Оновлена модель
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }
    
    with st.expander("🛠️ Технічний звіт"):
        try:
            response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=15)
            if response.status_code == 200:
                result = response.json()
                raw_content = result['choices'][0]['message']['content']
                st.code(raw_content, language="json")
                
                # Очищення від Markdown
                start = raw_content.find('[')
                end = raw_content.rfind(']') + 1
                return json.loads(raw_content[start:end])
            else:
                st.error(f"Помилка API: {response.text}")
        except Exception as e:
            st.error(f"Помилка: {e}")
    return []

if st.button("🚀 Аналізувати склад"):
    if source_input:
        with st.spinner('ШІ розшифровує рецепт...'):
            ingredients = ask_ai(source_input)
            if ingredients:
                st.subheader("📊 Результати розрахунку:")
                total_cal = 0
                
                for item in ingredients:
                    data = get_nutrition(item['name'])
                    item_cal = (data['cal'] * item['weight']) / 100
                    total_cal += item_cal
                    st.write(f"✅ **{data['name']}** ({item['weight']}г) — **{int(item_cal)} ккал**")
                
                st.divider()
                st.metric("ЗАГАЛЬНА ЕНЕРГІЯ", f"{int(total_cal)} ккал")
            else:
                st.warning("ШІ не зміг розпізнати продукти. Спробуйте вставити текст інгредієнтів.")
    else:
        st.info("Будь ласка, вставте дані у поле вище.")
