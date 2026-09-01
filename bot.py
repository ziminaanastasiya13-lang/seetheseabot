"""
🌊 See The Sea FM Bot для Telegram
=====================================
Радио с лучшими треками Techno, Trance, Deep House, Tech House, Chillout,  Progressive House

УСТАНОВКА:
    pip install python-telegram-bot==21.3 requests

ЗАПУСК:
    Токен читается из переменной окружения BOT_TOKEN (для Fly.io/Railway)
    Либо впиши напрямую в BOT_TOKEN ниже для локального теста.
"""

import logging
import requests
import os

# Запускаем API сервер для метаданных (если файл присутствует)
try:
    import nowplaying_api
except Exception as e:
    print(f"API сервер не запустился: {e}")
    nowplaying_api = None

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ──────────────────────────────────────────────
#  КОНФИГ
# ──────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "ВСТАВЬ_ТОКЕН_СЮДА")

# URL мини-приложения (GitHub Pages), вставь после публикации
WEBAPP_URL = "https://ziminaanastasiya13-lang.github.io/seetheseabot/"
# Прямая ссылка на поток See The Sea FM
STREAM_URL = "https://myradio24.org/seethesea"  # fallback, будет уточнён при поиске
STATION_NAME = "See The Sea FM 🌊"
STATION_GENRE = "Techno · Trance · Deep House "
STATION_COUNTRY = "Узбекистан 🇺🇿"
STATION_SITE = "https://seethesearecords.wixsite.com/home"
STATION_LOGO = "https://static.wixstatic.com/media/1b0b32_4d864e5a7d8e4566b6414a9ae0c8b1d4~mv2_d_1577_1577_s_2.png/v1/fill/w_206,h_206,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/1b0b32_4d864e5a7d8e4566b6414a9ae0c8b1d4~mv2_d_1577_1577_s_2.png"

# ──────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def find_stream_url() -> str:
    """Ищет актуальный stream URL через открытый Radio Browser API."""
    global STREAM_URL
    try:
        apis = [
            "https://de1.api.radio-browser.info",
            "https://nl1.api.radio-browser.info",
            "https://at1.api.radio-browser.info",
        ]
        for base in apis:
            resp = requests.get(
                f"{base}/json/stations/byname/See%20The%20Sea",
                headers={"User-Agent": "SeeTheSeaBot/1.0"},
                timeout=5,
            )
            if resp.ok:
                stations = resp.json()
                if stations:
                    url = stations[0].get("url_resolved") or stations[0].get("url")
                    if url:
                        STREAM_URL = url
                        logger.info(f"✅ Stream URL найден: {STREAM_URL}")
                        return STREAM_URL
    except Exception as e:
        logger.warning(f"Radio Browser недоступен: {e}")
    logger.info(f"Использую fallback URL: {STREAM_URL}")
    return STREAM_URL


def main_keyboard(webapp_url: str = "") -> InlineKeyboardMarkup:
    """Главная клавиатура бота."""
    keyboard = []
    if webapp_url:
        keyboard.append([InlineKeyboardButton("🎧 Слушать в Telegram", web_app=WebAppInfo(url=webapp_url))])
    keyboard += [
        [InlineKeyboardButton("▶️ Открыть в браузере", url=STREAM_URL)],
        [InlineKeyboardButton("ℹ️ О радио", callback_data="info"),
         InlineKeyboardButton("🎵 Жанры", callback_data="genres")],
        [InlineKeyboardButton("🔗 Сайт лейбла", url=STATION_SITE)],
        [InlineKeyboardButton("📡 Прямая ссылка", callback_data="stream_url")],
    ]
    return InlineKeyboardMarkup(keyboard)


def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="back")]])


# ──────────────────── HANDLERS ────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start — главное меню."""
    user = update.effective_user

    artist, track, artwork = "", "", ""
    if nowplaying_api:
        try:
            now = nowplaying_api.get_now_playing()
            artist = now.get("artist", "")
            track = now.get("track", "")
            artwork = now.get("artwork", "")
        except Exception as e:
            logger.warning(f"Не удалось получить now playing: {e}")

    now_playing_line = ""
    if artist or track:
        now_playing_line = f"\n🎵 Сейчас играет: *{artist} — {track}*\n"

    text = (
        f"🌊 *Привет, {user.first_name}!*\n\n"
        f"Добро пожаловать в *See The Sea FM Bot* — андеграундное радио "
        f"с лучшими треками techno, trance, deep и chillout!\n"
        f"Выбери действие 👇"
    )

    if artwork:
        photo = artwork
    else:
        photo = open("logo circle копия.png", "rb")

    await update.message.reply_photo(
        photo=photo,
        caption=text,
        parse_mode="Markdown",
        reply_markup=main_keyboard(WEBAPP_URL),
    )


async def play_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /play — отправить аудиопоток."""
    await send_stream(update.message, context)


async def info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /info."""
    await update.message.reply_text(
        build_info_text(), parse_mode="Markdown", reply_markup=back_keyboard()
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик инлайн-кнопок."""
    query = update.callback_query
    await query.answer()

    if query.data == "play":
        await send_stream(query.message, context, edit=True)

    elif query.data == "info":
        await query.edit_message_caption(
            caption=build_info_text(),
            parse_mode="Markdown",
            reply_markup=back_keyboard(),
        )

    elif query.data == "genres":
        text = (
            "🎶 *Жанры See The Sea FM:*\n\n"
            "🎛️ *Techno* — гипнотический ритм, электронное звучание\n"
            "✨ *Trance* — мелодичные и атмосферные композиции\n"
            "🌀 *Deep* — глубокий, минималистичный хаус\n"
            "🌅 *Chillout* — расслабляющая, атмосферная музыка\n\n"
            "_Никакой рекламы, никаких разговоров — только музыка!_"
        )
        await query.edit_message_caption(
            caption=text, parse_mode="Markdown", reply_markup=back_keyboard()
        )

    elif query.data == "stream_url":
        url = STREAM_URL
        text = (
            f"📡 *Прямая ссылка на поток:*\n\n"
            f"`{url}`\n\n"
            f"Вставь в VLC, Winamp, foobar2000 или любой медиаплеер с поддержкой потоков."
        )
        await query.edit_message_caption(
            caption=text, parse_mode="Markdown", reply_markup=back_keyboard()
        )

    elif query.data == "back":
        text = (
            f"🌊 *See The Sea FM*\n\n"
            f"{STATION_GENRE}\n"
            f"{STATION_COUNTRY}\n\n"
            "Выбери действие 👇"
        )
        await query.edit_message_caption(
            caption=text, parse_mode="Markdown", reply_markup=main_keyboard(WEBAPP_URL)
        )


async def send_stream(message, context: ContextTypes.DEFAULT_TYPE, edit=False) -> None:
    """Отправляет аудиопоток пользователю."""
    url = STREAM_URL
    text = (
        f"🎧 *{STATION_NAME}*\n"
        f"_{STATION_GENRE}_\n\n"
       f"▶️ Нажми Play чтобы слушать прямо в Telegram!\n\n"
        f"Или открой ссылку в браузере / медиаплеере:\n`{url}`"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Открыть в браузере", url=url)],
        [InlineKeyboardButton("⬅️ Главное меню", callback_data="back")],
    ])

    if edit:
        try:
            await message.edit_caption(
                caption=text, parse_mode="Markdown", reply_markup=keyboard
            )
        except Exception:
            pass
    else:
        try:
            await message.reply_audio(
                audio=url,
                title=STATION_NAME,
                performer="See The Sea Records",
                caption=f"🌊 {STATION_GENRE}",
            )
        except Exception:
            await message.reply_text(
                text, parse_mode="Markdown", reply_markup=keyboard
            )


def build_info_text() -> str:
    return (
        f"🌊 *{STATION_NAME}*\n\n"
        f"🎵 Жанры: {STATION_GENRE}\n"
        f"🌍 Страна: {STATION_COUNTRY}\n\n"
        f"_See The Sea FM — андеграундное радио, которое транслирует лучшие "
        f"композиции немейнстримных музыкантов и диджеев. Никакой рекламы, "
        f"никаких разговоров — 24 часа качественной музыки, разделённой "
        f"тематически по жанрам._\n\n"
        f"🌐 [Сайт]({STATION_SITE})\n"
        f"📘 [Facebook](http://www.facebook.com/seethesearecords)\n"
        f"🐦 [Twitter](http://twitter.com/seethesearec)"
    )


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Неизвестная команда."""
    await update.message.reply_text(
        "Используй /start для главного меню или /play для запуска радио 🎧"
    )


def main() -> None:
    if BOT_TOKEN == "ВСТАВЬ_ТОКЕН_СЮДА":
        print("❌ Вставь токен бота в переменную BOT_TOKEN!")
        print("   Получи токен у @BotFather в Telegram")
        return

    print("🔍 Ищу актуальный stream URL...")
    find_stream_url()
    print(f"📡 Stream URL: {STREAM_URL}")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("play", play_cmd))
    app.add_handler(CommandHandler("info", info_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    print(f"🌊 See The Sea FM Bot запущен!")
    print(f"   Поток: {STREAM_URL}")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
