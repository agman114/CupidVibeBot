import hashlib
from aiogram import Router, F
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

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
    user_link = f'<a href="tg://user?id={inline_query.from_user.id}">{user_name}</a>'
    
    results = []

    if not query:
        # Показываем список всех доступных действий, если запрос пуст
        for action, data in ACTIONS.items():
            result_id = hashlib.md5(action.encode()).hexdigest()
            text_message = f"{data['emoji']} {user_link} {data['text']} всех!"
            
            results.append(
                InlineQueryResultArticle(
                    id=result_id,
                    title=f"{action.capitalize()} {data['emoji']}",
                    description=f"{data['text']} всех",
                    input_message_content=InputTextMessageContent(
                        message_text=text_message,
                        parse_mode="HTML"
                    )
                )
            )
    else:
        lower_query = query.lower()
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
                final_text = f"{emoji} {user_link} {action_text} всех!"
                desc = f"{action_text} всех"
                
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
