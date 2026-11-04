import os
import telebot
from telebot import types
import requests
import threading
import urllib.parse
import re
import time
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== 1. خادم فحص الحالة السحابي (Render 24/7) ====================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return
    
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Bot is Live 24/7!")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        server.serve_forever()
    except Exception as e:
        logger.error(f"Health Server Error: {e}")

threading.Thread(target=run_health_server, daemon=True).start()

# ==================== 2. تهيئة التوكن والإعدادات ====================
DEFAULT_TOKEN = "9157081412:AAFNd58PvaVueVhHeWB_b0AWheOYDUi2_zE"
BOT_TOKEN = os.environ.get("BOT_TOKEN", DEFAULT_TOKEN).strip()

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=True)
BOT_USERNAME = "saleh_down_bot"
AUDIO_STORE = {}

RAPIDAPI_KEY = "2bbc6b508amshf8ae4c3acc0945ap121032jsn8dc7afbfa9bc"
RAPIDAPI_HOST = "instagram-tiktok-youtube-downloader.p.rapidapi.com"

# ==================== 3. فك الروابط المختصرة ====================
def unshorten_url(url: str) -> str:
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X)'}
        res = requests.head(url, allow_redirects=True, timeout=8, headers=headers)
        return res.url
    except Exception:
        return url

# ==================== 4. محرك الاستخراج الذكي الشامل ====================
def extract_media(raw_url: str):
    real_url = unshorten_url(raw_url)
    clean_url = real_url.split('?')[0]

    headers_web = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }

    # 1. فحص تيك توك وتويين (يدعم الصور المتعددة والفيديو والصوت)
    if "tiktok.com" in real_url or "douyin.com" in real_url:
        try:
            # طلب مباشر لمحرك TikWM المتخصص في تفكيك الصور والفيديو
            api_url = f"https://www.tikwm.com/api/?url={urllib.parse.quote(real_url)}"
            res = requests.get(api_url, headers=headers_web, timeout=12).json()
            if res.get("code") == 0:
                data = res["data"]
                title = data.get("title", "تيك توك")
                author = data.get("author", {}).get("nickname", "مجهول")
                views = data.get("play_count", 0)
                likes = data.get("digg_count", 0)

                music = data.get("music")
                if music and music.startswith("/"):
                    music = "https://www.tikwm.com" + music

                # إذا كان ألبوم صور (Photo Mode)
                if data.get("images") and isinstance(data["images"], list):
                    images = []
                    for img in data["images"]:
                        if img.startswith("/"):
                            images.append("https://www.tikwm.com" + img)
                        else:
                            images.append(img)
                    return {
                        "type": "images",
                        "images": images,
                        "audio": music,
                        "title": title,
                        "author": author,
                        "views": views,
                        "likes": likes
                    }

                # إذا كان فيديو عادي
                video = data.get("hdplay") or data.get("play") or data.get("wmplay")
                if video and video.startswith("/"):
                    video = "https://www.tikwm.com" + video

                if video:
                    return {
                        "type": "video",
                        "video": video,
                        "audio": music or video,
                        "title": title,
                        "author": author,
                        "views": views,
                        "likes": likes
                    }
        except Exception as e:
            logger.error(f"Tikwm failed: {e}")

    # 2. الاستعلام عبر RapidAPI الشامل (لإنستغرام، فيسبوك، ثريدز، يوتيوب، إلخ)
    try:
        rapid_headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": RAPIDAPI_HOST
        }
        res = requests.get(f"https://{RAPIDAPI_HOST}/", headers=rapid_headers, params={"url": real_url}, timeout=15)
        if res.status_code == 200:
            data = res.json()
            # فحص إذا كان المنشور يحتوي صور
            if data.get("images") and isinstance(data["images"], list):
                return {
                    "type": "images",
                    "images": data["images"],
                    "audio": data.get("music_url") or data.get("audio"),
                    "title": data.get("title", "منشور صور"),
                    "author": data.get("author", "مستخدم"),
                    "views": data.get("views", 0),
                    "likes": data.get("likes", 0)
                }

            # فحص الفيديو
            video = data.get("download_url") or data.get("url") or data.get("media")
            if not video and data.get("items") and isinstance(data["items"], list):
                video = data["items"][0].get("download_url") or data["items"][0].get("url")

            if video:
                return {
                    "type": "video",
                    "video": video,
                    "audio": data.get("music_url") or video,
                    "title": data.get("title", "مقطع فيديو"),
                    "author": data.get("author", "مستخدم"),
                    "views": data.get("views", 0),
                    "likes": data.get("likes", 0)
                }
    except Exception as e:
        logger.error(f"RapidAPI failed: {e}")

    return None

# ==================== 5. لوحة المفاتيح والترحيب ====================
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📥 كيفية التحميل", "🔥 حساب صلوح تيك توك")
    return markup

@bot.message_handler(commands=['start'])
def handle_start(message):
    welcome_msg = (
        f"👑 <b>أهلاً بك يا {message.from_user.first_name} في بوت صلوح الشامل!</b>\n\n"
        "⚡️ <b>يدعم السحب الفوري بأعلى دقة:</b>\n"
        "• <b>الصور:</b> ألبومات تيك توك وإنستغرام كاملة\n"
        "• <b>الفيديو:</b> تيك توك، إنستغرام، ثريدز، فيسبوك، يوتيوب\n"
        "• <b>الصوت:</b> استخراج الصوت الأصلي MP3\n\n"
        "🚀 <i>أرسل الرابط مباشرة وسأتولى الباقي...</i>"
    )
    bot.reply_to(message, welcome_msg, reply_markup=get_main_keyboard())

# ==================== 6. معالجة الروابط والإرسال الذكي ====================
@bot.message_handler(func=lambda m: bool(re.search(r'(https?://[^\s]+)', m.text or "")))
def handle_download_request(message):
    url_match = re.search(r'(https?://[^\s]+)', message.text)
    if not url_match:
        return
    raw_url = url_match.group(0)

    wait_msg = bot.reply_to(
        message, 
        "⏳ <b>جاري الاتصال وفك محتوى الرابط...</b>\n"
        "<code>[████░░░░░░] 40%</code>"
    )

    try:
        media = extract_media(raw_url)

        if media:
            bot.delete_message(message.chat.id, wait_msg.message_id)

            caption = (
                f"📝 <b>العنوان:</b> {media['title']}\n"
                f"👤 <b>الناشر:</b> @{media['author']}\n\n"
                f"🤖 @{BOT_USERNAME}"
            )

            # حالة 1: ألبوم صور (Photo Album)
            if media["type"] == "images":
                images_list = media["images"]
                media_group = []
                
                # تليجرام يستقبل بحد أقصى 10 صور في المجموعة الواحدة
                for i, img_url in enumerate(images_list[:10]):
                    if i == 0:
                        media_group.append(types.InputMediaPhoto(img_url, caption=caption, parse_mode="HTML"))
                    else:
                        media_group.append(types.InputMediaPhoto(img_url))
                
                bot.send_media_group(message.chat.id, media_group)

                # إرسال الصوت المرفق مع الصور إن وجد
                if media.get("audio"):
                    try:
                        bot.send_audio(
                            message.chat.id, 
                            media["audio"], 
                            title=f"{media['title'][:30]}", 
                            performer=f"@{media['author']}",
                            caption=f"🎵 الصوت الأصلي المرفق بالألبوم\n🤖 @{BOT_USERNAME}"
                        )
                    except Exception:
                        pass
                return

            # حالة 2: فيديو عادي (Video Mode)
            elif media["type"] == "video":
                key = f"aud_{message.chat.id}_{int(time.time())}"
                AUDIO_STORE[key] = media["audio"]

                markup = types.InlineKeyboardMarkup(row_width=2)
                btn_share = types.InlineKeyboardButton("🔗 شارك البوت", switch_inline_query="")
                btn_group = types.InlineKeyboardButton("✈️ أرسله في قروب", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")
                btn_audio = types.InlineKeyboardButton("استخراج الصوت MP3", callback_data=f"ext_{key}")
                markup.row(btn_share, btn_group)
                markup.row(btn_audio)

                try:
                    bot.send_video(
                        message.chat.id, 
                        media["video"], 
                        caption=caption, 
                        reply_markup=markup, 
                        supports_streaming=True
                    )
                    return
                except Exception:
                    stream = requests.get(media["video"], headers={'User-Agent': 'Mozilla/5.0'}, stream=True, timeout=30)
                    bot.send_video(
                        message.chat.id, 
                        stream.raw, 
                        caption=caption, 
                        reply_markup=markup, 
                        supports_streaming=True
                    )
                    return

    except Exception as e:
        logger.error(f"Download Engine Error: {e}")

    bot.edit_message_text(
        "❌ تعذر تحميل المقطع مباشرة، تأكد أن الفيديو عام وغير محذوف.",
        message.chat.id, wait_msg.message_id
    )

# ==================== 7. استخراج الصوت MP3 ====================
@bot.callback_query_handler(func=lambda c: c.data.startswith("ext_"))
def handle_audio_btn(call):
    key = call.data.replace("ext_", "")
    source = AUDIO_STORE.get(key)

    if not source:
        bot.answer_callback_query(call.id, "⚠️ انتهت صلاحية الرابط، أعد إرسال الفيديو.", show_alert=True)
        return

    bot.answer_callback_query(call.id, "🎵 جاري استخراج الصوت...")
    load = bot.send_message(call.message.chat.id, "⚡️ <b>جاري إرسال ملف الصوت MP3...</b>")
    try:
        bot.send_audio(
            call.message.chat.id, 
            source, 
            title="الصوت المستخرج",
            caption=f"🎵 تم استخراج الصوت بنجاح\n🤖 @{BOT_USERNAME}"
        )
        bot.delete_message(call.message.chat.id, load.message_id)
    except Exception:
        bot.edit_message_text("❌ تعذر إرسال الصوت بشكل منفصل لهذا المقطع.", call.message.chat.id, load.message_id)

# ==================== 8. النصوص العامة ====================
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    text = message.text.strip()
    if text == "📥 كيفية التحميل":
        bot.reply_to(message, "فقط انسخ رابط أي مقطع أو صور من تيك توك، إنستغرام، ثريدز، أو فيسبوك وأرسله هنا وسأسحبه لك فوراً 🚀")
    elif text == "🔥 حساب صلوح تيك توك":
        bot.reply_to(message, "🎬 تابع الحساب الرسمي على تيك توك:\nhttps://www.tiktok.com/@almanay22")
    else:
        bot.reply_to(message, "أهلاً بك! أرسل رابط المقطع أو الصور وسأسحبه لك فوراً 🚀")

# ==================== 9. التشغيل الآمن ====================
if __name__ == "__main__":
    logger.info("Mega All-In-One Bot Started...")
    try:
        bot.remove_webhook()
        time.sleep(1)
    except Exception:
        pass

    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=25)
        except Exception:
            time.sleep(5)
