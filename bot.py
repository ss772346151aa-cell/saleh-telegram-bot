import os
import glob
import logging
import random
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import yt_dlp

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)

# ==================== الإعدادات الأساسية ====================
BOT_TOKEN = "9157081412:AAF-LegdEK1zKi_ZUCPOarhFXwphmPpqFUE"
BOT_NAME = "بوت صالح عبد المانع الشامل"
BOT_USERNAME = "saleh_down_bot"
CHANNEL_URL = "https://t.me/saleh_down_bot"
WHATSAPP_NUMBER = "967782953692"
WHATSAPP_URL = f"https://wa.me/{WHATSAPP_NUMBER}"
MAX_FILE_SIZE = 50 * 1024 * 1024
# ============================================================

# قاعدة بيانات مصغرة للأفلام والمسلسلات الرائجة
TRENDING_MOVIES = [
    {"title": "Oppenheimer", "type": "فيلم", "genre": "تاريخ / دراما", "rate": "8.9/10", "desc": "قصة صناعة القنبلة الذرية والعالم روبرت أوبنهايمر."},
    {"title": "Dune: Part Two", "type": "فيلم", "genre": "خيال علمي / مغامرة", "rate": "8.6/10", "desc": "رحلة بول أتريدس الأسطورية في كوكب أراكيس."},
    {"title": "Breaking Bad", "type": "مسلسل", "genre": "جريمة / إثارة", "rate": "9.5/10", "desc": "تحول معلم كيمياء إلى إمبراطور لتجارة الممنوعات."},
    {"title": "قيامة عثمان (Kuruluş Osman)", "type": "مسلسل", "genre": "تاريخي / أكشن", "rate": "8.2/10", "desc": "تأسيس الدولة العثمانية والصراعات التاريخية."},
    {"title": "Game of Thrones", "type": "مسلسل", "genre": "فانتازيا / ملحمي", "rate": "9.2/10", "desc": "صراع العائلات النبيلة على العرش الحديدي."}
]

ATHKAR = [
    "سُبْحَانَ اللَّهِ وَبِحَمْدِهِ، سُبْحَانَ اللَّهِ الْعَظِيمِ 🌸",
    "لا حَوْلَ وَلا قُوَّةَ إِلا بِاللَّهِ الْعَلِيِّ الْعَظِيمِ ✨",
    "اللَّهُمَّ صَلِّ وَسَلِّمْ عَلَى نَبِيِّنَا مُحَمَّدٍ وَعَلَى آلِهِ وَصَحْبِهِ أَجْمَعِينَ 🌿",
    "أَسْتَغْفِرُ اللَّهَ الْعَظِيمَ وَأَتُوبُ إِلَيْهِ 💫",
    "لا إِلَهَ إِلا أَنْتَ سُبْحَانَكَ إِنِّي كُنْتُ مِنَ الظَّالِمِينَ 🤲"
]


def get_main_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("📥 تنزيل الوسائط", callback_data="download_guide"),
            InlineKeyboardButton("🎬 أفلام ومسلسلات", callback_data="movies_section"),
        ],
        [
            InlineKeyboardButton("📿 ذكر اليوم", callback_data="daily_zekr"),
            InlineKeyboardButton("🤖 أفكار ومحتوى AI", callback_data="ai_tools"),
        ],
        [
            InlineKeyboardButton("📢 قناة التحديثات", url=CHANNEL_URL),
            InlineKeyboardButton("💬 واتساب الدعم", url=WHATSAPP_URL),
        ],
        [
            InlineKeyboardButton("ℹ️ حول البوت والمطور", callback_data="about_dev"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    welcome_text = (
        f"👑 <b>أهلاً بك يا {user_name} في {BOT_NAME}!</b>\n\n"
        "منصتك المتكاملة على تيليجرام لجميع الخدمات والاهتمامات اليومية:\n"
        "⚡️ <b>تحميل فوري</b> من تيك توك، يوتيوب، إنستغرام، وفيسبوك.\n"
        "🎬 <b>دليل وتوصيات</b> لأقوى الأفلام والمسلسلات العالمية والعربية.\n"
        "📿 <b>أدعية وأذكار</b> وتنبيهات يومية.\n"
        "🤖 <b>أدوات ذكية</b> لصناع المحتوى والشباب.\n\n"
        "👇 اختر ما تبحث عنه من القائمة أدناه أو <b>أرسل أي رابط فيديو للتحميل فوراً:</b>"
    )
    await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard(), parse_mode="HTML")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "download_guide":
        text = (
            "📥 <b>طريقة تحميل أي مقطع فيديو أو صوت:</b>\n\n"
            "1. افتح تطبيقك المفضل (تيك توك، يوتيوب، إنستغرام، فيسبوك، X).\n"
            "2. انسخ رابط المنشور أو المقطع.\n"
            "3. الصقه هنا في الشات مباشرة.\n"
            "⚡️ سيتم فحص الرابط وإرسال الفيديو إليك بدون علامة مائية وبأعلى جودة!"
        )
        await query.message.reply_text(text, parse_mode="HTML")

    elif query.data == "movies_section":
        item = random.choice(TRENDING_MOVIES)
        text = (
            f"🎬 <b>ترشيح اليوم للشباب:</b>\n\n"
            f"📌 <b>الاسم:</b> {item['title']}\n"
            f"🏷 <b>النوع:</b> {item['type']} ({item['genre']})\n"
            f"⭐ <b>التقييم العالمي:</b> {item['rate']}\n"
            f"📖 <b>نبذة:</b> {item['desc']}\n\n"
            "🍿 <i>مشاهدة ممتعة! اضغط الزر مرة أخرى للحصول على ترشيح جديد.</i>"
        )
        keyboard = [[InlineKeyboardButton("🔄 ترشيح فيلم / مسلسل آخر", callback_data="movies_section")]]
        await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif query.data == "daily_zekr":
        zekr = random.choice(ATHKAR)
        text = f"✨ <b>غذاء الروح:</b>\n\n<blockquote>{zekr}</blockquote>\n\nاجعل لسانك رطباً بذكر الله."
        keyboard = [[InlineKeyboardButton("📿 ذكر آخر", callback_data="daily_zekr")]]
        await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif query.data == "ai_tools":
        text = (
            "🤖 <b>أدوات وأفكار صناعة المحتوى:</b>\n\n"
            "• <b>هاشتاقات تيك توك النشطة:</b>\n"
            "<code>#fyp #viral #explore #foryou #ترند #اكسبلور</code>\n\n"
            "• <b>أفضل أوقات النشر المقترحة:</b>\n"
            "من 1:00 ظهراً إلى 3:00 عصراً ومن 8:00 مساءً إلى 11:00 ليلاً.\n\n"
            "💡 <i>نصيحة: المقاطع التي تقل عن 30 ثانية وتحتوي على حركة سريعة تحقق أعلى نسبة وصول!</i>"
        )
        await query.message.reply_text(text, parse_mode="HTML")

    elif query.data == "about_dev":
        text = (
            f"👑 <b>{BOT_NAME}</b>\n\n"
            f"• المعرف: @{BOT_USERNAME}\n"
            f"• المطور والدعم الفني: <b>صالح عبد المانع</b>\n"
            f"• واتساب: <code>+{WHATSAPP_NUMBER}</code>\n\n"
            "نسعى دائماً لتقديم أفضل الخدمات التقنية المجانية لخدمة الجميع 🤝"
        )
        await query.message.reply_text(text, parse_mode="HTML")


def resolve_redirect(url: str) -> str:
    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        resp = session.get(url, allow_redirects=True, timeout=10)
        return resp.url
    except Exception:
        return url


def download_tiktok_direct(url: str, output_path: str):
    full_url = resolve_redirect(url)
    api_url = f"https://www.tikwm.com/api/?url={full_url}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    resp = requests.get(api_url, headers=headers, timeout=20)
    data = resp.json()
    if data.get("code") == 0 and "data" in data:
        download_url = data["data"].get("play") or data["data"].get("wmplay")
        title = data["data"].get("title", "فيديو تيك توك")
        video_bytes = requests.get(download_url, headers=headers, timeout=40).content
        with open(output_path, "wb") as f:
            f.write(video_bytes)
        return {"title": title, "path": output_path, "platform": "تيك توك بدون علامة مائية"}
    else:
        raise Exception("فشل تنزيل تيك توك")


def download_general(url: str, output_template: str):
    ydl_opts = {
        "outtmpl": output_template,
        "format": "best[ext=mp4]/best",
        "quiet": True,
        "no_warnings": True,
        "max_filesize": MAX_FILE_SIZE,
        "nocheckcertificate": True,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=True)


async def handle_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        await update.message.reply_text("❌ يرجى إرسال رابط صحيح، أو اختيار إحدى الخدمات من القائمة عبر إرسال /start.")
        return

    status_msg = await update.message.reply_text(
        "⚡️ <b>جاري سحب المقطع والمعالجة بأعلى جودة...</b>",
        parse_mode="HTML"
    )
    chat_id = update.effective_chat.id
    output_base = f"downloads/{chat_id}_{update.message.message_id}"
    os.makedirs("downloads", exist_ok=True)

    file_path = None
    title = "فيديو"
    platform_name = "مواقع التواصل"

    try:
        if "tiktok.com" in url:
            output_file = f"{output_base}.mp4"
            info = download_tiktok_direct(url, output_file)
            file_path = info["path"]
            title = info["title"]
            platform_name = info["platform"]
        else:
            output_template = f"{output_base}.%(ext)s"
            info = download_general(url, output_template)
            files = glob.glob(f"{output_base}.*")
            if files:
                file_path = files[0]
                title = info.get("title", "فيديو بدون عنوان")
                extractor = info.get("extractor", "").lower()
                if "youtube" in extractor:
                    platform_name = "يوتيوب"
                elif "instagram" in extractor:
                    platform_name = "إنستغرام"
                elif "facebook" in extractor:
                    platform_name = "فيسبوك"
                elif "twitter" in extractor:
                    platform_name = "منصة X"

        if not file_path or not os.path.exists(file_path):
            await status_msg.edit_text("❌ تعذر تنزيل الملف، تأكد من صحة الرابط وأن الحساب عام.")
            return

        if os.path.getsize(file_path) > MAX_FILE_SIZE:
            await status_msg.edit_text(
                "⚠️ حجم الفيديو يتعدى 50 ميغابايت (الحد الأقصى المسموح للبوت)."
            )
            os.remove(file_path)
            return

        await status_msg.edit_text(
            "📤 <b>جاري الرفع والإرسال إليك الآن...</b>", 
            parse_mode="HTML"
        )
        caption_text = (
            f"🎬 <b>{title[:120]}</b>\n\n"
            f"📌 المصدر: <b>{platform_name}</b>\n"
            f"⚡️ تم التحميل بواسطة: <b>{BOT_NAME}</b>\n"
            f"💬 للتواصل وخدمات الدعم: <code>+{WHATSAPP_NUMBER}</code>"
        )

        dl_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 واتساب المطور", url=WHATSAPP_URL),
             InlineKeyboardButton("📢 قناة التحديثات", url=CHANNEL_URL)]
        ])

        with open(file_path, "rb") as video:
            await update.message.reply_video(
                video=video,
                caption=caption_text,
                reply_markup=dl_buttons,
                parse_mode="HTML",
                supports_streaming=True,
            )

        await status_msg.delete()

    except Exception:
        await status_msg.edit_text(
            "❌ تعذر التنزيل: تأكد من أن الرابط مباشر وأن المحتوى عام وليس مقيداً."
        )
    finally:
        for f in glob.glob(f"{output_base}*"):
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception:
                pass


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_download))

    print(f"✅ {BOT_NAME} يعمل الآن بكامل مميزاته...")
    app.run_polling()


if __name__ == "__main__":
    main()