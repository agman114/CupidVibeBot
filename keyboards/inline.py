from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_swipe_keyboard(target_user_id, is_admin=False, is_vip=False):
    buttons = [
        [
            InlineKeyboardButton(text="👎", callback_data=f"swipe_dislike_{target_user_id}"),
            InlineKeyboardButton(text="❤️", callback_data=f"swipe_like_{target_user_id}")
        ]
    ]
    if is_vip:
        buttons.append([InlineKeyboardButton(text="⭐ Супер-лайк", callback_data=f"swipe_super_{target_user_id}")])
        
    if is_admin:
        buttons.append([
            InlineKeyboardButton(text="⛔ Бан", callback_data=f"admin_ban_{target_user_id}"),
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"admin_delete_{target_user_id}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

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
            [InlineKeyboardButton(text=f"Кого ищу: {user['looking_for']}", callback_data="filter_looking")],
            [InlineKeyboardButton(text=f"Только мой город: {city_status}", callback_data="filter_city")],
            [InlineKeyboardButton(text=f"Цели: {purpose_status}", callback_data="filter_purposes_menu")],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="filter_close")]
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
            [InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_menu")],
            [InlineKeyboardButton(text="🗑️ Удалить", callback_data="delete_profile")]
        ]
    )

def get_edit_profile_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Имя", callback_data="edit_field_name"), 
             InlineKeyboardButton(text="🔢 Возраст", callback_data="edit_field_age")],
            [InlineKeyboardButton(text="🚻 Пол", callback_data="edit_field_gender"), 
             InlineKeyboardButton(text="🔍 Кого ищу", callback_data="edit_field_looking")],
            [InlineKeyboardButton(text="🎯 Цель", callback_data="edit_field_purpose"), 
             InlineKeyboardButton(text="🏙️ Город", callback_data="edit_field_city")],
            [InlineKeyboardButton(text="📝 О себе", callback_data="edit_field_desc")],
            [InlineKeyboardButton(text="📸 Фото/Видео", callback_data="edit_field_media")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="show_profile")]
        ]
    )

def get_liker_swipe_keyboard(target_user_id, is_admin=False):
    buttons = [
        [
            InlineKeyboardButton(text="👎", callback_data=f"likerswipe_dislike_{target_user_id}"),
            InlineKeyboardButton(text="❤️", callback_data=f"likerswipe_like_{target_user_id}")
        ]
    ]
    if is_admin:
        buttons.append([
            InlineKeyboardButton(text="⛔ Бан", callback_data=f"admin_ban_{target_user_id}"),
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"admin_delete_{target_user_id}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_support_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💎 Купить VIP (100 ⭐️)", callback_data="buy_vip_stars")],
            [InlineKeyboardButton(text="🔗 Реферальная программа", callback_data="referral_menu")],
            [InlineKeyboardButton(text="Discord Сервер 💬", url="https://discord.gg/RE7QPefw8t")],
            [InlineKeyboardButton(text="Написать в поддержку (Telegram) ✈️", url="https://t.me/burninglovesupport")]
        ]
    )
    return keyboard

def get_matches_keyboard(matches_on_page, page, total_pages):
    buttons = []
    
    # Кнопки для каждого мэтча
    for match in matches_on_page:
        match_dict = dict(match)
        name = match_dict['name']
        if match_dict['is_vip']: name += " 💎"
        
        # Если есть username, даем прямую ссылку, иначе ссылку на профиль
        if match_dict.get('username'):
            url = f"https://t.me/{match_dict['username']}"
        else:
            url = f"tg://user?id={match_dict['id']}"
            
        buttons.append([InlineKeyboardButton(text=f"💌 {name}", url=url)])
    
    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"matches_page_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"matches_page_{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
        
    return InlineKeyboardMarkup(inline_keyboard=buttons)
