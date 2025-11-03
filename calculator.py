import streamlit as st
import pandas as pd
import math
import json

# --- 0. НАСТРОЙКИ И ЗАГРУЗКА ДАННЫХ ---

# Глобальные параметры (можно менять прямо здесь)
DOLLAR_RATE = 43.5  # Глобальный курс доллара

# @st.cache_data - эта команда кеширует данные, чтобы они не загружались каждый раз
# при изменении полей. Это делает калькулятор очень быстрым.
@st.cache_data
def load_data():
    try:
        # Словарь для хранения всех наших данных
        data = {}
        
        # Загружаем все CSV
        data['pricelist_new'] = pd.read_csv("Формула просчета стоимости.xlsx - Прайс_new.csv", header=1)
        data['blinds_params'] = pd.read_csv("Формула просчета стоимости.xlsx - Жалюзи.csv", skiprows=1, index_col=1)
        data['roller_blinds'] = pd.read_csv("Формула просчета стоимости.xlsx - РОЛЕТЫ_СПЛОШНЫЕ.csv", skiprows=8)
        data['nets_kiev'] = pd.read_csv("Формула просчета стоимости.xlsx - !Сетки_Киев.csv")
        data['glass_units'] = pd.read_csv("Формула просчета стоимости.xlsx - Стеклопакеты.csv", skiprows=44)
        data['glass_params_raw'] = pd.read_csv("Формула просчета стоимости.xlsx - Стеклопакеты.csv", nrows=40)
        data['windowsills'] = pd.read_csv("Формула просчета стоимости.xlsx - Подоконники.csv", skiprows=8)
        data['drips'] = pd.read_csv("Формула просчета стоимости.xlsx - Отливы.csv", skiprows=8)
        data['film'] = pd.read_csv("Формула просчета стоимости.xlsx - Бронепленка.csv", skiprows=15).set_index("Unnamed: 0")

        # Дополнительная обработка данных
        
        # Параметры для Стеклопакетов
        params_dict = data['glass_params_raw'].set_index(data['glass_params_raw'].columns[0])[data['glass_params_raw'].columns[1]].to_dict()
        data['glass_params'] = {k: v for k, v in params_dict.items() if pd.notna(v)}
        
        # Параметры для Рулонных штор
        data['roller_config'] = {
            "dollar_rate": 43.5,
            "delivery_cost": 150,
            "application_fee": 200,
            "surcharges": {"width_gt_height_percent": 10, "brown_system_usd": 1},
            "commissions": {"открытый тип": 200, "закрытый тип": 250},
            "area_rounding": {"19 мм": 0.7, "25 мм": 1.0, "35 мм": 1.0}
        }
        data['roller_blinds'].columns = ['system_type', 'fabric', 'base_price_uah_sqm', 'width_example', 'height_example', 'area_example', 'final_price_example']

        # Параметры для Сеток
        data['nets_config'] = {"margin_per_net": 350, "delivery_cost": 200}
        
        # Параметры для Подоконников и Отливов
        data['windowsill_drip_config'] = {
            "dollar_rate": 43.0,
            "windowsill_master_commission_pm": 450, "windowsill_fuel_cost": 150,
            "windowsill_application_fee": 200, "windowsill_markup": 500,
            "drip_master_commission_pm": 150, "drip_markup_pm": 500, "drip_delivery_cost": 400
        }
        
        # Параметры для Бронепленки и ОСБ
        data['film_config'] = {"master_commission_sqm": 400, "margin_sqm": 600, "delivery_cost": 150, "budget_fee": 40}
        data['osb_config'] = {
            "sheet_purchase_price": 700, "sheet_area": 3.125, "cutting_per_sheet": 100,
            "master_commission_sqm": 380, "margin_sqm": 350, "delivery_cost": 300
        }

        return data
    except FileNotFoundError as e:
        st.error(f"ОШИБКА: Не найден файл CSV: {e.filename}. Убедитесь, что все файлы лежат в той же папке, что и `calculator.py`.")
        return None
    except Exception as e:
        st.error(f"Произошла ошибка при загрузке данных: {e}")
        return None

# Загружаем данные
data = load_data()

# --- 1. ЛОГИКА РАСЧЕТОВ (НАШИ ФУНКЦИИ ИЗ ШАГОВ 1-6) ---

def calculate_horizontal_blinds_price(params, data):
    try:
        df_pricelist_new = data['pricelist_new']
        df_blinds_params = data['blinds_params']

        # Извлечение параметров
        MASTER_COMMISSION_SQM = float(df_blinds_params.loc['мастер, 1 м2', 'Unnamed: 2'])
        FUEL_COST = float(df_blinds_params.loc['топливо', 'Unnamed: 2'])
        MARGIN_SQM = float(df_blinds_params.loc['маржа, 1 м2', 'Unnamed: 2'])
        MIN_AREA = 0.7 

        # 1. Получаем базовую закупочную цену в USD
        product_info = df_pricelist_new[
            (df_pricelist_new['Виріб'] == 'Жалюзі горизонтальні') &
            (df_pricelist_new['Вид виробу'] == params['blind_type']) &
            (df_pricelist_new['Тип'] == params['color'])
        ].iloc[0]
        
        base_price_usd_sqm = float(product_info['Вартість'])
        
        # 2. Рассчитываем площадь
        area = params['width'] * params['height']
        if area < MIN_AREA:
            area = MIN_AREA
            
        # 3. Считаем компоненты
        purchase_price = base_price_usd_sqm * DOLLAR_RATE * area
        master_fee = MASTER_COMMISSION_SQM * area
        total_margin = MARGIN_SQM * area
        
        # 4. Итоговая цена
        final_price = purchase_price + master_fee + total_margin + FUEL_COST
        
        return {
            "calculation_details": {
                "Закупочная стоимость": f"{purchase_price:.2f} грн",
                "Работа мастера": f"{master_fee:.2f} грн",
                "Маржа": f"{total_margin:.2f} грн",
                "Транспортные расходы": f"{FUEL_COST:.2f} грн"
            },
            "total_price_uah": f"{final_price:.2f}",
            "notes": f"Расчетная площадь: {area:.2f} м² (мин. {MIN_AREA} м²)"
        }
    except (IndexError, KeyError):
        return {"error": "Не удалось найти товар с указанными параметрами."}
    except Exception as e:
        return {"error": f"Произошла ошибка в расчетах: {e}"}

def calculate_roller_blinds_price(params, data):
    try:
        df_roller_blinds = data['roller_blinds']
        CONFIG = data['roller_config']

        # 1. Находим базовую цену
        product_info = df_roller_blinds[
            (df_roller_blinds['system_type'].str.contains(params['system_type'], case=False, na=False)) &
            (df_roller_blinds['fabric'].str.contains(params['fabric'], case=False, na=False))
        ].iloc[0]
        base_price_sqm = float(product_info['base_price_uah_sqm'])

        # 2. Площадь
        area = params['width'] * params['height']
        min_area = CONFIG["area_rounding"].get(params['shaft_diameter'], 0)
        if area < min_area:
            area = min_area

        # 3. Стоимость изделия
        product_cost = base_price_sqm * area

        # 4. Наценки
        if params['width'] > params['height']:
            product_cost *= (1 + CONFIG["surcharges"]["width_gt_height_percent"] / 100)
        
        if params.get('is_brown_system', False):
            product_cost += CONFIG["surcharges"]["brown_system_usd"] * CONFIG["dollar_rate"]
            
        # 5. Комиссия
        master_commission_type = "открытый тип" if "ОТКРЫТЫЙ" in params['system_type'] else "закрытый тип"
        master_fee = CONFIG["commissions"][master_commission_type]

        # 6. Итог
        final_price = product_cost + master_fee + CONFIG["delivery_cost"] + CONFIG["application_fee"]

        return {
            "calculation_details": {
                "Базовая стоимость изделия": f"{product_cost:.2f} грн",
                "Комиссия мастера": f"{master_fee:.2f} грн",
                "Доставка и Заявка": f"{CONFIG['delivery_cost'] + CONFIG['application_fee']:.2f} грн"
            },
            "total_price_uah": f"{final_price:.2f}",
            "notes": f"Расчетная площадь: {area:.2f} м² (мин. для вала {params['shaft_diameter']} - {min_area} м²)"
        }
    except (IndexError, KeyError):
        return {"error": f"Не удалось найти ткань '{params['fabric']}' для системы '{params['system_type']}'."}
    except Exception as e:
        return {"error": f"Произошла ошибка в расчетах: {e}"}

def calculate_mosquito_net_price(params, data):
    try:
        df_nets = data['nets_kiev']
        CONFIG = data['nets_config']
        
        # 1. Находим цену
        product_info = df_nets[
            (df_nets['Профіль'] == params['profile_type']) &
            (df_nets['Вид '] == params['color'])
        ].iloc[0]

        base_price_sqm = float(product_info['Ціна'])
        min_area = float(product_info[' S ≥  м²'])
        master_commission = float(product_info['Комісія майстра'])

        # 2. Площадь
        area = params['width'] * params['height']
        if area < min_area:
            area = min_area

        # 3. Закупка
        purchase_price = base_price_sqm * area
        additional_cost = 0

        # 4. Доп. опции
        if params.get('add_corner_cut', False):
            corner_cut_info = df_nets[
                (df_nets['Профіль'] == params['profile_type']) &
                (df_nets['Вид '].str.contains("ПРИРІЗКА КУТА", na=False))
            ]
            if not corner_cut_info.empty:
                additional_cost = float(corner_cut_info.iloc[0]['Комісія майстра']) 

        # 5. Итог
        final_price = (
            purchase_price + master_commission +
            CONFIG["margin_per_net"] + CONFIG["delivery_cost"] + additional_cost
        )

        return {
            "calculation_details": {
                "Закупочная стоимость изделия": f"{purchase_price:.2f} грн",
                "Комиссия мастера": f"{master_commission:.2f} грн",
                "Маржа и доставка": f"{CONFIG['margin_per_net'] + CONFIG['delivery_cost']:.2f} грн",
                "Дополнительные опции": f"{additional_cost:.2f} грн"
            },
            "total_price_uah": f"{final_price:.2f}",
            "notes": f"Расчетная площадь: {area:.2f} м² (мин. для профиля - {min_area} м²)"
        }
    except (IndexError, KeyError):
        return {"error": f"Не удалось найти профиль '{params['profile_type']}' с цветом '{params['color']}'."}
    except Exception as e:
        return {"error": f"Произошла непредвиденная ошибка: {e}"}

def calculate_glass_unit_price(params, data):
    try:
        df_glass_units = data['glass_units']
        params_dict = data['glass_params']
        
        # 1. Находим цену
        product_info = df_glass_units[
            (df_glass_units['Город'] == params['city']) &
            (df_glass_units['Вид'] == params['glass_type'])
        ].iloc[0]
        base_price_sqm = float(product_info['Цена'])
        num_chambers = int(product_info['К-во камер'])

        # 2. Площадь и правила
        area = params['width'] * params['height']
        note = f"Фактическая площадь: {area:.2f} м²"
        
        # Правила для городов (пример)
        min_area_poltava = float(params_dict.get('Стеклопакеты площадью меньше 0,3 м2 = 0,3м2 по стоимости ', 0.3))
        if params['city'] == "Полтава" and area < min_area_poltava:
            area = min_area_poltava
            note += f", расчетная площадь увеличена до {min_area_poltava} м²"
        
        # ... (здесь можно добавить остальные правила для других городов) ...

        # 3. Закупка
        purchase_price = base_price_sqm * area

        # 4. Комиссия и наценка
        commission_key = f'Комиссия мастера если {"двух" if num_chambers == 2 else "одно"}камерный стеклопакет {params["profile_system"]}'
        markup_key = f'Процент наценки если {params["profile_system"].lower()}'
        
        master_commission = float(params_dict.get(commission_key, 0))
        markup_percentage = float(params_dict.get(markup_key, 1.0)) 

        # 5. Итог
        final_price = (purchase_price * markup_percentage) + master_commission + \
                      float(params_dict.get('Доставка мастером', 0)) + \
                      float(params_dict.get('Заявка', 0))

        return {
            "calculation_details": {
                "Закупочная стоимость": f"{purchase_price:.2f} грн",
                "Наценка ({params['profile_system']})": f"x{markup_percentage}",
                "Комиссия мастера": f"{master_commission:.2f} грн",
                "Доставка и Заявка": f"{float(params_dict.get('Доставка мастером', 0)) + float(params_dict.get('Заявка', 0)):.2f} грн"
            },
            "total_price_uah": f"{final_price:.2f}",
            "notes": note
        }
    except (IndexError, KeyError) as e:
        return {"error": f"Не удалось найти параметры для: Город='{params['city']}', Тип='{params['glass_type']}', Профиль='{params['profile_system']}'. Ошибка: {e}"}
    except Exception as e:
        return {"error": f"Непредвиденная ошибка: {e}"}

def calculate_windowsill_price(params, data):
    try:
        df_windowsills = data['windowsills']
        CONFIG = data['windowsill_drip_config']
        
        # 1. Находим цену
        product_info = df_windowsills[
            (df_windowsills['Город'] == params['city']) &
            (df_windowsills['Бренд'] == params['brand']) &
            (df_windowsills['Цвет'] == params['color']) &
            (df_windowsills['Текстура'] == params['texture']) &
            (df_windowsills['Ширина'] == params['width_mm'])
        ].iloc[0]

        price_per_meter = float(product_info['Цена'])
        currency = product_info['Валюта']
        cap_price = float(product_info['Заглушка'])

        # 2. Конвертация
        if str(currency).lower() == 'доллар':
            price_per_meter *= CONFIG['dollar_rate']

        # 3. Расчет
        length = params['length'] # params['width'] - это ширина в м, а нам нужна длина
        purchase_price = price_per_meter * length
        caps_total_cost = cap_price * params['num_caps']
        master_fee = CONFIG['windowsill_master_commission_pm'] * length

        # 4. Итог
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
        return {"error": "Не удалось найти подоконник с указанными параметрами."}
    except Exception as e:
        return {"error": f"Непредвиденная ошибка: {e}"}


def calculate_drip_price(params, data):
    try:
        df_drips = data['drips']
        CONFIG = data['windowsill_drip_config']
        
        # 1. Находим цену
        product_info = df_drips[df_drips['ширина'] == params['width_mm']].iloc[0]
        price_per_meter_usd = float(product_info['"цена, у.е."'])

        # 2. Закупка
        length = params['length'] # params['width'] - это ширина в м, а нам нужна длина
        purchase_price = price_per_meter_usd * CONFIG['dollar_rate'] * length

        # 3. Комиссия и маржа
        master_fee = CONFIG['drip_master_commission_pm'] * length
        total_markup = CONFIG['drip_markup_pm'] * length

        # 4. Итог
        final_price = purchase_price + master_fee + total_markup + CONFIG['drip_delivery_cost']

        return {
            "calculation_details": {
                "Закупочная стоимость": f"{purchase_price:.2f} грн",
                "Работа мастера": f"{master_fee:.2f} грн",
                "Маржа": f"{total_markup:.2f} грн",
                "Доставка": f"{CONFIG['drip_delivery_cost']:.2f} грн"
            },
            "total_price_uah": f"{final_price:.2f}",
            "notes": f"Расчет для {length} пог.м."
        }
    except (IndexError, KeyError):
        return {"error": f"Не удалось найти отлив шириной {params['width_mm']} мм."}
    except Exception as e:
        return {"error": f"Непредвиденная ошибка: {e}"}


def calculate_security_film_price(params, data):
    try:
        df_film = data['film']
        CONFIG = data['film_config']

        # 1. Находим цену
        price_key = f"Закупочная стоимость за кв.м {params['thickness_mkm']} мкм"
        purchase_price_sqm = float(df_film.loc[price_key, 'Unnamed: 7'])

        # 2. Площадь
        area = params['width'] * params['height']

        # 3. Компоненты
        total_purchase_price = purchase_price_sqm * area
        master_fee = CONFIG['master_commission_sqm'] * area
        total_margin = CONFIG['margin_sqm'] * area
        
        # 4. Итог
        final_price = (
            total_purchase_price + master_fee + total_margin +
            CONFIG['delivery_cost'] + CONFIG['budget_fee']
        )
        
        return {
            "calculation_details": {
                "Закупка пленки": f"{total_purchase_price:.2f} грн",
                "Работа мастера": f"{master_fee:.2f} грн",
                "Маржа": f"{total_margin:.2f} грн",
                "Прочие расходы": f"{CONFIG['delivery_cost'] + CONFIG['budget_fee']:.2f} грн"
            },
            "total_price_uah": f"{final_price:.2f}"
        }
    except KeyError:
        return {"error": f"Не найдена цена для пленки толщиной {params['thickness_mkm']} мкм."}
    except Exception as e:
        return {"error": f"Непредвиденная ошибка: {e}"}

def calculate_osb_price(params, data):
    try:
        CONFIG = data['osb_config']
        
        # 1. Площадь и листы
        area = params['width'] * params['height']
        sheets_needed = math.ceil(area / CONFIG['sheet_area'])

        # 2. Компоненты
        total_purchase_price = CONFIG['sheet_purchase_price'] * sheets_needed
        total_cutting_cost = CONFIG['cutting_per_sheet'] * sheets_needed
        master_fee = CONFIG['master_commission_sqm'] * area
        total_margin = CONFIG['margin_sqm'] * area

        # 3. Итог
        final_price = (
            total_purchase_price + total_cutting_cost + master_fee +
            total_margin + CONFIG['delivery_cost']
        )

        return {
            "calculation_details": {
                "Закупка листов ОСБ": f"{total_purchase_price:.2f} грн ({sheets_needed} шт.)",
                "Порезка": f"{total_cutting_cost:.2f} грн",
                "Работа мастера": f"{master_fee:.2f} грн",
                "Маржа и доставка": f"{total_margin + CONFIG['delivery_cost']:.2f} грн"
            },
            "total_price_uah": f"{final_price:.2f}"
        }
    except Exception as e:
        return {"error": f"Произошла ошибка: {e}"}

# --- 2. ГЛАВНЫЙ ДИСПЕТЧЕР ---

def calculate_total_price(service_name, params, data):
    if not data:
        return {"error": "Данные не загружены. Проверьте CSV файлы."}

    # Карта, связывающая имя услуги с функцией для её расчета
    calculator_mapping = {
        "horizontal_blinds": calculate_horizontal_blinds_price,
        "roller_blinds": calculate_roller_blinds_price,
        "mosquito_net": calculate_mosquito_net_price,
        "glass_unit": calculate_glass_unit_price,
        "windowsill": calculate_windowsill_price,
        "drip": calculate_drip_price,
        "security_film": calculate_security_film_price,
        "osb": calculate_osb_price
    }
    
    calculation_function = calculator_mapping.get(service_name)
    
    if calculation_function:
        return calculation_function(params, data)
    else:
        return {"error": f"Услуга с именем '{service_name}' не найдена."}


# --- 3. ИНТЕРФЕЙС (STREAMLIT) ---

st.title("Онлайн-калькулятор стоимости")

# Словарь с названиями услуг и их ключами
service_options = {
    "Жалюзи горизонтальные": "horizontal_blinds",
    "Рулонные шторы": "roller_blinds",
    "Антимоскитные сетки": "mosquito_net",
    "Стеклопакеты": "glass_unit",
    "Подоконники": "windowsill",
    "Отливы": "drip",
    "Бронепленка": "security_film",
    "ОСБ-плиты": "osb"
}

# Проверка, что данные загружены
if data:
    # --- ОБЩИЕ ПОЛЯ ---
    service_name_display = st.selectbox(
        "Выберите услугу:",
        options=list(service_options.keys())
    )
    # Получаем ключ услуги (например, "horizontal_blinds")
    service_key = service_options[service_name_display]
    
    # Инициализируем словарь для параметров
    params = {}

    # --- УСЛОВНЫЕ (ДИНАМИЧЕСКИЕ) ПОЛЯ ---
    
    if service_key in ["windowsill", "drip"]:
        # Для подоконников и отливов используем "Длина"
        params['length'] = st.number_input("Длина (в метрах):", min_value=0.1, value=1.0, step=0.1)
        # Поле "Ширина" для них - это выбор из списка
    else:
        # Для всех остальных - "Ширина" и "Высота"
        params['width'] = st.number_input("Ширина (в метрах):", min_value=0.1, value=1.0, step=0.1)
        params['height'] = st.number_input("Высота (в метрах):", min_value=0.1, value=1.0, step=0.1)


    # --- Детализация по каждой услуге ---

    if service_key == "horizontal_blinds":
        st.subheader("Параметры жалюзи")
        params['blind_type'] = st.selectbox(
            "Тип системы:",
            options=data['pricelist_new'][data['pricelist_new']['Виріб'] == 'Жалюзі горизонтальні']['Вид виробу'].unique()
        )
        params['color'] = st.selectbox(
            "Цвет:",
            options=data['pricelist_new'][
                (data['pricelist_new']['Виріб'] == 'Жалюзі горизонтальні') &
                (data['pricelist_new']['Вид виробу'] == params['blind_type'])
            ]['Тип'].unique()
        )

    elif service_key == "roller_blinds":
        st.subheader("Параметры рулонных штор")
        params['system_type'] = st.selectbox("Тип системы:", ["ОТКРЫТЫЙ ТИП", "ЗАКРЫТЫЙ ТИП"])
        params['shaft_diameter'] = st.selectbox("Диаметр вала:", ["19 мм", "25 мм", "35 мм"])
        params['fabric'] = st.selectbox(
            "Ткань:",
            options=data['roller_blinds']['fabric'].unique()
        )
        params['is_brown_system'] = st.checkbox("Коричневая система (+1$)")

    elif service_key == "mosquito_net":
        st.subheader("Параметры сетки")
        params['profile_type'] = st.selectbox(
            "Тип профиля:",
            options=data['nets_kiev']['Профіль'].unique()
        )
        params['color'] = st.selectbox(
            "Цвет:",
            options=data['nets_kiev'][data['nets_kiev']['Профіль'] == params['profile_type']]['Вид '].unique()
        )
        params['add_corner_cut'] = st.checkbox("Прирезка угла под 45 градусов")

    elif service_key == "glass_unit":
        st.subheader("Параметры стеклопакета")
        params['city'] = st.selectbox(
            "Город:",
            options=data['glass_units']['Город'].unique()
        )
        params['profile_system'] = st.selectbox("Профильная система:", ["ПВХ", "Евробрус", "Алюминий"])
        params['glass_type'] = st.selectbox(
            "Тип стеклопакета:",
            options=data['glass_units'][data['glass_units']['Город'] == params['city']]['Вид'].unique()
        )

    elif service_key == "windowsill":
        st.subheader("Параметры подоконника")
        params['city'] = st.selectbox(
            "Город:",
            options=data['windowsills']['Город'].unique()
        )
        params['brand'] = st.selectbox(
            "Бренд:",
            options=data['windowsills'][data['windowsills']['Город'] == params['city']]['Бренд'].unique()
        )
        params['color'] = st.selectbox(
            "Цвет:",
            options=data['windowsills'][
                (data['windowsills']['Город'] == params['city']) &
                (data['windowsills']['Бренд'] == params['brand'])
            ]['Цвет'].unique()
        )
        params['texture'] = st.selectbox(
            "Текстура:",
            options=data['windowsills'][
                (data['windowsills']['Город'] == params['city']) &
                (data['windowsills']['Бренд'] == params['brand']) &
                (data['windowsills']['Цвет'] == params['color'])
            ]['Текстура'].unique()
        )
        params['width_mm'] = st.selectbox(
            "Ширина (мм):",
            options=data['windowsills'][
                (data['windowsills']['Город'] == params['city']) &
                (data['windowsills']['Бренд'] == params['brand']) &
                (data['windowsills']['Цвет'] == params['color']) &
                (data['windowsills']['Текстура'] == params['texture'])
            ]['Ширина'].unique()
        )
        params['num_caps'] = st.number_input("Количество заглушек:", min_value=0, value=2, step=1)

    elif service_key == "drip":
        st.subheader("Параметры отлива")
        params['width_mm'] = st.selectbox(
            "Ширина (мм):",
            options=data['drips']['ширина'].unique()
        )

    elif service_key == "security_film":
        st.subheader("Параметры бронепленки")
        params['thickness_mkm'] = st.selectbox("Толщина (мкм):", [100, 200, 300])

    elif service_key == "osb":
        st.subheader("Параметры ОСБ-плит")
        # Для ОСБ ширина и высота уже введены, доп. параметры не нужны
        pass
    
    # --- КНОПКА РАСЧЕТА ---
    st.divider() # Разделительная линия
    
    if st.button("Рассчитать стоимость", type="primary"):
        # Вызываем наш главный диспетчер
        result = calculate_total_price(service_key, params, data)
        
        # Отображаем результат
        if "error" in result:
            st.error(f"Ошибка в расчете: {result['error']}")
        else:
            st.success(f"Итоговая стоимость: {result['total_price_uah']} грн")
            
            if "calculation_details" in result:
                st.subheader("Детализация расчета:")
                st.json(result['calculation_details'])
            
            if "notes" in result:
                st.info(result['notes'])

else:
    st.error("Не удалось загрузить данные. Проверьте наличие и правильность CSV файлов в папке.")
