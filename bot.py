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
BOT_NAME = "بوت صلوح المانعي التفاعلي ⚡️"
BOT_USERNAME = "saleh_down_bot"
CHANNEL_URL = "https://t.me/saleh_down_bot"
WHATSAPP_NUMBER = "967782953692"
WHATSAPP_URL = f"https://wa.me/{WHATSAPP_NUMBER}"
MAX_FILE_SIZE = 49 * 1024 * 1024  # حد تيليجرام المجاني (أقل من 50MB)
# ============================================================

class SimpleHealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Bot is active 24/7!")

def start_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHealthServer)
    server.serve_forever()

def ask_fast_ai(prompt: str) -> str:
    """محرك الذكاء الاصطناعي السريع والمرح"""
    system_prompt = (
        "أنت المساعد الذكي الخارق لبوت صلوح المانعي على تيليجرام. "
        "تحدث بأسلوب لبق، مرح، ومتحمس باللغة العربية. "
        "عند الحديث عن الأفلام أو المسلسلات أو المباريات، اذكر القصة، سنة الإنتاج، التقييم، وتفاصيل النجوم باختصار شيق. "
        "نسق النص دائماً بنقاط ورموز تعبيرية راقية."
    )
    url = f"https://text.pollinations.ai/{requests.utils.quote(system_prompt + ' | طلب المستخدم: ' + prompt)}?model=openai"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200 and r.text.strip():
            return r.text.strip()
    except Exception as e:
        logging.error(f"AI Error: {e}")

    return f"يا هلا وغلا يا غالي! 🌹 طلبك بخصوص: <b>{prompt}</b> في بالي وجاري خدمتك دائماً بأجمل محتوى حي!"

def search_and_download(query: str, output_base: str, max_size_limit=True):
    """البحث في يوتيوب وتحميل الفيديو مع مراعاة الحجم"""
    fmt = "best[ext=mp4][filesize<48M]/best[filesize<48M]/best" if max_size_limit else "best[ext=mp4]/best"
    ydl_opts = {
        "format": fmt,
        "outtmpl": f"{output_base}.%(ext)s",
        "default_search": "ytsearch1:",
        "quiet": True,
        "no_warnings": True,
        "writethumbnail": True,
        "nocheckcertificate": True,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=True)
        if "entries" in info and len(info["entries"]) > 0:
            return info["entries"][0]
        return info

def download_by_url(url: str, output_base: str):
    ydl_opts = {
        "format": "best[ext=mp4][filesize<48M]/best[filesize<48M]/best",
        "outtmpl": f"{output_base}.%(ext)s",
        "quiet": True,
        "no_warnings": True,
        "max_filesize": MAX_FILE_SIZE,
        "nocheckcertificate": True,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    msg = (
        f"👑 <b>أهلاً وسهلاً بك يا {name} في {BOT_NAME}!</b>\n\n"
        "🎬 <b>أنا لا أرسل لك مجرد روابط.. بل أرسل لك المحتوى حياً ومباشراً:</b>\n\n"
        "• <b>الأفلام والمسلسلات:</b> اكتب اسم أي عمل، وسأرسل لك مقطعه الترويجي أو ملخصه كفيديو كامل داخل المحادثة.\n"
        "• <b>المباريات:</b> اطلب أي مباراة أو ملخص وستصلك الأهداف كفيديو مباشر.\n"
        "• <b>تنزيل الوسائط:</b> أرسل رابط أي فيديو من تيك توك، يوتيوب، أو إنستغرام ليتم تحميله فوراً.\n"
        "• <b>ذكاء اصطناعي تفاعلي:</b> اسألني عن أي موضوع وسأجيبك بسرعة فائقة!\n"
    )
    keyboard = [
        [InlineKeyboardButton("💬 واتساب صلوح المانعي", url=WHATSAPP_URL)],
        [InlineKeyboardButton("📢 قناة التحديثات", url=CHANNEL_URL)]
    ]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_id = update.effective_chat.id
    msg_id = update.message.message_id
    output_base = f"downloads/{chat_id}_{msg_id}"
    os.makedirs("downloads", exist_ok=True)

    # 1. إذا كان المدخل رابطاً مباشراً
    if text.startswith("http://") or text.startswith("https://"):
        wait_msg = await update.message.reply_text("⚡️ <b>جاري سحب الفيديو وإرساله لك مباشرة...</b>", parse_mode="HTML")
        try:
            info = download_by_url(text, output_base)
            files = [f for f in glob.glob(f"{output_base}.*") if not f.endswith(('.webp', '.jpg', '.png'))]
            if files and os.path.getsize(files[0]) <= MAX_FILE_SIZE:
                title = info.get("title", "فيديو مباشر")
                with open(files[0], "rb") as vid:
                    await update.message.reply_video(video=vid, caption=f"🎬 <b>{title[:100]}</b>\n\n⚡️ بواسطة {BOT_NAME}", parse_mode="HTML")
                await wait_msg.delete()
            else:
                await wait_msg.edit_text("⚠️ حجم الفيديو يتعدى 50MB (الحد الأقصى لملفات تيليجرام المباشرة).")
        except Exception:
            await wait_msg.edit_text("❌ تعذر تحميل المقطع، تأكد من صحة الرابط.")
        finally:
            for f in glob.glob(f"{output_base}*"):
                try: os.remove(f)
                except Exception: pass
        return

    # 2. الكلمات المفتاحية للمحتوى الحي (أفلام، مسلسلات، مباريات، أهداف، أنمي)
    media_keywords = ["فيلم", "فلم", "مسلسل", "حلقة", "اهداف", "أهداف", "ملخص", "انمي", "مباراة", "مباراه", "هدف", "عرض", "اعلان"]
    is_media_request = any(kw in text.lower() for kw in media_keywords)

    if is_media_request:
        wait_msg = await update.message.reply_text(
            "⚡️ <b>جاري البحث... صلوح المانعي يجلب لك المقطع والبوستر الحي الآن مباشرة ✨</b>", 
            parse_mode="HTML"
        )
        
        info = None
        # محاولة البحث وسحب الفيديو المناسب أولاً
        try:
            info = search_and_download(text, output_base, max_size_limit=True)
        except Exception:
            pass

        video_files = [f for f in glob.glob(f"{output_base}.*") if not f.endswith(('.webp', '.jpg', '.png'))]
        
        # الحالة الأولى: وجدنا الفيديو وكان حجمه ضمن المسموح (أقل من 50MB) -> إرساله فوراً كفيديو
        if video_files and os.path.exists(video_files[0]) and os.path.getsize(video_files[0]) <= MAX_FILE_SIZE:
            title = info.get("title", text) if info else text
            caption = (
                f"🎬 <b>{title[:120]}</b>\n\n"
                f"🍿 تم جلب الفيديو حياً ومباشراً بواسطة: <b>{BOT_NAME}</b>\n"
                f"💬 للتواصل: <code>+{WHATSAPP_NUMBER}</code>"
            )
            watch_url = info.get("webpage_url") if info else f"https://www.google.com/search?q={requests.utils.quote(text)}"
            btn = InlineKeyboardMarkup([[InlineKeyboardButton("🎬 مشاهدة المصدر بجودة 4K", url=watch_url)]])
            
            with open(video_files[0], "rb") as vid:
                await update.message.reply_video(video=vid, caption=caption, reply_markup=btn, parse_mode="HTML", supports_streaming=True)
            await wait_msg.delete()

        # الحالة الثانية: المحتوى كبير جداً (أكثر من 50MB) -> إرسال التريلر أو البوستر كفيديو/صورة حية
        else:
            # تنظيف المحاولة السابقة
            for f in glob.glob(f"{output_base}*"):
                try: os.remove(f)
                except Exception: pass

            # جلب إعلان/تريلر سريع (حجمه دائماً خفيف) أو البوستر
            trailer_query = f"{text} trailer اعلان رسمي"
            try:
                trailer_info = search_and_download(trailer_query, output_base, max_size_limit=True)
                t_files = [f for f in glob.glob(f"{output_base}.*") if not f.endswith(('.webp', '.jpg', '.png'))]
                thumb_files = glob.glob(f"{output_base}.webp") + glob.glob(f"{output_base}.jpg") + glob.glob(f"{output_base}.png")
                
                ai_details = ask_fast_ai(text)
                search_url = f"https://www.google.com/search?q={requests.utils.quote(text + ' مشاهدة وتحميل مباشر')}"
                btn = InlineKeyboardMarkup([[InlineKeyboardButton("▶️ بدء تشغيل العمل كاملاً", url=search_url)]])

                caption_body = (
                    f"🎬 <b>{text.upper()}</b>\n"
                    f"⚠️ <i>العمل الكامل حجمه يتجاوز 50MB، تم جلب البوستر والعرض الحي لك:</i>\n\n"
                    f"{ai_details}\n\n"
                    f"⚡️ <b>{BOT_NAME}</b>"
                )

                if t_files and os.path.exists(t_files[0]) and os.path.getsize(t_files[0]) <= MAX_FILE_SIZE:
                    with open(t_files[0], "rb") as vid:
                        await update.message.reply_video(video=vid, caption=caption_body[:1024], reply_markup=btn, parse_mode="HTML")
                elif thumb_files and os.path.exists(thumb_files[0]):
                    with open(thumb_files[0], "rb") as photo:
                        await update.message.reply_photo(photo=photo, caption=caption_body[:1024], reply_markup=btn, parse_mode="HTML")
                else:
                    await update.message.reply_text(caption_body, reply_markup=btn, parse_mode="HTML")

                await wait_msg.delete()
            except Exception as e:
                logging.error(f"Trailer error: {e}")
                ai_details = ask_fast_ai(text)
                await wait_msg.edit_text(ai_details, parse_mode="HTML")

        # تنظيف الملفات المؤقتة
        for f in glob.glob(f"{output_base}*"):
            try: os.remove(f)
            except Exception: pass
        return

    # 3. للمحادثة والذكاء الاصطناعي العام
    wait_msg = await update.message.reply_text(
        "⚡️ <b>جاري البحث... صلوح المانعي يبحث لك الآن عن أفضل محتوى ✨</b>", 
        parse_mode="HTML"
    )
    reply = ask_fast_ai(text)
    try:
        await wait_msg.edit_text(reply, parse_mode="HTML")
    except Exception:
        await wait_msg.edit_text(reply)

def main():
    threading.Thread(target=start_server, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"✅ {BOT_NAME} يعمل الآن بالمحتوى الحي والفيديوهات المباشرة...")
    app.run_polling()

if __name__ == "__main__":
    main()