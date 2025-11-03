import streamlit as st
import pandas as pd
import math
import json

# --- 0. НАСТРОЙКИ И ЗАГРУЗКА ДАННЫХ ---
# ТЕСТОВАЯ ВЕРСИЯ: Загружаем ТОЛЬКО 'price_main.csv'
# Эта версия кода написана специально для вашего "чистого" файла 
# 'price_main.csv' (который вы только что загрузили).

# Глобальные параметры
DOLLAR_RATE = 43.5  # Глобальный курс доллара

# @st.cache_data - кеширует данные для быстрой работы
@st.cache_data
def load_data():
    try:
        data = {}
        
        # --- ЗАГРУЗКА "ЧИСТОГО" CSV-ФАЙЛА ---
        data['pricelist_main'] = pd.read_csv("price_main.csv")
        
        # Очистка данных от лишних пробелов (ВАЖНО!)
        for col in data['pricelist_main'].columns:
            if data['pricelist_main'][col].dtype == 'object':
                data['pricelist_main'][col] = data['pricelist_main'][col].str.strip()

        # --- ПАРАМЕТРЫ, КОТОРЫХ НЕТ В ФАЙЛЕ ---
        data['params'] = {
            "windowsill_fuel_cost": 150,
            "windowsill_application_fee": 200,
            "windowsill_markup": 500,
            # ВАЖНО: Цена заглушки. Берем ее из конфига, т.к. в файле она в тексте
            "windowsill_cap_price": 50, # Поставьте сюда правильную цену заглушки
        }
        
        return data
    except FileNotFoundError as e:
        st.error(f"ОШИБКА: Не найден файл CSV: {e.filename}. Убедитесь, что вы переименовали ваш файл 'price_main - Лист1.csv' в 'price_main.csv' на GitHub.")
        return None
    except Exception as e:
        st.error(f"Произошла ошибка при загрузке данных: {e}")
        return None

# --- Вспомогательная функция для конвертации ---
def convert_to_float(value):
    """Конвертирует строку (например, "101,4") в число (101.4)"""
    return float(str(value).replace(',', '.'))

# Загружаем данные
data = load_data()

# --- 1. ЛОГИКА РАСЧЕТОВ ---

def calculate_windowsill_price(params, data):
    # --- ЭТОТ КОД НАПИСАН ДЛЯ ВАШЕЙ НОВОЙ ТАБЛИЦЫ ---
    try:
        df_pricelist = data['pricelist_main'] 
        CONFIG = data['params']
        
        # 1. Находим товар по НОВЫМ, "чистым" колонкам
        product_info = df_pricelist[
            (df_pricelist['Виріб'].str.contains('Підвіконня', na=False)) & 
            (df_pricelist['Місто'] == params['city']) &
            (df_pricelist['Бренд'] == params['brand']) & 
            (df_pricelist['Тип'] == params['texture']) & 
            (df_pricelist['Колір'] == params['color']) & 
            (df_pricelist['Од виміру'].astype(str) == str(params['width_mm'])) # 'Од виміру' = Ширина
        ].iloc[0]

        # 2. Получаем цену, валюту и комиссию из ПРАВИЛЬНЫХ колонок
        price_per_meter = convert_to_float(product_info['Вартість']) # Цена
        currency = str(product_info['Валюта'])
        
        # --- ИСПРАВЛЕНО (еще раз, на всякий случай): ---
        # Комиссия мастера (колонка 'Коміссія майстра')
        master_commission_pm = convert_to_float(product_info['Коміссія майстра']) 
        # --- КОНЕЦ ИСПРАВЛЕНИЯ ---
        
        cap_price = CONFIG['windowsill_cap_price'] # Цена заглушки

        # 3. Конвертация (на всякий случай)
        base_price_uah = price_per_meter
        if currency.lower() == 'доллар' or currency == '$':
            base_price_uah = price_per_meter * DOLLAR_RATE

        # 4. Расчет
        length = params['length']
        purchase_price = base_price_uah * length
        caps_total_cost = cap_price * params['num_caps']
        master_fee = master_commission_pm * length

        # 5. Итог
        final_price = (
            purchase_price + caps_total_cost + master_fee +
            CONFIG['windowsill_fuel_cost'] + CONFIG['windowsill_application_fee'] +
            CONFIG['windowsill_markup']
        )

        return {
            "calculation_details": {
                "Закупка подоконника": f"{purchase_price:.2f} грн",
                "Стоимость заглушек": f"{caps_total_cost:.2f} грн ({params['num_caps']} шт.)",
                "Работа мастера": f"{master_fee:.2f} грн",
                "Прочие расходы": f"{CONFIG['windowsill_fuel_cost'] + CONFIG['windowsill_application_fee'] + CONFIG['windowsill_markup']:.2f} грн"
            },
            "total_price_uah": f"{final_price:.2f}",
            "notes": f"Расчет для {length} пог.м."
        }
    except (IndexError, KeyError):
        return {"error": "Не удалось найти подоконник с выбранными параметрами."}
    except Exception as e:
        return {"error": f"Непредвиденная ошибка в Подоконниках: {e}"}


# --- 2. ГЛАВНЫЙ ДИСПЕТЧЕР ---
def calculate_total_price(service_name, params, data):
    if not data:
        return {"error": "Данные не загружены. Проверьте CSV файлы."}
    
    # В тесте работает только 'windowsill'
    if service_name == "windowsill":
        try:
            return calculate_windowsill_price(params, data)
        except Exception as e:
            return {"error": f"Критическая ошибка при расчете '{service_name}': {e}"}
    else:
        return {"error": f"Услуга с именем '{service_name}' не найдена (включен тестовый режим)."}


# --- 3. ИНТЕРФЕЙС (STREAMLIT) ---

st.title("Онлайн-калькулятор (Тест Подоконников)")

service_options = {
    "Подоконники": "windowsill",
}

if data:
    service_name_display = st.selectbox("Выберите услугу:", options=list(service_options.keys()))
    service_key = service_options[service_name_display]
    params = {}
    
    params['length'] = st.number_input("Длина (в метрах):", min_value=0.1, value=1.0, step=0.1, key=f"{service_key}_length")
    
    try:
        if service_key == "windowsill":
            st.subheader("Параметры подоконника")
            
            # ИСПРАВЛЕНО: Читаем из "чистого" файла
            df_options = data['pricelist_main'][data['pricelist_main']['Виріб'].str.contains('Підвіконня', na=False)]
            
            if df_options.empty:
                st.error("ОШИБКА: Не найдено ни одной строки со словом 'Підвіконня' в колонке 'Виріб' вашего файла 'price_main.csv'.")
            else:
                # --- ЕСЛИ ВСЕ ХОРОШО, ПОКАЗЫВАЕМ ПОЛЯ ---
                
                params['city'] = st.selectbox(
                    "Город:", options=df_options['Місто'].unique(), key="sill_city"
                )
                
                df_options_brand = df_options[df_options['Місто'] == params['city']]
                params['brand'] = st.selectbox(
                    "Бренд:", options=df_options_brand['Бренд'].unique(), key="sill_brand"
                )
                
                df_options_texture = df_options_brand[df_options_brand['Бренд'] == params['brand']]
                params['texture'] = st.selectbox(
                    "Тип (текстура):", options=df_options_texture['Тип'].unique(), key="sill_texture"
                )
                
                df_options_color = df_options_texture[df_options_texture['Тип'] == params['texture']]
                params['color'] = st.selectbox(
                    "Цвет:", options=df_options_color['Колір'].unique(), key="sill_color"
                )
                
                df_options_width = df_options_color[df_options_color['Колір'] == params['color']]
                width_options = df_options_width['Од виміру'].astype(str).unique()
                
                params['width_mm'] = st.selectbox(
                    "Ширина (мм):", options=width_options, key="sill_width_mm"
                )
                
                params['num_caps'] = st.number_input("Количество заглушек:", min_value=0, value=2, step=1, key="sill_caps")
        
        st.divider() 
        if st.button("Рассчитать стоимость", type="primary"):
            result = calculate_total_price(service_key, params, data)
            if "error" in result:
                st.error(f"Ошибка в расчете: {result['error']}")
            else:
                st.success(f"Итоговая стоимость: {result['total_price_uah']} грн")
                if "calculation_details" in result:
                    st.json(result['calculation_details'])
                if "notes" in result:
                    st.info(result['notes'])
    
    except (KeyError, IndexError) as e:
        st.error(f"Ошибка при отображении опций: {e}. Возможно, в 'price_main.csv' не хватает данных или колонка названа неверно.")
    except Exception as e:
        st.error(f"Критическая ошибка интерфейса: {e}")

else:
    st.error("Не удалось загрузить данные. Проверьте наличие 'price_main.csv' в папке.")
