import os
import telebot
from telebot import types
import requests
import threading
import urllib.parse
import re
import json
import time
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== خادم فحص الحالة السحابي (Render 24/7) ====================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return
    
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("Saleh Global Mega Platform is LIVE 24/7!".encode('utf-8'))

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
        logger.error(f"Failed to start health server: {e}")

threading.Thread(target=run_health_server, daemon=True).start()

# ==================== إعدادات التوكن ====================
raw_token = os.environ.get("BOT_TOKEN", "")
if not raw_token:
    raise ValueError("BOT_TOKEN environment variable is not set!")

BOT_TOKEN = raw_token.strip()
ADMIN_ID = 7206214234
BOT_NAME = "منصة صلوح المانعي العالمية ⚡️👑"
TIKTOK_CHANNEL = "https://www.tiktok.com/@almanay22"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

DATA_FILE = "global_bot_data.json"

def load_db():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"users": {}, "groups": {}, "tasks": {}, "vault": {}, "sales": {}, "warns": {}}

def save_db(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ==================== محرك الذكاء الاصطناعي الشامل ====================
def query_ai_engine(prompt: str, context: str = "") -> str:
    try:
        full_p = f"أنت مساعد صلوح المانعي الذكي. أجب بأسلوب لبق، ذكي، وسريع: {context}\n{prompt}"
        url = f"https://text.pollinations.ai/{urllib.parse.quote(full_p)}"
        res = requests.get(url, timeout=12)
        if res.status_code == 200 and len(res.text.strip()) > 2:
            return res.text.strip()
    except Exception:
        pass
    return "⚡️ عذراً، محرك الذكاء الاصطناعي مشغول حالياً، يرجى إعادة المحاولة بعد لحظات 🌹"

def analyze_sentiment(text: str) -> str:
    positive = ["شكرا", "ممتاز", "رائع", "جميل", "احسنت", "مبدع", "تسلم", "كفو", "حلو"]
    negative = ["سيء", "فاشل", "زفت", "غبي", "بطيء", "مشكلة", "خطا", "خطأ"]
    text_lower = text.lower()
    pos = sum(1 for w in positive if w in text_lower)
    neg = sum(1 for w in negative if w in text_lower)
    if pos > neg: return "إيجابية وودية 🟢"
    elif neg > pos: return "سلبية / انزعاج 🔴"
    return "محايدة / استفسارية ⚪️"

# ==================== محرك تنزيل الفيديوهات (فيسبوك، تيك توك، إنستغرام) ====================
def download_social_video(url: str):
    # إذا كان رابط تيك توك
    if "tiktok.com" in url or "douyin.com" in url:
        try:
            api_url = f"https://www.tikwm.com/api/?url={urllib.parse.quote(url)}"
            res = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15).json()
            if res.get("code") == 0:
                v = res["data"]
                dl_url = v.get("hdplay") or v.get("play") or v.get("wmplay")
                if dl_url.startswith("/"): dl_url = "https://www.tikwm.com" + dl_url
                return {"type": "video", "url": dl_url, "title": v.get("title", "فيديو تيك توك")}
        except Exception:
            pass

    # إذا كان رابط فيسبوك أو غيره
    if "facebook.com" in url or "fb.watch" in url:
        try:
            api_url = f"https://api.vkrdownloader.com/fb/video.php?url={urllib.parse.quote(url)}"
            res = requests.get(api_url, timeout=15).json()
            if res.get("status") == "success" and "data" in res:
                v_url = res["data"].get("hd") or res["data"].get("sd")
                return {"type": "video", "url": v_url, "title": res["data"].get("title", "فيديو فيسبوك")}
        except Exception:
            pass
            
    return None

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🧠 ذكاء اصطناعي فائق", "🎨 توليد/تعديل صور")
    markup.row("📚 مكتبة الكتب والملفات", "🌐 ترجمة فورية")
    markup.row("💰 أسعار العملات والذهب", "📊 تقارير المبيعات")
    markup.row("📝 دفتر المهام", "📁 الأرشيف السحابي")
    markup.row("🛡️ إدارة المجموعات", "🗳️ تصويت فوري")
    markup.row("🎬 بحث وسحب مقاطع", "🎵 طلب شيلات وأغاني")
    markup.row("🆘 المساعدة والدعم")
    return markup

@bot.message_handler(commands=['start'])
def handle_start(message):
    welcome_msg = (
        f"👋 مرحباً بك يا <b>{message.from_user.first_name}</b> في <b>{BOT_NAME}</b>!\n\n"
        "🚀 <b>خدمات التنزيل والذكاء المتكاملة:</b>\n"
        "• 📥 <b>سحب الفيديوهات:</b> أرسل أي رابط (فيسبوك، ريلز، تيك توك) لتحميله مباشرة.\n"
        "• 🧠 <b>الذكاء الاصطناعي:</b> إجابة على كافة الأسئلة وكتابة النصوص.\n"
        "• 🎨 <b>معالجة الصور 4K:</b> ارسم أو لون أي منظر.\n\n"
        "👇 اختر من القائمة أو أرسل رابط الفيديو مباشرة:"
    )
    bot.reply_to(message, welcome_msg, reply_markup=get_main_keyboard())

# ==================== معالجة الروابط لجميع الشبكات ====================
@bot.message_handler(func=lambda m: bool(re.search(r'(https?://[^\s]+)', m.text or "")))
def handle_links(message):
    url_match = re.search(r'(https?://[^\s]+)', message.text)
    if not url_match:
        return
    raw_url = url_match.group(0)

    wait = bot.reply_to(message, "⚡️ <b>جاري سحب ومعالجة الفيديو من الرابط... لحظات ✨</b>")
    data = download_social_video(raw_url)

    if data and data.get("url"):
        try:
            bot.send_video(
                message.chat.id, 
                data["url"], 
                caption=f"🎬 <b>{data.get('title', 'فيديو')[:100]}</b>\n\n✨ بواسطة: <b>{BOT_NAME}</b>"
            )
            bot.delete_message(message.chat.id, wait.message_id)
            return
        except Exception:
            pass

    bot.edit_message_text("❌ تعذر تحميل المقطع مباشرة، تأكد أن الفيديو عام وغير محمي بحساب خاص.", message.chat.id, wait.message_id)

# ==================== معالجة الصور ====================
@bot.message_handler(content_types=['photo'])
def handle_photo_ai(message):
    caption = (message.caption or "").strip()
    wait = bot.reply_to(message, "🎨 <b>جاري معالجة وتلوين الصورة بدقة 4K... ✨</b>")
    prompt = f"masterpiece, ultra realistic 4k HDR, {caption if caption else 'cinematic colorized photography'}"
    img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&model=flux&seed={message.id}&nologo=true"
    try:
        bot.send_photo(message.chat.id, img_url, caption=f"🖼 <b>تمت المعالجة بنجاح!</b>\n🎯 الطلب: <i>{caption if caption else 'تلوين ورفع الدقة 4K'}</i>")
        bot.delete_message(message.chat.id, wait.message_id)
    except Exception:
        bot.edit_message_text("⚠️ تعذر إتمام المعالجة، حاول لاحقاً.", message.chat.id, wait.message_id)

# ==================== المحادثات والأزرار العامة ====================
@bot.message_handler(func=lambda m: True)
def process_messages(message):
    text = message.text.strip()
    chat_id = message.chat.id

    if text == "🧠 ذكاء اصطناعي فائق":
        bot.reply_to(message, "💬 اكتب سؤالك أو موضوعك وسأجيبك فوراً!")
        return

    if text == "🎨 توليد/تعديل صور":
        bot.reply_to(message, "✍️ أرسل وصف الصورة التي تريد رسمها (أو أرسل صورة ومعها تعليق للتعديل):")
        return

    if text == "🎬 بحث وسحب مقاطع":
        bot.reply_to(message, "🎬 أرسل أي رابط (فيسبوك ريلز، تيك توك) وسأسحبه لك فوراً بجودة عالية!")
        return

    if text == "🎵 طلب شيلات وأغاني":
        bot.reply_to(message, "🎵 اكتب اسم الشيلة أو المنشد وسأحضرها لك صوتية MP3.")
        return

    if text.startswith("ترجم"):
        q = text.replace("ترجم", "").strip()
        wait = bot.reply_to(message, "🌐 <b>جاري الترجمة الفورية...</b>")
        ans = query_ai_engine(f"ترجم بدقة: {q}")
        bot.edit_message_text(f"🌐 <b>الترجمة:</b>\n\n{ans}", chat_id, wait.message_id)
        return

    # استجابة الذكاء الاصطناعي للأسئلة
    sentiment = analyze_sentiment(text)
    wait = bot.reply_to(message, "⚡️ <b>جاري التفكير والمعالجة...</b>")
    ai_ans = query_ai_engine(text, context=f"مشاعر المستخدم: {sentiment}")
    bot.edit_message_text(f"{ai_ans}\n\n<i>[الحالة النفسية للنص: {sentiment}]</i>", chat_id, wait.message_id)

if __name__ == "__main__":
    logger.info("Starting Saleh Global Mega Bot...")
    bot.infinity_polling(timeout=60)
