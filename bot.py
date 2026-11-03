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
        self.wfile.write(b"Saleh Mega Engine is Live 24/7!")

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

# ==================== 3. محرك الاستخراج الأصلي السريع ====================
def expand_url(short_url: str) -> str:
    """فك الروابط المختصرة لـ TikTok و Instagram و Facebook"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'
        }
        res = requests.get(short_url, headers=headers, allow_redirects=True, timeout=10)
        return res.url
    except Exception:
        return short_url

def extract_direct_video(url: str):
    """استخراج رابط البث المباشر متعدد المسارات بدون حظر السيرفرات"""
    real_url = expand_url(url)
    clean_url = real_url.split('?')[0] if ("tiktok.com" in real_url or "instagram.com" in real_url) else real_url

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*'
    }

    # 1. مسار TikTok الشامل
    if "tiktok.com" in real_url or "douyin.com" in real_url:
        # خادم SSSTik المباشر
        try:
            s_url = "https://ssstik.io/abc?url=dl"
            post_data = {"id": clean_url, "locale": "en", "tt": "0"}
            res = requests.post(s_url, data=post_data, headers={'User-Agent': 'Mozilla/5.0'}, timeout=12)
            match = re.search(r'href="(https://tikcdn\.io/ssstik/[^"]+)"', res.text) or re.search(r'href="([^"]+)" class="pure-button', res.text)
            if match:
                v_url = match.group(1)
                return {"video": v_url, "audio": v_url, "title": "فيديو تيك توك"}
        except Exception:
            pass

        # خادم TikWM الاحتياطي
        try:
            r = requests.get(f"https://www.tikwm.com/api/?url={urllib.parse.quote(clean_url)}", headers=headers, timeout=10).json()
            if r.get("code") == 0:
                d = r["data"]
                v_url = d.get("hdplay") or d.get("play") or d.get("wmplay")
                if v_url.startswith("/"): v_url = "https://www.tikwm.com" + v_url
                a_url = d.get("music")
                if a_url and a_url.startswith("/"): a_url = "https://www.tikwm.com" + a_url
                return {"video": v_url, "audio": a_url, "title": d.get("title", "فيديو تيك توك")}
        except Exception:
            pass

    # 2. مسار Instagram Reels المباشر
    if "instagram.com" in real_url:
        # بوابة FastDL المباشرة
        try:
            f_url = "https://fastdl.app/c/"
            f_res = requests.post(f_url, json={"url": real_url}, headers=headers, timeout=12).json()
            if f_res.get("items") and len(f_res["items"]) > 0:
                item = f_res["items"][0]
                video_url = item.get("urls", [{}])[0].get("url")
                if video_url:
                    return {"video": video_url, "audio": video_url, "title": "ريلز إنستغرام"}
        except Exception:
            pass

        # بوابة SnapInsta المباشرة
        try:
            api_snap = f"https://api.snapinsta.to/api/ajaxSearch"
            res_snap = requests.post(api_snap, data={"q": real_url, "t": "media", "lang": "en"}, headers=headers, timeout=12).json()
            if "data" in res_snap:
                match = re.search(r'href="(https://[^"]+)" download', res_snap["data"])
                if match:
                    return {"video": match.group(1), "audio": match.group(1), "title": "ريلز إنستغرام"}
        except Exception:
            pass

    # 3. مسار Facebook Videos & Reels
    if "facebook.com" in real_url or "fb.watch" in real_url:
        try:
            fb_api = "https://fdownloader.net/api/ajaxSearch"
            r_fb = requests.post(fb_api, data={"k_exp": "", "k_token": "", "q": real_url, "lang": "en"}, headers=headers, timeout=12).json()
            if "data" in r_fb:
                m = re.search(r'href="(https://[^"]+)"\s*class="btn\s*btn-download', r_fb["data"])
                if m:
                    return {"video": m.group(1), "audio": m.group(1), "title": "فيديو فيسبوك"}
        except Exception:
            pass

    # 4. البوابات الاحتياطية المفتوحة (Cobalt & VKR)
    for gate in ["https://api.cobalt.tools/api/json", "https://co.wuk.sh/api/json"]:
        try:
            r = requests.post(gate, json={"url": real_url, "vQuality": "720"}, headers={"Accept": "application/json", "Content-Type": "application/json"}, timeout=8).json()
            if r.get("url"):
                return {"video": r["url"], "audio": r["url"], "title": "مقطع فيديو"}
        except Exception:
            continue

    return None

# ==================== 4. الواجهة والأزرار ====================
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📥 كيفية التحميل", "🔥 حساب صلوح تيك توك")
    return markup

@bot.message_handler(commands=['start'])
def handle_start(message):
    welcome_msg = (
        f"👑 <b>أهلاً بك يا {message.from_user.first_name} في بوت صلوح للتحميل السريع!</b>\n\n"
        "⚡️ <b>يدعم التحميل الفوري وبأعلى دقة متجاوزاً أي حدود للحجم من:</b>\n"
        "• <b>Instagram:</b> Reels & Posts\n"
        "• <b>TikTok:</b> بدون علامة مائية\n"
        "• <b>Facebook:</b> Reels & Videos\n"
        "• <b>YouTube:</b> Shorts & Videos\n\n"
        "🚀 <i>أرسل أي رابط مباشرة للتحميل...</i>"
    )
    bot.reply_to(message, welcome_msg, reply_markup=get_main_keyboard())

# ==================== 5. معالجة الروابط وعرض العداد الفوري ====================
@bot.message_handler(func=lambda m: bool(re.search(r'(https?://[^\s]+)', m.text or "")))
def handle_download_request(message):
    url_match = re.search(r'(https?://[^\s]+)', message.text)
    if not url_match:
        return
    raw_url = url_match.group(0)

    wait_msg = bot.reply_to(
        message, 
        "⏳ <b>جاري الاتصال بالسيرفر وفك تشفير الرابط...</b>\n"
        "<code>[██░░░░░░░░] 20%</code>"
    )

    try:
        time.sleep(0.3)
        bot.edit_message_text(
            "⚡️ <b>جاري تجهيز البث المباشر بأعلى دقة وتخطي حد 50MB...</b>\n"
            "<code>[██████░░░░] 60%</code>",
            message.chat.id, wait_msg.message_id
        )

        media = extract_direct_video(raw_url)

        if media and media.get("video"):
            bot.edit_message_text(
                "🚀 <b>تم التجهيز، جاري تسليم المقطع لشاشتك...</b>\n"
                "<code>[██████████] 100%</code>",
                message.chat.id, wait_msg.message_id
            )

            key = f"aud_{message.chat.id}_{int(time.time())}"
            AUDIO_STORE[key] = media.get("audio") or media.get("video")

            markup = types.InlineKeyboardMarkup(row_width=2)
            btn_share = types.InlineKeyboardButton("🔗 شارك البوت", switch_inline_query="")
            btn_group = types.InlineKeyboardButton("✈️ أرسله في قروب", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")
            btn_audio = types.InlineKeyboardButton("استخراج الصوت MP3", callback_data=f"ext_{key}")
            markup.row(btn_share, btn_group)
            markup.row(btn_audio)

            caption = (
                "تم التحميل بنجاح ✅\n"
                "إذا أردت الصوت فقط، استخدم الزر بالأسفل.\n\n"
                f"🤖 @{BOT_USERNAME}"
            )

            # إرسال الفيديو كبث مباشر
            try:
                bot.send_video(
                    message.chat.id, 
                    media["video"], 
                    caption=caption, 
                    reply_markup=markup, 
                    supports_streaming=True
                )
                bot.delete_message(message.chat.id, wait_msg.message_id)
                return
            except Exception:
                # سحب متدفق (Stream) لإرساله دون حفظ في القرص
                headers = {'User-Agent': 'Mozilla/5.0'}
                stream = requests.get(media["video"], headers=headers, stream=True, timeout=30)
                bot.send_video(
                    message.chat.id, 
                    stream.raw, 
                    caption=caption, 
                    reply_markup=markup, 
                    supports_streaming=True
                )
                bot.delete_message(message.chat.id, wait_msg.message_id)
                return

    except Exception as e:
        logger.error(f"Download processing failed: {e}")

    bot.edit_message_text(
        "❌ تعذر تحميل المقطع مباشرة، تأكد أن الفيديو عام وغير محذوف.",
        message.chat.id, wait_msg.message_id
    )

# ==================== 6. استخراج الصوت MP3 ====================
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
        caption = f"🎵 تم استخراج الصوت بنجاح\n🤖 @{BOT_USERNAME}"
        bot.send_audio(call.message.chat.id, source, caption=caption)
        bot.delete_message(call.message.chat.id, load.message_id)
    except Exception:
        bot.edit_message_text("❌ تعذر إرسال الصوت بشكل منفصل لهذا المقطع.", call.message.chat.id, load.message_id)

# ==================== 7. الرسائل العامة ====================
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    text = message.text.strip()
    if text == "📥 كيفية التحميل":
        bot.reply_to(message, "فقط انسخ رابط أي مقطع من إنستغرام، تيك توك، أو فيسبوك وأرسله هنا وسأسحبه لك فوراً 🚀")
    elif text == "🔥 حساب صلوح تيك توك":
        bot.reply_to(message, "🎬 تابع الحساب الرسمي على تيك توك:\nhttps://www.tiktok.com/@almanay22")
    else:
        bot.reply_to(message, "أهلاً بك! أرسل رابط الفيديو (Instagram, TikTok, Facebook, YouTube) وسأسحبه لك فوراً 🚀")

# ==================== 8. حلقة التشغيل الآمنة ====================
if __name__ == "__main__":
    logger.info("Saleh Engine Started...")
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
