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
BOT_NAME = "بوت صلوح المانعي الذكي ⚡️"
BOT_USERNAME = "saleh_down_bot"
CHANNEL_URL = "https://t.me/saleh_down_bot"
WHATSAPP_NUMBER = "967782953692"
WHATSAPP_URL = f"https://wa.me/{WHATSAPP_NUMBER}"
MAX_FILE_SIZE = 50 * 1024 * 1024
# ============================================================

# خادم وهمي لمنصة Render لضمان بقائه Live على مدار الساعة
class SimpleHealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Saleh AI Bot is active 24/7!")

def start_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHealthServer)
    logging.info(f"Health server running on port {port}")
    server.serve_forever()

def ask_fast_ai(prompt: str) -> str:
    """محرك ذكاء اصطناعي فائق السرعة يعتمد على DDG GPT-4o mini API"""
    system_prompt = (
        "أنت المساعد الذكي الخارق لبوت صلوح المانعي على تيليجرام. "
        "شخصيتك: ودود جداً، ذكي، مرح، ولبق في الكلام بأسلوب شيق وجذاب يرحب بالمستخدم كأخ وعزيز. "
        "عند طلب أفلام أو مسلسلات (مثل تركي، أجنبي، أنمي كـ سولو ليفلينج): اذكر الاسم، القصة باختصار مشوق، التقييم العالمي، ورابط للبحث والمشاهدة. "
        "عند السؤال عن كرة القدم والرياضة (مثل برشلونة والدوريات): قدم تحليلاً حماسياً ومعلومات دقيقة عن المباريات والمواعيد. "
        "عند السؤال عن ألعاب أو تطبيقات: اقترح أفضل الخيارات فوراً وروابط البحث عنها. "
        "نسق الإجابة بنقاط ورموز تعبيرية جميلة وممتعة."
    )
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/event-stream",
        "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
        "Referer": "https://duckduckgo.com/",
        "x-vqd-accept": "1"
    }

    try:
        # جلب التوكن الأولي السريع
        status_resp = requests.get("https://duckduckgo.com/duckchat/v1/status", headers=headers, timeout=4)
        vqd = status_resp.headers.get("x-vqd-4")

        if vqd:
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "user", "content": f"{system_prompt}\n\nطلب المستخدم: {prompt}"}
                ]
            }
            chat_headers = {
                **headers,
                "Content-Type": "application/json",
                "x-vqd-4": vqd
            }
            resp = requests.post("https://duckduckgo.com/duckchat/v1/chat", headers=chat_headers, json=payload, timeout=6)
            full_text = ""
            for line in resp.iter_lines(decode_unicode=True):
                if line and line.startswith("data: "):
                    content = line[6:].strip()
                    if content == "[DONE]":
                        break
                    import json
                    try:
                        data = json.loads(content)
                        if "message" in data:
                            full_text += data["message"]
                    except Exception:
                        pass
            if full_text.strip():
                return full_text.strip()
    except Exception as e:
        logging.error(f"DDG AI error: {e}")

    # محرك احتياطي سريع جداً في حال تعذر المحرك الأول
    try:
        sys_encoded = requests.utils.quote(f"{system_prompt} | المستخدم: {prompt}")
        url = f"https://text.pollinations.ai/{sys_encoded}?model=openai"
        r = requests.get(url, timeout=5)
        if r.status_code == 200 and r.text.strip():
            return r.text.strip()
    except Exception:
        pass

    return (
        f"يا هلا وغلا يا عزيزي نورتني! 🌟\n\n"
        f"طلبك بخصوص: <b>{prompt}</b> في بالي دائماً!\n"
        f"🎬 إذا تبحث عن مشاهدة الفيلم أو الحلقة بجودة عالية، تفضل الرابط المباشر للبحث:\n"
        f"👉 https://www.google.com/search?q={requests.utils.quote(prompt + ' مشاهدة وتحميل بجودة عالية')}\n\n"
        f"أنا رهن إشارتك في أي وقت، تبي فيلم، مباراة، أو تنزيل فيديو؟ أرسل وبشر بالسعد! ✨"
    )

def resolve_redirect(url: str) -> str:
    try:
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0"})
        return session.get(url, allow_redirects=True, timeout=8).url
    except Exception:
        return url

def download_tiktok_direct(url: str, output_path: str):
    full_url = resolve_redirect(url)
    api_url = f"https://www.tikwm.com/api/?url={full_url}"
    resp = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    data = resp.json()
    if data.get("code") == 0 and "data" in data:
        dl_url = data["data"].get("play") or data["data"].get("wmplay")
        title = data["data"].get("title", "فيديو تيك توك")
        video_bytes = requests.get(dl_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30).content
        with open(output_path, "wb") as f:
            f.write(video_bytes)
        return {"title": title, "path": output_path, "platform": "تيك توك بدون علامة مائية"}
    raise Exception("Tiktok download error")

def download_general(url: str, output_template: str):
    ydl_opts = {
        "outtmpl": output_template,
        "format": "best[ext=mp4]/best",
        "quiet": True,
        "no_warnings": True,
        "max_filesize": MAX_FILE_SIZE,
        "nocheckcertificate": True,
        "user_agent": "Mozilla/5.0",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=True)

def get_main_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🎬 سينما وأفلام", callback_data="movies_hint"),
            InlineKeyboardButton("⚽ كرة القدم والمباريات", callback_data="sports_hint"),
        ],
        [
            InlineKeyboardButton("🎮 ألعاب وتطبيقات", callback_data="games_hint"),
            InlineKeyboardButton("📿 ذكر اليوم", callback_data="daily_zekr"),
        ],
        [
            InlineKeyboardButton("💬 واتساب صلوح المانعي", url=WHATSAPP_URL),
            InlineKeyboardButton("📢 قناة التحديثات", url=CHANNEL_URL),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    welcome_text = (
        f"👑 <b>أهلاً وسهلاً بك يا أغلى الناس {user_name}!</b> نورت {BOT_NAME} 🌹\n\n"
        "أنا مساعدك ورفيقك الشخصي المزود بأحدث وأسرع ذكاء اصطناعي ⚡️\n\n"
        "✨ <b>كيف أقدر أسعدك اليوم؟</b>\n"
        "• 🎬 <b>الأفلام والمسلسلات:</b> اطلب أي فيلم، حلقة مسلسل تركي، أو أنمي وسأعطيك قصته وتقييمه وروابطه فوراً.\n"
        "• ⚽ <b>عالم الرياضة:</b> اسألني عن المباريات، نادي برشلونة، الدوريات الأوروبية والتحليلات الرياضية.\n"
        "• 🎮 <b>الألعاب والبرامج:</b> اقترح لك أفضل الألعاب والتطبيقات للهاتف والكمبيوتر.\n"
        "• 📥 <b>التحميل الخارق:</b> أرسل رابط أي مقطع من (تيك توك، يوتيوب، إنستغرام، فيسبوك) وسأحمله لك في ثوانٍ بدون علامة مائية!\n\n"
        "👇 <i>تفضل بسؤالي مباشرة في الشات أو اختر من القائمة:</i>"
    )
    await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard(), parse_mode="HTML")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "movies_hint":
        text = (
            "🎬 <b>عالم السينما والمسلسلات في خدمتك:</b>\n\n"
            "اكتب لي مباشرة في الشات أي طلب مثل:\n"
            "• <i>أريد أفضل فيلم أكشن لعام 2024</i>\n"
            "• <i>أعطني ملخص مسلسل قيامة عثمان</i>\n"
            "• <i>حلقات أنمي سولو ليفلينج</i>\n\n"
            "وسأجلب لك القصة، التقييم، وأفضل روابط المشاهدة في لحظات! 🍿"
        )
        await query.message.reply_text(text, parse_mode="HTML")

    elif query.data == "sports_hint":
        text = (
            "⚽ <b>ركن الرياضة وعشاق الساحرة المستديرة:</b>\n\n"
            "اسألني عن:\n"
            "• <i>مباريات اليوم في دوري الأبطال</i>\n"
            "• <i>أخبار نادي برشلونة وتشكيلته</i>\n"
            "• <i>ترتيب الدوري الإسباني أو الإنجليزي</i>\n\n"
            "وسأعطيك التحليل والمعلومات الكروية فوراً! 🏆"
        )
        await query.message.reply_text(text, parse_mode="HTML")

    elif query.data == "games_hint":
        text = (
            "🎮 <b>أفضل الألعاب والبرامج المختارة لك:</b>\n\n"
            "اسألني عن أي مجال:\n"
            "• <i>أفضل لعبة قتال للأندرويد بدون إنترنت</i>\n"
            "• <i>برامج لتعديل الفيديو للموبايل</i>\n\n"
            "وسأرشح لك أفضل الخيارات مع الروابط! 🕹"
        )
        await query.message.reply_text(text, parse_mode="HTML")

    elif query.data == "daily_zekr":
        athkar = [
            "سُبْحَانَ اللَّهِ وَبِحَمْدِهِ، سُبْحَانَ اللَّهِ الْعَظِيمِ 🌸",
            "لا حَوْلَ وَلا قُوَّةَ إِلا بِاللَّهِ الْعَلِيِّ الْعَظِيمِ ✨",
            "اللَّهُمَّ صَلِّ وَسَلِّمْ عَلَى نَبِيِّنَا مُحَمَّدٍ وَعَلَى آلِهِ وَصَحْبِهِ أَجْمَعِينَ 🌿",
            "أَسْتَغْفِرُ اللَّهَ الْعَظِيمَ الَّذِي لا إِلَهَ إِلا هُوَ الْحَيُّ الْقَيُّومُ وَأَتُوبُ إِلَيْهِ 💫",
            "لا إِلَهَ إِلا أَنْتَ سُبْحَانَكَ إِنِّي كُنْتُ مِنَ الظَّالِمِينَ 🤲"
        ]
        text = f"✨ <b>ذكر اليوم لراحة بالك:</b>\n\n<blockquote>{random.choice(athkar)}</blockquote>"
        await query.message.reply_text(text, parse_mode="HTML")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # التحقق إن كانت الرسالة رابط فيديو للتحميل
    video_domains = ["tiktok.com", "douyin.com", "youtube.com", "youtu.be", "instagram.com", "facebook.com", "fb.watch", "twitter.com", "x.com"]
    is_video_link = (text.startswith("http://") or text.startswith("https://")) and any(d in text.lower() for d in video_domains)

    if is_video_link:
        status_msg = await update.message.reply_text("⚡️ <b>جاري سحب الفيديو وتجهيزه بأعلى جودة...</b>", parse_mode="HTML")
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
                    platform_name = "فيديو مباشر"

            if not file_path or not os.path.exists(file_path):
                await status_msg.edit_text("❌ تعذر تحميل المقطع، تأكد من أن الرابط مباشر ومتاح للعامة.")
                return

            if os.path.getsize(file_path) > MAX_FILE_SIZE:
                await status_msg.edit_text("⚠️ حجم الفيديو يتعدى 50MB (الحد المسموح في تيليجرام).")
                os.remove(file_path)
                return

            await status_msg.edit_text("📤 <b>جاري إرسال المقطع إليك الآن...</b>", parse_mode="HTML")
            caption_text = (
                f"🎬 <b>{title[:120]}</b>\n\n"
                f"📌 المنصة: <b>{platform_name}</b>\n"
                f"⚡️ تم التنزيل عبر: <b>{BOT_NAME}</b>\n"
                f"💬 للتواصل: <code>+{WHATSAPP_NUMBER}</code>"
            )
            keyboard = [[
                InlineKeyboardButton("💬 واتساب صلوح المانعي", url=WHATSAPP_URL),
                InlineKeyboardButton("📢 قناة التحديثات", url=CHANNEL_URL)
            ]]
            with open(file_path, "rb") as video:
                await update.message.reply_video(video=video, caption=caption_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML", supports_streaming=True)
            await status_msg.delete()

        except Exception:
            await status_msg.edit_text("❌ تعذر تنزيل الفيديو، يرجى التأكد من صحة الرابط.")
        finally:
            for f in glob.glob(f"{output_base}*"):
                try:
                    if os.path.exists(f):
                        os.remove(f)
                except Exception:
                    pass
        return

    # محادثة وبحث فائق السرعة بالذكاء الاصطناعي مع رسالة الانتظار المخصصة
    search_msg = await update.message.reply_text(
        "⚡️ <b>جاري البحث... صلوح المانعي يبحث لك الآن عن أفضل محتوى ✨</b>", 
        parse_mode="HTML"
    )
    
    ai_reply = ask_fast_ai(text)
    
    # إضافة زر بحث مباشر في Google أسفل كل رد لتسهيل الوصول للمشاهدة
    search_url = f"https://www.google.com/search?q={requests.utils.quote(text)}"
    quick_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 فتح نتائج المشاهدة والتحميل", url=search_url)],
        [InlineKeyboardButton("💬 تواصل مع صلوح المانعي", url=WHATSAPP_URL)]
    ])
    
    try:
        await search_msg.edit_text(ai_reply, reply_markup=quick_keyboard, parse_mode="HTML")
    except Exception:
        # في حال وجود رموز تعارض مع وسم HTML
        await search_msg.edit_text(ai_reply, reply_markup=quick_keyboard)

def main():
    threading.Thread(target=start_server, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"✅ {BOT_NAME} يعمل الآن بالذكاء الاصطناعي فائق السرعة...")
    app.run_polling()

if __name__ == "__main__":
    main()