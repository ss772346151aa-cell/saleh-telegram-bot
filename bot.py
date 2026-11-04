
import os
import re
import html
import time
import uuid
import shutil
import logging
import tempfile
import threading

import telebot
from telebot import types
from yt_dlp import YoutubeDL
from concurrent.futures import ThreadPoolExecutor
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

# ==========================================
# 1. CONFIGURATION
# ==========================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
BOT_USERNAME = os.getenv("BOT_USERNAME", "saleh_down_bot").lstrip("@")

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "48"))
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "2"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing in Render Environment")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("SALOUH_BOT")

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML",
    threaded=True,
    num_threads=MAX_WORKERS + 2
)

executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
semaphore = threading.BoundedSemaphore(MAX_WORKERS)

AUDIO_STORE = {}
AUDIO_LOCK = threading.Lock()

# ==========================================
# 2. HEALTH SERVER FOR RENDER
# ==========================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        body = b"SALOUH DOWNLOADER BOT RUNNING"

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()

        self.wfile.write(body)

    def log_message(self, *args):
        pass


def start_server():

    port = os.getenv("PORT")

    if not port:
        return

    server = ThreadingHTTPServer(
        ("0.0.0.0", int(port)),
        HealthHandler
    )

    threading.Thread(
        target=server.serve_forever,
        daemon=True
    ).start()

# ==========================================
# 3. HELPERS
# ==========================================

def get_url(text):

    if not text:
        return None

    match = re.search(
        r"https?://[^\s<>]+",
        text
    )

    if not match:
        return None

    return match.group(0).rstrip(".,!?،؛)]}»\"'")


def safe_text(value, limit=700):

    return html.escape(
        str(value or "")
    )[:limit]


def cleanup_audio_store():

    now = time.time()

    with AUDIO_LOCK:

        expired = [
            key for key, value in AUDIO_STORE.items()
            if now - value["time"] > 3600
        ]

        for key in expired:
            AUDIO_STORE.pop(key, None)


# ==========================================
# 4. MEDIA DOWNLOADER
# ==========================================

def download_media(url, folder, audio=False):

    output = os.path.join(
        folder,
        "%(title).70s_%(id)s.%(ext)s"
    )

    options = {
        "outtmpl": output,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "retries": 3,
        "fragment_retries": 3,
        "socket_timeout": 25,
        "restrictfilenames": True,
        "max_filesize": MAX_UPLOAD_MB * 1024 * 1024,
        "http_headers": {
            "User-Agent": "Mozilla/5.0"
        }
    }

    if audio:

        options.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }]
        })

    else:

        options.update({
            "format": (
                f"best[ext=mp4][filesize<={MAX_UPLOAD_MB}M]/"
                f"best[filesize<={MAX_UPLOAD_MB}M]/"
                "best[height<=720]/best"
            ),
            "merge_output_format": "mp4"
        })

    with YoutubeDL(options) as ydl:

        info = ydl.extract_info(
            url,
            download=True
        )

    files = [
        os.path.join(folder, name)
        for name in os.listdir(folder)
        if os.path.isfile(os.path.join(folder, name))
        and not name.endswith((".part", ".ytdl"))
    ]

    if audio:
        files = [
            p for p in files
            if p.lower().endswith(".mp3")
        ]
    else:
        files = [
            p for p in files
            if os.path.splitext(p)[1].lower()
            not in (".jpg", ".jpeg", ".png", ".webp", ".json")
        ]

    if not files:
        raise RuntimeError("No media file downloaded")

    path = max(
        files,
        key=os.path.getsize
    )

    size = os.path.getsize(path)

    if size > MAX_UPLOAD_MB * 1024 * 1024:
        raise RuntimeError("File exceeds upload limit")

    title = (info or {}).get("title", "Media")

    return path, title


# ==========================================
# 5. AUDIO BUTTON STORAGE
# ==========================================

def save_audio_url(url):

    cleanup_audio_store()

    key = uuid.uuid4().hex[:12]

    with AUDIO_LOCK:
        AUDIO_STORE[key] = {
            "url": url,
            "time": time.time()
        }

    return key


# ==========================================
# 6. MAIN DOWNLOAD ENGINE
# ==========================================

def process_download(message, url):

    status = None

    try:

        status = bot.reply_to(
            message,
            "⏳ <b>جاري فحص الرابط وتحميل الوسائط...</b>"
        )

        if not semaphore.acquire(timeout=180):

            bot.edit_message_text(
                "⏳ جميع عمليات التحميل مشغولة، حاول لاحقاً.",
                message.chat.id,
                status.message_id
            )

            return

        try:

            with tempfile.TemporaryDirectory() as folder:

                path, title = download_media(
                    url,
                    folder
                )

                caption = (
                    "✅ <b>تم تحميل الوسائط بنجاح</b>\n\n"
                    f"📝 {safe_text(title, 250)}\n\n"
                    f"🤖 @{safe_text(BOT_USERNAME, 50)}"
                )

                key = save_audio_url(url)

                markup = types.InlineKeyboardMarkup()

                markup.add(
                    types.InlineKeyboardButton(
                        "🎵 استخراج الصوت MP3",
                        callback_data=f"audio:{key}"
                    )
                )

                markup.add(
                    types.InlineKeyboardButton(
                        "✈️ مشاركة البوت",
                        url=f"https://t.me/{BOT_USERNAME}"
                    )
                )

                bot.edit_message_text(
                    "🚀 <b>تم التحميل، جاري الإرسال...</b>",
                    message.chat.id,
                    status.message_id
                )

                with open(path, "rb") as media:

                    if path.lower().endswith(
                        (".mp4", ".mov", ".m4v", ".webm")
                    ):

                        bot.send_video(
                            message.chat.id,
                            media,
                            caption=caption,
                            reply_markup=markup,
                            supports_streaming=True,
                            timeout=120
                        )

                    else:

                        bot.send_document(
                            message.chat.id,
                            media,
                            caption=caption,
                            reply_markup=markup,
                            timeout=120
                        )

                bot.delete_message(
                    message.chat.id,
                    status.message_id
                )

        finally:

            semaphore.release()

    except Exception as error:

        logger.exception("DOWNLOAD ERROR")

        text = (
            "❌ تعذر تحميل هذا الرابط.\n\n"
            "قد يكون المنشور خاصاً أو محذوفاً، "
            "أو أن الموقع لا يسمح بالتنزيل حالياً."
        )

        if status:

            try:
                bot.edit_message_text(
                    text,
                    message.chat.id,
                    status.message_id
                )
            except Exception:
                bot.send_message(message.chat.id, text)

        else:
            bot.send_message(message.chat.id, text)


# ==========================================
# 7. AUDIO EXTRACTION
# ==========================================

def send_audio(chat_id, url):

    status = bot.send_message(
        chat_id,
        "🎵 <b>جاري استخراج وتحويل الصوت إلى MP3...</b>"
    )

    try:

        if not semaphore.acquire(timeout=180):

            bot.edit_message_text(
                "الخدمة مشغولة حالياً.",
                chat_id,
                status.message_id
            )

            return

        try:

            with tempfile.TemporaryDirectory() as folder:

                path, title = download_media(
                    url,
                    folder,
                    audio=True
                )

                with open(path, "rb") as audio:

                    bot.send_audio(
                        chat_id,
                        audio,
                        title=safe_text(title, 60),
                        caption="🎵 <b>تم استخراج الصوت بنجاح</b>",
                        timeout=120
                    )

            bot.delete_message(
                chat_id,
                status.message_id
            )

        finally:

            semaphore.release()

    except Exception:

        logger.exception("AUDIO ERROR")

        bot.edit_message_text(
            "❌ تعذر استخراج الصوت.",
            chat_id,
            status.message_id
        )


@bot.callback_query_handler(
    func=lambda c: bool(c.data and c.data.startswith("audio:"))
)
def audio_callback(call):

    key = call.data.split(":", 1)[1]

    with AUDIO_LOCK:
        item = AUDIO_STORE.get(key)

    if not item or time.time() - item["time"] > 3600:

        bot.answer_callback_query(
            call.id,
            "انتهت صلاحية الرابط. أعد إرساله.",
            show_alert=True
        )

        return

    bot.answer_callback_query(
        call.id,
        "🎵 جاري استخراج الصوت..."
    )

    executor.submit(
        send_audio,
        call.message.chat.id,
        item["url"]
    )


# ==========================================
# 8. WELCOME
# ==========================================

@bot.message_handler(commands=["start", "help"])
def start(message):

    name = safe_text(
        message.from_user.first_name,
        60
    )

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.row(
        "📥 كيفية التحميل",
        "🔥 حساب صلوح تيك توك"
    )

    text = (
        f"👑 <b>أهلاً بك يا {name}</b>\n\n"
        "مرحباً بك في بوت صلوح للتحميل السريع.\n\n"
        "📥 أرسل رابط منشور عام.\n"
        "🎬 سأحاول تنزيل الفيديو أو الوسائط.\n"
        "🎵 يمكنك استخراج الصوت MP3.\n\n"
        "🚀 أرسل الرابط للبدء."
    )

    bot.reply_to(
        message,
        text,
        reply_markup=markup
    )


# ==========================================
# 9. URL HANDLER
# ==========================================

@bot.message_handler(
    func=lambda m: bool(get_url(m.text))
)
def link_handler(message):

    url = get_url(message.text)

    executor.submit(
        process_download,
        message,
        url
    )


# ==========================================
# 10. TEXT COMMANDS
# ==========================================

@bot.message_handler(
    func=lambda m: m.text == "📥 كيفية التحميل"
)
def help_download(message):

    bot.reply_to(
        message,
        "📥 انسخ رابط منشور عام وأرسله هنا.\n"
        "سأحاول تنزيل الوسائط وإرسالها إليك."
    )


@bot.message_handler(
    func=lambda m: m.text == "🔥 حساب صلوح تيك توك"
)
def tiktok_account(message):

    bot.reply_to(
        message,
        "🎬 الحساب الرسمي:\n"
        "https://www.tiktok.com/@almanay22"
    )


@bot.message_handler(
    func=lambda m: bool(m.text)
    and not m.text.startswith("/")
)
def unknown_text(message):

    bot.reply_to(
        message,
        "أرسل رابط فيديو أو منشور عام للبدء. 📥"
    )


# ==========================================
# 11. START BOT
# ==========================================

def main():

    start_server()

    logger.info(
        "SALOUH DOWNLOADER BOT STARTED"
    )

    bot.remove_webhook()

    bot.infinity_polling(
        timeout=30,
        long_polling_timeout=25,
        skip_pending=True
    )


if __name__ == "__main__":

    main()
