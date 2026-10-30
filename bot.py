import os
import glob
import logging
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
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
BOT_NAME = "بوت صالح عبد المانع الشامل الذكي"
BOT_USERNAME = "saleh_down_bot"
CHANNEL_URL = "https://t.me/saleh_down_bot"
WHATSAPP_NUMBER = "967782953692"
WHATSAPP_URL = f"https://wa.me/{WHATSAPP_NUMBER}"
MAX_FILE_SIZE = 50 * 1024 * 1024
# ============================================================

# خادم ويب صغير لتخطي فحص الصحة على المنصات السحابية وضمان عمل البوت 24/7
class SimpleHealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Saleh AI Bot is fully operational 24/7!")

def start_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHealthServer)
    logging.info(f"Health server running on port {port}")
    server.serve_forever()

def ask_ai(prompt: str) -> str:
    """محرك الذكاء الاصطناعي الشامل للإجابة عن الأفلام، المباريات، الألعاب، والبرامج"""
    system_instruction = (
        "أنت المساعد الذكي الخارق لبوت صالح عبد المانع في تيليجرام. "
        "أسلوبك ودود، لبق، وسريع الإجابة باللغة العربية. "
        "مهامك الأساسية: "
        "1. إذا سألك المستخدم عن فيلم أو مسلسل: اعطه الاسم، النوع، سنة الإنتاج، التقييم، ملخص القصة باختصار، وروابط وأماكن المشاهدة الرسمية. "
        "2. إذا سألك عن مباريات أو كرة قدم: اعطه تحليلاً رياضياً أو معلومات عن البطولات والفرق والنجوم. "
        "3. إذا سألك عن ألعاب أو برامج: اقترح له أفضل التطبيقات والألعاب مع شرح مميزاتها وروابط الحصول عليها إن أمكن. "
        "4. أجب دائماً بتنسيق جميل ومرتب مستخدماً الرموز التعبيرية المناسبة."
    )
    url = f"https://text.pollinations.ai/{requests.utils.quote(system_instruction + ' | طلب المستخدم: ' + prompt)}"
    try:
        response = requests.get(url, timeout=25)
        if response.status_code == 200 and response.text:
            return response.text.strip()
    except Exception as e:
        logging.error(f"AI response error: {e}")
    return "أهلاً بك! أنا رفيقك الذكي. يمكنك سؤالي عن أي فيلم، مسلسل، جدول مباريات، لعبة أو برنامج، أو إرسال أي رابط فيديو لتحميله فوراً!"

def resolve_redirect(url: str) -> str:
    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        resp = session.get(url, allow_redirects=True, timeout=10)
        return resp.url
    except Exception:
        return url

def download_tiktok_direct(url: str, output_path: str):
    full_url = resolve_redirect(url)
    api_url = f"https://www.tikwm.com/api/?url={full_url}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    resp = requests.get(api_url, headers=headers, timeout=20)
    data = resp.json()
    if data.get("code") == 0 and "data" in data:
        download_url = data["data"].get("play") or data["data"].get("wmplay")
        title = data["data"].get("title", "فيديو تيك توك")
        video_bytes = requests.get(download_url, headers=headers, timeout=45).content
        with open(output_path, "wb") as f:
            f.write(video_bytes)
        return {"title": title, "path": output_path, "platform": "تيك توك بدون علامة مائية"}
    raise Exception("فشل تنزيل تيك توك")

def download_general(url: str, output_template: str):
    ydl_opts = {
        "outtmpl": output_template,
        "format": "best[ext=mp4]/best",
        "quiet": True,
        "no_warnings": True,
        "max_filesize": MAX_FILE_SIZE,
        "nocheckcertificate": True,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=True)

def get_main_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🎬 ترشيحات أفلام ومسلسلات", callback_data="movies_hint"),
            InlineKeyboardButton("⚽ قسم الرياضة والمباريات", callback_data="sports_hint"),
        ],
        [
            InlineKeyboardButton("🎮 ألعاب وتطبيقات مميزة", callback_data="games_hint"),
            InlineKeyboardButton("📿 ذكر ودعاء اليوم", callback_data="daily_zekr"),
        ],
        [
            InlineKeyboardButton("💬 واتساب المطور والدعم", url=WHATSAPP_URL),
            InlineKeyboardButton("📢 قناة التحديثات", url=CHANNEL_URL),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    welcome_text = (
        f"👑 <b>أهلاً وسهلاً بك يا {user_name} في {BOT_NAME}!</b>\n\n"
        "منصتك الذكية والشاملة على مدار الساعة:\n"
        "🤖 <b>تحدث معي واسألني عن أي شيء:</b>\n"
        "• أفلام ومسلسلات (قصص، تقييمات، ترشيحات، وروابط مشاهدة).\n"
        "• مباريات كرة القدم والرياضة وتحليلات البطولات.\n"
        "• أفضل ألعاب الهواتف والكمبيوتر والبرامج الخدمية.\n\n"
        "📥 <b>التنزيل الفوري للوسائط:</b>\n"
        "أرسل رابط أي مقطع من (TikTok, YouTube, Instagram, Facebook, X) وسأقوم بتحميله وإرساله بأعلى جودة فوراً.\n\n"
        "👇 <i>اختر أحد الأقسام السريعة أدناه أو اكتب لي رسالتك مباشرة:</i>"
    )
    await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard(), parse_mode="HTML")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "movies_hint":
        text = (
            "🎬 <b>قسم الأفلام والمسلسلات:</b>\n\n"
            "اكتب لي اسم أي فيلم أو مسلسل في الشات (مثال: <code>قصة فيلم Oppenheimer</code> أو <code>اقترح لي فيلم رعب قوي</code>)، "
            "وسأعطيك ملخصه، التقييم، وتفاصيل مشاهدته فوراً!"
        )
        await query.message.reply_text(text, parse_mode="HTML")

    elif query.data == "sports_hint":
        text = (
            "⚽ <b>قسم الرياضة وكرة القدم:</b>\n\n"
            "اسألني عن أي فريق، مباراة، دوريات أبطال أوروبا، الدوريات الكبرى، أو أخبار الانتقالات وسأوافيك بالتفاصيل والتحليلات فوراً!"
        )
        await query.message.reply_text(text, parse_mode="HTML")

    elif query.data == "games_hint":
        text = (
            "🎮 <b>قسم الألعاب والبرامج:</b>\n\n"
            "اطلب أي نوع من الألعاب (أكشن، استراتيجية، سيارات، أندرويد/كمبيوتر) أو برامج التعديل والإنترنت وسأقترح عليك الأفضل دائماً."
        )
        await query.message.reply_text(text, parse_mode="HTML")

    elif query.data == "daily_zekr":
        athkar = [
            "سُبْحَانَ اللَّهِ وَبِحَمْدِهِ، سُبْحَانَ اللَّهِ الْعَظِيمِ 🌸",
            "لا حَوْلَ وَلا قُوَّةَ إِلا بِاللَّهِ الْعَلِيِّ الْعَظِيمِ ✨",
            "اللَّهُمَّ صَلِّ وَسَلِّمْ عَلَى نَبِيِّنَا مُحَمَّدٍ وَعَلَى آلِهِ وَصَحْبِهِ أَجْمَعِينَ 🌿",
            "أَسْتَغْفِرُ اللَّهَ الْعَظِيمَ وَأَتُوبُ إِلَيْهِ 💫",
            "لا إِلَهَ إِلا أَنْتَ سُبْحَانَكَ إِنِّي كُنْتُ مِنَ الظَّالِمِينَ 🤲"
        ]
        text = f"✨ <b>ذكر اليوم:</b>\n\n<blockquote>{random.choice(athkar)}</blockquote>"
        await query.message.reply_text(text, parse_mode="HTML")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # فحص ما إذا كانت الرسالة رابط وسائط للتحميل
    video_domains = ["tiktok.com", "douyin.com", "youtube.com", "youtu.be", "instagram.com", "facebook.com", "fb.watch", "twitter.com", "x.com"]
    is_video_link = (text.startswith("http://") or text.startswith("https://")) and any(domain in text.lower() for domain in video_domains)

    if is_video_link:
        status_msg = await update.message.reply_text("⚡️ <b>جاري سحب المقطع والمعالجة بأعلى جودة...</b>", parse_mode="HTML")
        chat_id = update.effective_chat.id
        output_base = f"downloads/{chat_id}_{update.message.message_id}"
        os.makedirs("downloads", exist_ok=True)
        file_path = None
        title = "فيديو"
        platform_name = "مواقع التواصل"

        try:
            if "tiktok.com" in text or "douyin.com" in text:
                output_file = f"{output_base}.mp4"
                info = download_tiktok_direct(text, output_file)
                file_path = info["path"]
                title = info["title"]
                platform_name = info["platform"]
            else:
                output_template = f"{output_base}.%(ext)s"
                info = download_general(text, output_template)
                files = glob.glob(f"{output_base}.*")
                if files:
                    file_path = files[0]
                    title = info.get("title", "فيديو مباشر")
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
                await status_msg.edit_text("❌ تعذر تحميل المقطع، تأكد أن الرابط يعمل والمنشور عام.")
                return

            if os.path.getsize(file_path) > MAX_FILE_SIZE:
                await status_msg.edit_text("⚠️ حجم الفيديو يتعدى 50MB (الحد الأقصى للإرسال عبر تيليجرام).")
                os.remove(file_path)
                return

            await status_msg.edit_text("📤 <b>جاري إرسال المقطع إليك الآن...</b>", parse_mode="HTML")
            caption_text = (
                f"🎬 <b>{title[:120]}</b>\n\n"
                f"📌 المنصة: <b>{platform_name}</b>\n"
                f"⚡️ تم التنزيل عبر: <b>{BOT_NAME}</b>\n"
                f"💬 للتواصل والدعم: <code>+{WHATSAPP_NUMBER}</code>"
            )
            keyboard = [[
                InlineKeyboardButton("💬 واتساب المطور", url=WHATSAPP_URL),
                InlineKeyboardButton("📢 قناة التحديثات", url=CHANNEL_URL)
            ]]
            with open(file_path, "rb") as video:
                await update.message.reply_video(video=video, caption=caption_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML", supports_streaming=True)
            await status_msg.delete()

        except Exception:
            await status_msg.edit_text("❌ تعذر تنزيل الفيديو، تأكد من صحة الرابط.")
        finally:
            for f in glob.glob(f"{output_base}*"):
                try:
                    if os.path.exists(f):
                        os.remove(f)
                except Exception:
                    pass
        return

    # إذا كانت الرسالة نصاً أو سؤالاً أو طلباً لفيلم/مسلسل/مباراة/لعبة/رابط عام
    thinking_msg = await update.message.reply_text("💭 <i>جاري التفكير والبحث لك...</i>", parse_mode="HTML")
    ai_reply = ask_ai(text)
    await thinking_msg.edit_text(ai_reply)

def main():
    threading.Thread(target=start_server, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"✅ {BOT_NAME} يعمل الآن بكامل مميزاته الذكية...")
    app.run_polling()

if __name__ == "__main__":
    main()