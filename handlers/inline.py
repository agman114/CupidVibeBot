from aiogram import Router, F, Bot
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import database.db as db
import hashlib

router = Router()

ACTIONS = {
    "обнять": {"emoji": "🫂", "text": "обнимает"},
    "поцеловать": {"emoji": "💋", "text": "целует"},
    "погладить": {"emoji": "✋", "text": "гладит"},
    "укусить": {"emoji": "🧛", "text": "кусает"},
    "дать пять": {"emoji": "🙏", "text": "дает пять"},
    "ударить": {"emoji": "🥊", "text": "бьет"},
    "кусь": {"emoji": "🧛", "text": "делает кусь"},
    "пожать руку": {"emoji": "🤝", "text": "жмет руку"}
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
            text_message = f"{data['emoji']} {user_link} {data['text']} собеседника!"
            
            results.append(
                InlineQueryResultArticle(
                    id=result_id,
                    title=f"{action.capitalize()} {data['emoji']}",
                    description=f"{data['text']} собеседника",
                    input_message_content=InputTextMessageContent(
                        message_text=text_message,
                        parse_mode="HTML"
                    )
                )
            )
        
        # Добавляем "Свадьбу" в список
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
        
        # Специальная обработка для "свадьба"
        if lower_query.startswith("свадьба"):
            target = query[7:].strip()
            if not target:
                results.append(
                    InlineQueryResultArticle(
                        id="marry_no_target",
                        title="💍 Кому делаем предложение?",
                        description="Укажите имя или @username после слова свадьба",
                        input_message_content=InputTextMessageContent(
                            message_text="Нужно указать, кому вы делаете предложение!"
                        )
                    )
                )
            else:
                # Проверяем, не женат ли уже отправитель
                spouse = await db.get_spouse(user_id)
                if spouse:
                    results.append(
                        InlineQueryResultArticle(
                            id="marry_already",
                            title="💍 Вы уже женаты/замужем!",
                            description="Сначала нужно развестись.",
                            input_message_content=InputTextMessageContent(
                                message_text="Вы не можете делать предложение, так как уже состоите в браке! 🚫"
                            )
                        )
                    )
                else:
                    kb = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text="Согласиться ❤️", callback_data=f"marry_agree:{user_id}"),
                            InlineKeyboardButton(text="Отказаться 💔", callback_data=f"marry_decline:{user_id}")
                        ]
                    ])
                    results.append(
                        InlineQueryResultArticle(
                            id=hashlib.md5(f"marry_{target}".encode()).hexdigest(),
                            title="💍 Сделать предложение",
                            description=f"Предложение для {target}",
                            input_message_content=InputTextMessageContent(
                                message_text=f"💍 {user_link} делает предложение <b>{target}</b>!\n\nВы согласны?",
                                parse_mode="HTML"
                            ),
                            reply_markup=kb
                        )
                    )
        elif lower_query.startswith("развод"):
            # Проверяем, женат ли пользователь
            spouse = await db.get_spouse(user_id)
            if not spouse:
                results.append(
                    InlineQueryResultArticle(
                        id="divorce_not_married",
                        title="💔 Вы не в браке",
                        description="Не с кем разводиться...",
                        input_message_content=InputTextMessageContent(
                            message_text="Вы не состоите в браке, поэтому развод невозможен. 🕊️"
                        )
                    )
                )
            else:
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Подтвердить развод 💔", callback_data=f"marry_divorce_confirm:{user_id}")]
                ])
                results.append(
                    InlineQueryResultArticle(
                        id="divorce_confirm",
                        title="💔 Подать на развод",
                        description="Это действие нельзя отменить",
                        input_message_content=InputTextMessageContent(
                            message_text=f"❗ {user_link} хочет подать на <b>развод</b>!\n\nВы уверены?",
                            parse_mode="HTML"
                        ),
                        reply_markup=kb
                    )
                )
        else:
            matched_action = None
            target = ""
            
            # Проверяем, начинается ли запрос с одного из предустановленных действий
            for action in ACTIONS:
                if lower_query.startswith(action):
                    matched_action = action
                    target = query[len(action):].strip()
                    break
                    
            if matched_action:
                data = ACTIONS[matched_action]
                emoji = data["emoji"]
                action_text = data["text"]
                
                if target:
                    final_text = f"{emoji} {user_link} {action_text} {target}!"
                    desc = f"{action_text} {target}"
                else:
                    final_text = f"{emoji} {user_link} {action_text} собеседника!"
                    desc = f"{action_text} собеседника"
                    
                results.append(
                    InlineQueryResultArticle(
                        id=hashlib.md5(f"action_{matched_action}_{target}".encode()).hexdigest(),
                        title=f"{matched_action.capitalize()} {emoji}",
                        description=desc,
                        input_message_content=InputTextMessageContent(
                            message_text=final_text,
                            parse_mode="HTML"
                        )
                    )
                )
            else:
                # Кастомное действие
                custom_id = hashlib.md5(f"custom_{query}".encode()).hexdigest()
                custom_text = f"✨ {user_link} {query}"
                results.append(
                    InlineQueryResultArticle(
                        id=custom_id,
                        title="Свое действие ✨",
                        description=query,
                        input_message_content=InputTextMessageContent(
                            message_text=custom_text,
                            parse_mode="HTML"
                        )
                    )
                )

    await inline_query.answer(results, cache_time=1, is_personal=True)

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
