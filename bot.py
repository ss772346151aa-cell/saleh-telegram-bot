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
        self.wfile.write("Saleh Mega Downloader Engine is Live 24/7!".encode('utf-8'))

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
        logger.error(f"Server Error: {e}")

threading.Thread(target=run_health_server, daemon=True).start()

# ==================== 2. تهيئة التوكن والهوية ====================
raw_token = os.environ.get("BOT_TOKEN", "")
if not raw_token:
    raise ValueError("BOT_TOKEN environment variable is not set!")

BOT_TOKEN = raw_token.strip()
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

BOT_USERNAME = "saleh_down_bot"
AUDIO_STORE = {}

# ==================== 3. فك الروابط المختصرة التلقائي ====================
def expand_short_url(url: str) -> str:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
        res = requests.head(url, allow_redirects=True, timeout=10, headers=headers)
        return res.url
    except Exception:
        return url

# ==================== 4. المحرك العالمي المباشر لسحب الـ CDN ====================
def extract_media_stream(url: str):
    real_url = expand_short_url(url)
    clean_url = real_url.split('?')[0] if ("tiktok.com" in real_url or "instagram.com" in real_url) else real_url

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }

    # 1. محرك تيك توك فائق السرعة
    if "tiktok.com" in real_url or "douyin.com" in real_url:
        try:
            api_url = f"https://www.tikwm.com/api/?url={urllib.parse.quote(real_url)}"
            res = requests.get(api_url, headers=headers, timeout=12).json()
            if res.get("code") == 0:
                d = res["data"]
                v_url = d.get("hdplay") or d.get("play") or d.get("wmplay")
                if v_url.startswith("/"): v_url = "https://www.tikwm.com" + v_url
                a_url = d.get("music")
                if a_url and a_url.startswith("/"): a_url = "https://www.tikwm.com" + a_url
                return {"video": v_url, "audio": a_url, "title": d.get("title", "مقطع تيك توك")}
        except Exception as e:
            logger.warning(f"TikTok API 1 failed: {e}")

        try:
            api2 = f"https://api.tiklydown.eu.org/api/download?url={urllib.parse.quote(real_url)}"
            res2 = requests.get(api2, headers=headers, timeout=12).json()
            v_url = res2.get("video", {}).get("noWatermark")
            a_url = res2.get("music", {}).get("play_url")
            if v_url:
                return {"video": v_url, "audio": a_url, "title": res2.get("title", "مقطع تيك توك")}
        except Exception:
            pass

    # 2. محرك إنستغرام وفيسبوك وسائر المنصات (بوابة CDN المتعددة)
    gateways = [
        # بوابة Cobalt العالمية السريعة
        ("https://co.wuk.sh/api/json", {"url": real_url, "vQuality": "1080"}),
        ("https://cobalt-api.kwiatekm.tokyo/api/json", {"url": real_url, "vQuality": "720"}),
        ("https://api.cobalt.tools/api/json", {"url": real_url, "vQuality": "max"})
    ]

    for g_url, payload in gateways:
        try:
            req_headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }
            res = requests.post(g_url, json=payload, headers=req_headers, timeout=10).json()
            if res.get("url"):
                return {"video": res["url"], "audio": res.get("url"), "title": "مقطع فيديو"}
        except Exception:
            continue

    # 3. بوابة VKR الاحتياطية لفيسبوك وإنستغرام
    try:
        if "facebook.com" in real_url or "fb.watch" in real_url:
            vkr_fb = f"https://api.vkrdownloader.com/fb/video.php?url={urllib.parse.quote(real_url)}"
            r = requests.get(vkr_fb, timeout=12, headers=headers).json()
            if r.get("status") == "success" and "data" in r:
                return {
                    "video": r["data"].get("hd") or r["data"].get("sd"),
                    "audio": None,
                    "title": r["data"].get("title", "فيديو فيسبوك")
                }
    except Exception:
        pass

    try:
        if "instagram.com" in real_url:
            ig_api = f"https://api.vkrdownloader.com/instagram/video.php?url={urllib.parse.quote(real_url)}"
            r2 = requests.get(ig_api, timeout=12, headers=headers).json()
            if r2.get("status") == "success" and "data" in r2:
                v_url = r2["data"].get("url") or r2["data"].get("video_url")
                if v_url:
                    return {"video": v_url, "audio": None, "title": "ريلز إنستغرام"}
    except Exception:
        pass

    return None

# ==================== 5. لوحة المفاتيح والترحيب ====================
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📥 كيفية التحميل", "🔥 حساب صلوح تيك توك")
    return markup

@bot.message_handler(commands=['start'])
def handle_start_cmd(message):
    welcome_text = (
        f"👑 <b>أهلاً بك يا {message.from_user.first_name} في بوت صلوح للتحميل السريع!</b>\n\n"
        "⚡️ <b>سحب فوري ومباشر بدون حدود للحجم من:</b>\n"
        "• <b>Instagram:</b> Reels & Posts\n"
        "• <b>TikTok:</b> بدون علامة مائية\n"
        "• <b>Facebook:</b> Reels & Videos\n"
        "• <b>YouTube:</b> Shorts & Videos\n\n"
        "🚀 <i>أرسل أي رابط مباشرة للتحميل الفوري...</i>"
    )
    bot.reply_to(message, welcome_text, reply_markup=get_main_keyboard())

# ==================== 6. معالجة الروابط وعرض العداد التفاعلي ====================
@bot.message_handler(func=lambda m: bool(re.search(r'(https?://[^\s]+)', m.text or "")))
def handle_links_execution(message):
    url_match = re.search(r'(https?://[^\s]+)', message.text)
    if not url_match:
        return
    target_url = url_match.group(0)

    # 1. بداية العداد (20%)
    wait_msg = bot.reply_to(
        message, 
        "⏳ <b>جاري الاتصال بالسيرفر وجلب الفيديو...</b>\n"
        "<code>[██░░░░░░░░] 20%</code>"
    )

    try:
        # 2. المرحلة الثانية (60%)
        time.sleep(0.3)
        bot.edit_message_text(
            "⚡️ <b>جاري فك التشفير وتجهيز البث المباشر بأعلى دقة...</b>\n"
            "<code>[██████░░░░] 60%</code>",
            message.chat.id, wait_msg.message_id
        )

        media = extract_media_stream(target_url)

        if media and media.get("video"):
            # 3. اكتمال التجهيز (100%)
            bot.edit_message_text(
                "🚀 <b>جاري الإرسال النهائي إلى شاشتك...</b>\n"
                "<code>[██████████] 100%</code>",
                message.chat.id, wait_msg.message_id
            )

            # تخزين رابط الصوت لاستخراجه
            audio_key = f"aud_{message.chat.id}_{int(time.time())}"
            AUDIO_STORE[audio_key] = media.get("audio") or media.get("video")

            # بناء الأزرار التفاعلية المطابقة للبوت العالمي
            markup = types.InlineKeyboardMarkup(row_width=2)
            btn_share = types.InlineKeyboardButton("🔗 شارك البوت", switch_inline_query="")
            btn_group = types.InlineKeyboardButton("✈️ أرسله في قروب", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")
            btn_audio = types.InlineKeyboardButton("استخراج الصوت MP3", callback_data=f"ext_{audio_key}")
            
            markup.row(btn_share, btn_group)
            markup.row(btn_audio)

            caption_text = (
                "تم التحميل بنجاح ✅\n"
                "إذا أردت الصوت فقط، استخدم الزر بالأسفل.\n\n"
                f"🤖 @{BOT_USERNAME}"
            )

            # إرسال الفيديو مباشرة عبر الرابط السحابي لتجاوز حد الـ 50MB
            try:
                bot.send_video(
                    message.chat.id, 
                    media["video"], 
                    caption=caption_text, 
                    reply_markup=markup
                )
                bot.delete_message(message.chat.id, wait_msg.message_id)
                return
            except Exception:
                # إذا تطلب المصدر تيار مباشر (Stream)
                res_stream = requests.get(media["video"], stream=True, timeout=25)
                bot.send_video(
                    message.chat.id, 
                    res_stream.raw, 
                    caption=caption_text, 
                    reply_markup=markup
                )
                bot.delete_message(message.chat.id, wait_msg.message_id)
                return

    except Exception as err:
        logger.error(f"Execution Error: {err}")

    bot.edit_message_text(
        "❌ تعذر تحميل المقطع مباشرة، تأكد أن المنشور متاح للعامة وليس من حساب خاص مغلق.",
        message.chat.id, wait_msg.message_id
    )

# ==================== 7. استخراج الصوت MP3 عبر الأزرار ====================
@bot.callback_query_handler(func=lambda c: c.data.startswith("ext_"))
def process_audio_extraction(call):
    key = call.data.replace("ext_", "")
    target_media = AUDIO_STORE.get(key)

    if not target_media:
        bot.answer_callback_query(call.id, "⚠️ انتهت صلاحية هذا الرابط، يرجى إعادة إرسال الفيديو مجدداً.", show_alert=True)
        return

    bot.answer_callback_query(call.id, "🎵 جاري استخراج ملف الصوت MP3...")
    load = bot.send_message(call.message.chat.id, "⚡️ <b>جاري تحويل ومعالجة الصوتية بنقاء تام...</b>")

    try:
        caption = f"🎵 تم استخراج الصوت بنجاح\n🤖 @{BOT_USERNAME}"
        bot.send_audio(call.message.chat.id, target_media, caption=caption)
        bot.delete_message(call.message.chat.id, load.message_id)
    except Exception:
        bot.edit_message_text("❌ تعذر استخراج الصوت من هذا المقطع بشكل منفصل.", call.message.chat.id, load.message_id)

# ==================== 8. الرسائل العامة ====================
@bot.message_handler(func=lambda m: True)
def process_text_replies(message):
    text = message.text.strip()
    if text == "📥 كيفية التحميل":
        bot.reply_to(message, "فقط انسخ رابط أي مقطع من تيك توك، إنستغرام ريلز، أو فيسبوك وأرسله هنا مباشرة في المحادثة وسيقوم البوت بسحبه فوراً 🚀")
    elif text == "🔥 حساب صلوح تيك توك":
        bot.reply_to(message, "🎬 تابع الحساب الرسمي على تيك توك:\nhttps://www.tiktok.com/@almanay22")
    else:
        bot.reply_to(message, "أهلاً بك يا غالي! أرسل رابط الفيديو (Instagram, TikTok, Facebook) وسأسحبه لك فوراً 🚀")

if __name__ == "__main__":
    logger.info("Master Saleh Downloader Bot is Running...")
    bot.infinity_polling(timeout=60)
