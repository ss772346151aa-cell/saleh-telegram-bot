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

# ==================== 1. سيرفر البقاء حياً لـ Render ====================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Bot is Running 24/7!")

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        server.serve_forever()
    except Exception as e:
        logger.error(f"Server Error: {e}")

threading.Thread(target=run_health_server, daemon=True).start()

# ==================== 2. الإعدادات ====================
DEFAULT_TOKEN = "9157081412:AAFNd58PvaVueVhHeWB_b0AWheOYDUi2_zE"
BOT_TOKEN = os.environ.get("BOT_TOKEN", DEFAULT_TOKEN).strip()
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=True)

BOT_USERNAME = "saleh_down_bot"
AUDIO_STORE = {}

RAPIDAPI_KEY = "2bbc6b508amshf8ae4c3acc0945ap121032jsn8dc7afbfa9bc"
RAPIDAPI_HOST = "instagram-tiktok-youtube-downloader.p.rapidapi.com"

# دالة لتنسيق الأرقام مثل (24.2K)
def format_number(num):
    if not num:
        return "0"
    try:
        num = int(num)
        if num >= 1_000_000:
            return f"{num / 1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num / 1_000:.1f}K"
        return str(num)
    except Exception:
        return str(num)

# ==================== 3. معالج محتوى TikTok الشامل (فيديو + صور + صوت + إحصائيات) ====================
def process_tiktok(url: str):
    try:
        api_url = f"https://www.tikwm.com/api/?url={urllib.parse.quote(url)}&web=1"
        res = requests.get(api_url, timeout=15).json()
        
        if res.get("code") == 0 and "data" in res:
            d = res["data"]
            author = d.get("author", {})
            music_info = d.get("music_info", {})

            stats_caption = (
                f"👤 <b>اسم الحساب :</b> {author.get('nickname', 'مستخدم')}\n"
                f"🔖 <b>المعرّف :</b> @{author.get('unique_id', '')}\n"
                f"📝 <b>الوصف :</b> {d.get('title', '')[:100]}\n\n"
                f"👁 <b>المشاهدات:</b> {format_number(d.get('play_count'))}\n"
                f"❤️ <b>الإعجابات:</b> {format_number(d.get('digg_count'))}\n"
                f"💬 <b>التعليقات:</b> {format_number(d.get('comment_count'))}\n"
                f"🔁 <b>المشاركات:</b> {format_number(d.get('share_count'))}\n\n"
                f"🤖 @{BOT_USERNAME}"
            )

            # فحص إذا كان المنشور عبارة عن ألبوم صور
            images = d.get("images")
            if images and isinstance(images, list) and len(images) > 0:
                music_url = d.get("music")
                if music_url and music_url.startswith("/"):
                    music_url = "https://www.tikwm.com" + music_url

                return {
                    "type": "images",
                    "images": images,
                    "caption": stats_caption,
                    "music": music_url,
                    "music_title": music_info.get("title", "صوت TikTok"),
                    "music_author": author.get("nickname", "TikTok")
                }

            # إذا كان المنشور فيديو عادي
            video_url = d.get("play") or d.get("hdplay") or d.get("wmplay")
            if video_url and video_url.startswith("/"):
                video_url = "https://www.tikwm.com" + video_url

            music_url = d.get("music")
            if music_url and music_url.startswith("/"):
                music_url = "https://www.tikwm.com" + music_url

            return {
                "type": "video",
                "video": video_url,
                "caption": stats_caption,
                "music": music_url or video_url
            }
    except Exception as e:
        logger.error(f"TikWM Engine Error: {e}")
    return None

# ==================== 4. معالج المنصات الأخرى (Instagram / Facebook / Threads) ====================
def process_rapidapi(url: str):
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    endpoints = [
        f"https://{RAPIDAPI_HOST}/",
        f"https://{RAPIDAPI_HOST}/media"
    ]
    for ep in endpoints:
        try:
            res = requests.get(ep, headers=headers, params={"url": url}, timeout=15)
            if res.status_code == 200:
                data = res.json()
                
                # مقاطع الفيديو
                video = data.get("download_url") or data.get("url") or data.get("media")
                if not video and isinstance(data.get("items"), list) and len(data["items"]) > 0:
                    video = data["items"][0].get("download_url") or data["items"][0].get("url")
                
                if video:
                    caption = f"✅ تم التحميل بنجاح\n🤖 @{BOT_USERNAME}"
                    return {"type": "video", "video": video, "caption": caption, "music": data.get("music_url") or video}
        except Exception as e:
            logger.error(f"RapidAPI query error: {e}")
    return None

# ==================== 5. استقبال الروابط ====================
@bot.message_handler(func=lambda m: bool(re.search(r'(https?://[^\s]+)', m.text or "")))
def handle_download(message):
    url_match = re.search(r'(https?://[^\s]+)', message.text)
    if not url_match:
        return
    raw_url = url_match.group(0)

    wait_msg = bot.reply_to(
        message, 
        "⏳ <b>جاري الاتصال بالسيرفر وفحص المحتوى...</b>\n"
        "<code>[██░░░░░░░░] 20%</code>"
    )

    try:
        # 1. إذا كان الرابط تيك توك
        if "tiktok.com" in raw_url or "douyin.com" in raw_url:
            data = process_tiktok(raw_url)
        else:
            data = process_rapidapi(raw_url)

        if not data:
            bot.edit_message_text("❌ تعذر العثور على الوسائط، تأكد أن المنشور عام وغير محذوف.", message.chat.id, wait_msg.message_id)
            return

        # ================= حالة ألبوم الصور (Photo Slideshow) =================
        if data["type"] == "images":
            bot.edit_message_text("⚡️ <b>تم العثور على ألبوم صور! جاري رفع الصور والموسيقى...</b>", message.chat.id, wait_msg.message_id)
            
            # إرسال كرت المعلومات مع أول صورة
            bot.send_photo(message.chat.id, data["images"][0], caption=data["caption"])

            # إرسال بقية الصور على هيئة ألبومات جماعية (Media Groups بحجم أقصاه 10 صور لكل دفعة)
            other_images = data["images"][1:]
            for i in range(0, len(other_images), 10):
                chunk = other_images[i:i+10]
                media_group = [types.InputMediaPhoto(img_url) for img_url in chunk]
                try:
                    bot.send_media_group(message.chat.id, media_group)
                except Exception as e:
                    logger.error(f"Error sending group: {e}")

            # إرسال مقطع الصوت MP3 المرفق
            if data.get("music"):
                try:
                    bot.send_audio(
                        message.chat.id, 
                        data["music"], 
                        title=data.get("music_title", "صوت المقطع"),
                        performer=data.get("music_author", "TikTok"),
                        caption=f"🎵 الصوت المرفق بالصور\n🤖 @{BOT_USERNAME}"
                    )
                except Exception as e:
                    logger.error(f"Error sending audio: {e}")

            bot.delete_message(message.chat.id, wait_msg.message_id)
            return

        # ================= حالة مقطع الفيديو (Video) =================
        elif data["type"] == "video":
            bot.edit_message_text("🚀 <b>جاري إرسال المقطع لشاشتك...</b>\n<code>[██████████] 100%</code>", message.chat.id, wait_msg.message_id)
            
            key = f"aud_{message.chat.id}_{int(time.time())}"
            AUDIO_STORE[key] = data.get("music") or data.get("video")

            markup = types.InlineKeyboardMarkup(row_width=2)
            btn_share = types.InlineKeyboardButton("🔗 شارك البوت", switch_inline_query="")
            btn_group = types.InlineKeyboardButton("✈️ أرسله في قروب", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")
            btn_audio = types.InlineKeyboardButton("استخراج الصوت MP3", callback_data=f"ext_{key}")
            markup.row(btn_share, btn_group)
            markup.row(btn_audio)

            try:
                bot.send_video(
                    message.chat.id, 
                    data["video"], 
                    caption=data["caption"], 
                    reply_markup=markup, 
                    supports_streaming=True
                )
                bot.delete_message(message.chat.id, wait_msg.message_id)
                return
            except Exception:
                stream = requests.get(data["video"], headers={'User-Agent': 'Mozilla/5.0'}, stream=True, timeout=30)
                bot.send_video(
                    message.chat.id, 
                    stream.raw, 
                    caption=data["caption"], 
                    reply_markup=markup, 
                    supports_streaming=True
                )
                bot.delete_message(message.chat.id, wait_msg.message_id)
                return

    except Exception as e:
        logger.error(f"General processing error: {e}")

    bot.edit_message_text("❌ تعذر تحميل المحتوى، تأكد من صحة الرابط.", message.chat.id, wait_msg.message_id)

# ==================== 6. استخراج الصوت ====================
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
        bot.send_audio(call.message.chat.id, source, caption=f"🎵 تم استخراج الصوت بنجاح\n🤖 @{BOT_USERNAME}")
        bot.delete_message(call.message.chat.id, load.message_id)
    except Exception:
        bot.edit_message_text("❌ تعذر إرسال الصوت لهذا المقطع.", call.message.chat.id, load.message_id)

# ==================== 7. الترحيب ====================
@bot.message_handler(commands=['start'])
def handle_start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📥 كيفية التحميل", "🔥 حساب صلوح تيك توك")
    welcome_text = (
        f"👑 <b>أهلاً بك يا {message.from_user.first_name} في بوت صلوح للتحميل السريع!</b>\n\n"
        "⚡️ <b>البوت يدعم الآن بشكل كامل:</b>\n"
        "• سحب فيديوهات TikTok بدون علامة مائية\n"
        "• سحب ألبومات وسلايدات صور TikTok دفعة واحدة كألبوم\n"
        "• استخراج الصوت والموسيقى MP3 المرفقة تلقائياً\n"
        "• تحميل مقاطع Instagram و Threads و Facebook\n\n"
        "🚀 <i>أرسل أي رابط الآن وسأجلبه لك فوراً...</i>"
    )
    bot.reply_to(message, welcome_text, reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    if message.text == "📥 كيفية التحميل":
        bot.reply_to(message, "فقط انسخ رابط أي مقطع أو صور من تيك توك أو المنصات الأخرى وأرسله هنا وسأجلبه لك فوراً 🚀")
    elif message.text == "🔥 حساب صلوح تيك توك":
        bot.reply_to(message, "🎬 تابع الحساب الرسمي على تيك توك:\nhttps://www.tiktok.com/@almanay22")
    else:
        bot.reply_to(message, "أرسل رابط المقطع أو الصور وسأقوم بسحبه فوراً 🚀")

# ==================== 8. حلقة التشغيل ====================
if __name__ == "__main__":
    logger.info("Universal Downloader Bot Started...")
    try:
        bot.remove_webhook()
        time.sleep(1)
    except Exception:
        pass

    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=25)
        except telebot.apihelper.ApiTelegramException as api_err:
            if api_err.error_code == 409:
                time.sleep(10)
            else:
                time.sleep(3)
        except Exception:
            time.sleep(5)
