import streamlit as st
import requests
import json

# Налаштування сторінки
st.set_page_config(page_title="AI Recipe Tester", page_icon="🥗")
st.title("🥗 AI Nutri-Scanner Prototype")
st.write("Це безкоштовна веб-версія для тестування функцій розбору рецептів.")

# 1. Поле для вводу (симуляція посилання або тексту)
recipe_input = st.text_area("Вставте текст рецепта або опис відео:", 
                            placeholder="Приклад: Салат з 200г курячого філе, 100г томатів та ложкою олії...")

# 2. Функція пошуку в безкоштовній базі продуктів
def get_nutrition(item_name):
    url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={item_name}&search_simple=1&action=process&json=1&page_size=1"
    try:
        r = requests.get(url).json()
        if r['products']:
            p = r['products'][0]
            return {
                "cal": p['nutriments'].get('energy-kcal_100g', 0),
                "p": p['nutriments'].get('proteins_100g', 0),
                "f": p['nutriments'].get('fat_100g', 0),
                "c": p['nutriments'].get('carbohydrates_100g', 0)
            }
    except:
        return None
    return None

# 3. Кнопка аналізу
if st.button("Проаналізувати ШІ ✨"):
    if recipe_input:
        with st.spinner('ШІ розбирає інгредієнти...'):
            # ТУТ СИМУЛЯЦІЯ РОБОТИ ШІ (можна підключити Groq API безкоштовно)
            # Для тесту ми візьмемо приклад розбору:
            st.success("ШІ розпізнав інгредієнти!")
            
            # Припустимо, ШІ витягнув ці дані (це те, що зробить Llama 3)
            mock_extracted = [
                {"name": "Chicken", "weight": 200},
                {"name": "Tomato", "weight": 100},
                {"name": "Olive Oil", "weight": 10}
            ]
            
            total_cal = 0
            cols = st.columns(len(mock_extracted))
            
            for i, item in enumerate(mock_extracted):
                nutri = get_nutrition(item['name'])
                if nutri:
                    item_cal = (nutri['cal'] * item['weight']) / 100
                    total_cal += item_cal
                    with cols[i]:
                        st.metric(item['name'], f"{item['weight']}г", f"{int(item_cal)} ккал")
            
            st.divider()
            st.header(f"Загальна калорійність: {int(total_cal)} ккал")
    else:
        st.warning("Будь ласка, введіть текст для аналізу.")
