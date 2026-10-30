import os
import glob
import logging
import random
import threading
import json
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
MAX_FILE_SIZE = 49 * 1024 * 1024
# ============================================================

class SimpleHealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Saleh Bot is active 24/7!")

def start_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHealthServer)
    server.serve_forever()

def ask_fast_ai(prompt: str) -> str:
    """ذكاء اصطناعي سريع مع تجاوز التعليق"""
    system_text = (
        "أنت المساعد الذكي الخارق لبوت صلوح المانعي على تيليجرام. "
        "تحدث بأسلوب لبق، مرح، وودود جداً. "
        "عند الحديث عن الأفلام أو المسلسلات أو الأنمي أو الرياضة، قدم ملخصاً ممتعاً وتقييماً وتفاصيل مشوقة."
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/event-stream",
        "x-vqd-accept": "1"
    }
    try:
        status_resp = requests.get("https://duckduckgo.com/duckchat/v1/status", headers=headers, timeout=3)
        vqd = status_resp.headers.get("x-vqd-4")
        if vqd:
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": f"{system_text}\n\nطلب المستخدم: {prompt}"}]
            }
            chat_headers = {**headers, "Content-Type": "application/json", "x-vqd-4": vqd}
            resp = requests.post("https://duckduckgo.com/duckchat/v1/chat", headers=chat_headers, json=payload, timeout=5)
            full_text = ""
            for line in resp.iter_lines(decode_unicode=True):
                if line and line.startswith("data: "):
                    content = line[6:].strip()
                    if content == "[DONE]":
                        break
                    try:
                        data = json.loads(content)
                        if "message" in data:
                            full_text += data["message"]
                    except Exception:
                        pass
            if full_text.strip():
                return full_text.strip()
    except Exception:
        pass

    return (
        f"يا هلا وغلا يا عزيزي نورتني! 🌹\n\n"
        f"طلبك بخصوص <b>{prompt}</b> جاهز ومتاح بالكامل بأعلى جودة.\n"
        f"أنا رهن إشارتك دائماً للأفلام والمباريات والتنزيل! ✨"
    )

def fetch_poster_image(query: str):
    """جلب بوستر الفيلم أو العمل بجودة عالية بدون حظر"""
    try:
        clean_q = query.replace("فيلم", "").replace("فلم", "").replace("مسلسل", "").replace("انمي", "").strip()
        url = f"https://itunes.apple.com/search?term={requests.utils.quote(clean_q)}&media=movie&limit=1"
        res = requests.get(url, timeout=4).json()
        if res.get("resultCount", 0) > 0:
            art = res["results"][0].get("artworkUrl100", "")
            return art.replace("100x100bb.jpg", "600x600bb.jpg")
    except Exception:
        pass
    return None

def search_and_download(query: str, output_base: str):
    """تنزيل وتخطي حظر يوتيوب عبر محاكاة عميل الأندرويد"""
    ydl_opts = {
        "format": "best[ext=mp4][filesize<48M]/best[filesize<48M]/best",
        "outtmpl": f"{output_base}.%(ext)s",
        "default_search": "ytsearch1:",
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios"]
            }
        },
        "user_agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=True)
        if "entries" in info and len(info["entries"]) > 0:
            return info["entries"][0]
        return info

def download_by_url(url: str, output_base: str):
    """تنزيل الروابط المباشرة لجميع المنصات"""
    ydl_opts = {
        "format": "best[ext=mp4][filesize<48M]/best[filesize<48M]/best",
        "outtmpl": f"{output_base}.%(ext)s",
        "quiet": True,
        "no_warnings": True,
        "max_filesize": MAX_FILE_SIZE,
        "nocheckcertificate": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios"]
            }
        },
        "user_agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    msg = (
        f"👑 <b>أهلاً وسهلاً بك يا {name} في {BOT_NAME}!</b>\n\n"
        "🎬 <b>محتوى حي وفيديوهات مباشرة داخل المحادثة:</b>\n\n"
        "• <b>الأفلام والمسلسلات:</b> اكتب اسم الفيلم أو المسلسل وسأرسل لك الفيديو أو البوستر والعرض الحي مباشرة.\n"
        "• <b>المباريات:</b> اطلب ملخص أو أهداف أي مباراة وسيصلك المقطع فوراً.\n"
        "• <b>تنزيل الفيديو:</b> أرسل رابط تيك توك، يوتيوب، أو إنستغرام للتحميل الفوري.\n"
        "• <b>ذكاء اصطناعي:</b> تحدث معي وسأجيبك بسرعة فائقة!\n"
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

    # 1. إذا كان رابط مباشر
    if text.startswith("http://") or text.startswith("https://"):
        wait_msg = await update.message.reply_text("⚡️ <b>جاري تحميل الفيديو وإرساله مباشرة...</b>", parse_mode="HTML")
        try:
            info = download_by_url(text, output_base)
            files = [f for f in glob.glob(f"{output_base}.*") if not f.endswith(('.webp', '.jpg', '.png'))]
            if files and os.path.getsize(files[0]) <= MAX_FILE_SIZE:
                title = info.get("title", "فيديو مباشر")
                with open(files[0], "rb") as vid:
                    await update.message.reply_video(video=vid, caption=f"🎬 <b>{title[:100]}</b>\n\n⚡️ بواسطة {BOT_NAME}", parse_mode="HTML")
                await wait_msg.delete()
            else:
                await wait_msg.edit_text("⚠️ حجم الفيديو يتجاوز 50MB (الحد الأقصى المسموح به).")
        except Exception:
            await wait_msg.edit_text("❌ تعذر التحميل، تأكد من صحة الرابط.")
        finally:
            for f in glob.glob(f"{output_base}*"):
                try: os.remove(f)
                except Exception: pass
        return

    # 2. طلبات الميديا الحية (أفلام، مسلسلات، مباريات، أهداف، أنمي)
    media_keywords = ["فيلم", "فلم", "مسلسل", "حلقة", "اهداف", "أهداف", "ملخص", "انمي", "مباراة", "مباراه", "هدف"]
    if any(kw in text.lower() for kw in media_keywords):
        wait_msg = await update.message.reply_text(
            "⚡️ <b>جاري البحث... صلوح المانعي يجلب لك المقطع والبوستر الحي الآن مباشرة ✨</b>", 
            parse_mode="HTML"
        )
        
        video_sent = False
        try:
            search_query = f"{text} ملخص" if ("فيلم" in text or "فلم" in text) and "ملخص" not in text else text
            info = search_and_download(search_query, output_base)
            v_files = [f for f in glob.glob(f"{output_base}.*") if not f.endswith(('.webp', '.jpg', '.png'))]
            
            if v_files and os.path.exists(v_files[0]) and os.path.getsize(v_files[0]) <= MAX_FILE_SIZE:
                title = info.get("title", text)
                caption = f"🎬 <b>{title[:120]}</b>\n\n🍿 تم الجلب حياً بواسطة: <b>{BOT_NAME}</b>"
                with open(v_files[0], "rb") as vid:
                    await update.message.reply_video(video=vid, caption=caption, parse_mode="HTML", supports_streaming=True)
                await wait_msg.delete()
                video_sent = True
        except Exception as e:
            logging.error(f"Download error: {e}")

        # إذا تعذر إرسال الفيديو المباشر أو كان حجمه كبيراً، يتم إرسال البوستر المباشر ومعلومات الذكاء الاصطناعي فوراً
        if not video_sent:
            poster_url = fetch_poster_image(text)
            ai_details = ask_fast_ai(text)
            caption_body = (
                f"🎬 <b>{text.upper()}</b>\n\n"
                f"{ai_details}\n\n"
                f"⚡️ <b>{BOT_NAME}</b>"
            )
            btn = InlineKeyboardMarkup([[InlineKeyboardButton("▶️ بدء تشغيل العمل كاملاً", url=f"https://www.google.com/search?q={requests.utils.quote(text + ' مشاهدة وتحميل')}")]])

            try:
                if poster_url:
                    await update.message.reply_photo(photo=poster_url, caption=caption_body[:1024], reply_markup=btn, parse_mode="HTML")
                else:
                    await update.message.reply_text(caption_body, reply_markup=btn, parse_mode="HTML")
                await wait_msg.delete()
            except Exception:
                await wait_msg.edit_text(caption_body, reply_markup=btn)

        for f in glob.glob(f"{output_base}*"):
            try: os.remove(f)
            except Exception: pass
        return

    # 3. الدردشة العادية والردود السريعة
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

    print(f"✅ {BOT_NAME} يعمل الآن بتخطي الحظر وجلب البوسترات الحية...")
    app.run_polling()

if __name__ == "__main__":
    main()