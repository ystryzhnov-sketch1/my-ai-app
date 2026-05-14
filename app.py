import streamlit as st
import requests
import json

# КОНФІГУРАЦІЯ GROQ (Llama 3)
# Отримайте безкоштовний ключ тут: https://console.groq.com/keys
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

st.set_page_config(page_title="AI Recipe Scanner", page_icon="🥗")

st.title("🥗 Безкоштовний AI Сканер (Llama 3)")
st.write("Аналіз інгредієнтів без обмежень Google API.")

source_input = st.text_input("Вставте текст або посилання:", placeholder="Наприклад: 2 яйця та 100г бекону")

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

def ask_llama(input_data):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""
    Ти — кулінарний помічник. Витягни інгредієнти та їх вагу з цього тексту: "{input_data}".
    Поверни відповідь ТІЛЬКИ у форматі JSON масиву:
    [
      {{"name": "назва продукту", "weight": 100}}
    ]
    Якщо вага не вказана, постав середню порцію. Не пиши нічого, крім JSON.
    """
    
    payload = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }
    
    with st.expander("🛠️ Debug Logs"):
        try:
            response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=15)
            st.write(f"Статус: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                raw_content = result['choices'][0]['message']['content']
                st.code(raw_content)
                
                # Очищення JSON
                start = raw_content.find('[')
                end = raw_content.rfind(']') + 1
                return json.loads(raw_content[start:end])
            else:
                st.error(f"Помилка: {response.text}")
        except Exception as e:
            st.error(f"Помилка: {e}")
    return []

if st.button("🚀 Розрахувати"):
    if source_input:
        if GROQ_API_KEY == "ВАШ_КЛЮЧ_GROQ_ТУТ":
            st.error("Будь ласка, вставте свій API ключ від Groq!")
        else:
            ingredients = ask_llama(source_input)
            if ingredients:
                st.subheader("📊 Результати:")
                total_cal = 0
                for item in ingredients:
                    data = get_nutrition(item['name'])
                    item_cal = (data['cal'] * item['weight']) / 100
                    total_cal += item_cal
                    st.write(f"✅ **{data['name']}** ({item['weight']}г) — **{int(item_cal)} ккал**")
                
                st.divider()
                st.metric("ЗАГАЛЬНА СУМА", f"{int(total_cal)} ккал")
    else:
        st.warning("Введіть дані.")
