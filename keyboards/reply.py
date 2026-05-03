from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❤️ Смотреть анкеты")],
            [KeyboardButton(text="🙏 Кто меня лайкнул"), KeyboardButton(text="💞 Взаимности")],
            [KeyboardButton(text="👤 Моя анкета"), KeyboardButton(text="⚙️ Настройки поиска")],
            [KeyboardButton(text="💎 VIP-статус"), KeyboardButton(text="🆘 Поддержка")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_gender_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Парень"), KeyboardButton(text="Девушка")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_looking_for_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Парня"), KeyboardButton(text="Девушку")],
            [KeyboardButton(text="Всех")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_purpose_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Поиск секса/одноразового развлечения")],
            [KeyboardButton(text="Поиск отношения")],
            [KeyboardButton(text="Создание семьи")],
            [KeyboardButton(text="Дружба")],
            [KeyboardButton(text="Поиск тимейта для игры")],
            [KeyboardButton(text="Поиск творческого партнёра(Музыкальная группа)")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_location_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Отправить геолокацию", request_location=True)]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_media_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Завершить")]
        ],
        resize_keyboard=True
    )
    return keyboard
