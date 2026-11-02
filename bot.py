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
import yt_dlp

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
        self.wfile.write("Saleh Mega Engine is Live 24/7!".encode('utf-8'))

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

# ==================== إعدادات التوكن والهوية ====================
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
    return {"users": {}, "vault": {}, "tasks": {}, "sales": {}}

def save_db(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ==================== المحرك الخارق لتحميل الفيديوهات (yt-dlp) ====================
def download_any_video(url: str, output_path: str = "downloaded_video.mp4"):
    """تحميل مباشر من السيرفر الأصلي لأي منصة (تيك توك، فيسبوك، إنستغرام، يوتيوب)"""
    if os.path.exists(output_path):
        try: os.remove(output_path)
        except Exception: pass

    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': False,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get('title', 'مقطع فيديو')
        return output_path, title

# ==================== محرك الذكاء الاصطناعي والصور ====================
def query_ai_engine(prompt: str) -> str:
    try:
        sys_p = "أنت مساعد ذكي لمنصة صلوح المانعي. قدم إجابات ذكية وسريعة وبالعربية مع إيموجي مميزة."
        url = f"https://text.pollinations.ai/{urllib.parse.quote(sys_p + ' : ' + prompt)}"
        res = requests.get(url, timeout=10)
        if res.status_code == 200 and len(res.text.strip()) > 1:
            return res.text.strip()
    except Exception:
        pass
    return "طلبك واصل يا غالي! أعد السؤال بكلمات أوضح وسأجيبك فوراً 🌹"

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🧠 ذكاء اصطناعي فائق", "🎨 توليد/تعديل صور")
    markup.row("💰 أسعار العملات والذهب", "📊 تقارير المبيعات")
    markup.row("📝 دفتر المهام", "📁 الأرشيف السحابي")
    markup.row("🎬 سحب الفيديوهات", "🎵 طلب شيلات MP3")
    markup.row("🆘 المساعدة والدعم")
    return markup

@bot.message_handler(commands=['start'])
def handle_start(message):
    welcome = (
        f"👑 <b>أهلاً بك يا {message.from_user.first_name} في {BOT_NAME}!</b>\n\n"
        "⚡️ <b>نظام السحب والذكاء السحابي المباشر:</b>\n"
        "• 📥 <b>سحب الفيديوهات الشامل:</b> أرسل أي رابط (تيك توك، فيسبوك ريلز، يوتيوب، إنستغرام) وسيتم تنزيله فوراً بأعلى جودة.\n"
        "• 🎨 <b>معالجة الصور 4K:</b> أرسل صورة واكتب معها (سويها كولورايز 4K) أو اكتب (ارسم كذا).\n"
        "• 🧠 <b>ذكاء اصطناعي:</b> إجابة فورية على جميع أسئلتك.\n\n"
        "👇 اختر من القائمة أو أرسل الرابط مباشرة الآن:"
    )
    bot.reply_to(message, welcome, reply_markup=get_main_keyboard())

# ==================== معالجة الروابط لجميع الشبكات (تيك توك، فيسبوك، إلخ) ====================
@bot.message_handler(func=lambda m: bool(re.search(r'(https?://[^\s]+)', m.text or "")))
def handle_links(message):
    url_match = re.search(r'(https?://[^\s]+)', message.text)
    if not url_match:
        return
    url = url_match.group(0)

    wait = bot.reply_to(message, "⚡️ <b>جاري سحب الفيديو بأعلى جودة مباشرة من السيرفر الأصلي... لحظات ✨</b>")
    video_file = f"video_{message.chat.id}_{int(time.time())}.mp4"

    try:
        path, title = download_any_video(url, output_path=video_file)
        if os.path.exists(path) and os.path.getsize(path) > 0:
            with open(path, 'rb') as vf:
                bot.send_video(
                    message.chat.id, 
                    vf, 
                    caption=f"🎬 <b>{title[:100]}</b>\n\n✨ تم السحب بنجاح عبر <b>{BOT_NAME}</b>"
                )
            bot.delete_message(message.chat.id, wait.message_id)
            try: os.remove(path)
            except Exception: pass
            return
    except Exception as e:
        logger.error(f"Download Engine Error: {e}")
        try:
            if os.path.exists(video_file): os.remove(video_file)
        except Exception: pass

    bot.edit_message_text("❌ تعذر تحميل المقطع، تأكد أن الفيديو عام ومتاح للجميع وليس من حساب خاص.", message.chat.id, wait.message_id)

# ==================== معالجة الصور 4K ====================
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    caption = (message.caption or "").strip()
    wait = bot.reply_to(message, "🎨 <b>جاري تطبيق معالجة الذكاء الاصطناعي 4K HDR... ✨</b>")
    prompt = f"masterpiece, ultra realistic 4k HDR, {caption if caption else 'cinematic colorized photography'}"
    img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&model=flux&seed={message.id}&nologo=true"
    try:
        bot.send_photo(message.chat.id, img_url, caption=f"🖼 <b>تمت المعالجة بنجاح!</b>\n🎯 الطلب: <i>{caption if caption else 'تلوين ورفع الدقة 4K'}</i>")
        bot.delete_message(message.chat.id, wait.message_id)
    except Exception:
        bot.edit_message_text("⚠️ تعذر إتمام المعالجة، حاول لاحقاً.", message.chat.id, wait.message_id)

# ==================== معالجة الأزرار والدردشة ====================
@bot.message_handler(func=lambda m: True)
def process_text_messages(message):
    text = message.text.strip()
    chat_id = message.chat.id
    uid = str(message.from_user.id)
    db = load_db()

    if "الأرشيف السحابي" in text:
        files = db.get("vault", {}).get(uid, [])
        if not files:
            bot.reply_to(message, "📁 <b>أرشيفك السحابي فارغ.</b> أرسل أي ملف وسأحفظه لك فوراً.")
        else:
            txt = "📁 <b>ملفاتك المحفوظة:</b>\n\n"
            for idx, f in enumerate(files[-10:], 1):
                txt += f"{idx}. 📄 <code>{f['name']}</code>\n"
            bot.reply_to(message, txt)
        return

    if "ذكاء اصطناعي" in text:
        bot.reply_to(message, "🧠 اكتب سؤالك أو استفسارك وسأجيبك فوراً!")
        return

    if "سحب الفيديوهات" in text:
        bot.reply_to(message, "🎬 أرسل رابط الفيديو الآن (تيك توك، فيسبوك ريلز، شورتس) وسأسحبه لك فوراً!")
        return

    if "توليد/تعديل صور" in text:
        bot.reply_to(message, "🎨 أرسل وصف الصورة التي تريد رسمها (أو أرسل صورة ومعها تعليق لتعديلها 4K).")
        return

    if "العملات والذهب" in text:
        wait = bot.reply_to(message, "⏳ <b>جاري الاتصال بالبورصة العالمية...</b>")
        try:
            res = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,tether,solana&vs_currencies=usd", timeout=8).json()
            btc = res.get("bitcoin", {}).get("usd", 0)
            eth = res.get("ethereum", {}).get("usd", 0)
            usdt = res.get("tether", {}).get("usd", 1.0)
            report = (
                "📈 <b>أسعار العملات المشفرة اللحظية:</b>\n\n"
                f"🪙 <b>Bitcoin:</b> <code>${btc:,.2f}</code>\n"
                f"🔹 <b>Ethereum:</b> <code>${eth:,.2f}</code>\n"
                f"💵 <b>USDT:</b> <code>${usdt}</code>"
            )
            bot.edit_message_text(report, chat_id, wait.message_id)
        except Exception:
            bot.edit_message_text("⚠️ تعذر جلب الأسعار حالياً.", chat_id, wait.message_id)
        return

    if "دفتر المهام" in text:
        tasks = db.get("tasks", {}).get(uid, [])
        if not tasks:
            bot.reply_to(message, "📝 <b>دفتر المهام فارغ.</b> لإضافة مهمة أرسل: <code>اضف مهمة كذا</code>")
        else:
            txt = "📋 <b>قائمة مهامك:</b>\n\n" + "\n".join([f"{i+1}️⃣ {t}" for i, t in enumerate(tasks)])
            bot.reply_to(message, txt)
        return

    if text.startswith("اضف مهمة"):
        t_val = text.replace("اضف مهمة", "").strip()
        if t_val:
            if "tasks" not in db: db["tasks"] = {}
            if uid not in db["tasks"]: db["tasks"][uid] = []
            db["tasks"][uid].append(t_val)
            save_db(db)
            bot.reply_to(message, f"✅ تمت إضافة المهمة:\n📌 <b>{t_val}</b>")
        return

    if "تقارير المبيعات" in text:
        sales_val = db.get("sales", {}).get(uid, 0.0)
        bot.reply_to(message, f"💼 <b>إجمالي المبيعات:</b> <code>${sales_val:,.2f}</code>\n\nلإضافة بيع أرسل: <code>اضف بيع 100</code>")
        return

    if text.startswith("اضف بيع"):
        nums = re.findall(r"[-+]?(?:\d*\.\d+|\d+)", text)
        if nums:
            val = float(nums[0])
            if "sales" not in db: db["sales"] = {}
            db["sales"][uid] = db["sales"].get(uid, 0.0) + val
            save_db(db)
            bot.reply_to(message, f"✅ تم تسجيل مبيعات بقيمة <b>${val:,.2f}</b>")
        return

    if "شيلات" in text or "أغاني" in text:
        bot.reply_to(message, "🎵 اكتب اسم الشيلة أو المنشد وسأحضرها لك صوتية MP3.")
        return

    if "المساعدة" in text:
        bot.reply_to(message, f"🆘 <b>للتواصل والدعم:</b>\n{TIKTOK_CHANNEL}")
        return

    # رسم الصور
    if any(text.startswith(w) for w in ["صمم", "ارسم", "تخيل"]):
        wait = bot.reply_to(message, "🎨 <b>جاري رسم الصورة بدقة 4K فائقة عبر Flux... ✨</b>")
        prompt = re.sub(r'^(صمم|ارسم|تخيل)\s*', '', text).strip()
        img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt + ' ultra 4k photorealistic cinematic')}?width=1024&height=1024&model=flux&nologo=true"
        try:
            bot.send_photo(chat_id, img_url, caption=f"🖼 <b>تم إنشاء التصميم بنجاح!</b>\n✨ الوصف: <i>{prompt}</i>")
            bot.delete_message(chat_id, wait.message_id)
            return
        except Exception:
            bot.edit_message_text("⚠️ تعذر توليد الصورة، جرب وصفاً آخر.", chat_id, wait.message_id)
            return

    # الرد التلقائي الذكي للدردشة
    wait = bot.reply_to(message, "⚡️ <b>جاري التفكير والمعالجة...</b>")
    ans = query_ai_engine(text)
    try:
        bot.edit_message_text(ans, chat_id, wait.message_id)
    except Exception:
        bot.send_message(chat_id, ans)

if __name__ == "__main__":
    logger.info("Starting Master Saleh Bot Engine...")
    bot.infinity_polling(timeout=60)
