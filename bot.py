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

class SimpleHealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Bot Active 24/7!")

def start_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHealthServer)
    server.serve_forever()

def extract_tiktok_url_from_text(text: str) -> str:
    """استخراج رابط التيك توك حتى لو كانت الرسالة تحتوي على نصوص إضافية"""
    pattern = r'(https?://(?:vt\.tiktok\.com|vm\.tiktok\.com|www\.tiktok\.com|tiktok\.com)/[^\s]+)'
    match = re.search(pattern, text)
    if match:
        return match.group(0).split('?')[0]
    return ""

def get_tiktok_direct_data(raw_url: str):
    """
    استخراج رابط الفيديو المباشر من تيك توك بدون تحميل محلي
    مماثل تماماً لأقوى بوتات تيليجرام
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        "Accept": "application/json"
    }

    # 1. المصدر الأول: واجهة TikWM المباشرة
    try:
        api_url = f"https://www.tikwm.com/api/?url={urllib.parse.quote(raw_url)}"
        r = requests.get(api_url, headers=headers, timeout=8).json()
        if r.get("code") == 0 and "data" in r:
            video_url = r["data"].get("play") or r["data"].get("wmplay")
            title = r["data"].get("title", "فيديو تيك توك")
            if video_url:
                # إذا كان الرابط يبدأ بـ / يكون نسبي
                if video_url.startswith("/"):
                    video_url = "https://www.tikwm.com" + video_url
                return {"url": video_url, "title": title}
    except Exception as e:
        logging.warning(f"TikWM direct error: {e}")

    # 2. المصدر الثاني: واجهة Tiklydown السريعة
    try:
        api_url2 = f"https://api.tiklydown.eu.org/api/download?url={urllib.parse.quote(raw_url)}"
        r2 = requests.get(api_url2, headers=headers, timeout=8).json()
        if "video" in r2:
            v_url = r2["video"].get("noWatermark") or r2["video"].get("watermark")
            if v_url:
                return {"url": v_url, "title": r2.get("title", "فيديو تيك توك")}
    except Exception as e:
        logging.warning(f"Tiklydown direct error: {e}")

    return None

def ask_instant_ai(prompt: str) -> str:
    """محرك ردود سريع ومرح"""
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

    return f"طلبك بخصوص <b>{prompt}</b> في البال وجاري خدمتك دائماً بأفضل شكل 🌸✨"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    msg = (
        f"👑 <b>أهلاً وسهلاً بك يا {name} في {BOT_NAME}!</b>\n\n"
        "⚡️ <b>أسرع بوت لتحميل مقاطع التيك توك والميديا المباشرة:</b>\n\n"
        "• 📥 <b>تيك توك:</b> فقط أرسل رابط الفيديو (مثل <code>vt.tiktok.com</code>) وسيصلك المقطع فوراً وبدون علامة مائية كما في أكبر البوتات!\n"
        "• 🎵 <b>أغاني وأفلام ومباريات:</b> اكتب اسم المقطع وسأجلبه لك.\n\n"
        "👇 <i>أرسل رابط تيك توك الآن وجربه مباشرة:</i>"
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
    output_base = f"downloads/{chat_id}_{msg_id}"
    os.makedirs("downloads", exist_ok=True)

    # ================= 1. فك روابط تيك توك وإرسالها فوراً =================
    tiktok_url = extract_tiktok_url_from_text(text)
    if tiktok_url:
        wait_msg = await update.message.reply_text(
            "⚡️ <b>جاري البحث... صلوح المانعي يجلب لك المقطع الآن مباشرة ✨</b>", 
            parse_mode="HTML"
        )
        try:
            # استخراج رابط البث المباشر
            data = get_tiktok_direct_data(tiktok_url)
            
            if data and data.get("url"):
                caption_text = (
                    f"🎬 <b>تفضل الفيديو بدون علامة مائية يا غالي:</b>\n\n"
                    f"📌 <b>{data['title'][:100]}</b>\n\n"
                    f"✨ تم التحميل بواسطة: <b>{BOT_NAME}</b>"
                )
                # إرسال عبر الرابط المباشر (طريقة البوتات السريعة بدون تخزين)
                try:
                    await update.message.reply_video(
                        video=data["url"],
                        caption=caption_text,
                        parse_mode="HTML",
                        supports_streaming=True
                    )
                    await wait_msg.delete()
                    return
                except Exception as send_err:
                    logging.warning(f"Telegram URL stream failed, falling back to stream download: {send_err}")

                # إذا رفض تيليجرام الرابط المباشر، يتم تنزيله بحجم خفيف وتمريره
                out_file = f"{output_base}.mp4"
                v_res = requests.get(data["url"], headers={"User-Agent": "Mozilla/5.0"}, timeout=25)
                with open(out_file, "wb") as f:
                    f.write(v_res.content)
                
                with open(out_file, "rb") as vid:
                    await update.message.reply_video(
                        video=vid,
                        caption=caption_text,
                        parse_mode="HTML",
                        supports_streaming=True
                    )
                await wait_msg.delete()
                try: os.remove(out_file)
                except Exception: pass
                return
            else:
                await wait_msg.edit_text("❌ تعذر العثور على الفيديو، تأكد أن الفيديو ليس خاصاً أو محذوفاً.")
        except Exception as e:
            logging.error(f"TikTok process error: {e}")
            await wait_msg.edit_text("❌ حدث خطأ أثناء جلب الفيديو، يرجى إعادة المحاولة.")
        finally:
            for f in glob.glob(f"{output_base}*"):
                try: os.remove(f)
                except Exception: pass
        return

    # ================= 2. الروابط العامة (يوتيوب، فيسبوك، إنستغرام) =================
    if text.startswith("http://") or text.startswith("https://"):
        wait_msg = await update.message.reply_text(
            "⚡️ <b>جاري البحث... صلوح المانعي يجلب لك المقطع الآن مباشرة ✨</b>", 
            parse_mode="HTML"
        )
        out_file = f"{output_base}.mp4"
        try:
            ydl_opts = {
                "format": "best[ext=mp4][filesize<45M]/best[filesize<45M]/worst[ext=mp4]/worst",
                "outtmpl": out_file,
                "quiet": True,
                "no_warnings": True,
                "nocheckcertificate": True,
                "max_filesize": MAX_FILE_SIZE,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=True)
                title = info.get("title", "فيديو مباشر")
            
            if os.path.exists(out_file) and os.path.getsize(out_file) > 1000:
                with open(out_file, "rb") as vid:
                    await update.message.reply_video(
                        video=vid, 
                        caption=f"🎬 <b>{title[:100]}</b>\n\n✨ بواسطة: <b>{BOT_NAME}</b>", 
                        parse_mode="HTML"
                    )
                await wait_msg.delete()
            else:
                await wait_msg.edit_text("⚠️ حجم المقطع يتجاوز 50MB (الحد المسموح به).")
        except Exception:
            await wait_msg.edit_text("❌ تعذر تحميل المقطع، تأكد من صلاحية الرابط.")
        finally:
            for f in glob.glob(f"{output_base}*"):
                try: os.remove(f)
                except Exception: pass
        return

    # ================= 3. الكلمات المفتاحية والبحث السريع =================
    media_words = ["اغنيه", "أغنية", "اغنية", "فيلم", "فلم", "افلام", "أفلام", "مسلسل", "اهداف", "أهداف", "مباراة", "مباراه", "ملخص"]
    if any(w in text.lower() for w in media_words):
        wait_msg = await update.message.reply_text(
            "⚡️ <b>جاري البحث... صلوح المانعي يبحث لك الآن عن أفضل محتوى ✨</b>", 
            parse_mode="HTML"
        )
        out_file = f"{output_base}.mp4"
        try:
            clean_q = text.replace("قم بتنزيل", "").replace("تنزيل", "").replace("اريد", "").strip()
            ydl_opts = {
                "format": "best[ext=mp4][filesize<45M]/best[filesize<45M]/worst[ext=mp4]/worst",
                "outtmpl": out_file,
                "quiet": True,
                "no_warnings": True,
                "nocheckcertificate": True,
                "max_filesize": MAX_FILE_SIZE,
                "extractor_args": {"youtube": {"player_client": ["android", "ios"]}},
                "user_agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36",
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{clean_q}", download=True)
                if "entries" in info and len(info["entries"]) > 0:
                    info = info["entries"][0]
                title = info.get("title", clean_q)

            if os.path.exists(out_file) and os.path.getsize(out_file) > 1000:
                with open(out_file, "rb") as vid:
                    await update.message.reply_video(
                        video=vid,
                        caption=f"🎬 <b>{title[:120]}</b>\n\n🍿 تم الجلب عبر: <b>{BOT_NAME}</b>",
                        parse_mode="HTML"
                    )
                await wait_msg.delete()
                for f in glob.glob(f"{output_base}*"):
                    try: os.remove(f)
                    except Exception: pass
                return
        except Exception:
            pass

    # ================= 4. الردود والدردشة الذكية =================
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

    print(f"✅ {BOT_NAME} يعمل الآن بنفس محرك تيك توك السريع والمباشر...")
    app.run_polling()

if __name__ == "__main__":
    main()