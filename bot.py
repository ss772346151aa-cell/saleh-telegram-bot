import os
import telebot
import requests

# قراءة التوكن بأمان من متغيرات البيئة في السيرفر
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 7206214234
BOT_NAME = "بوت صلوح المانعي الذكي ⚡️👑"
TIKTOK_CHANNEL = "https://www.tiktok.com/@almanay22"
TIKTOK_USER = "@almanay22"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    name = message.from_user.first_name
    text = (
        f"👑 <b>أهلاً وسهلاً بك يا {name} في {BOT_NAME}!</b>\n\n"
        "⚡️ البوت جاهز لخدمتك على مدار الساعة:\n"
        "• 📥 <b>سحب تيك توك:</b> أرسل رابط الفيديو مباشرة.\n"
        "• 🎵 <b>شيلات وأغاني MP3:</b> اكتب اسم الشيلة وسأبحث عنها.\n"
        "• 🧠 <b>ذكاء اصطناعي:</b> اسأل أي سؤال وسأجيبك فوراً.\n\n"
        f"🌟 <b>حساب تيك توك الرسمي:</b> <code>{TIKTOK_CHANNEL}</code>"
    )
    markup = telebot.types.InlineKeyboardMarkup()
    btn = telebot.types.InlineKeyboardButton("🔥 حساب صلوح على تيك توك", url=TIKTOK_CHANNEL)
    markup.add(btn)
    bot.reply_to(message, text, reply_markup=markup)

@bot.message_handler(commands=['stats'])
def show_stats(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.reply_to(message, f"📊 <b>لوحة التحكم:</b>\n\nالسيرفر نشط ومتصل 24/7 ⚡️\nالمطور: <b>{message.from_user.first_name}</b>")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    text = message.text.strip()
    
    # 1. روابط تيك توك
    if "tiktok.com" in text or "douyin.com" in text:
        wait = bot.reply_to(message, "⚡️ <b>جاري سحب المقطع بأعلى دقة وبدون علامة مائية...</b>")
        try:
            api_url = f"https://www.tikwm.com/api/?url={text}"
            res = requests.get(api_url, timeout=15).json()
            if res.get("code") == 0:
                video_url = res["data"].get("play") or res["data"].get("wmplay")
                title = res["data"].get("title", "مقطع تيك توك")
                if video_url.startswith("/"):
                    video_url = "https://www.tikwm.com" + video_url
                
                caption = f"🎬 <b>{title[:100]}</b>\n\n✨ بواسطة: <b>{BOT_NAME}</b>\n🔥 تابعنا: <b>{TIKTOK_USER}</b>"
                bot.send_video(message.chat.id, video_url, caption=caption)
                bot.delete_message(message.chat.id, wait.message_id)
                return
            else:
                bot.edit_message_text("❌ تعذر تحميل المقطع، تأكد أن الفيديو عام.", message.chat.id, wait.message_id)
        except Exception:
            bot.edit_message_text("⚠️ حدث خطأ أثناء المعالجة، حاول لاحقاً.", message.chat.id, wait.message_id)
        return

    # 2. الشيلات والأغاني
    if any(k in text.lower() for k in ["شيله", "شيلة", "اغنيه", "اغنية", "صوت"]):
        bot.reply_to(message, f"🎵 تم استلام طلبك لـ <b>{text}</b>، جاري تجهيز المحتوى...")
        return

    # 3. الذكاء الاصطناعي
    wait = bot.reply_to(message, "⚡️ <b>لحظات أجهز لك الرد...</b>")
    try:
        url = "https://text.pollinations.ai/" + text
        res = requests.get(url, timeout=8)
        if res.status_code == 200 and len(res.text.strip()) > 0:
            bot.edit_message_text(res.text.strip(), message.chat.id, wait.message_id)
            return
    except Exception:
        pass
    bot.edit_message_text("أهلاً بك يا غالي! أرسل رابط تيك توك لتنزيله أو اكتب استفسارك وسأساعدك فوراً 🌹", message.chat.id, wait.message_id)

print("✅ تم تشغيل البوت على السيرفر بنجاح...")
bot.infinity_polling()
