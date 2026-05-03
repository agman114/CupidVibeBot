from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_swipe_keyboard(target_user_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👎", callback_data=f"swipe_dislike_{target_user_id}"),
                InlineKeyboardButton(text="❤️", callback_data=f"swipe_like_{target_user_id}")
            ]
        ]
    )
    return keyboard

VALID_PURPOSES = [
    "Поиск секса/одноразового развлечения",
    "Поиск отношения",
    "Создание семьи",
    "Дружба",
    "Поиск тимейта для игры",
    "Поиск творческого партнёра(Музыкальная группа)"
]

def get_filters_keyboard(user):
    city_status = "Вкл" if user["filter_city_only"] else "Выкл"
    
    purposes_str = dict(user).get("filter_purposes") or ""
    if not purposes_str:
        purpose_status = "Все"
    else:
        selected_count = len(purposes_str.split(","))
        purpose_status = f"{selected_count} выбрано"
    
    age_text = f"{user['filter_age_min']}" if user['filter_age_min'] == user['filter_age_max'] else f"{user['filter_age_min']}-{user['filter_age_max']}"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"Возраст: {age_text}", callback_data="filter_age")],
            [InlineKeyboardButton(text=f"Только мой город: {city_status}", callback_data="filter_city")],
            [InlineKeyboardButton(text=f"Цели: {purpose_status}", callback_data="filter_purposes_menu")]
        ]
    )
    return keyboard

def get_purposes_filter_keyboard(user):
    purposes_str = dict(user).get("filter_purposes") or ""
    selected_purposes = purposes_str.split(",") if purposes_str else []
    
    inline_keyboard = []
    
    for i, p in enumerate(VALID_PURPOSES):
        check = "✅ " if p in selected_purposes else ""
        inline_keyboard.append([InlineKeyboardButton(text=f"{check}{p}", callback_data=f"purpose_toggle_{i}")])
        
    inline_keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="filter_back")])
    
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def get_profile_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Изменить анкету", callback_data="edit_profile")],
            [InlineKeyboardButton(text="🗑️ Удалить", callback_data="delete_profile")]
        ]
    )

def get_liker_swipe_keyboard(target_user_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👎", callback_data=f"likerswipe_dislike_{target_user_id}"),
                InlineKeyboardButton(text="❤️", callback_data=f"likerswipe_like_{target_user_id}")
            ]
        ]
    )
    return keyboard

def get_support_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Discord Сервер 💬", url="https://discord.gg/RE7QPefw8t")],
            [InlineKeyboardButton(text="Написать в поддержку (Telegram) ✈️", url="https://t.me/burninglovesupport")]
        ]
    )
    return keyboard
