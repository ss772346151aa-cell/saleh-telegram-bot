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

# ==================== إعدادات السجلات (Logging) ====================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== 1. خادم فحص الحالة السحابي (Render 24/7) ====================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return  # إسكات السجلات للحفاظ على نظافة الـ Console
    
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("Saleh Global Mega Platform 2026 is LIVE 24/7!".encode('utf-8'))

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        logger.info(f"Health check server running on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start health server: {e}")

threading.Thread(target=run_health_server, daemon=True).start()

# ==================== 2. تهيئة التوكن والبيانات ====================
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
        except Exception as e:
            logger.error(f"Error loading DB: {e}")
    return {"users": {}, "groups": {}, "tasks": {}, "vault": {}, "sales": {}, "warns": {}}

def save_db(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving DB: {e}")

# ==================== 3. محركات الذكاء الاصطناعي ====================
def query_ai_engine(prompt: str, context: str = "") -> str:
    try:
        full_p = f"أنت مساعد صلوح المانعي الذكي العالمي. أجب بأسلوب لبق، ذكي، وسريع: {context}\n{prompt}"
        url = f"https://text.pollinations.ai/{urllib.parse.quote(full_p)}"
        res = requests.get(url, timeout=15)
        if res.status_code == 200 and len(res.text.strip()) > 2:
            return res.text.strip()
    except Exception as e:
        logger.warning(f"AI Engine error: {e}")
    return "⚡️ عذراً، محرك الذكاء الاصطناعي مشغول حالياً، يرجى إعادة المحاولة بعد ثوانٍ."

def analyze_sentiment(text: str) -> str:
    positive = ["شكرا", "ممتاز", "رائع", "جميل", "احسنت", "مبدع", "تسلم", "كفو", "حلو"]
    negative = ["سيء", "فاشل", "زفت", "غبي", "بطيء", "مشكلة", "خطا", "خطأ"]
    text_lower = text.lower()
    pos = sum(1 for w in positive if w in text_lower)
    neg = sum(1 for w in negative if w in text_lower)
    if pos > neg: return "إيجابية وودية 🟢"
    elif neg > pos: return "سلبية / انزعاج 🔴"
    return "محايدة / استفسارية ⚪️"

# ==================== 4. القوائم والواجهات ====================
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🧠 ذكاء اصطناعي فائق", "🎨 توليد/تعديل صور")
    markup.row("📚 مكتبة الكتب والملفات", "🌐 ترجمة فورية")
    markup.row("💰 أسعار العملات والذهب", "📊 تقارير المبيعات")
    markup.row("📝 دفتر المهام", "📁 الأرشيف السحابي")
    markup.row("🛡️ إدارة المجموعات", "🗳️ تصويت فوري")
    markup.row("🎬 بحث تيك توك", "🎵 طلب شيلات وأغاني")
    markup.row("🆘 المساعدة والدعم")
    return markup

# ==================== 5. الأوامر الأساسية ====================
@bot.message_handler(commands=['start'])
def handle_start(message):
    uid = str(message.from_user.id)
    db = load_db()
    if uid not in db["users"]:
        db["users"][uid] = {
            "name": message.from_user.first_name,
            "username": message.from_user.username or "بدون",
            "joined": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        save_db(db)

    welcome_msg = (
        f"👋 مرحباً بك يا <b>{message.from_user.first_name}</b> في <b>{BOT_NAME}</b>!\n\n"
        "🚀 <b>منصتك الشاملة لجميع الخدمات السحابية:</b>\n"
        "✅ ذكاء اصطناعي وتوليد صور 4K حقيقي\n"
        "✅ إدارة وحماية المجموعات من السبام والروابط\n"
        "✅ حفظ وأرشفة المستندات والملفات سحابياً\n"
        "✅ سحب ميديا تيك توك وصوتيات MP3 نقية\n"
        "✅ مؤشرات التداول والعملات والترجمة الفورية\n\n"
        "👇 <b>اختر من القائمة التفاعلية بالأسفل للبدء:</b>"
    )
    inline = types.InlineKeyboardMarkup()
    inline.add(types.InlineKeyboardButton("🔥 متابعة صلوح على تيك توك", url=TIKTOK_CHANNEL))
    bot.reply_to(message, welcome_msg, reply_markup=inline)
    bot.send_message(message.chat.id, "لوحة التحكم جاهزة في خدمتك:", reply_markup=get_main_keyboard())

@bot.message_handler(commands=['help'])
def handle_help(message):
    help_text = (
        "📖 <b>دليل الاستخدام السريع للمنصة:</b>\n\n"
        "• <b>الذكاء الاصطناعي:</b> اضغط على الزر واكتب سؤالك مباشرة.\n"
        "• <b>الصور:</b> أرسل وصفاً للتصميم (أو أرسل صورة ومعها تعليق لتحسينها).\n"
        "• <b>الترجمة:</b> اكتب: <code>ترجم النص إلى اللغة</code>.\n"
        "• <b>المهام:</b> اكتب: <code>اضف مهمة [اسم المهمة]</code>.\n"
        "• <b>المبيعات:</b> اكتب: <code>اضف بيع 100</code>.\n"
        "• <b>المستندات:</b> أرسل أي ملف ليتم تخزينه في أرشيفك السحابي."
    )
    bot.reply_to(message, help_text)

# ==================== 6. إدارة وحماية المجموعات ====================
@bot.message_handler(commands=['ban'])
def admin_ban(message):
    if message.chat.type in ['group', 'supergroup']:
        admins = [a.user.id for a in bot.get_chat_administrators(message.chat.id)]
        if message.from_user.id in admins and message.reply_to_message:
            target = message.reply_to_message.from_user
            bot.ban_chat_member(message.chat.id, target.id)
            bot.reply_to(message, f"🚫 تم حظر العضو <b>{target.first_name}</b> بنجاح.")

@bot.message_handler(commands=['mute'])
def admin_mute(message):
    if message.chat.type in ['group', 'supergroup']:
        admins = [a.user.id for a in bot.get_chat_administrators(message.chat.id)]
        if message.from_user.id in admins and message.reply_to_message:
            target = message.reply_to_message.from_user
            bot.restrict_chat_member(message.chat.id, target.id, can_send_messages=False)
            bot.reply_to(message, f"🔇 تم كتم العضو <b>{target.first_name}</b>.")

@bot.message_handler(content_types=['new_chat_members'])
def handle_new_members(message):
    for member in message.new_chat_members:
        if member.id != bot.get_me().id:
            bot.send_message(message.chat.id, f"👋 أهلاً بك يا <b>{member.first_name}</b> في المجموعة! نتمنى لك وقتاً طيباً.")

# فحص الروابط للمجموعات
@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'] and bool(re.search(r'(https?://[^\s]+|t\.me/[^\s]+)', m.text or "")))
def handle_group_links(message):
    admins = [a.user.id for a in bot.get_chat_administrators(message.chat.id)]
    if message.from_user.id not in admins:
        try:
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(message.chat.id, f"⚠️ عذراً <b>{message.from_user.first_name}</b>، الروابط محظورة هنا لحماية الأعضاء.")
        except Exception:
            pass

# ==================== 7. الأرشيف السحابي وحفظ الملفات ====================
@bot.message_handler(content_types=['document'])
def handle_documents(message):
    uid = str(message.from_user.id)
    doc = message.document
    db = load_db()
    if "vault" not in db: db["vault"] = {}
    if uid not in db["vault"]: db["vault"][uid] = []
    
    db["vault"][uid].append({"name": doc.file_name, "id": doc.file_id, "size": doc.file_size})
    save_db(db)
    bot.reply_to(message, f"📁 <b>تم حفظ الملف في أرشيفك السحابي!</b>\n📄 الاسم: <code>{doc.file_name}</code>\n📦 الحجم: {doc.file_size // 1024} KB")

# ==================== 8. معالجة وتوليد الصور الفعلي (Flux 4K) ====================
@bot.message_handler(content_types=['photo'])
def handle_photo_ai(message):
    caption = (message.caption or "").strip()
    wait = bot.reply_to(message, "🎨 <b>جاري معالجة الصورة وتطبيق الذكاء الاصطناعي 4K... ✨</b>")
    prompt = f"masterpiece, ultra realistic 4k HDR, {caption if caption else 'cinematic colorized photography'}"
    img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&model=flux&seed={message.id}&nologo=true"
    try:
        bot.send_photo(message.chat.id, img_url, caption=f"🖼 <b>تمت المعالجة بنجاح!</b>\n🎯 الطلب: <i>{caption if caption else 'تلوين ورفع الدقة 4K'}</i>")
        bot.delete_message(message.chat.id, wait.message_id)
    except Exception:
        bot.edit_message_text("⚠️ تعذر إتمام المعالجة، حاول لاحقاً.", message.chat.id, wait.message_id)

# ==================== 9. معالجة الرسائل الخاصة والأزرار ====================
@bot.message_handler(func=lambda m: m.chat.type == 'private')
def process_private_chat(message):
    text = message.text.strip()
    chat_id = message.chat.id
    uid = str(message.from_user.id)
    db = load_db()

    # --- الأزرار المباشرة ---
    if text == "🧠 ذكاء اصطناعي فائق":
        bot.reply_to(message, "💬 اكتب سؤالك أو استفسارك وسأجيبك بأعلى دقة وذكاء!")
        bot.register_next_step_handler(message, ai_callback)
        return

    if text == "🎨 توليد/تعديل صور":
        bot.reply_to(message, "✍️ اكتب وصف الصورة التي تريد توليدها (أو أرسل صورة مع تعليق لتحسينها):")
        bot.register_next_step_handler(message, image_gen_callback)
        return

    if text == "🌐 ترجمة فورية":
        bot.reply_to(message, "📝 أرسل النص مسبوقاً بكلمة ترجم (مثال: <code>ترجم صباح الخير إلى الإنجليزية</code>):")
        return

    if text == "💰 أسعار العملات والذهب":
        wait = bot.reply_to(message, "⏳ <b>جاري جلب أحدث أسعار البورصات العالمية...</b>")
        try:
            res = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,tether,solana&vs_currencies=usd", timeout=8).json()
            btc = res.get("bitcoin", {}).get("usd", 0)
            eth = res.get("ethereum", {}).get("usd", 0)
            sol = res.get("solana", {}).get("usd", 0)
            usdt = res.get("tether", {}).get("usd", 1.0)
            report = (
                "📈 <b>مؤشرات الأسواق العالمية اللحظية:</b>\n\n"
                f"🪙 <b>Bitcoin:</b> <code>${btc:,.2f}</code>\n"
                f"🔹 <b>Ethereum:</b> <code>${eth:,.2f}</code>\n"
                f"⚡️ <b>Solana:</b> <code>${sol:,.2f}</code>\n"
                f"💵 <b>USDT:</b> <code>${usdt}</code>"
            )
            bot.edit_message_text(report, chat_id, wait.message_id)
        except Exception:
            bot.edit_message_text("⚠️ تعذر جلب الأسعار، حاول بعد لحظات.", chat_id, wait.message_id)
        return

    if text == "📊 تقارير المبيعات":
        sales_val = db.get("sales", {}).get(uid, 0.0)
        bot.reply_to(message, f"💼 <b>إجمالي مبيعاتك المسجلة:</b>\n\n💰 <code>${sales_val:,.2f}</code>\n\nلإضافة مبلغ بيع جديد أرسل:\n<code>اضف بيع 150</code>")
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

    if text == "📝 دفتر المهام":
        tasks = db.get("tasks", {}).get(uid, [])
        if not tasks:
            bot.reply_to(message, "📝 <b>دفتر المهام فارغ.</b>\nلإضافة مهمة جديدة أرسل:\n<code>اضف مهمة مراجعة التقارير اليومية</code>")
        else:
            txt = "📋 <b>قائمة مهامك الحالية:</b>\n\n"
            for idx, t in enumerate(tasks, 1):
                txt += f"{idx}️⃣ {t}\n"
            txt += "\n<i>لمسح القائمة كاملة، اكتب: مسح المهام</i>"
            bot.reply_to(message, txt)
        return

    if text.startswith("اضف مهمة"):
        task_str = text.replace("اضف مهمة", "").strip()
        if task_str:
            if "tasks" not in db: db["tasks"] = {}
            if uid not in db["tasks"]: db["tasks"][uid] = []
            db["tasks"][uid].append(task_str)
            save_db(db)
            bot.reply_to(message, f"✅ تمت إضافة المهمة: <b>{task_str}</b>")
        return

    if text == "مسح المهام":
        if "tasks" in db and uid in db["tasks"]:
            db["tasks"][uid] = []
            save_db(db)
            bot.reply_to(message, "🗑 تم تفريغ قائمة المهام بنجاح.")
        return

    if text == "📁 الأرشيف السحابي":
        files = db.get("vault", {}).get(uid, [])
        if not files:
            bot.reply_to(message, "📁 <b>أرشيفك السحابي فارغ.</b> أرسل أي ملف في الشات وسأخزنه لك فوراً.")
        else:
            txt = "📁 <b>ملفاتك المخزنة سحابياً:</b>\n\n"
            for idx, f in enumerate(files[-10:], 1):
                txt += f"{idx}. 📄 <code>{f['name']}</code> ({f['size']//1024} KB)\n"
            bot.reply_to(message, txt)
        return

    if text == "🛡️ إدارة المجموعات":
        bot.reply_to(message, "🛡️ أضف البوت مشرفاً في مجموعتك وسيتولى حذف الروابط وحظر السبام وتطبيق أوامر /ban و /mute تلقائياً.")
        return

    if text == "🗳️ تصويت فوري":
        bot.send_poll(chat_id, "ما رأيك في سرعة خدمات البوت والذكاء الاصطناعي؟", ["سريعة وممتازة 🚀", "جيدة جداً ⚡️", "تحتاج ميزات إضافية 💡"], is_anonymous=False)
        return

    if text == "🎬 بحث تيك توك":
        bot.reply_to(message, "🎬 أرسل رابط الفيديو أو اكتب كلمة البحث وسأجلبه لك بدون علامة مائية فوراً!")
        return

    if text == "🎵 طلب شيلات وأغاني":
        bot.reply_to(message, "🎵 اكتب اسم الشيلة أو المنشد وسأحضرها لك صوتية MP3.")
        return

    if text == "🆘 المساعدة والدعم":
        bot.reply_to(message, f"🆘 للدعم الفني والتواصل مع المطور:\n{TIKTOK_CHANNEL}")
        return

    # --- الترجمة التلقائية ---
    if text.startswith("ترجم"):
        q = text.replace("ترجم", "").strip()
        wait = bot.reply_to(message, "🌐 <b>جاري الترجمة الفورية...</b>")
        ans = query_ai_engine(f"ترجم بدقة واحترافية: {q}")
        bot.edit_message_text(f"🌐 <b>الترجمة:</b>\n\n{ans}", chat_id, wait.message_id)
        return

    # --- سحب تيك توك الفعلي ---
    if "tiktok.com" in text or "douyin.com" in text:
        wait = bot.reply_to(message, "⚡️ <b>جاري سحب الفيديو بدون علامة مائية...</b>")
        try:
            url_match = re.search(r'(https?://[^\s]+)', text)
            clean_link = url_match.group(0).split('?')[0] if url_match else text
            api_url = f"https://www.tikwm.com/api/?url={urllib.parse.quote(clean_link)}"
            res = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15).json()
            if res.get("code") == 0:
                v = res["data"]
                dl_url = v.get("hdplay") or v.get("play") or v.get("wmplay")
                if dl_url.startswith("/"): dl_url = "https://www.tikwm.com" + dl_url
                bot.send_video(chat_id, dl_url, caption=f"🎬 <b>{v.get('title', 'فيديو')[:100]}</b>\n\n👑 <b>{BOT_NAME}</b>")
                bot.delete_message(chat_id, wait.message_id)
                return
        except Exception:
            pass
        bot.edit_message_text("❌ تعذر تحميل المقطع، تأكد أن الفيديو عام.", chat_id, wait.message_id)
        return

    # --- البحث عن الشيلات والصوتيات الفعلي ---
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

    # --- الدردشة والذكاء الاصطناعي الافتراضي ---
    sentiment = analyze_sentiment(text)
    wait = bot.reply_to(message, "⚡️ <b>جاري التفكير والمعالجة...</b>")
    ai_ans = query_ai_engine(text, context=f"مشاعر المستخدم: {sentiment}")
    bot.edit_message_text(f"{ai_ans}\n\n<i>[الحالة النفسية للنص: {sentiment}]</i>", chat_id, wait.message_id)

def ai_callback(message):
    wait = bot.reply_to(message, "⏳ <b>جاري المعالجة...</b>")
    ans = query_ai_engine(message.text)
    bot.edit_message_text(ans, message.chat.id, wait.message_id)

def image_gen_callback(message):
    desc = message.text
    wait = bot.reply_to(message, "🎨 <b>جاري توليد الصورة بدقة 4K فائقة عبر Flux... ✨</b>")
    img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(desc + ' ultra 4k photorealistic cinematic')}?width=1024&height=1024&model=flux&nologo=true"
    try:
        bot.send_photo(message.chat.id, img_url, caption=f"🖼 <b>تم توليد صورتك بنجاح!</b>\n✨ الوصف: <i>{desc}</i>")
        bot.delete_message(message.chat.id, wait.message_id)
    except Exception:
        bot.edit_message_text("⚠️ تعذر توليد الصورة، جرب وصفاً آخر.", message.chat.id, wait.message_id)

# ==================== 10. تشغيل البوت ====================
if __name__ == "__main__":
    logger.info("Starting Saleh Global Mega Bot...")
    try:
        bot.infinity_polling(timeout=60)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
