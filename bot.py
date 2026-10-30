import os
import glob
import logging
import threading
import json
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
        self.wfile.write(b"Saleh Fast Bot Active 24/7!")

def start_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHealthServer)
    server.serve_forever()

def fast_tiktok_download(url: str, output_path: str):
    """سحب سريع جداً ومباشر لمقاطع تيك توك بدون علامة مائية"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    
    # محرك 1: TikWM السريع
    try:
        api_url = f"https://www.tikwm.com/api/?url={urllib.parse.quote(url)}"
        r = requests.get(api_url, headers=headers, timeout=6).json()
        if r.get("code") == 0 and "data" in r:
            video_url = r["data"].get("play") or r["data"].get("wmplay")
            title = r["data"].get("title", "فيديو تيك توك")
            if video_url:
                v_res = requests.get(video_url, headers=headers, timeout=15)
                with open(output_path, "wb") as f:
                    f.write(v_res.content)
                return {"title": title, "path": output_path}
    except Exception as e:
        logging.warning(f"Engine 1 failed: {e}")

    # محرك 2: Tiklydown المباشر
    try:
        api2 = f"https://api.tiklydown.eu.org/api/download?url={urllib.parse.quote(url)}"
        r2 = requests.get(api2, headers=headers, timeout=6).json()
        video_url = None
        if "video" in r2:
            video_url = r2["video"].get("noWatermark") or r2["video"].get("watermark")
        if video_url:
            v_res = requests.get(video_url, headers=headers, timeout=15)
            with open(output_path, "wb") as f:
                f.write(v_res.content)
            return {"title": r2.get("title", "فيديو تيك توك"), "path": output_path}
    except Exception as e:
        logging.warning(f"Engine 2 failed: {e}")

    # محرك 3: yt-dlp الاحتياطي
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

def fast_search_media(query: str, output_path: str):
    """محرك بحث يوتيوب فائق السرعة لجلب المقاطع المباشرة"""
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
        info = ydl.extract_info(f"ytsearch1:{query}", download=True)
        if "entries" in info and len(info["entries"]) > 0:
            return info["entries"][0]
        return info

def ask_instant_ai(prompt: str) -> str:
    """رد ذكي لحظي ولطيف دون تأخير"""
    p = prompt.lower().strip()
    if any(w in p for w in ["مرحبا", "هلا", "السلام", "أهلاً", "اهلا"]):
        return (
            "يا هلا ومية مرحبا يا غالي نورتني! 🌹✨\n\n"
            "أنا المساعد الذكي الخاص بـ <b>صلوح المانعي</b> 👑\n"
            "أرسل لي أي رابط أو اسم فيلم، أغنية، أو مباراة وسأحضر لك الفيديو فوراً!"
        )
    if any(w in p for w in ["من انت", "من أنت", "مين انت"]):
        return "أنا بوت صلوح المانعي الذكي ⚡️ خادمك وسلاحك السريع لسحب الفيديوهات والأغاني بأعلى سرعة!"

    try:
        url = "https://text.pollinations.ai/" + urllib.parse.quote(
            f"أنت المساعد الذكي لصلوح المانعي، تحدث بكلام لطيف وذكي ومرح ومختصر مع إيموجي: {prompt}"
        )
        res = requests.get(url, timeout=4)
        if res.status_code == 200 and len(res.text.strip()) > 3:
            return res.text.strip()
    except Exception:
        pass

    return f"طلبك بخصوص <b>{prompt}</b> على راسي من فوق يا غالي! جاري تجهيز كل ما يسعدك دائماً 🌸✨"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    msg = (
        f"👑 <b>أهلاً وسهلاً بك يا أغلى الناس {name}!</b>\n"
        f"نورت <b>{BOT_NAME}</b> السريع الخارق ⚡️\n\n"
        "🎬 <b>أنا لا أعطيك مجرد روابط، بل أرسل لك الفيديو مباشرة:</b>\n\n"
        "• 📥 <b>تيك توك وسوشيال ميديا:</b> فقط ألصق الرابط وسأرسل لك المقطع فوراً وبدون علامة مائية!\n"
        "• 🎵 <b>أغاني وصوتيات:</b> اكتب (اغنية كذا) لتصلك مباشرة.\n"
        "• 🍿 <b>أفلام ومسلسلات:</b> اكتب اسم الفيلم أو الملخص وسيصلك الفيديو هنا.\n"
        "• ⚽ <b>مباريات:</b> اطلب أهداف أو ملخص أي مباراة وسأجلبه لك.\n\n"
        "👇 <i>جرب الآن وأرسل رابطك أو طلبك مباشرة:</i>"
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

    # 1. فحص روابط تيك توك وسحبها فوراً وبسرعة فائقة
    is_tiktok = "tiktok.com" in text.lower() or "douyin.com" in text.lower()
    if is_tiktok:
        wait_msg = await update.message.reply_text(
            "⚡️ <b>جاري البحث... صلوح المانعي يبحث لك الآن عن أفضل محتوى ✨</b>", 
            parse_mode="HTML"
        )
        try:
            res = fast_tiktok_download(text, output_path)
            if res and os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                title = res.get("title", "فيديو تيك توك")
                caption = (
                    f"🎬 <b>تفضل الفيديو يا غالي بأعلى جودة وبدون علامة مائية:</b>\n\n"
                    f"📌 <b>{title[:100]}</b>\n\n"
                    f"🌹 مشاهدة ممتعة نتمناها لك عبر: <b>{BOT_NAME}</b>\n"
                    f"💬 للتواصل مع صلوح: <code>+{WHATSAPP_NUMBER}</code>"
                )
                with open(output_path, "rb") as vid:
                    await update.message.reply_video(video=vid, caption=caption, parse_mode="HTML", supports_streaming=True)
                await wait_msg.delete()
                try: os.remove(output_path)
                except Exception: pass
                return
            else:
                await wait_msg.edit_text("⚠️ تعذر تحميل المقطع، تأكد من أن حساب الناشر عام وليس خاصاً.")
        except Exception as e:
            logging.error(f"TikTok error: {e}")
            await wait_msg.edit_text("❌ حدث خطأ أثناء سحب الفيديو، يرجى المحاولة بعد لحظات.")
        finally:
            try: os.remove(output_path)
            except Exception: pass
        return

    # 2. فحص الروابط المباشرة الأخرى (يوتيوب، فيسبوك، إنستغرام)
    if text.startswith("http://") or text.startswith("https://"):
        wait_msg = await update.message.reply_text(
            "⚡️ <b>جاري البحث... صلوح المانعي يبحث لك الآن عن أفضل محتوى ✨</b>", 
            parse_mode="HTML"
        )
        try:
            ydl_opts = {
                "format": "best[ext=mp4][filesize<45M]/best[filesize<45M]/worst[ext=mp4]/worst",
                "outtmpl": output_path,
                "quiet": True,
                "no_warnings": True,
                "nocheckcertificate": True,
                "max_filesize": MAX_FILE_SIZE,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=True)
                title = info.get("title", "فيديو مباشر")
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                caption = (
                    f"🎬 <b>تفضل طلبك يا عزيزي بأعلى جودة:</b>\n\n"
                    f"📌 <b>{title[:100]}</b>\n\n"
                    f"✨ تم التجهيز بواسطة: <b>{BOT_NAME}</b>"
                )
                with open(output_path, "rb") as vid:
                    await update.message.reply_video(video=vid, caption=caption, parse_mode="HTML")
                await wait_msg.delete()
            else:
                await wait_msg.edit_text("⚠️ حجم المقطع يتجاوز 50MB (الحد المسموح في تيليجرام).")
        except Exception:
            await wait_msg.edit_text("❌ تعذر تحميل المقطع، يرجى التأكد من صلاحية الرابط.")
        finally:
            try: os.remove(output_path)
            except Exception: pass
        return

    # 3. كلمات البحث المباشرة عن وسائط (أغاني، أفلام، مباريات)
    media_words = ["اغنيه", "أغنية", "اغنية", "فيلم", "فلم", "افلام", "أفلام", "مسلسل", "اهداف", "أهداف", "مباراة", "مباراه", "ملخص", "شيلة", "شيله"]
    if any(w in text.lower() for w in media_words):
        wait_msg = await update.message.reply_text(
            "⚡️ <b>جاري البحث... صلوح المانعي يبحث لك الآن عن أفضل محتوى ✨</b>", 
            parse_mode="HTML"
        )
        try:
            clean_q = text.replace("قم بتنزيل", "").replace("تنزيل", "").replace("اريد", "").strip()
            info = fast_search_media(clean_q, output_path)
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                title = info.get("title", clean_q)
                caption = (
                    f"🎬 <b>تفضل المقطع الذي طلبته يا غالي:</b>\n\n"
                    f"🍿 <b>{title[:120]}</b>\n\n"
                    f"✨ تم الجلب خصيصاً لك عبر: <b>{BOT_NAME}</b>\n"
                    f"💬 للتواصل: <code>+{WHATSAPP_NUMBER}</code>"
                )
                with open(output_path, "rb") as vid:
                    await update.message.reply_video(video=vid, caption=caption, parse_mode="HTML", supports_streaming=True)
                await wait_msg.delete()
                try: os.remove(output_path)
                except Exception: pass
                return
            else:
                ai_text = ask_instant_ai(clean_q)
                await wait_msg.edit_text(
                    f"⚠️ <b>المقطع المطلوب حجمه يتجاوز 50MB.</b>\n\n{ai_text}", 
                    parse_mode="HTML"
                )
        except Exception:
            ai_text = ask_instant_ai(text)
            await wait_msg.edit_text(ai_text, parse_mode="HTML")
        finally:
            try: os.remove(output_path)
            except Exception: pass
        return

    # 4. الردود والمحادثة السريعة والذكاء الاصطناعي
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
    threading.Thread(target=start_server, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"✅ {BOT_NAME} يعمل الآن بالسرعة الفائقة والتحميل المباشر...")
    app.run_polling()

if __name__ == "__main__":
    main()