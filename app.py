import streamlit as st
import requests

st.set_page_config(page_title="AI Recipe Scanner", page_icon="🍲")

# Заголовок
st.title("🍲 AI Recipe Scanner (Web Test)")
st.info("Вставте посилання на відео або текст рецепта нижче.")

# Поле для введення
url_input = st.text_input("Посилання на TikTok / Reels / YouTube:", placeholder="https://www.tiktok.com/@user/video/...")
text_manual = st.text_area("Або вставте опис відео/текст рецепта сюди:")

# Функція пошуку калорій (Open Food Facts)
def get_nutrition(item_name):
    url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={item_name}&search_simple=1&action=process&json=1&page_size=1"
    try:
        r = requests.get(url, timeout=5).json()
        if r['products']:
            p = r['products'][0]
            nutri = p.get('nutriments', {})
            return {
                "name": p.get('product_name_uk', p.get('product_name', item_name)),
                "cal": nutri.get('energy-kcal_100g', 0),
                "p": nutri.get('proteins_100g', 0),
                "f": nutri.get('fat_100g', 0),
                "c": nutri.get('carbohydrates_100g', 0)
            }
    except:
        return None
    return None

# Кнопка запуску
if st.button("🚀 Проаналізувати"):
    if url_input or text_manual:
        with st.spinner('ШІ аналізує вміст...'):
            # СИМУЛЯЦІЯ РОБОТИ ШІ (Тут у майбутньому буде запит до Gemini/Groq)
            # Для тесту ми «витягуємо» дані з прикладу
            st.subheader("📊 Результати аналізу:")
            
            # Тимчасовий список (імітація того, що знайшов ШІ)
            # В ідеалі ШІ бачить посилання і каже: "Там куряче філе і рис"
            mock_data = [
                {"name": "Куряче філе", "weight": 250},
                {"name": "Рис басматі", "weight": 100},
                {"name": "Олія", "weight": 10}
            ]
            
            total_cal = 0
            for item in mock_data:
                data = get_nutrition(item['name'])
                if data:
                    item_cal = (data['cal'] * item['weight']) / 100
                    total_cal += item_cal
                    st.write(f"✅ **{data['name']}**: {item['weight']}г — {int(item_cal)} ккал")
            
            st.divider()
            st.metric("Загальна калорійність", f"{int(total_cal)} ккал")
            
            # Додаємо графік для наочності
            st.bar_chart({item['name']: (get_nutrition(item['name'])['cal'] * item['weight'] / 100) for item in mock_data})
    else:
        st.warning("Будь ласка, додайте дані для аналізу.")
