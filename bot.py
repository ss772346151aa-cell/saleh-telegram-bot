import os
import telebot
from telebot import types
import requests
import threading
import urllib.parse
import re
import json
import time
import random
import logging
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

# ==================== إعدادات السجلات (Logging) ====================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== 1. خادم فحص الحالة السحابي (Render 24/7) ====================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return  # Silence default logs to keep console clean
    
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Saleh Global Mega Platform 2026 is LIVE 24/7! 🚀")

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
ADMIN_ID = 7206214234  # يمكنك تغيير هذا الرقم إلى معرفك الخاص
BOT_NAME = "منصة صلوح المانعي العالمية ⚡️👑"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", thread_name="SalehBot")

DATA_FILE = "global_bot_data.json"

# قاعدة البيانات المحلية
def load_db():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading DB: {e}")
    return {"users": {}, "groups": {}, "tasks": {}, "vault": {}, "sales": {}, "warns": {}, "settings": {}}

def save_db(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving DB: {e}")

# تحميل البيانات عند البدء
db = load_db()
save_db(db)  # Ensure file exists even if empty

# ==================== 3. محركات الذكاء الاصطناعي المتطورة ====================
def query_ai_engine(prompt: str, context: str = "", model: str = "openai") -> str:
    """
    محرك ذكاء اصطناعي متعدد المصادر مع Retry Logic
    """
    try:
        full_prompt = f"{context}\n{prompt}" if context else prompt
        
        # محاولة 1: Pollinations AI (مجاني وسريع)
        url = f"https://text.pollinations.ai/{urllib.parse.quote(full_prompt)}"
        res = requests.get(url, timeout=25)
        
        if res.status_code == 200 and len(res.text.strip()) > 5:
            response_text = res.text.strip()
            # تنظيف بسيط للرد
            if response_text.startswith("```"):
                response_text = response_text.replace("```", "").replace("json", "").strip()
            return response_text
            
    except Exception as e:
        logger.warning(f"Pollinations failed: {e}")

    # محاولة 2: Fallback بسيط إذا فشل الأول
    try:
        url = f"https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        payload = {"inputs": full_prompt, "parameters": {"max_new_tokens": 250}}
        res = requests.post(url, json=payload, timeout=25)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list) and len(data) > 0:
                return data[0].get('generated_text', 'لا يوجد رد')
    except Exception:
        pass

    return "⚡️ عذراً، المحرك الرئيسي مشغول حالياً. يرجى المحاولة بعد ثوانٍ معدودة."

def analyze_sentiment(text: str) -> str:
    positive = ["شكرا", "ممتاز", "رائع", "جميل", "احسنت", "مبدع", "تسلم", "كفو", "حلو", "good", "great", "awesome"]
    negative = ["سيء", "فاشل", "زفت", "غبي", "بطيء", "مشكلة", "خطا", "خطأ", "bad", "terrible", "worst"]
    
    text_lower = text.lower()
    pos_count = sum(1 for w in positive if w in text_lower)
    neg_count = sum(1 for w in negative if w in text_lower)
    
    if pos_count > neg_count:
        return "إيجابية وودية 🟢"
    elif neg_count > pos_count:
        return "سلبية / انزعاج 🔴"
    return "محايدة / استفسارية ⚪️"

# ==================== 4. مكافحة التكرار السريع (Anti-Flood) ====================
USER_LAST_ACTION = {}
GROUP_FLOOD_LOGS = {}

def is_flooding(user_id, group_id=None, interval=1.0):
    now = time.time()
    key = f"{user_id}:{group_id}" if group_id else user_id
    
    last = USER_LAST_ACTION.get(key, 0)
    if now - last < interval:
        return True
    USER_LAST_ACTION[key] = now
    return False

# ==================== 5. القوائم والواجهات التفاعلية ====================
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🧠 ذكاء اصطناعي فائق", "🎨 توليد/تعديل صور")
    markup.row("📚 مكتبة الكتب والملفات", "🌐 ترجمة فورية")
    markup.row("💰 أسعار العملات والذهب", "📊 تقارير المبيعات")
    markup.row("📝 دفتر المهام", "📁 الأرشيف السحابي")
    markup.row("🛡️ إدارة المجموعات", "🗳️ تصويت فوري")
    markup.row("🎬 بحث تيك توك", "🎵 طلب أغاني")
    markup.row("⚙️ الإعدادات", "🆘 المساعدة والدعم")
    return markup

def get_admin_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("👥 إدارة الأعضاء", callback_data="admin_users"))
    markup.row(types.InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats"))
    markup.row(types.InlineKeyboardButton("🔧 الإعدادات العامة", callback_data="admin_settings"))
    return markup

# ==================== 6. معالجات الرسائل والأوامر ====================

@bot.message_handler(commands=['start'])
def handle_start(message):
    uid = str(message.from_user.id)
    db = load_db()
    
    if uid not in db["users"]:
        db["users"][uid] = {
            "name": message.from_user.first_name,
            "username": message.from_user.username or "بدون",
            "joined": datetime.now().isoformat(),
            "messages_count": 0,
            "level": 1,
            "xp": 0
        }
        save_db(db)
    
    # تحديث عدد الرسائل
    if uid in db["users"]:
        db["users"][uid]["messages_count"] += 1
        save_db(db)

    welcome_msg = f"""
👋 مرحباً بك يا **{message.from_user.first_name}** في منصة **صلوح المانعي العالمية**!

🚀 أنا بوتك الشخصي الذي يجمع لك كل شيء في مكان واحد:
✅ ذكاء اصطناعي متكامل
✅ إدارة مجموعات احترافية
✅ تحويل الملفات والصور
✅ أسعار العملات لحظة بلحظة
✅ وأكثر من ذلك بكثير!

👇 اضغط على أي خيار من القائمة أدناه للبدء:
"""
    bot.reply_to(message, welcome_msg, reply_markup=get_main_keyboard())

@bot.message_handler(commands=['help'])
def handle_help(message):
    help_text = """
📖 **دليل الاستخدام السريع:**

🧠 **الذكاء الاصطناعي:** أرسل أي سؤال أو اكتب "ذكاء"
🎨 **الصور:** اكتب "صورة [وصف الصورة]"
🌐 **الترجمة:** اكتب "ترجم [النص] [اللغة]"
💰 **الأسعار:** اكتب "سعر [العملة/الذهب]"
📝 **المهام:** اكتب "مهمة [اسم المهمة]"
📁 **الأرشيف:** ارفع ملف وسيتم حفظه تلقائياً

للمساعدة الإضافية، تواصل مع المطور @almanay22
"""
    bot.reply_to(message, help_text, parse_mode="HTML")

@bot.message_handler(func=lambda m: True)
def handle_general_messages(message):
    if message.chat.type == 'private':
        process_private_message(message)
    else:
        process_group_message(message)

def process_private_message(message):
    text = message.text.strip()
    uid = str(message.from_user.id)
    db = load_db()
    
    # تحديث المستخدم
    if uid in db["users"]:
        db["users"][uid]["last_active"] = datetime.now().isoformat()
        save_db(db)

    # زر لوحة التحكم الرئيسية
    if text == "🧠 ذكاء اصطناعي فائق":
        bot.reply_to(message, "💬 أجبني بأي سؤال وسأجيبك بذكاء وسرعة!", reply_markup=get_main_keyboard())
        # انتظار الرد التالي كسياق
        bot.register_next_step_handler(message, ai_callback)
        return

    if text == "🎨 توليد/تعديل صور":
        bot.reply_to(message, "✍️ اكتب وصف الصورة التي تريد توليدها بالتفصيل:", reply_markup=get_main_keyboard())
        bot.register_next_step_handler(message, image_gen_callback)
        return

    if text == "🌐 ترجمة متعددة اللغات":
        bot.reply_to(message, "📝 اكتب النص ثم اللغة التي تريد الترجمة إليها (مثال: Hello world English):", reply_markup=get_main_keyboard())
        bot.register_next_step_handler(message, translate_callback)
        return

    if text == "💰 التداول والعملات والذهب":
        fetch_financial_news(message)
        return

    if text == "📊 تقارير المبيعات والأرباح":
        bot.reply_to(message, "📈 جاري تحميل التقرير المالي...", reply_markup=get_main_keyboard())
        # محاكاة تقرير
        report = f"""
📊 **تقرير المبيعات الشهري**
📅 التاريخ: {datetime.now().strftime('%Y-%m-%d')}
💰 إجمالي المبيعات: $12,450
📦 الطلبات المكتملة: 145
🔄 نسبة النمو: +15% مقارنة بالشهر الماضي
"""
        bot.reply_to(message, report, parse_mode="HTML")
        return

    if text == "📝 دفتر المهام والمذكرات":
        bot.reply_to(message, "📝 اكتب اسم المهمة الجديدة:", reply_markup=get_main_keyboard())
        bot.register_next_step_handler(message, task_add_callback)
        return

    if text == "📁 الأرشيف السحابي الخاص":
        bot.reply_to(message, "📂 يمكنك الآن رفع الملفات (صور، مستندات، فيديو) وسيتم حفظها في أرشيفك الخاص بشكل آمن.", reply_markup=get_main_keyboard())
        return

    if text == "🛡 لوحة حماية المجموعات":
        bot.reply_to(message, "🛡️ لتفعيل الحماية في مجموعتك، أضف البوت كمسؤول وسيقوم بالحماية تلقائياً.", reply_markup=get_main_keyboard())
        return

    if text == "🗳 استطلاع / تصويت فوري":
        bot.reply_to(message, "🗳️ اكتب نص السؤال ثم الخيارات مفصولة بفاصلة (مثال: من هو الأفضل؟ A, B, C):", reply_markup=get_main_keyboard())
        bot.register_next_step_handler(message, poll_callback)
        return

    if text == "🎬 سحب وبحث تيك توك":
        bot.reply_to(message, "🔍 اكتب كلمة البحث عن مقطع تيك توك:", reply_markup=get_main_keyboard())
        bot.register_next_step_handler(message, tiktok_search_callback)
        return

    if text == "🎵 طلب شيلة MP3":
        bot.reply_to(message, "🎶 اكتب اسم الشيلة أو كلماتها:", reply_markup=get_main_keyboard())
        bot.register_next_step_handler(message, music_callback)
        return

    if text == "⚙️ الإعدادات":
        bot.reply_to(message, "⚙️ يمكنك تخصيص إعدادات البوت هنا (قريباً)", reply_markup=get_main_keyboard())
        return

    if text == "🆘 المساعدة والدعم":
        bot.reply_to(message, "🆘 للدعم الفني، تواصل مع المطور @almanay22", reply_markup=get_main_keyboard())
        return

    # إذا كان المستخدم يرسل نصاً عادياً، نفترض أنه يريد استخدام الذكاء الاصطناعي
    if not any(cmd in text for cmd in ["🧠", "🎨", "🌐", "💰", "📊", "📝", "📁", "🛡", "🗳", "🎬", "🎵", "⚙️", "🆘"]):
        # معالجة بسيطة للطلبات الشائعة
        if text.lower().startswith("ما هو") or text.lower().startswith("من هو") or text.lower().startswith("كيف"):
            bot.reply_to(message, "🧠 جاري التفكير في سؤالك العميق...")
            result = query_ai_engine(text)
            bot.reply_to(message, result)
        else:
            # رد افتراضي ذكي
            sentiment = analyze_sentiment(text)
            bot.reply_to(message, f"🤔 فهمت رسالتك ({sentiment}). هل تريد مني تحليلها أكثر أو البحث عنها؟", reply_markup=get_main_keyboard())


def ai_callback(message):
    """معالجة رد الذكاء الاصطناعي"""
    prompt = message.text
    bot.reply_to(message, "⏳ جاري المعالجة بواسطة خوارزميات صلوح الذكية...")
    result = query_ai_engine(prompt)
    bot.reply_to(message, result)

def image_gen_callback(message):
    """معالجة طلب توليد الصور"""
    desc = message.text
    bot.reply_to(message, "🎨 جاري رسم صورتك بدقة عالية...")
    # يمكن ربط API مثل DALL-E أو Stable Diffusion هنا
    # للمثال، سنستخدم رابط صورة عشوائية كـ Placeholder
    img_url = f"https://source.unsplash.com/random/800x600/?{urllib.parse.quote(desc)}"
    bot.send_photo(message.chat.id, img_url, caption=f"🖼️ صورة مولدة بناءً على: {desc}")

def translate_callback(message):
    """معالجة الترجمة"""
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ الرجاء كتابة النص واللغة الهدف. مثال: Hello world English")
        return
    
    text_to_translate = " ".join(parts[:-1])
    target_lang = parts[-1]
    
    bot.reply_to(message, "🌐 جاري الترجمة الدقيقة...")
    # استخدام Google Translate API مجاني عبر requests
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={urllib.parse.quote(text_to_translate)}"
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json()
            translated = "".join([sentence[0] for sentence in data[0]])
            bot.reply_to(message, f"📝 الترجمة:\n\n{translated}")
        else:
            bot.reply_to(message, "❌ حدث خطأ أثناء الترجمة.")
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {str(e)}")

def fetch_financial_news(message):
    """جلب أسعار العملات والذهب"""
    bot.reply_to(message, "💰 جاري جلب أحدث الأسعار من الأسواق العالمية...")
    try:
        # استخدام API مجاني للأسعار
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json()
            rates = data['rates']
            sar = rates.get('SAR', 0)
            eur = rates.get('EUR', 0)
            gbp = rates.get('GBP', 0)
            
            gold_price = "1950.50 $" # سعر ثابت كمثال
            
            news = f"""
💱 **أسعار العملات مقابل الدولار الأمريكي**
🇸🇦 الريال السعودي: 1 USD = {sar:.2f} SAR
🇪🇺 اليورو: 1 USD = {eur:.2f} EUR
🇬🇧 الجنيه الإسترليني: 1 USD = {gbp:.2f} GBP

🥇 **سعر الذهب العالمي (أونصة):**
💲 {gold_price}

📉 تم التحديث: {datetime.now().strftime('%H:%M:%S')}
"""
            bot.reply_to(message, news, parse_mode="HTML")
        else:
            bot.reply_to(message, "❌ فشل جلب الأسعار.")
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {str(e)}")

def task_add_callback(message):
    """إضافة مهمة جديدة"""
    task_name = message.text
    db = load_db()
    task_id = f"task_{len(db['tasks']) + 1}_{int(time.time())}"
    
    db["tasks"][task_id] = {
        "name": task_name,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "owner": str(message.from_user.id)
    }
    save_db(db)
    
    bot.reply_to(message, f"✅ تمت إضافة المهمة: **{task_name}** بنجاح!\n🆔 ID: {task_id}", parse_mode="HTML")

def poll_callback(message):
    """إنشاء تصويت"""
    parts = message.text.split(",")
    if len(parts) < 2:
        bot.reply_to(message, "❌ الرجاء كتابة السؤال والخيارات مفصولة بفاصلة. مثال: من هو الأفضل؟ A, B, C")
        return
    
    question = parts[0]
    options = [opt.strip() for opt in parts[1:]]
    
    bot.send_poll(
        message.chat.id, 
        question, 
        options, 
        is_anonymous=False, 
        allows_multiple_answers=False
    )

def tiktok_search_callback(message):
    """بحث تيك توك"""
    query = message.text
    bot.reply_to(message, f"🔍 جاري البحث عن: {query} في تيك توك...")
    # محاكاة نتيجة
    bot.reply_to(message, f"🎬 وجدت مقطعاً مشابهاً لـ '{query}'\n🔗 https://www.tiktok.com/@almanay22/video/1234567890")

def music_callback(message):
    """طلب أغنية"""
    song_name = message.text
    bot.reply_to(message, f"🎵 جاري البحث عن أغنية: {song_name}...")
    # محاكاة نتيجة
    bot.reply_to(message, f"🎶 وجدت الأغنية: {song_name}\n🔗 اضغط للتحميل: https://example.com/music/{urllib.parse.quote(song_name)}")

# ==================== 7. إدارة المجموعات والحماية ====================

@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'])
def process_group_message(message):
    chat_id = str(message.chat.id)
    db = load_db()
    
    # التأكد من وجود المجموعة في قاعدة البيانات
    if chat_id not in db["groups"]:
        db["groups"][chat_id] = {
            "name": message.chat.title,
            "members": [],
            "settings": {
                "anti_spam": True,
                "welcome_message": True,
                "link_protection": True
            },
            "warns": {}
        }
        save_db(db)

    # فحص التكرار السريع
    if is_flooding(message.from_user.id, chat_id, interval=1.5):
        bot.restrict_chat_member(chat_id, message.from_user.id, until_date=time.time() + 60, can_send_messages=False, can_send_media_messages=False)
        bot.reply_to(message, "⚠️ تنبيه: تكرار سريع! تم تجميد عضويتك مؤقتاً.")
        return

    # التحقق من الروابط
    if db["groups"].get(chat_id, {}).get("settings", {}).get("link_protection", True):
        if message.link_preview_enabled:
            bot.restrict_chat_member(chat_id, message.from_user.id, until_date=time.time() + 30, can_send_messages=False)
            bot.reply_to(message, "🔗 تم حذف الرابط غير المصرح به.")

    # رد الترحيب
    if db["groups"].get(chat_id, {}).get("settings", {}).get("welcome_message", True):
        if message.new_chat_members:
            for new_member in message.new_chat_members:
                welcome_msg = f"👋 مرحباً @{new_member.username} في مجموعة **{message.chat.title}**!"
                bot.reply_to(message, welcome_msg, reply_to_message_id=message.message_id)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.message:
        if call.data == "admin_users":
            bot.send_message(call.message.chat.id, "👥 قائمة الأعضاء محدثة.")
        elif call.data == "admin_stats":
            bot.send_message(call.message.chat.id, "📊 جاري تحميل الإحصائيات...")
        elif call.data == "admin_settings":
            bot.send_message(call.message.chat.id, "⚙️ إعدادات المجموعة.")

# ==================== 8. تشغيل البوت ====================
if __name__ == "__main__":
    logger.info("Starting Saleh Global Mega Bot...")
    try:
        bot.infinity_polling(timeout=60)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")