import streamlit as st
import pandas as pd
import math
import json

# --- 0. НАСТРОЙКИ И ЗАГРУЗКА ДАННЫХ ---
# ТЕСТОВАЯ ВЕРСИЯ: Загружаем ТОЛЬКО 'price_main.csv'

# Глобальные параметры
DOLLAR_RATE = 43.5  # Глобальный курс доллара

# @st.cache_data - кеширует данные для быстрой работы
@st.cache_data
def load_data():
    try:
        data = {}
        
        # --- ЗАГРУЗКА "ЧИСТЫХ" CSV-ФАЙЛОВ ---
        # 1. Главный прайс (Жалюзи, Подоконники, Отливы)
        data['pricelist_main'] = pd.read_csv("price_main.csv")
        
        # --- Остальные прайсы отключены для теста ---
        # data['nets_kiev'] = pd.read_csv("nets_kiev.csv")
        # data['glass_units_prices'] = pd.read_csv("glass_units.csv")
        # data['film_prices_raw'] = pd.read_csv("security_film.csv")
        # data['roller_blinds'] = pd.read_csv("roller_blinds_solid.csv", skiprows=8)
        # data['roller_blinds'].columns = ['system_type', 'fabric', 'base_price_uah_sqm', 'width_example', 'height_example', 'area_example', 'final_price_example']

        # --- ОБРАБОТКА ДАННЫХ И ПАРАМЕТРОВ ---
        
        # ПАРАМЕТРЫ, КОТОРЫХ НЕТ В ФАЙЛАХ
        data['params'] = {
            "min_area_blinds": 0.7,
            "blinds_fuel_cost": 150,
            "blinds_margin_sqm": 800,
            "nets_margin_per_net": 350,
            "nets_delivery_cost": 200,
            "windowsill_fuel_cost": 150,
            "windowsill_application_fee": 200,
            "windowsill_markup": 500,
            "windowsill_cap_price": 90, # Добавил цену заглушки (т.к. ее нет в price_main.csv)
            "windowsill_master_commission_pm": 450, # Добавил комиссию (т.к. ее нет в price_main.csv)
            "drip_markup_pm": 500,
            "drip_delivery_cost": 400,
            "film_margin_sqm": 600,
            "film_delivery_cost": 150,
            "film_budget_fee": 40,
            "osb_sheet_purchase_price": 700,
            "osb_sheet_area": 3.125,
            "osb_cutting_per_sheet": 100,
            "osb_master_commission_sqm": 380,
            "osb_margin_sqm": 350,
            "osb_delivery_cost": 300
        }
        
        # --- Динамическая загрузка параметров (Отключена для теста) ---
        
        # data['glass_params'] = ...
        # data['roller_config'] = ...
        # data['film_prices_dict'] = ...

        return data
    except FileNotFoundError as e:
        st.error(f"ОШИКА: Не найден файл CSV: {e.filename}. Для этого теста нужен ТОЛЬКО 'price_main.csv' в той же папке.")
        return None
    except Exception as e:
        st.error(f"Произошла ошибка при загрузке данных: {e}")
        return None

# --- Вспомогательная функция для конвертации ---
def convert_to_float(value):
    """Конвертирует строку (например, "1,56") в число (1.56)"""
    return float(str(value).replace(',', '.'))

# Загружаем данные
data = load_data()

# --- 1. ЛОГИКА РАСЧЕТОВ ---
# (Весь код для других услуг остается здесь, но он не будет вызываться)

def calculate_horizontal_blinds_price(params, data):
    # ... (код для жалюзи) ...
    pass # Не используется в тесте

def calculate_roller_blinds_price(params, data):
    # ... (код для ролет) ...
    pass # Не используется в тесте

def calculate_mosquito_net_price(params, data):
    # ... (код для сеток) ...
    pass # Не используется в тесте

def calculate_glass_unit_price(params, data):
    # ... (код для стеклопакетов) ...
    pass # Не используется в тесте

def calculate_windowsill_price(params, data):
    # --- ЭТОТ КОД БУДЕТ РАБОТАТЬ ---
    try:
        df_pricelist = data['pricelist_main'] 
        CONFIG = data['params']
        
        # 1. Находим товар
        product_info = df_pricelist[
            (df_pricelist['Виріб'] == 'Підвіконня Економ') & 
            (df_pricelist['Вид виробу'] == params['brand']) & 
            (df_pricelist['Тип'] == params['texture']) & 
            (df_pricelist['Вартість'] == params['color']) & 
            (df_pricelist['Валюта'] == params['width_mm']) # Валюта = Ширина (мм)
        ].iloc[0]

        # 2. Получаем цену
        # Од виміру = Цена
        price_per_meter = convert_to_float(product_info['Од виміру'])
        currency = "грн" # В 'price_main.csv' для подоконников все в грн
        
        # 3. Берем параметры из CONFIG
        cap_price = CONFIG['windowsill_cap_price'] # Цена заглушки
        master_commission_pm = CONFIG['windowsill_master_commission_pm'] # Комиссия

        # 4. Расчет
        length = params['length']
        purchase_price = price_per_meter * length
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
        return {"error": "Не удалось найти подоконник. (Проверьте структуру 'price_main.csv')"}
    except Exception as e:
        return {"error": f"Непредвиденная ошибка в Подоконниках: {e}"}


def calculate_drip_price(params, data):
    # ... (код для отливов) ...
    pass # Не используется в тесте


def calculate_security_film_price(params, data):
    # ... (код для бронепленки) ...
    pass # Не используется в тесте

def calculate_osb_price(params, data):
    # ... (код для ОСБ) ...
    pass # Не используется в тесте


# --- 2. ГЛАВНЫЙ ДИСПЕТЧЕР ---
def calculate_total_price(service_name, params, data):
    if not data:
        return {"error": "Данные не загружены. Проверьте CSV файлы."}
    calculator_mapping = {
        # "horizontal_blinds": calculate_horizontal_blinds_price,
        # "roller_blinds": calculate_roller_blinds_price,
        # "mosquito_net": calculate_mosquito_net_price,
        # "glass_unit": calculate_glass_unit_price,
        "windowsill": calculate_windowsill_price,
        # "drip": calculate_drip_price,
        # "security_film": calculate_security_film_price,
        # "osb": calculate_osb_price
    }
    calculation_function = calculator_mapping.get(service_name)
    if calculation_function:
        try:
            return calculation_function(params, data)
        except Exception as e:
            return {"error": f"Критическая ошибка при расчете '{service_name}': {e}"}
    else:
        return {"error": f"Услуга с именем '{service_name}' не найдена."}


# --- 3. ИНТЕРФЕЙС (STREAMLIT) ---

st.title("Онлайн-калькулятор (Тест Подоконников)")

# --- ИЗМЕНЕНО: Оставляем только Подоконники ---
service_options = {
    "Подоконники": "windowsill",
    # "Жалюзи горизонтальные": "horizontal_blinds",
    # "Рулонные шторы": "roller_blinds",
    # "Антимоскитные сетки": "mosquito_net",
    # "Стеклопакеты": "glass_unit",
    # "Отливы": "drip",
    # "Бронепленка": "security_film",
    # "ОСБ-плиты": "osb"
}

if data:
    service_name_display = st.selectbox("Выберите услугу:", options=list(service_options.keys()))
    service_key = service_options[service_name_display]
    params = {}
    
    # Так как у нас только подоконники, код ниже можно упростить:
    params['length'] = st.number_input("Длина (в метрах):", min_value=0.1, value=1.0, step=0.1, key=f"{service_key}_length")
    
    try:
        # --- ИЗМЕНЕНО: Оставляем только 'windowsill' ---
        if service_key == "windowsill":
            st.subheader("Параметры подоконника")
            # Читаем из 'pricelist_main'
            df_options = data['pricelist_main'][data['pricelist_main']['Виріб'] == 'Підвіконня Економ']
            
            # 'Вид виробу' -> Бренд
            params['brand'] = st.selectbox(
                "Бренд:", options=df_options['Вид виробу'].unique(), key="sill_brand"
            )
            # 'Тип' -> Текстура
            df_options_texture = df_options[df_options['Вид виробу'] == params['brand']]
            params['texture'] = st.selectbox(
                "Текстура:", options=df_options_texture['Тип'].unique(), key="sill_texture"
            )
            # 'Вартість' -> Цвет
            df_options_color = df_options_texture[df_options_texture['Тип'] == params['texture']]
            params['color'] = st.selectbox(
                "Цвет:", options=df_options_color['Вартість'].unique(), key="sill_color"
            )
            # 'Валюта' -> Ширина (мм)
            df_options_width = df_options_color[
                (df_options_color['Вартість'] == params['color'])
            ]
            params['width_mm'] = st.selectbox(
                "Ширина (мм):", options=df_options_width['Валюта'].unique(), key="sill_width_mm"
            )
            params['num_caps'] = st.number_input("Количество заглушек:", min_value=0, value=2, step=1, key="sill_caps")
        
        # --- (Остальные 'elif' отключены) ---
        
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
