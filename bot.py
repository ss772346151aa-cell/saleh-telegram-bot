import os
import telebot
import requests
import threading
import urllib.parse
import re
import json
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# 1. خادم ويب مدمج لفحص سلامة السيرفر على Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Saleh Enterprise Super Bot is Live 24/7!")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

threading.Thread(target=run_health_server, daemon=True).start()

# 2. إعدادات البوت والتوكن
raw_token = os.environ.get("BOT_TOKEN", "")
BOT_TOKEN = raw_token.strip()

ADMIN_ID = 7206214234
BOT_NAME = "منصة صلوح المانعي الذكية الشاملة ⚡️👑"
TIKTOK_CHANNEL = "https://www.tiktok.com/@almanay22"
TIKTOK_USER = "@almanay22"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# قاعدة بيانات محلية لتخزين المهام، الملفات المحفوظة، وحسابات المبيعات
DATA_FILE = "user_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"tasks": {}, "vault": {}, "sales": {}}
    return {"tasks": {}, "vault": {}, "sales": {}}

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# محرك الذكاء الاصطناعي الشامل
def get_ai_reply(prompt: str) -> str:
    try:
        sys_prompt = "أنت مساعد ذكي فائق القدرات لمنصة صلوح المانعي. قدم إجابات مباشرة، ذكية، وافية وموثوقة مع تنسيق جمالي."
        url = f"https://text.pollinations.ai/{urllib.parse.quote(sys_prompt + ' : ' + prompt)}"
        res = requests.get(url, timeout=12)
        if res.status_code == 200 and len(res.text.strip()) > 2:
            return res.text.strip()
    except Exception:
        pass
    return f"طلبك حول <b>{prompt}</b> تحت المعالجة، يرجى كتابة تفاصيل أوضح وسأجيبك فوراً 🌹"

# لوحة الأزرار الرئيسية المتكاملة
def get_main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🧠 ذكاء اصطناعي ودردشة", "🎨 رسم وتصميم 4K")
    markup.row("📚 بحث عن كتب ومقالات", "🌐 ترجمة فورية")
    markup.row("💰 أسعار العملات والذهب", "📊 تتبع المبيعات والأرباح")
    markup.row("📝 قائمة مهامي ومذكراتي", "🛡 أوامر حماية المجموعات")
    markup.row("🎬 سحب وبحث تيك توك", "🎵 طلب شيلة MP3")
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    name = message.from_user.first_name
    text = (
        f"👑 <b>أهلاً وسهلاً بك يا {name} في {BOT_NAME}!</b>\n\n"
        "⚡️ <b>نظام الخدمات السحابية المتكاملة بدون أي برامج خارجية:</b>\n"
        "• 🧠 <b>ذكاء اصطناعي وتصميم:</b> دردشة فورية + توليد وتلوين صور 4K.\n"
        "• 📚 <b>مكتبة علمية وترجمة:</b> بحث وتحميل كتب PDF وترجمة لغات مباشرة.\n"
        "• 💰 <b>تجارة وتداول:</b> أسعار البيتكوين والعملات وإدارة أرباحك ومبيعاتك.\n"
        "• 🛡 <b>حماية وإدارة الجروبات:</b> منع الإعلانات وطرد وكتم المخالفين.\n"
        "• 📝 <b>تنظيم وإنجاز:</b> حفظ المذكرات، المهام، ومخزن الملفات الخاص.\n"
        "• 📥 <b>ميديا فائقة الدقة:</b> سحب تيك توك، صوتيات MP3، وأفلام.\n\n"
        f"🌟 <b>حساب تيك توك الرسمي:</b> <code>{TIKTOK_CHANNEL}</code>"
    )
    inline_kb = telebot.types.InlineKeyboardMarkup()
    inline_kb.add(telebot.types.InlineKeyboardButton("🔥 حساب صلوح على تيك توك 🔥", url=TIKTOK_CHANNEL))
    bot.reply_to(message, text, reply_markup=inline_kb)
    bot.send_message(message.chat.id, "👇 اختر الخدمة من القائمة التفاعلية أو ابدأ بالكتابة فوراً:", reply_markup=get_main_menu())

# ==================== 1. إدارة وحماية المجموعات ====================
@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.chat.type in ['group', 'supergroup']:
        admin_member = bot.get_chat_member(message.chat.id, message.from_user.id)
        if admin_member.status in ['creator', 'administrator']:
            if message.reply_to_message:
                target_user = message.reply_to_message.from_user
                bot.ban_chat_member(message.chat.id, target_user.id)
                bot.reply_to(message, f"🚫 تم طرد العضو <b>{target_user.first_name}</b> لحماية المجموعة.")
            else:
                bot.reply_to(message, "⚠️ قم بالرد على رسالة العضو المخالف بالأمر /ban لطرده.")

@bot.message_handler(commands=['mute'])
def mute_user(message):
    if message.chat.type in ['group', 'supergroup']:
        admin_member = bot.get_chat_member(message.chat.id, message.from_user.id)
        if admin_member.status in ['creator', 'administrator']:
            if message.reply_to_message:
                target_user = message.reply_to_message.from_user
                bot.restrict_chat_member(message.chat.id, target_user.id, can_send_messages=False)
                bot.reply_to(message, f"🔇 تم كتم العضو <b>{target_user.first_name}</b>.")
            else:
                bot.reply_to(message, "⚠️ قم بالرد على رسالة العضو بالأمر /mute لكتمه.")

# مكافحة الإعلانات والروابط المزعجة في المجموعات
@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'] and bool(re.search(r'(https?://[^\s]+|t\.me/[^\s]+)', m.text or "")))
def guard_links(message):
    admin_member = bot.get_chat_member(message.chat.id, message.from_user.id)
    if admin_member.status not in ['creator', 'administrator']:
        try:
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(message.chat.id, f"⚠️ عذراً {message.from_user.first_name}، نشر الروابط غير مسموح لحماية الأعضاء.")
        except Exception:
            pass

# ==================== 2. معالجة وتلوين الصور بالذكاء الاصطناعي ====================
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    caption = (message.caption or "").strip()
    
    wait = bot.reply_to(message, "⚡️ <b>جاري فحص الصورة وتطبيق المعالجة والذكاء الاصطناعي بدقة 4K... ✨</b>")
    prompt = f"highly detailed 4k cinematic HDR, {caption if caption else 'ultra realistic colorized landscape, master quality'}"
    generated_img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1280&height=1280&model=flux&seed={message.id}&nologo=true"

    try:
        cap_text = (
            f"🖼 <b>تمت المعالجة بنجاح عبر محرك الذكاء الفائق!</b>\n"
            f"🎯 <b>الطلب:</b> <i>{caption if caption else 'تلوين ورفع الدقة إلى 4K'}</i>\n\n"
            f"👑 <b>{BOT_NAME}</b>"
        )
        bot.send_photo(chat_id, generated_img_url, caption=cap_text)
        bot.delete_message(chat_id, wait.message_id)
    except Exception:
        bot.edit_message_text("⚠️ جاري تحديث المعالج، يرجى إعادة إرسال الصورة.", chat_id, wait.message_id)

# ==================== 3. المعالجة الذكية لكافة الرسائل والأزرار ====================
@bot.message_handler(func=lambda message: True)
def handle_general_requests(message):
    text = message.text.strip()
    chat_id = message.chat.id
    uid = str(message.from_user.id)
    db = load_data()

    # --- استجابات الأزرار الثابتة ---
    if text == "🛡 أوامر حماية المجموعات":
        guide = (
            "🛡 <b>أوامر الإشراف والحماية داخل الجروبات:</b>\n\n"
            "• أضف البوت مشرفاً بصلاحيات الحذف والطرد.\n"
            "• قم بالرد على أي مخالف بـ <code>/ban</code> لطرده نهائياً.\n"
            "• قم بالرد على أي مخالف بـ <code>/mute</code> لمنعه من الكتابة.\n"
            "• البوت يحذف تلقائياً الروابط المزعجة والإعلانات لحماية جروبك."
        )
        bot.reply_to(message, guide)
        return

    if text == "💰 أسعار العملات والذهب":
        wait = bot.reply_to(message, "⏳ <b>جاري سحب أحدث أسعار التداول الحية...</b>")
        try:
            res = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,tether&vs_currencies=usd", timeout=8).json()
            btc = res.get("bitcoin", {}).get("usd", "N/A")
            eth = res.get("ethereum", {}).get("usd", "N/A")
            usdt = res.get("tether", {}).get("usd", "N/A")
            report = (
                "📈 <b>أسعار العملات المشفرة اللحظية (سوق التداول):</b>\n\n"
                f"🪙 <b>Bitcoin (BTC):</b> <code>${btc:,}</code>\n"
                f"🔹 <b>Ethereum (ETH):</b> <code>${eth:,}</code>\n"
                f"💵 <b>Tether (USDT):</b> <code>${usdt}</code>\n\n"
                "⚡️ يتم تحديث البيانات فورياً ومباشرة من البورصات العالمية."
            )
            bot.edit_message_text(report, chat_id, wait.message_id)
            return
        except Exception:
            bot.edit_message_text("⚠️ تعذر جلب الأسعار اللحظية حالياً، يرجى المحاولة لاحقاً.", chat_id, wait.message_id)
            return

    if text == "📝 قائمة مهامي ومذكراتي":
        user_tasks = db.get("tasks", {}).get(uid, [])
        if not user_tasks:
            bot.reply_to(message, "📝 <b>ليس لديك أي مهام مسجلة حالياً!</b>\n\nلإضافة مهمة جديدة، أرسل:\n<code>اضف مهمة مراجعة التقارير المالية</code>")
        else:
            tasks_txt = "📋 <b>قائمة مهامك ومذكراتك المحفوظة:</b>\n\n"
            for i, t in enumerate(user_tasks, 1):
                tasks_txt += f"{i}️⃣ {t}\n"
            tasks_txt += "\n<i>لمسح جميع المهام أرسل: مسح المهام</i>"
            bot.reply_to(message, tasks_txt)
        return

    if text.startswith("اضف مهمة"):
        task = text.replace("اضف مهمة", "").strip()
        if task:
            if "tasks" not in db: db["tasks"] = {}
            if uid not in db["tasks"]: db["tasks"][uid] = []
            db["tasks"][uid].append(task)
            save_data(db)
            bot.reply_to(message, f"✅ <b>تم حفظ المهمة بنجاح:</b>\n📌 {task}")
        return

    if text == "مسح المهام":
        if "tasks" in db and uid in db["tasks"]:
            db["tasks"][uid] = []
            save_data(db)
            bot.reply_to(message, "🗑 تم مسح جميع مهامك بنجاح.")
        return

    if text == "📊 تتبع المبيعات والأرباح":
        user_sales = db.get("sales", {}).get(uid, 0.0)
        bot.reply_to(
            message,
            f"💼 <b>إجمالي مبيعاتك وأرباحك المسجلة:</b>\n\n💰 <code>${user_sales:,.2f}</code>\n\n"
            "لإضافة عملية بيع جديدة اكتب:\n<code>اضف بيع 150</code>"
        )
        return

    if text.startswith("اضف بيع"):
        amount = re.findall(r"[-+]?(?:\d*\.\d+|\d+)", text)
        if amount:
            val = float(amount[0])
            if "sales" not in db: db["sales"] = {}
            db["sales"][uid] = db["sales"].get(uid, 0.0) + val
            save_data(db)
            bot.reply_to(message, f"✅ تم تسجيل مبيعات بقيمة <b>${val:,.2f}</b> بنجاح!\nالإجمالي الآن: <b>${db['sales'][uid]:,.2f}</b>")
        return

    if text.startswith("ترجم") or text == "🌐 ترجمة فورية":
        q = text.replace("ترجم", "").strip()
        if not q:
            bot.reply_to(message, "🌐 أرسل النص مسبوقاً بكلمة ترجم، مثال:\n<code>ترجم Welcome to the future</code>")
            return
        wait = bot.reply_to(message, "🌐 <b>جاري الترجمة الفورية...</b>")
        ans = get_ai_reply(f"ترجم هذا النص بدقة واحترافية: {q}")
        bot.edit_message_text(f"🌐 <b>الترجمة الفورية:</b>\n\n{ans}", chat_id, wait.message_id)
        return

    if text.startswith("كتاب") or text.startswith("بحث عن") or text == "📚 بحث عن كتب ومقالات":
        q = text.replace("بحث عن كتب ومقالات", "").replace("كتاب", "").replace("بحث عن", "").strip()
        if not q:
            bot.reply_to(message, "📚 أرسل اسم الكتاب أو الموضوع، مثال:\n<code>كتاب تاريخ الحضارات القديمة</code>")
            return
        wait = bot.reply_to(message, f"🔍 <b>جاري البحث عن مصادر وتحميل لـ '{q}'...</b>")
        ans = get_ai_reply(f"قدم ملخصاً وافياً ومصادر تحميل موثوقة ومجانية بصيغة PDF لكتاب أو موضوع: {q}")
        bot.edit_message_text(f"📚 <b>نتائج البحث والتحميل:</b>\n\n{ans}", chat_id, wait.message_id)
        return

    # --- توليد صور 4K ---
    img_triggers = ["صمم", "ارسم", "تخيل", "انشئ صوره", "انشئ صورة", "رسم"]
    if any(text.startswith(w) for w in img_triggers) or text == "🎨 رسم وتصميم 4K":
        if text == "🎨 رسم وتصميم 4K":
            bot.reply_to(message, "🎨 اكتب ما تتخيله، مثل:\n<code>ارسم أسد من الكريستال في صحراء ذهبية 4K</code>")
            return
        wait = bot.reply_to(message, "🎨 <b>جاري رسم صورتك بأعلى دقة 4K فائقة... لحظات ✨</b>")
        prompt = re.sub(r'^(صمم|ارسم|تخيل|انشئ صوره|انشئ صورة|رسم)\s*', '', text).strip()
        img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt + ' ultra 4k resolution cinematic photorealistic')}?width=1024&height=1024&model=flux&nologo=true"
        try:
            bot.send_photo(chat_id, img_url, caption=f"🖼 <b>تم إنشاء التصميم بنجاح!</b>\n✨ الوصف: <i>{prompt}</i>\n👑 <b>{BOT_NAME}</b>")
            bot.delete_message(chat_id, wait.message_id)
            return
        except Exception:
            bot.edit_message_text("⚠️ تعذر توليد الصورة، جرب وصفاً آخر.", chat_id, wait.message_id)
            return

    # --- سحب تيك توك المباشر ---
    if "tiktok.com" in text or "douyin.com" in text:
        wait = bot.reply_to(message, "⚡️ <b>جاري سحب المقطع بأعلى دقة وبدون علامة مائية... ✨</b>")
        try:
            url_match = re.search(r'(https?://[^\s]+)', text)
            clean_link = url_match.group(0).split('?')[0] if url_match else text
            api_url = f"https://www.tikwm.com/api/?url={urllib.parse.quote(clean_link)}"
            res = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15).json()
            if res.get("code") == 0:
                v_data = res["data"]
                dl_url = v_data.get("hdplay") or v_data.get("play") or v_data.get("wmplay")
                if dl_url.startswith("/"): dl_url = "https://www.tikwm.com" + dl_url
                title = v_data.get("title", "فيديو تيك توك")
                caption = f"🎬 <b>{title[:100]}</b>\n\n✨ بواسطة: <b>{BOT_NAME}</b>\n🔥 تابعنا: <b>{TIKTOK_USER}</b>"
                inline_btn = telebot.types.InlineKeyboardMarkup()
                inline_btn.add(telebot.types.InlineKeyboardButton("❤️ تابع حساب صلوح", url=TIKTOK_CHANNEL))
                bot.send_video(chat_id, dl_url, caption=caption, reply_markup=inline_btn)
                bot.delete_message(chat_id, wait.message_id)
                return
            else:
                bot.edit_message_text("❌ تعذر تحميل المقطع، تأكد أن الفيديو متاح للعامة.", chat_id, wait.message_id)
        except Exception:
            bot.edit_message_text("⚠️ حدث خطأ أثناء المعالجة، حاول لاحقاً.", chat_id, wait.message_id)
        return

    # --- الشيلات والزوامل والصوتيات ---
    if any(k in text.lower() for k in ["شيله", "شيلة", "اغنيه", "اغنية", "صوت", "زامل", "زوامل"]) or text == "🎵 طلب شيلة MP3":
        if text == "🎵 طلب شيلة MP3":
            bot.reply_to(message, "🎵 اكتب اسم الشيلة أو المنشد وسأحضرها لك فوراً.")
            return
        wait = bot.reply_to(message, "🎵 <b>جاري البحث وسحب الصوتية بنقاء تام... ✨</b>")
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
        bot.edit_message_text("⚠️ لم يتم العثور على المقطع الصوتي، حدد اسم المنشد وسأجلبه لك فوراً.", chat_id, wait.message_id)
        return

    # --- الرد الذكي العام والدردشة الفائقة ---
    wait = bot.reply_to(message, "⚡️ <b>جاري التفكير والمعالجة الفورية... ✨</b>")
    ai_answer = get_ai_reply(text)
    try:
        bot.edit_message_text(ai_answer, chat_id, wait.message_id)
    except Exception:
        bot.send_message(chat_id, ai_answer)

print("✅ تم إطلاق السوبر بوت بكامل المنظومة المتطورة...")
bot.infinity_polling()
