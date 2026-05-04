from aiogram import Router, F, Bot
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import database.db as db
import hashlib

router = Router()

ACTIONS = {
    "обнять": {"emoji": "🫂", "req": "обнять", "res": "обнял(а)", "target": "собеседника"},
    "поцеловать": {"emoji": "💋", "req": "поцеловать", "res": "поцеловал(а)", "target": "собеседника"},
    "погладить": {"emoji": "✋", "req": "погладить", "res": "погладил(а)", "target": "собеседника"},
    "укусить": {"emoji": "🧛", "req": "укусить", "res": "укусил(а)", "target": "собеседника"},
    "дать пять": {"emoji": "🙏", "req": "дать пять", "res": "дал(а) пять", "target": "собеседнику"},
    "ударить": {"emoji": "🥊", "req": "ударить", "res": "ударил(а)", "target": "собеседника"},
    "кусь": {"emoji": "🧛", "req": "сделать кусь", "res": "сделал(а) кусь", "target": "собеседнику"},
    "пожать руку": {"emoji": "🤝", "req": "пожать руку", "res": "пожал(а) руку", "target": "собеседнику"}
}

@router.inline_query()
async def inline_actions_handler(inline_query: InlineQuery):
    query = inline_query.query.strip()
    user_name = inline_query.from_user.first_name
    user_id = inline_query.from_user.id
    user_link = f'<a href="tg://user?id={user_id}">{user_name}</a>'
    
    results = []

    if not query:
        # Показываем список всех доступных действий, если запрос пуст
        for action, data in ACTIONS.items():
            result_id = hashlib.md5(action.encode()).hexdigest()
            # Текст запроса согласия
            request_text = f"{data['emoji']} {user_link} предлагает <b>{data['req']}</b> {data['target']}! ✨\n\nВы согласны?"
            
            cb_data = f"act:{action}:{user_id}:{data['target']}"
            if len(cb_data.encode()) > 64: cb_data = cb_data[:60] + "..."

            kb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="Принять ✅", callback_data=cb_data),
                    InlineKeyboardButton(text="Отклонить ❌", callback_data=f"act_dec:{user_id}")
                ]
            ])
            
            results.append(
                InlineQueryResultArticle(
                    id=result_id,
                    title=f"{action.capitalize()} {data['emoji']}",
                    description=f"{data['req'].capitalize()} {data['target']}",
                    input_message_content=InputTextMessageContent(
                        message_text=request_text,
                        parse_mode="HTML"
                    ),
                    reply_markup=kb
                )
            )
        
        results.append(
            InlineQueryResultArticle(
                id="hint_marry",
                title="Сделать предложение 💍",
                description="Напишите: свадьба @имя",
                input_message_content=InputTextMessageContent(
                    message_text="Чтобы сделать предложение, напишите: @имя_бота свадьба @username"
                )
            )
        )
    else:
        lower_query = query.lower()
        
        if lower_query.startswith("свадьба"):
            target = query[7:].strip()
            if not target:
                results.append(
                    InlineQueryResultArticle(id="marry_no", title="💍 Кому делаем предложение?", input_message_content=InputTextMessageContent(message_text="Укажите, кому вы делаете предложение!")))
            else:
                spouse = await db.get_spouse(user_id)
                if spouse:
                    results.append(InlineQueryResultArticle(id="marry_al", title="💍 Вы уже в браке", input_message_content=InputTextMessageContent(message_text="Вы не можете делать предложение, так как уже в браке! 🚫")))
                else:
                    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Согласиться ❤️", callback_data=f"marry_agree:{user_id}"), InlineKeyboardButton(text="Отказаться 💔", callback_data=f"marry_decline:{user_id}")]])
                    results.append(InlineQueryResultArticle(id=hashlib.md5(f"marry_{target}".encode()).hexdigest(), title="💍 Сделать предложение", input_message_content=InputTextMessageContent(message_text=f"💍 {user_link} делает предложение <b>{target}</b>!\n\nВы согласны?", parse_mode="HTML"), reply_markup=kb))
        
        elif lower_query.startswith("развод"):
            spouse = await db.get_spouse(user_id)
            if not spouse:
                results.append(InlineQueryResultArticle(id="div_no", title="💔 Вы не в браке", input_message_content=InputTextMessageContent(message_text="Вы не в браке.")))
            else:
                kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Подтвердить развод 💔", callback_data=f"marry_divorce_confirm:{user_id}")]])
                results.append(InlineQueryResultArticle(id="div_conf", title="💔 Подать на развод", input_message_content=InputTextMessageContent(message_text=f"❗ {user_link} хочет подать на развод!", parse_mode="HTML"), reply_markup=kb))
        
        else:
            matched_action = None
            target_text = ""
            for action in ACTIONS:
                if lower_query.startswith(action):
                    matched_action = action
                    target_text = query[len(action):].strip() or ACTIONS[action]['target']
                    break
                    
            if matched_action:
                data = ACTIONS[matched_action]
                request_text = f"{data['emoji']} {user_link} предлагает <b>{data['req']}</b> {target_text}! ✨\n\nВы согласны?"
                cb_data = f"act:{matched_action}:{user_id}:{target_text}"
                if len(cb_data.encode()) > 64: cb_data = cb_data.encode()[:60].decode('utf-8', 'ignore') + "..."
                
                kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Принять ✅", callback_data=cb_data), InlineKeyboardButton(text="Отклонить ❌", callback_data=f"act_dec:{user_id}")]])
                results.append(InlineQueryResultArticle(id=hashlib.md5(f"action_{matched_action}_{target_text}".encode()).hexdigest(), title=f"{matched_action.capitalize()} {data['emoji']}", input_message_content=InputTextMessageContent(message_text=request_text, parse_mode="HTML"), reply_markup=kb))
            else:
                # Кастомное действие
                request_text = f"✨ {user_link} предлагает: <b>{query}</b>! ⚡\n\nВы согласны?"
                cb_data = f"act:custom:{user_id}:{query}"
                if len(cb_data.encode()) > 64: cb_data = cb_data.encode()[:60].decode('utf-8', 'ignore') + "..."
                
                kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Принять ✅", callback_data=cb_data), InlineKeyboardButton(text="Отклонить ❌", callback_data=f"act_dec:{user_id}")]])
                results.append(InlineQueryResultArticle(id=hashlib.md5(f"custom_{query}".encode()).hexdigest(), title="Свое действие ✨", input_message_content=InputTextMessageContent(message_text=request_text, parse_mode="HTML"), reply_markup=kb))

    await inline_query.answer(results, cache_time=1, is_personal=True)

@router.callback_query(F.data.startswith("act:"))
async def action_accept_handler(callback: CallbackQuery, bot: Bot):
    parts = callback.data.split(":", 3)
    action_key = parts[1]
    proposer_id = int(parts[2])
    target_text = parts[3]
    
    clicker_id = callback.from_user.id
    if clicker_id == proposer_id:
        await callback.answer("Вы не можете принять действие от самого себя! 😂", show_alert=True)
        return
        
    proposer = await bot.get_chat(proposer_id)
    proposer_name = proposer.first_name
    clicker_name = callback.from_user.first_name
    
    if action_key == "custom":
        final_text = f"✨ <b>{proposer_name}</b> {target_text} <i>(согласие: {clicker_name})</i>"
    else:
        data = ACTIONS.get(action_key, {"emoji": "✨", "res": "сделал(а) действие с"})
        # Убираем "собеседника/собеседнику" из финального текста и вставляем имя
        final_text = f"{data['emoji']} <b>{proposer_name}</b> {data['res']} <b>{clicker_name}</b>! 🎉"
        
    await bot.edit_message_text(
        text=final_text,
        inline_message_id=callback.inline_message_id,
        parse_mode="HTML"
    )
    await callback.answer("Действие выполнено! ✨")

@router.callback_query(F.data.startswith("act_dec:"))
async def action_decline_handler(callback: CallbackQuery, bot: Bot):
    proposer_id = int(callback.data.split(":")[1])
    
    if callback.from_user.id == proposer_id:
        text = "❌ Действие отменено автором."
    else:
        text = f"❌ <b>{callback.from_user.first_name}</b> отклонил(а) действие."
        
    await bot.edit_message_text(
        text=text,
        inline_message_id=callback.inline_message_id,
        parse_mode="HTML"
    )
    await callback.answer("Отклонено.")

@router.callback_query(F.data.startswith("marry_agree:"))
async def marry_agree_handler(callback: CallbackQuery, bot: Bot):
    proposer_id = int(callback.data.split(":")[1])
    target_id = callback.from_user.id
    
    if target_id == proposer_id:
        await callback.answer("Вы не можете жениться на самом себе! 😂", show_alert=True)
        return

    # Проверяем обоих на наличие брака
    spouse1 = await db.get_spouse(proposer_id)
    spouse2 = await db.get_spouse(target_id)
    
    if spouse1:
        await callback.answer("Этот человек уже успел жениться/выйти замуж! 💍", show_alert=True)
        return
    if spouse2:
        await callback.answer("Вы уже состоите в браке! 💍", show_alert=True)
        return
        
    # Сохраняем брак
    await db.add_marriage(proposer_id, target_id)
    
    proposer = await bot.get_chat(proposer_id)
    proposer_name = proposer.first_name
    target_name = callback.from_user.first_name
    
    text = f"🎉 <b>{proposer_name}</b> и <b>{target_name}</b> теперь женаты! 💍❤️\n\nПоздравляем молодых! ✨"
    
    await bot.edit_message_text(
        text=text,
        inline_message_id=callback.inline_message_id,
        parse_mode="HTML"
    )
    await callback.answer("Поздравляем со свадьбой! ✨")

@router.callback_query(F.data.startswith("marry_decline:"))
async def marry_decline_handler(callback: CallbackQuery, bot: Bot):
    proposer_id = int(callback.data.split(":")[1])
    
    if callback.from_user.id == proposer_id:
        # Отменил сам автор
        text = "❌ Предложение отменено автором."
    else:
        # Отклонил другой пользователь
        text = f"💔 <b>{callback.from_user.first_name}</b> отклонил(а) предложение."
        
    await bot.edit_message_text(
        text=text,
        inline_message_id=callback.inline_message_id,
        parse_mode="HTML"
    )
    await callback.answer("Предложение отклонено.")

@router.callback_query(F.data.startswith("marry_divorce_confirm:"))
async def marry_divorce_confirm_handler(callback: CallbackQuery, bot: Bot):
    user_id = int(callback.data.split(":")[1])
    clicker_id = callback.from_user.id
    
    if clicker_id != user_id:
        await callback.answer("Только тот, кто инициировал развод, может его подтвердить! 🚫", show_alert=True)
        return
        
    spouse_id = await db.get_spouse(user_id)
    if not spouse_id:
        await callback.answer("Вы уже не состоите в браке!", show_alert=True)
        return
        
    await db.remove_marriage(user_id)
    
    text = f"💔 <b>{callback.from_user.first_name}</b> официально расторг(ла) брак. Теперь оба партнера свободны."
    
    await bot.edit_message_text(
        text=text,
        inline_message_id=callback.inline_message_id,
        parse_mode="HTML"
    )
    await callback.answer("Вы успешно развелись. 💔")
    
    # Пытаемся уведомить бывшего супруга
    try:
        await bot.send_message(spouse_id, "💔 Ваш партнер расторг брак. Теперь вы свободны.")
    except Exception:
        pass
