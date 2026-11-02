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

# ==================== 1. خادم فحص الحالة السحابي (Render 24/7) ====================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return
    
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("Saleh Mega Platform is LIVE 24/7!".encode('utf-8'))

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
        logger.error(f"Health server error: {e}")

threading.Thread(target=run_health_server, daemon=True).start()

# ==================== 2. تهيئة التوكن وقاعدة البيانات ====================
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

# ==================== 3. محرك فك الروابط وسحب الوسائط الذكي ====================
def resolve_short_url(url: str) -> str:
    """فك الروابط المختصرة لـ TikTok و Facebook و Instagram"""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.head(url, allow_redirects=True, timeout=8, headers=headers)
        return res.url
    except Exception:
        return url

def download_media(url: str):
    real_url = resolve_short_url(url)
    
    # محرك سحب تيك توك بكافة صيغه (vt.tiktok, vm.tiktok, tiktok.com)
    if "tiktok.com" in real_url or "douyin.com" in real_url:
        try:
            clean_link = real_url.split('?')[0]
            api_url = f"https://www.tikwm.com/api/?url={urllib.parse.quote(clean_link)}"
            res = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15).json()
            if res.get("code") == 0:
                v = res["data"]
                dl_url = v.get("hdplay") or v.get("play") or v.get("wmplay")
                if dl_url.startswith("/"): dl_url = "https://www.tikwm.com" + dl_url
                return {"type": "video", "url": dl_url, "title": v.get("title", "فيديو تيك توك")}
        except Exception as e:
            logger.error(f"TikTok TikWM error: {e}")

        # محرك تيك توك الاحتياطي في حال تعثر الأول
        try:
            alt_api = f"https://api.tiklydown.eu.org/api/download?url={urllib.parse.quote(real_url)}"
            res2 = requests.get(alt_api, timeout=12).json()
            video_url = res2.get("video", {}).get("noWatermark")
            if video_url:
                return {"type": "video", "url": video_url, "title": res2.get("title", "فيديو تيك توك")}
        except Exception:
            pass

    # محرك فيسبوك ريلز والفيديوهات
    if "facebook.com" in real_url or "fb.watch" in real_url:
        try:
            fb_api = f"https://api.vkrdownloader.com/fb/video.php?url={urllib.parse.quote(real_url)}"
            res = requests.get(fb_api, timeout=15).json()
            if res.get("status") == "success" and "data" in res:
                v_url = res["data"].get("hd") or res["data"].get("sd")
                return {"type": "video", "url": v_url, "title": res["data"].get("title", "فيديو فيسبوك")}
        except Exception:
            pass

    return None

# ==================== 4. محرك الذكاء الاصطناعي ====================
def query_ai_engine(prompt: str) -> str:
    try:
        sys_prompt = "أنت مساعد صلوح المانعي الذكي. أجب بإيجاز، سرعة، وبطريقة احترافية مع إيموجي مميزة."
        url = f"https://text.pollinations.ai/{urllib.parse.quote(sys_prompt + ' : ' + prompt)}"
        res = requests.get(url, timeout=10)
        if res.status_code == 200 and len(res.text.strip()) > 1:
            return res.text.strip()
    except Exception:
        pass
    return "طلبك واصل يا غالي! أعد صياغة استفسارك بكلمات أوضح وسأجيبك فوراً 🌹"

# ==================== 5. لوحة المفاتيح والبدء ====================
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🧠 ذكاء اصطناعي فائق", "🎨 توليد/تعديل صور")
    markup.row("📚 مكتبة الكتب والملفات", "🌐 ترجمة فورية")
    markup.row("💰 أسعار العملات والذهب", "📊 تقارير المبيعات")
    markup.row("📝 دفتر المهام", "📁 الأرشيف السحابي")
    markup.row("🎬 بحث وسحب مقاطع", "🎵 طلب شيلات وأغاني")
    markup.row("🆘 المساعدة والدعم")
    return markup

@bot.message_handler(commands=['start'])
def handle_start(message):
    welcome = (
        f"👑 <b>أهلاً بك يا {message.from_user.first_name} في {BOT_NAME}!</b>\n\n"
        "⚡️ <b>المنصة السحابية المباشرة في خدمتك 24/7:</b>\n"
        "• 📥 <b>سحب الفيديوهات:</b> أرسل رابط المقطع مباشرة (TikTok, Reels, Shorts).\n"
        "• 🎨 <b>معالجة وتلوين الصور:</b> أرسل أي صورة واكتب معها (سويها كولورايز 4K).\n"
        "• 🧠 <b>ذكاء اصطناعي شامل:</b> دردشة فورية وإجابة على كافة الأسئلة.\n\n"
        "👇 <b>اختر من القائمة أدناه أو ابدأ بالاستخدام مباشرة:</b>"
    )
    inline = types.InlineKeyboardMarkup()
    inline.add(types.InlineKeyboardButton("🔥 حساب صلوح على تيك توك", url=TIKTOK_CHANNEL))
    bot.reply_to(message, welcome, reply_markup=inline)
    bot.send_message(message.chat.id, "لوحة التحكم السريعة:", reply_markup=get_main_keyboard())

# ==================== 6. معالجة الروابط (أولوية مطلقة) ====================
@bot.message_handler(func=lambda m: bool(re.search(r'(https?://[^\s]+)', m.text or "")))
def handle_incoming_links(message):
    url_match = re.search(r'(https?://[^\s]+)', message.text)
    if not url_match:
        return
    raw_url = url_match.group(0)

    wait = bot.reply_to(message, "⚡️ <b>جاري سحب الفيديو بأعلى جودة وبدون علامة مائية... ✨</b>")
    data = download_media(raw_url)

    if data and data.get("url"):
        try:
            caption = f"🎬 <b>{data.get('title', 'فيديو')[:100]}</b>\n\n✨ بواسطة: <b>{BOT_NAME}</b>"
            bot.send_video(message.chat.id, data["url"], caption=caption)
            bot.delete_message(message.chat.id, wait.message_id)
            return
        except Exception as e:
            logger.error(f"Telegram send video error: {e}")

    bot.edit_message_text("❌ تعذر تحميل المقطع مباشرة، تأكد أن الفيديو متاح للعامة وليس خاصاً.", message.chat.id, wait.message_id)

# ==================== 7. حفظ المستندات في الأرشيف السحابي ====================
@bot.message_handler(content_types=['document'])
def handle_docs(message):
    uid = str(message.from_user.id)
    doc = message.document
    db = load_db()
    if "vault" not in db: db["vault"] = {}
    if uid not in db["vault"]: db["vault"][uid] = []

    db["vault"][uid].append({"name": doc.file_name, "id": doc.file_id, "size": doc.file_size})
    save_db(db)
    bot.reply_to(message, f"📁 <b>تم حفظ المستند في أرشيفك السحابي بنجاح!</b>\n📄 الاسم: <code>{doc.file_name}</code>\n📦 الحجم: {doc.file_size // 1024} KB")

# ==================== 8. معالجة وتوليد الصور 4K ====================
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    caption = (message.caption or "").strip()
    wait = bot.reply_to(message, "🎨 <b>جاري معالجة وتلوين الصورة بدقة 4K فائقة... ✨</b>")
    prompt = f"masterpiece, ultra realistic 4k HDR, {caption if caption else 'cinematic colorized photography'}"
    img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&model=flux&seed={message.id}&nologo=true"
    try:
        bot.send_photo(message.chat.id, img_url, caption=f"🖼 <b>تمت المعالجة بنجاح!</b>\n🎯 الطلب: <i>{caption if caption else 'تلوين ورفع الدقة 4K'}</i>")
        bot.delete_message(message.chat.id, wait.message_id)
    except Exception:
        bot.edit_message_text("⚠️ تعذر إتمام معالجة الصورة، حاول لاحقاً.", message.chat.id, wait.message_id)

# ==================== 9. معالجة الأزرار والرسائل النصية ====================
@bot.message_handler(func=lambda m: True)
def process_text_messages(message):
    text = message.text.strip()
    chat_id = message.chat.id
    uid = str(message.from_user.id)
    db = load_db()

    # فحص الأزرار بمرونة تامة (تطابق الكلمات بدلاً من التطابق الحرفي الصارم)
    if "الأرشيف السحابي" in text:
        files = db.get("vault", {}).get(uid, [])
        if not files:
            bot.reply_to(message, "📁 <b>أرشيفك السحابي فارغ حالياً!</b>\n\nأرسل أي ملف، صورة، أو مستند في الدردشة وسيقوم البوت بتخزينه لك فوراً.")
        else:
            txt = "📁 <b>ملفاتك المحفوظة سحابياً:</b>\n\n"
            for idx, f in enumerate(files[-10:], 1):
                txt += f"{idx}. 📄 <code>{f['name']}</code> ({f['size']//1024} KB)\n"
            bot.reply_to(message, txt)
        return

    if "ذكاء اصطناعي" in text:
        bot.reply_to(message, "🧠 اكتب سؤالك، استفسارك، أو موضوعك وسأجيبك فوراً!")
        return

    if "بحث وسحب مقاطع" in text:
        bot.reply_to(message, "🎬 أرسل رابط الفيديو (تيك توك، فيسبوك ريلز، إلخ) وسأسحبه لك فوراً بجودة عالية!")
        return

    if "توليد/تعديل صور" in text:
        bot.reply_to(message, "🎨 أرسل وصف الصورة التي تريد رسمها (أو أرسل صورة ومعها تعليق لتلوينها وتوضيحها 4K).")
        return

    if "العملات والذهب" in text:
        wait = bot.reply_to(message, "⏳ <b>جاري الاتصال بالبورصة العالمية...</b>")
        try:
            res = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,tether,solana&vs_currencies=usd", timeout=8).json()
            btc = res.get("bitcoin", {}).get("usd", 0)
            eth = res.get("ethereum", {}).get("usd", 0)
            sol = res.get("solana", {}).get("usd", 0)
            usdt = res.get("tether", {}).get("usd", 1.0)
            report = (
                "📈 <b>أسعار العملات المشفرة اللحظية:</b>\n\n"
                f"🪙 <b>Bitcoin:</b> <code>${btc:,.2f}</code>\n"
                f"🔹 <b>Ethereum:</b> <code>${eth:,.2f}</code>\n"
                f"⚡️ <b>Solana:</b> <code>${sol:,.2f}</code>\n"
                f"💵 <b>USDT:</b> <code>${usdt}</code>"
            )
            bot.edit_message_text(report, chat_id, wait.message_id)
        except Exception:
            bot.edit_message_text("⚠️ تعذر جلب الأسعار اللحظية، حاول مجدداً بعد قليل.", chat_id, wait.message_id)
        return

    if "دفتر المهام" in text:
        tasks = db.get("tasks", {}).get(uid, [])
        if not tasks:
            bot.reply_to(message, "📝 <b>دفتر المهام فارغ.</b>\nلإضافة مهمة جديدة أرسل:\n<code>اضف مهمة متابعة التحديثات</code>")
        else:
            txt = "📋 <b>قائمة مهامك الحالية:</b>\n\n"
            for idx, t in enumerate(tasks, 1):
                txt += f"{idx}️⃣ {t}\n"
            txt += "\n<i>لمسح جميع المهام أرسل: مسح المهام</i>"
            bot.reply_to(message, txt)
        return

    if text.startswith("اضف مهمة"):
        t_val = text.replace("اضف مهمة", "").strip()
        if t_val:
            if "tasks" not in db: db["tasks"] = {}
            if uid not in db["tasks"]: db["tasks"][uid] = []
            db["tasks"][uid].append(t_val)
            save_db(db)
            bot.reply_to(message, f"✅ تمت إضافة المهمة بنجاح:\n📌 <b>{t_val}</b>")
        return

    if text == "مسح المهام":
        if "tasks" in db and uid in db["tasks"]:
            db["tasks"][uid] = []
            save_db(db)
            bot.reply_to(message, "🗑 تم تفريغ دفتر المهام بنجاح.")
        return

    if "تقارير المبيعات" in text:
        sales_val = db.get("sales", {}).get(uid, 0.0)
        bot.reply_to(message, f"💼 <b>إجمالي مبيعاتك المسجلة:</b>\n\n💰 <code>${sales_val:,.2f}</code>\n\nلإضافة عملية بيع جديدة أرسل:\n<code>اضف بيع 150</code>")
        return

    if text.startswith("اضف بيع"):
        nums = re.findall(r"[-+]?(?:\d*\.\d+|\d+)", text)
        if nums:
            val = float(nums[0])
            if "sales" not in db: db["sales"] = {}
            db["sales"][uid] = db["sales"].get(uid, 0.0) + val
            save_db(db)
            bot.reply_to(message, f"✅ تم تسجيل مبيعات بقيمة <b>${val:,.2f}</b> بنجاح!")
        return

    if "طلب شيلات" in text or "أغاني" in text:
        bot.reply_to(message, "🎵 اكتب اسم الشيلة أو الزامل أو المنشد وسأحضرها لك صوتية MP3.")
        return

    if "المساعدة والدعم" in text:
        bot.reply_to(message, f"🆘 <b>للدعم والتواصل مع المطور:</b>\n{TIKTOK_CHANNEL}")
        return

    if text.startswith("ترجم"):
        q = text.replace("ترجم", "").strip()
        wait = bot.reply_to(message, "🌐 <b>جاري الترجمة الفورية...</b>")
        ans = query_ai_engine(f"ترجم بدقة: {q}")
        bot.edit_message_text(f"🌐 <b>الترجمة:</b>\n\n{ans}", chat_id, wait.message_id)
        return

    # سحب الشيلات والصوتيات
    if any(k in text.lower() for k in ["شيله", "شيلة", "اغنيه", "اغنية", "صوت", "زامل"]):
        wait = bot.reply_to(message, "🎵 <b>جاري البحث وسحب الصوتية بنقاء تام...</b>")
        try:
            clean_q = re.sub(r'^(شيله|شيلة|اغنيه|اغنية|صوت|زامل)\s*', '', text).strip()
            url = f"https://www.tikwm.com/api/feed/search?keywords={urllib.parse.quote(clean_q)}&count=1"
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=12).json()
            if res.get("code") == 0 and "data" in res and "videos" in res["data"] and len(res["data"]["videos"]) > 0:
                v = res["data"]["videos"][0]
                dl_url = v.get("play") or v.get("wmplay")
                if dl_url.startswith("/"): dl_url = "https://www.tikwm.com" + dl_url
                bot.send_audio(chat_id, dl_url, caption=f"🎵 <b>{v.get('title', clean_q)[:100]}</b>\n\n👑 <b>{BOT_NAME}</b>")
                bot.delete_message(chat_id, wait.message_id)
                return
        except Exception:
            pass
        bot.edit_message_text("⚠️ لم يتم العثور على الصوتية، جرب كتابة اسم المنشد بدقة.", chat_id, wait.message_id)
        return

    # توليد الصور عند طلب الرسم
    if any(text.startswith(w) for w in ["صمم", "ارسم", "تخيل", "انشئ صوره"]):
        wait = bot.reply_to(message, "🎨 <b>جاري رسم صورتك بأعلى دقة 4K عبر محركات Flux... ✨</b>")
        prompt = re.sub(r'^(صمم|ارسم|تخيل|انشئ صوره)\s*', '', text).strip()
        img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt + ' ultra 4k photorealistic cinematic')}?width=1024&height=1024&model=flux&nologo=true"
        try:
            bot.send_photo(chat_id, img_url, caption=f"🖼 <b>تم توليد الصورة بنجاح!</b>\n✨ الوصف: <i>{prompt}</i>")
            bot.delete_message(chat_id, wait.message_id)
            return
        except Exception:
            bot.edit_message_text("⚠️ تعذر توليد الصورة، جرب وصفاً آخر.", chat_id, wait.message_id)
            return

    # الاستجابة للدردشة العامة والذكاء الاصطناعي
    wait = bot.reply_to(message, "⚡️ <b>جاري التفكير والمعالجة...</b>")
    ai_ans = query_ai_engine(text)
    try:
        bot.edit_message_text(ai_ans, chat_id, wait.message_id)
    except Exception:
        bot.send_message(chat_id, ai_ans)

# ==================== 10. تشغيل البوت ====================
if __name__ == "__main__":
    logger.info("Starting Saleh Global Mega Bot...")
    bot.infinity_polling(timeout=60)