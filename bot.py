import os
import glob
import logging
import threading
import json
import re
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
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
WHATSAPP_NUMBER = "967782953692"
WHATSAPP_URL = f"https://wa.me/{WHATSAPP_NUMBER}"
CHANNEL_URL = "https://t.me/saleh_down_bot"
MAX_FILE_SIZE = 49 * 1024 * 1024
# ============================================================

# خادم ويب مصغر لإبقاء خدمة Render نشطة (Live) باستمرار
class SimpleHealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Bot Active on Render 24/7!")

def start_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHealthServer)
    server.serve_forever()

def extract_tiktok_url(text: str) -> str:
    pattern = r'(https?://(?:vt\.tiktok\.com|vm\.tiktok\.com|www\.tiktok\.com|tiktok\.com)/[^\s]+)'
    match = re.search(pattern, text)
    if match:
        return match.group(0).split('?')[0]
    return ""

def download_tiktok(url: str, output_path: str):
    """محرك تنزيل تيك توك بدون علامة مائية بالواجهات الفعالة"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

    # المحاولة 1: TikWM
    try:
        api_url = f"https://www.tikwm.com/api/?url={urllib.parse.quote(url)}"
        res = requests.get(api_url, headers=headers, timeout=10).json()
        if res.get("code") == 0 and "data" in res:
            dl_url = res["data"].get("play") or res["data"].get("wmplay")
            title = res["data"].get("title", "فيديو تيك توك")
            if dl_url.startswith("/"):
                dl_url = "https://www.tikwm.com" + dl_url
            v_data = requests.get(dl_url, headers=headers, timeout=30).content
            with open(output_path, "wb") as f:
                f.write(v_data)
            return {"title": title, "path": output_path}
    except Exception as e:
        logging.warning(f"TikWM error: {e}")

    # المحاولة 2: Loover Tiklydown
    try:
        api_url2 = f"https://api.tiklydown.eu.org/api/download?url={urllib.parse.quote(url)}"
        res2 = requests.get(api_url2, headers=headers, timeout=10).json()
        if "video" in res2:
            dl_url = res2["video"].get("noWatermark") or res2["video"].get("watermark")
            title = res2.get("title", "فيديو تيك توك")
            v_data = requests.get(dl_url, headers=headers, timeout=30).content
            with open(output_path, "wb") as f:
                f.write(v_data)
            return {"title": title, "path": output_path}
    except Exception as e:
        logging.warning(f"Tiklydown error: {e}")

    # المحاولة 3: yt-dlp كحل احتياطي
    try:
        ydl_opts = {
            "format": "best[ext=mp4]/best",
            "outtmpl": output_path,
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "max_filesize": MAX_FILE_SIZE,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return {"title": info.get("title", "فيديو تيك توك"), "path": output_path}
    except Exception as e:
        logging.error(f"yt-dlp error: {e}")

    return None

def download_general_media(target: str, output_path: str, is_search=False):
    """تنزيل من باقي المواقع أو البحث في يوتيوب"""
    query = f"ytsearch1:{target}" if is_search else target
    ydl_opts = {
        "format": "best[ext=mp4][filesize<45M]/best[filesize<45M]/worst[ext=mp4]/worst",
        "outtmpl": output_path,
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "max_filesize": MAX_FILE_SIZE,
        "extractor_args": {"youtube": {"player_client": ["android", "ios"]}},
        "user_agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=True)
        if "entries" in info and len(info["entries"]) > 0:
            return info["entries"][0]
        return info

def ask_instant_ai(prompt: str) -> str:
    """ردود ذكية وتفاعلية وسريعة"""
    p = prompt.lower().strip()
    if any(w in p for w in ["مرحبا", "هلا", "السلام", "أهلاً", "اهلا"]):
        return "يا هلا ومية مرحبا يا غالي نورتني! 🌹✨ أنا في خدمتك دائماً، أرسل أي رابط أو طلب وسأنفذه فوراً."
    if any(w in p for w in ["من انت", "من أنت", "مين انت"]):
        return "أنا بوت صلوح المانعي الذكي ⚡️ رفيقك الأسرع لسحب فيديوهات التيك توك ومقاطع التواصل والأفلام فوراً في المحادثة!"

    try:
        url = "https://text.pollinations.ai/" + urllib.parse.quote(
            f"أنت المساعد الذكي لصلوح المانعي، تحدث بكلام لطيف وذكي ومرح ومختصر باللغة العربية: {prompt}"
        )
        res = requests.get(url, timeout=4)
        if res.status_code == 200 and len(res.text.strip()) > 3:
            return res.text.strip()
    except Exception:
        pass

    return f"طلبك بخصوص <b>{prompt}</b> على راسي من فوق! جاري تجهيز كل ما يسعدك دائماً 🌸✨"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    msg = (
        f"👑 <b>أهلاً بك يا {name} في {BOT_NAME}!</b>\n\n"
        "⚡️ أسرع بوت لتنزيل الوسائط مباشرة في المحادثة:\n"
        "• 📥 <b>تيك توك:</b> أرسل رابط الفيديو وسأرسله لك فوراً بدون علامة مائية.\n"
        "• 🎵 <b>أغاني وأفلام ومباريات:</b> اكتب اسم المقطع وسأجلبه لك.\n\n"
        "👇 <i>أرسل الرابط أو طلبك وسأبدأ فوراً:</i>"
    )
    kb = [
        [InlineKeyboardButton("💬 واتساب صلوح المانعي", url=WHATSAPP_URL)],
        [InlineKeyboardButton("📢 قناة التحديثات", url=CHANNEL_URL)]
    ]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_id = update.effective_chat.id
    msg_id = update.message.message_id
    output_path = f"downloads/{chat_id}_{msg_id}.mp4"
    os.makedirs("downloads", exist_ok=True)

    # 1. روابط تيك توك
    tiktok_url = extract_tiktok_url(text)
    if tiktok_url:
        wait_msg = await update.message.reply_text(
            "⚡️ <b>جاري البحث... صلوح المانعي يجلب لك المقطع الآن مباشرة ✨</b>", 
            parse_mode="HTML"
        )
        data = download_tiktok(tiktok_url, output_path)
        if data and os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            caption = (
                f"🎬 <b>تفضل الفيديو بدون علامة مائية يا غالي:</b>\n\n"
                f"📌 <b>{data['title'][:100]}</b>\n\n"
                f"✨ تم التحميل بواسطة: <b>{BOT_NAME}</b>"
            )
            with open(output_path, "rb") as vid:
                await update.message.reply_video(video=vid, caption=caption, parse_mode="HTML", supports_streaming=True)
            await wait_msg.delete()
            try: os.remove(output_path)
            except Exception: pass
            return
        else:
            await wait_msg.edit_text("❌ تعذر تحميل المقطع، تأكد أن الفيديو ليس خاصاً أو محذوفاً.")
            try: os.remove(output_path)
            except Exception: pass
            return

    # 2. روابط الوسائط الأخرى
    if text.startswith("http://") or text.startswith("https://"):
        wait_msg = await update.message.reply_text(
            "⚡️ <b>جاري البحث... صلوح المانعي يجلب لك المقطع الآن مباشرة ✨</b>", 
            parse_mode="HTML"
        )
        try:
            info = download_general_media(text, output_path, is_search=False)
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                with open(output_path, "rb") as vid:
                    await update.message.reply_video(video=vid, caption=f"🎬 <b>{info.get('title', 'فيديو')[:100]}</b>\n\n✨ بواسطة: <b>{BOT_NAME}</b>", parse_mode="HTML")
                await wait_msg.delete()
            else:
                await wait_msg.edit_text("⚠️ حجم المقطع يتجاوز 50MB.")
        except Exception:
            await wait_msg.edit_text("❌ تعذر تحميل الرابط.")
        finally:
            try: os.remove(output_path)
            except Exception: pass
        return

    # 3. طلبات الميديا والبحث
    media_words = ["اغنيه", "أغنية", "اغنية", "فيلم", "فلم", "افلام", "أفلام", "مسلسل", "اهداف", "أهداف", "مباراة", "مباراه", "ملخص"]
    if any(w in text.lower() for w in media_words):
        wait_msg = await update.message.reply_text(
            "⚡️ <b>جاري البحث... صلوح المانعي يبحث لك الآن عن أفضل محتوى ✨</b>", 
            parse_mode="HTML"
        )
        try:
            clean_q = text.replace("قم بتنزيل", "").replace("تنزيل", "").replace("اريد", "").strip()
            info = download_general_media(clean_q, output_path, is_search=True)
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                with open(output_path, "rb") as vid:
                    await update.message.reply_video(video=vid, caption=f"🎬 <b>{info.get('title', clean_q)[:100]}</b>\n\n✨ تم الجلب عبر: <b>{BOT_NAME}</b>", parse_mode="HTML")
                await wait_msg.delete()
                try: os.remove(output_path)
                except Exception: pass
                return
        except Exception:
            pass

    # 4. الذكاء الاصطناعي والمحادثة
    wait_msg = await update.message.reply_text(
        "⚡️ <b>جاري البحث... صلوح المانعي يبحث لك الآن عن أفضل محتوى ✨</b>", 
        parse_mode="HTML"
    )
    reply = ask_instant_ai(text)
    try:
        await wait_msg.edit_text(reply, parse_mode="HTML")
    except Exception:
        await wait_msg.edit_text(reply)

def main():
    # تشغيل خادم الويب في خلفية السيرفر
    threading.Thread(target=start_server, daemon=True).start()
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"✅ {BOT_NAME} يعمل الآن على السيرفر السحابي 24/7...")
    app.run_polling()

if __name__ == "__main__":
    main()
