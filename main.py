import logging
import os
import json
from typing import List

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")

MAX_MAIN = 12
MAX_RESERVE = 2
STATE_FILE = "state.json"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# ================= STATE =================

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {
        "active": False,
        "phase": "main",
        "main": [],
        "reserve": [],
        "message_id": None,
        "chat_id": None,
    }

def save_state():
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

state = load_state()

# ================= ADMIN =================

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    member = await context.bot.get_chat_member(
        update.effective_chat.id, update.effective_user.id
    )
    return member.status in ("administrator", "creator")

# ================= KEYBOARD =================

def build_keyboard(user_id: int) -> InlineKeyboardMarkup:
    if state["phase"] == "main":
        if user_id in state["main"]:
            return InlineKeyboardMarkup(
                [[InlineKeyboardButton("🧤 Не играю / Not playing", callback_data="leave_main")]]
            )
        return InlineKeyboardMarkup(
            [[InlineKeyboardButton("⚽ Играть / Play", callback_data="join_main")]]
        )

    if state["phase"] == "reserve":
        if user_id in state["reserve"]:
            return InlineKeyboardMarkup(
                [[InlineKeyboardButton("🧤 Не играю / Not playing", callback_data="leave_reserve")]]
            )
        return InlineKeyboardMarkup(
            [[InlineKeyboardButton("🥅 Играть (замена) / Play (reserve)", callback_data="join_reserve")]]
        )

    return InlineKeyboardMarkup([])

# ================= RENDER =================

async def render_list(context: ContextTypes.DEFAULT_TYPE) -> str:
    async def names(ids: List[int]) -> List[str]:
        result = []
        for uid in ids:
            try:
                member = await context.bot.get_chat_member(state["chat_id"], uid)
                result.append(member.user.full_name)
            except Exception:
                result.append(str(uid))
        return result

    main_names = await names(state["main"])
    reserve_names = await names(state["reserve"])

    text = "⚽ *Список игроков / Players list*\n\n"

    text += "*Основной состав / Main squad:*\n"
    if main_names:
        for i, name in enumerate(main_names, 1):
            text += f"{i}. {name}\n"
    else:
        text += "—\n"

    if state["phase"] in ("reserve", "finished"):
        text += "\n*Замена / Reserve:*\n"
        if reserve_names:
            for i, name in enumerate(reserve_names, 1):
                text += f"{i}. {name}\n"
        else:
            text += "—\n"

    return text

# ================= COMMANDS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    state["active"] = True
    state["phase"] = "main"
    state["main"].clear()
    state["reserve"].clear()
    state["chat_id"] = update.effective_chat.id

    text = await render_list(context)

    msg = await update.effective_chat.send_message(
        text,
        reply_markup=build_keyboard(update.effective_user.id),
        parse_mode="Markdown",
    )

    state["message_id"] = msg.message_id

    # 📌 Автозакреп
    await context.bot.pin_chat_message(
        state["chat_id"],
        state["message_id"],
        disable_notification=True
    )

    save_state()

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    state["active"] = False
    state["phase"] = "finished"
    save_state()

    await update.message.reply_text(
        "🛑 Процесс остановлен.\nProcess stopped."
    )

# ================= BUTTON =================

async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not state["active"]:
        return

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data == "join_main" and state["phase"] == "main":
        if user_id not in state["main"] and len(state["main"]) < MAX_MAIN:
            state["main"].append(user_id)

        if len(state["main"]) == MAX_MAIN:
            state["phase"] = "reserve"

    elif query.data == "leave_main":
        if user_id in state["main"]:
            state["main"].remove(user_id)

    elif query.data == "join_reserve" and state["phase"] == "reserve":
        if user_id not in state["reserve"] and len(state["reserve"]) < MAX_RESERVE:
            state["reserve"].append(user_id)

        if len(state["reserve"]) == MAX_RESERVE:
            state["phase"] = "finished"

    elif query.data == "leave_reserve":
        if user_id in state["reserve"]:
            state["reserve"].remove(user_id)

    save_state()

    text = await render_list(context)

    await context.bot.edit_message_text(
        chat_id=state["chat_id"],
        message_id=state["message_id"],
        text=text,
        reply_markup=build_keyboard(user_id),
        parse_mode="Markdown",
    )

# ================= MAIN =================

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CallbackQueryHandler(on_button))

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        webhook_url=os.getenv("RAILWAY_STATIC_URL")
    )

if __name__ == "__main__":
    main()
