import logging
import os
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

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

state = {
    "active": False,
    "phase": "main",  # main | reserve | finished
    "main": [],
    "reserve": [],
    "message_id": None,
    "chat_id": None,
}


# ================= ADMIN CHECK =================
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not update.effective_chat or not update.effective_user:
        return False

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

    if state["active"]:
        await update.message.reply_text(
            "⚽ Процесс уже запущен.\nProcess already started."
        )
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


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    state["active"] = False
    state["phase"] = "finished"

    await update.message.reply_text(
        "🛑 Процесс остановлен администратором.\nProcess stopped by administrator."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "⚽ Команды / Commands:\n"
        "/start — запустить набор / start process\n"
        "/stop — остановить / stop process\n"
        "/status — текущий статус / current status\n"
    )
    await update.message.reply_text(text)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"⚽ Активен / Active: {state['active']}\n"
        f"Фаза / Phase: {state['phase']}\n"
        f"Основной / Main: {len(state['main'])}/{MAX_MAIN}\n"
        f"Замена / Reserve: {len(state['reserve'])}/{MAX_RESERVE}"
    )
    await update.message.reply_text(text)


# ================= BUTTON HANDLER =================
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
            await context.bot.send_message(
                state["chat_id"],
                "⚽ Основной состав сформирован.\nMain squad completed."
            )

    elif query.data == "leave_main":
        if user_id in state["main"]:
            state["main"].remove(user_id)

    elif query.data == "join_reserve" and state["phase"] == "reserve":
        if user_id not in state["reserve"] and len(state["reserve"]) < MAX_RESERVE:
            state["reserve"].append(user_id)

        if len(state["reserve"]) == MAX_RESERVE:
            state["phase"] = "finished"
            await context.bot.send_message(
                state["chat_id"],
                "🥅 Список замены сформирован.\nReserve list completed."
            )

    elif query.data == "leave_reserve":
        if user_id in state["reserve"]:
            state["reserve"].remove(user_id)

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
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CallbackQueryHandler(on_button))

    app.run_polling()


if __name__ == "__main__":
    main()
