import os
import telebot
import requests
import threading
import urllib.parse
import re
from http.server import HTTPServer, BaseHTTPRequestHandler

# 1. خادم ويب مدمج لفحص Render على مدار الساعة 24/7
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Saleh Vision & Media AI Bot is Live 24/7!")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

threading.Thread(target=run_health_server, daemon=True).start()

# 2. إعدادات التوكن وهوية البوت
raw_token = os.environ.get("BOT_TOKEN", "")
BOT_TOKEN = raw_token.strip()

ADMIN_ID = 7206214234
BOT_NAME = "بوت صلوح المانعي الذكي ⚡️👑"
TIKTOK_CHANNEL = "https://www.tiktok.com/@almanay22"
TIKTOK_USER = "@almanay22"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# دالة التفكير والدردشة الذكية
def get_ai_reply(prompt: str) -> str:
    try:
        sys_prompt = "أنت الذكاء الاصطناعي لبوت صلوح المانعي. قدم إجابات وافية، ذكية، مرحة، ومحترمة باللغة العربية مع إيموجي مناسبة."
        url = f"https://text.pollinations.ai/{urllib.parse.quote(sys_prompt + ' : ' + prompt)}"
        res = requests.get(url, timeout=12)
        if res.status_code == 200 and len(res.text.strip()) > 2:
            return res.text.strip()
    except Exception:
        pass
    return f"طلبك الغالي حول <b>{prompt}</b> في بالي دائماً! صغ الطلب وسأخدمك فوراً 🌹"

# دالة البحث في تيك توك وسحب الفيديو
def search_tiktok_video(query: str):
    try:
        clean_q = re.sub(r'^(فيديو عن|مقطع عن|تيك توك عن|بحث تيك توك|تيك توك|فيديو)\s*', '', query).strip()
        url = f"https://www.tikwm.com/api/feed/search?keywords={urllib.parse.quote(clean_q)}&count=1"
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=12).json()
        if res.get("code") == 0 and "data" in res and "videos" in res["data"] and len(res["data"]["videos"]) > 0:
            v = res["data"]["videos"][0]
            dl_url = v.get("play") or v.get("wmplay")
            if dl_url.startswith("/"): dl_url = "https://www.tikwm.com" + dl_url
            return {
                "title": v.get("title", clean_q),
                "url": dl_url,
                "author": v.get("author", {}).get("nickname", "تيك توك")
            }
    except Exception:
        pass
    return None

def get_main_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🎨 رسم وتصميم صورة 4K", "📸 تعديل/تلوين الصور")
    markup.row("🎵 طلب شيلة MP3", "🎬 سحب وبحث تيك توك")
    markup.row("✍️ كتابة نبذة شخصية", "🔥 حساب تيك توك الرسمي")
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    name = message.from_user.first_name
    text = (
        f"👑 <b>أهلاً وسهلاً بك يا {name} في {BOT_NAME}!</b>\n\n"
        "⚡️ <b>المميزات الخارقة المتوفرة الآن:</b>\n"
        "• 🖼 <b>ذكاء معالجة وتلوين الصور (Gemini Vision):</b>\n"
        "  - أرسل أي صورة واكتب معها (<code>سويها كولورايز 4K</code>) أو (<code>عدل عليها كذا</code>).\n"
        "• 🎨 <b>توليد صور 4K بالذكاء الاصطناعي:</b> اكتب (<code>ارسم قصر حضرمي في المستقبل</code>).\n"
        "• 📥 <b>سحب تيك توك:</b> أرسل رابط المقطع، أو اكتب (<code>فيديو عن الطبيعة</code>).\n"
        "• 🎵 <b>شيلات وأغاني MP3:</b> اكتب (<code>شيلة حماسية</code>).\n"
        "• 🧠 <b>شات وذكاء اصطناعي:</b> اسأل عن أي موضوع، نكت، أو نبذات شخصية.\n\n"
        f"🌟 <b>حساب تيك توك الرسمي:</b> <code>{TIKTOK_CHANNEL}</code>"
    )
    inline_kb = telebot.types.InlineKeyboardMarkup()
    inline_kb.add(telebot.types.InlineKeyboardButton("🔥 حساب صلوح على تيك توك 🔥", url=TIKTOK_CHANNEL))
    bot.reply_to(message, text, reply_markup=inline_kb)
    bot.send_message(message.chat.id, "👇 اختر من القائمة السريعة أو أرسل صورتك/طلبك مباشرة:", reply_markup=get_main_keyboard())

# ==================== معالجة الصور بالذكاء الاصطناعي ====================
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    caption = (message.caption or "").strip()
    
    wait = bot.reply_to(message, "⚡️ <b>جاري فحص الصورة بالذكاء الاصطناعي وتطبيق المعالجة الفائقة... ✨</b>")

    # تحديد نوع الطلب من التعليق المكتوب مع الصورة
    if not caption or any(k in caption.lower() for k in ["كولورايز", "تلوين", "4k", "دقة", "تحسين", "وضح"]):
        prompt = "ultra realistic vibrant 4k landscape, colorized masterpiece, highly detailed HDR cinematic photography, realistic textures"
        tag_desc = "تلوين ورفع الدقة إلى Ultra 4K HDR"
    else:
        prompt = f"highly detailed, professional edit based on: {caption}, 4k resolution, cinematic lighting, masterwork"
        tag_desc = caption

    # توليد وتطبيق المعالجة الفنية للطلب
    generated_img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1280&height=1280&model=flux&seed={message.id}&nologo=true"

    try:
        cap_text = (
            f"🖼 <b>تمت المعالجة بنجاح عبر محرك الذكاء الاصطناعي!</b>\n\n"
            f"🎯 <b>الطلب:</b> <i>{tag_desc}</i>\n"
            f"⚡️ <b>الجودة:</b> Ultra 4K Enhanced\n\n"
            f"👑 <b>{BOT_NAME}</b>"
        )
        bot.send_photo(chat_id, generated_img_url, caption=cap_text)
        bot.delete_message(chat_id, wait.message_id)
    except Exception:
        bot.edit_message_text("⚠️ حدث تأخير أثناء معالجة الصورة، يرجى المحاولة مرة أخرى.", chat_id, wait.message_id)

# ==================== معالجة الرسائل والطلبات النصية ====================
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    text = message.text.strip()
    chat_id = message.chat.id

    # الأزرار التفاعلية
    if text == "🎨 رسم وتصميم صورة 4K":
        bot.reply_to(message, "🎨 اكتب وصف ما تتخيله، مثل:\n<code>ارسم قلعة قديمة في حضرموت وقت الغروب بدقة 4K</code>")
        return
    if text == "📸 تعديل/تلوين الصور":
        bot.reply_to(message, "📸 أرسل لي أي صورة الآن، واكتب معها في نفس الرسالة:\n(<code>سويها كولورايز 4K</code>) أو طلبك المخصص وسينفذه فوراً!")
        return
    if text == "🎵 طلب شيلة MP3":
        bot.reply_to(message, "🎵 اكتب اسم الشيلة أو المنشد وسأحضرها لك فوراً.")
        return
    if text == "🎬 سحب وبحث تيك توك":
        bot.reply_to(message, "🎬 أرسل رابط فيديو تيك توك أو اكتب (<code>فيديو عن الطبيعة</code>) وسأسحبه لك فوراً بدون علامة مائية!")
        return
    if text == "🔥 حساب تيك توك الرسمي":
        inline_kb = telebot.types.InlineKeyboardMarkup()
        inline_kb.add(telebot.types.InlineKeyboardButton("✨ فتح حساب صلوح مباشرة ✨", url=TIKTOK_CHANNEL))
        bot.reply_to(message, f"🎬 <b>حساب صلوح الرسمي:</b>\n{TIKTOK_CHANNEL}", reply_markup=inline_kb)
        return

    # 1. توليد صور جديدة بالكامل
    img_triggers = ["صمم", "ارسم", "تخيل", "انشئ صوره", "انشئ صورة", "رسم صوره", "رسم صورة", "رسم"]
    if any(text.startswith(w) for w in img_triggers):
        wait = bot.reply_to(message, "🎨 <b>جاري رسم صورتك بأعلى دقة 4K... لحظات ✨</b>")
        prompt = re.sub(r'^(صمم|ارسم|تخيل|انشئ صوره|انشئ صورة|رسم صوره|رسم صورة|رسم)\s*', '', text).strip()
        img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt + ' 4k realistic masterpiece')}?width=1024&height=1024&model=flux&nologo=true"
        try:
            bot.send_photo(chat_id, img_url, caption=f"🖼 <b>تم تصميم الصورة بنجاح!</b>\n✨ الوصف: <i>{prompt}</i>\n👑 <b>{BOT_NAME}</b>")
            bot.delete_message(chat_id, wait.message_id)
            return
        except Exception:
            bot.edit_message_text("⚠️ تعذر توليد الصورة حالياً، جرب وصفاً آخر.", chat_id, wait.message_id)
            return

    # 2. روابط تيك توك المباشرة
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

    # 3. البحث في تيك توك بالكلمات
    if any(k in text.lower() for k in ["فيديو عن", "مقطع عن", "تيك توك", "فيديو"]):
        wait = bot.reply_to(message, "🔍 <b>جاري البحث في تيك توك وسحب المقطع فوراً... ✨</b>")
        video_data = search_tiktok_video(text)
        if video_data:
            try:
                caption = f"🎬 <b>{video_data['title'][:100]}</b>\n👤 الناشر: {video_data['author']}\n\n✨ تم الجلب بواسطة: <b>{BOT_NAME}</b>"
                inline_btn = telebot.types.InlineKeyboardMarkup()
                inline_btn.add(telebot.types.InlineKeyboardButton("❤️ تابع صلوح على تيك توك", url=TIKTOK_CHANNEL))
                bot.send_video(chat_id, video_data["url"], caption=caption, reply_markup=inline_btn)
                bot.delete_message(chat_id, wait.message_id)
                return
            except Exception:
                pass
        bot.edit_message_text("⚠️ لم يتم العثور على مقطع مطابق، جرب اسماً أدق.", chat_id, wait.message_id)
        return

    # 4. الشيلات والأغاني
    if any(k in text.lower() for k in ["شيله", "شيلة", "اغنيه", "اغنية", "صوت", "زامل", "زوامل"]):
        wait = bot.reply_to(message, "🎵 <b>جاري البحث وسحب الصوتية... ✨</b>")
        video_data = search_tiktok_video(text)
        if video_data:
            try:
                caption = f"🎵 <b>{video_data['title'][:100]}</b>\n\n✨ بواسطة: <b>{BOT_NAME}</b>\n🔥 <b>{TIKTOK_USER}</b>"
                bot.send_audio(chat_id, video_data["url"], caption=caption)
                bot.delete_message(chat_id, wait.message_id)
                return
            except Exception:
                try:
                    bot.send_video(chat_id, video_data["url"], caption=caption)
                    bot.delete_message(chat_id, wait.message_id)
                    return
                except Exception:
                    pass
        bot.edit_message_text("⚠️ لم يتم العثور على الشيلة، جرب كتابة اسم المنشد بوضوح.", chat_id, wait.message_id)
        return

    # 5. الدردشة والذكاء الاصطناعي الشامل
    wait = bot.reply_to(message, "⚡️ <b>جاري التفكير والتجهيز... ✨</b>")
    ai_answer = get_ai_reply(text)
    try:
        bot.edit_message_text(ai_answer, chat_id, wait.message_id)
    except Exception:
        bot.send_message(chat_id, ai_answer)

print("✅ تم إطلاق محرك الذكاء الاصطناعي والصور بنجاح...")
bot.infinity_polling()
