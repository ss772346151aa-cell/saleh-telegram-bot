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
BOT_NAME = "بوت صلوح المانعي الشامل ⚡️"
CHANNEL_URL = "https://t.me/saleh_down_bot"
WHATSAPP_NUMBER = "967782953692"
WHATSAPP_URL = f"https://wa.me/{WHATSAPP_NUMBER}"
MAX_FILE_SIZE = 49 * 1024 * 1024  # حد تيليجرام 50MB
# ============================================================

class SimpleHealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Saleh Multi-Search Bot Active 24/7!")

def start_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHealthServer)
    server.serve_forever()

def ask_real_ai(prompt: str) -> str:
    """ذكاء اصطناعي تفاعلي وسريع دون ردود مكررة"""
    p_lower = prompt.lower().strip()
    if any(w in p_lower for w in ["مرحبا", "هلا", "السلام", "أهلاً", "اهلا"]):
        return (
            "يا هلا ومية مرحبا يا غالي! نورتني وأسعدتني بوجودك 🌹✨\n\n"
            "أنا المساعد الذكي الخاص بـ <b>صلوح المانعي</b> 👑\n"
            "جاهز أبحث لك في جميع المنصات عن أي فيلم، أغنية، أو أهداف مباراة وأجلبها لك مباشرة هنا!"
        )
    if any(w in p_lower for w in ["من انت", "من أنت", "مين انت"]):
        return "أنا بوت صلوح المانعي الذكي ⚡️ رفيقك الشامل لجلب الفيديوهات والأغاني وتجاوز الحظر وتلبية كل ما تطلبه فوراً!"

    try:
        url = "https://text.pollinations.ai/" + urllib.parse.quote(
            f"أنت المساعد الذكي لصلوح المانعي. تحدث بلباقة ومرح وقدم معلومات مفيدة وشيقة ومختصرة مع إيموجي باللغة العربية: {prompt}"
        )
        res = requests.get(url, timeout=7)
        if res.status_code == 200 and len(res.text.strip()) > 5:
            return res.text.strip()
    except Exception:
        pass

    return f"طلبك بخصوص <b>{prompt}</b> تحت أمرك! جاري البحث في كافة المصادر المتاحة لخدمتك بأفضل شكل 🎬✨"

def resolve_tiktok_url(short_url: str) -> str:
    """فك الروابط المختصرة من تيك توك لتجاوز الخطأ"""
    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        })
        resp = session.get(short_url, allow_redirects=True, timeout=10)
        return resp.url
    except Exception:
        return short_url

def download_tiktok_smart(url: str, output_path: str):
    """محرك تنزيل تيك توك ذكي متعدد المصادر وبدون علامة مائية"""
    resolved_url = resolve_tiktok_url(url)
    
    # 1. المحاولة الأولى: TikWM API
    try:
        api_url = f"https://www.tikwm.com/api/?url={urllib.parse.quote(resolved_url)}"
        resp = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=12).json()
        if resp.get("code") == 0 and "data" in resp:
            dl_url = resp["data"].get("play") or resp["data"].get("wmplay")
            title = resp["data"].get("title", "فيديو تيك توك بدون علامة مائية")
            if dl_url:
                v_data = requests.get(dl_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30).content
                with open(output_path, "wb") as f:
                    f.write(v_data)
                return {"title": title, "path": output_path, "source": "تيك توك بدون علامة مائية"}
    except Exception as e:
        logging.warning(f"TikWM failed: {e}")

    # 2. المحاولة الثانية: Loover TikTok API التبادلي
    try:
        backup_api = f"https://api.tiklydown.eu.org/api/download?url={urllib.parse.quote(resolved_url)}"
        resp2 = requests.get(backup_api, timeout=12).json()
        video_url = None
        if "video" in resp2:
            video_url = resp2["video"].get("noWatermark") or resp2["video"].get("watermark")
        if video_url:
            v_data = requests.get(video_url, timeout=30).content
            with open(output_path, "wb") as f:
                f.write(v_data)
            return {"title": resp2.get("title", "فيديو تيك توك"), "path": output_path, "source": "تيك توك بديل"}
    except Exception as e:
        logging.warning(f"Tiklydown backup failed: {e}")

    # 3. المحاولة الثالثة: yt-dlp بمحاكاة متصفح الموبايل
    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": output_path,
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(resolved_url, download=True)
        return {"title": info.get("title", "فيديو تيك توك"), "path": output_path, "source": "تيك توك"}

def multi_platform_download(query_or_url: str, output_base: str, is_search=False):
    """محرك تنزيل تبادلي لباقي المنصات"""
    output_file = f"{output_base}.mp4"

    # يوتيوب
    try:
        target = f"ytsearch1:{query_or_url}" if is_search else query_or_url
        ydl_opts = {
            "format": "best[ext=mp4][filesize<45M]/best[filesize<45M]/worst[ext=mp4]/worst",
            "outtmpl": output_file,
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "max_filesize": MAX_FILE_SIZE,
            "extractor_args": {"youtube": {"player_client": ["android", "ios", "mweb"]}},
            "user_agent": "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36",
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(target, download=True)
            if "entries" in info and len(info["entries"]) > 0:
                info = info["entries"][0]
            if os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
                return {"title": info.get("title", query_or_url), "path": output_file, "source": "YouTube"}
    except Exception:
        pass

    # Dailymotion في حال البحث
    if is_search:
        try:
            dm_target = f"dmsearch1:{query_or_url}"
            ydl_opts_dm = {
                "format": "best[ext=mp4][filesize<45M]/best[filesize<45M]/worst",
                "outtmpl": output_file,
                "quiet": True,
                "no_warnings": True,
                "nocheckcertificate": True,
                "max_filesize": MAX_FILE_SIZE,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            }
            with yt_dlp.YoutubeDL(ydl_opts_dm) as ydl:
                info = ydl.extract_info(dm_target, download=True)
                if "entries" in info and len(info["entries"]) > 0:
                    info = info["entries"][0]
                if os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
                    return {"title": info.get("title", query_or_url), "path": output_file, "source": "Dailymotion"}
        except Exception:
            pass

    return None

def fetch_media_meta(query: str):
    """جلب بوستر وتفاصيل العمل من محركات بديلة بدون حظر"""
    try:
        clean_q = query.replace("فيلم", "").replace("فلم", "").replace("مسلسل", "").strip()
        url = f"https://itunes.apple.com/search?term={urllib.parse.quote(clean_q)}&media=movie&limit=1"
        res = requests.get(url, timeout=4).json()
        if res.get("resultCount", 0) > 0:
            item = res["results"][0]
            poster = item.get("artworkUrl100", "").replace("100x100bb.jpg", "600x600bb.jpg")
            return {
                "title": item.get("trackName", query),
                "poster": poster,
                "genre": item.get("primaryGenreName", "عام"),
                "url": item.get("trackViewUrl", "")
            }
    except Exception:
        pass
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    msg = (
        f"👑 <b>أهلاً وسهلاً بك يا {name} في {BOT_NAME}!</b>\n\n"
        "⚡️ <b>نظام التحميل والبحث المباشر:</b>\n\n"
        "• 🎵 <b>تنزيل تيك توك:</b> أرسل أي رابط تيك توك وسأحمله لك فوراً وبدون علامة مائية!\n"
        "• 🎬 <b>الأفلام والمسلسلات:</b> اكتب اسم العمل لجلب ملخصه وفيديوهاته الحية.\n"
        "• ⚽ <b>مباريات كرة القدم:</b> اطلب أي مباراة أو أهداف وسيتم سحب المقطع فوراً.\n"
        "• 📥 <b>منصات الفيديو:</b> أرسل رابط يوتيوب، فيسبوك، أو إنستغرام ليتم التنزيل مباشرة.\n"
        "• 💬 <b>الدردشة الذكية:</b> تحدث معي وسأجيبك بسرعة فائقة ومرح!\n"
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

    is_url = text.startswith("http://") or text.startswith("https://")
    media_words = [
        "اغنيه", "أغنية", "اغنية", "فيلم", "فلم", "افلام", "أفلام", "مسلسل", 
        "اهداف", "أهداف", "مباراة", "مباراه", "ملخص", "فيديو", "مقطع", "شيلة", "شيله", "انمي", "تنزيل"
    ]
    is_media = is_url or any(w in text.lower() for w in media_words)

    if is_media:
        wait_msg = await update.message.reply_text(
            "⚡️ <b>جاري التحميل... صلوح المانعي يسحب لك الفيديو بأعلى جودة الآن ✨</b>", 
            parse_mode="HTML"
        )

        result = None

        # 1. معالجة تيك توك بالمحرك الذكي متعدد الطبقات
        if "tiktok.com" in text or "douyin.com" in text:
            try:
                out_path = f"{output_base}.mp4"
                result = download_tiktok_smart(text, out_path)
            except Exception as e:
                logging.error(f"TikTok smart engine error: {e}")

        # 2. تنزيل باقي الروابط والوسائط
        if not result:
            clean_search = text.replace("قم بتنزيل", "").replace("تنزيل", "").replace("فيديو", "").strip()
            result = multi_platform_download(clean_search, output_base, is_search=(not is_url))

        # 3. إرسال الفيديو كملف مباشر في حال النجاح
        if result and os.path.exists(result["path"]) and os.path.getsize(result["path"]) > 1000:
            title = result.get("title", "فيديو مباشر")
            source_platform = result.get("source", "مواقع التواصل")
            caption = (
                f"🎬 <b>{title[:120]}</b>\n\n"
                f"📌 المنصة: <b>{source_platform}</b>\n"
                f"🍿 تم التحميل بواسطة: <b>{BOT_NAME}</b>\n"
                f"💬 للتواصل: <code>+{WHATSAPP_NUMBER}</code>"
            )
            try:
                with open(result["path"], "rb") as vid:
                    await update.message.reply_video(video=vid, caption=caption, parse_mode="HTML", supports_streaming=True)
                await wait_msg.delete()
                for f in glob.glob(f"{output_base}*"):
                    try: os.remove(f)
                    except Exception: pass
                return
            except Exception as e:
                logging.error(f"Send Video Error: {e}")

        # 4. في حال تعذر التنزيل أو كان الحجم أكثر من 50MB
        meta = fetch_media_meta(text)
        ai_info = ask_real_ai(text)
        search_target = urllib.parse.quote(text + " مشاهدة وتحميل بجودة عالية")
        direct_btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ بدء تشغيل ومشاهدة العمل كاملاً", url=f"https://www.google.com/search?q={search_target}")],
            [InlineKeyboardButton("💬 تواصل مع صلوح المانعي", url=WHATSAPP_URL)]
        ])

        body_text = (
            f"🎬 <b>{text.upper()}</b>\n\n"
            f"{ai_info}\n\n"
            f"⚡️ <b>{BOT_NAME}</b>"
        )

        try:
            if meta and meta.get("poster"):
                await update.message.reply_photo(photo=meta["poster"], caption=body_text[:1024], reply_markup=direct_btn, parse_mode="HTML")
            else:
                await update.message.reply_text(body_text, reply_markup=direct_btn, parse_mode="HTML")
            await wait_msg.delete()
        except Exception:
            await wait_msg.edit_text(body_text, reply_markup=direct_btn)

        for f in glob.glob(f"{output_base}*"):
            try: os.remove(f)
            except Exception: pass
        return

    # المحادثة والذكاء الاصطناعي
    wait_msg = await update.message.reply_text("⚡️ <b>جاري الرد... صلوح المانعي معك الآن ✨</b>", parse_mode="HTML")
    reply = ask_real_ai(text)
    try:
        await wait_msg.edit_text(reply, parse_mode="HTML")
    except Exception:
        await wait_msg.edit_text(reply)

def main():
    threading.Thread(target=start_server, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"✅ {BOT_NAME} يعمل الآن بمحرك تيك توك المحسن وتجاوز الحظر...")
    app.run_polling()

if __name__ == "__main__":
    main()