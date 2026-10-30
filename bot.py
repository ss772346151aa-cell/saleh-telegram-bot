import os
import glob
import logging
import threading
import time
import json
import re
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
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

# ==================== إعدادات وهوية البوت الخارق ====================
BOT_TOKEN = "9157081412:AAF-LegdEK1zKi_ZUCPOarhFXwphmPpqFUE"
BOT_NAME = "بوت صلوح المانعي الإمبراطوري ⚡️👑"
TIKTOK_CHANNEL = "https://www.tiktok.com/@almanay22"
TIKTOK_USER = "@almanay22"
WHATSAPP_NUMBER = "967782953692"
WHATSAPP_URL = f"https://wa.me/{WHATSAPP_NUMBER}"
CHANNEL_URL = "https://t.me/saleh_down_bot"
MAX_FILE_SIZE = 49 * 1024 * 1024
# ====================================================================

# 1. خادم الويب لمنع الإغلاق في Render
class SimpleHealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Bot Active and Running 24/7!")

def start_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHealthServer)
    server.serve_forever()

def auto_clean_temp_files():
    """تنظيف الملفات المؤقتة كل 10 دقائق لتسريع أداء السيرفر"""
    while True:
        time.sleep(600)
        try:
            for f in glob.glob("downloads/*"):
                if os.path.isfile(f):
                    os.remove(f)
        except Exception:
            pass

def extract_url(text: str) -> str:
    pattern = r'(https?://[^\s]+)'
    match = re.search(pattern, text)
    if match:
        return match.group(0).split('?')[0]
    return ""

def download_tiktok_smart(url: str, output_path: str):
    """محرك تيك توك بدون علامة مائية عالي الدقة"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    # TikWM
    try:
        api_url = f"https://www.tikwm.com/api/?url={urllib.parse.quote(url)}"
        res = requests.get(api_url, headers=headers, timeout=10).json()
        if res.get("code") == 0 and "data" in res:
            dl_url = res["data"].get("play") or res["data"].get("wmplay")
            title = res["data"].get("title", "مقطع تيك توك حصري")
            if dl_url.startswith("/"):
                dl_url = "https://www.tikwm.com" + dl_url
            v_data = requests.get(dl_url, headers=headers, timeout=30).content
            with open(output_path, "wb") as f:
                f.write(v_data)
            return {"title": title, "path": output_path}
    except Exception:
        pass

    # Tiklydown
    try:
        api_url2 = f"https://api.tiklydown.eu.org/api/download?url={urllib.parse.quote(url)}"
        res2 = requests.get(api_url2, headers=headers, timeout=10).json()
        if "video" in res2:
            dl_url = res2["video"].get("noWatermark") or res2["video"].get("watermark")
            title = res2.get("title", "مقطع تيك توك حصري")
            v_data = requests.get(dl_url, headers=headers, timeout=30).content
            with open(output_path, "wb") as f:
                f.write(v_data)
            return {"title": title, "path": output_path}
    except Exception:
        pass

    # yt-dlp
    try:
        ydl_opts = {
            "format": "best[ext=mp4]/best",
            "outtmpl": output_path,
            "quiet": True,
            "nocheckcertificate": True,
            "max_filesize": MAX_FILE_SIZE,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return {"title": info.get("title", "مقطع تيك توك"), "path": output_path}
    except Exception:
        pass

    return None

def download_universal_media(target: str, output_path: str, is_audio=False, is_search=False):
    """محرك وسائط ذكي يدعم استخراج MP3 بدقة عالية ومقاطع الفيديو"""
    query = f"ytsearch1:{target}" if is_search else target
    ydl_opts = {
        "outtmpl": output_path,
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "max_filesize": MAX_FILE_SIZE,
        "user_agent": "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36",
    }
    if is_audio:
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    else:
        ydl_opts["format"] = "best[ext=mp4][filesize<45M]/best[filesize<45M]/worst[ext=mp4]/worst"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=True)
        if "entries" in info and len(info["entries"]) > 0:
            return info["entries"][0]
        return info

def get_media_info_fallback(query: str):
    """جلب معلومات وصورة الغلاف في حال تعذر تنزيل الملف كاملاً"""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch1:{query}", download=False)
        if "entries" in info and len(info["entries"]) > 0:
            item = info["entries"][0]
            return {
                "title": item.get("title", query),
                "url": item.get("url") or f"https://www.youtube.com/watch?v={item.get('id')}",
                "thumbnail": item.get("thumbnail") or item.get("thumbnails", [{}])[-1].get("url")
            }
    return None

def ask_super_ai(prompt: str) -> str:
    """أقوى محرك ذكاء اصطناعي تفاعلي وتحليلي سريع"""
    p = prompt.lower().strip()
    if any(w in p for w in ["مرحبا", "هلا", "السلام", "أهلاً", "اهلا"]):
        return (
            "يا هلا ومية مرحبا يا غالي! نورتني وأسعدتني بوجودك 🌹👑\n\n"
            f"أنا المساعد الذكي الخارق التابع لـ <b>صلوح المانعي</b>.\n"
            f"تابع حسابنا المبدع على تيك توك: <b>{TIKTOK_USER}</b>\n\n"
            "✨ اطلب أي شيلة، أغنية، ملخص فيلم، أو رابط تيك توك وسأنفذه فوراً!"
        )

    # استخدام خادم الذكاء الاصطناعي بنموذج OpenAI المتطور
    try:
        sys_prompt = "أنت المساعد الذكي الخارق والمطور لصلوح المانعي. قدم إجابات كاملة، عميقة، وممتعة باللغة العربية مع إيموجي وتنسيق جميل بدون عجز."
        url = "https://text.pollinations.ai/" + urllib.parse.quote(f"{sys_prompt}\nالسؤال: {prompt}")
        res = requests.get(url, timeout=6)
        if res.status_code == 200 and len(res.text.strip()) > 3:
            return res.text.strip()
    except Exception:
        pass

    return f"طلبك بخصوص <b>{prompt}</b> على راسي من فوق! سأبحث لك عنه بدقة عالية دائماً 🌸✨"

# ==================== التفاعل مع الرسائل ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    msg = (
        f"👑 <b>أهلاً وسهلاً بك يا {name} في {BOT_NAME}!</b>\n\n"
        "⚡️ <b>أقوى وأسرع بوت على الإطلاق:</b>\n"
        "• 📥 <b>سحب تيك توك:</b> بدون علامة مائية وفوري.\n"
        "• 🎵 <b>شيلات وأغاني MP3:</b> أرسل اسم أي شيلة وسأرسلها لك صوت فوراً.\n"
        "• 🎬 <b>أفلام ومسلسلات:</b> اكتب اسم الفيلم وسأجلب لك مقطعه وملخصه فوراً.\n"
        "• 🧠 <b>ذكاء اصطناعي فائق:</b> أجب على أي استفسار وتحليل دون عجز.\n\n"
        f"🌟 <b>حسابنا الرسمي على تيك توك لمشاهدة المقاطع الحصرية:</b>\n"
        f"👉 <code>{TIKTOK_CHANNEL}</code>\n\n"
        "👇 <i>أرسل طلبك الآن:</i>"
    )
    inline_kb = [
        [InlineKeyboardButton("🔥 حساب صلوح المانعي على تيك توك 🔥", url=TIKTOK_CHANNEL)],
        [InlineKeyboardButton("💬 واتساب صلوح", url=WHATSAPP_URL), InlineKeyboardButton("📢 قناة التحديثات", url=CHANNEL_URL)]
    ]
    reply_kb = [
        [KeyboardButton("🔥 حساب تيك توك الرسمي"), KeyboardButton("🎬 طلب فيلم سينمائي")],
        [KeyboardButton("🎵 طلب شيلة MP3"), KeyboardButton("⚽ أهداف وملخصات")],
        [KeyboardButton("💬 تواصل مع المطور صلوح")]
    ]
    await update.message.reply_text(
        msg, 
        reply_markup=InlineKeyboardMarkup(inline_kb), 
        parse_mode="HTML"
    )
    await update.message.reply_text(
        "⚡️ أزرار التحكم السريع مدمجة في شاشتك دائماً:",
        reply_markup=ReplyKeyboardMarkup(reply_kb, resize_keyboard=True)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_id = update.effective_chat.id
    msg_id = update.message.message_id
    output_base = f"downloads/{chat_id}_{msg_id}"
    os.makedirs("downloads", exist_ok=True)

    # أزرار الكيبورد السريع
    if text == "🔥 حساب تيك توك الرسمي":
        msg = (
            f"🎬 <b>الحساب الرسمي لصلوح المانعي على تيك توك:</b>\n\n"
            f"شاهد أقوى المقاطع والشروحات الحصرية 🌟\n"
            f"🔗 {TIKTOK_CHANNEL}"
        )
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("✨ فتح حساب التيك توك مباشرة ✨", url=TIKTOK_CHANNEL)]])
        await update.message.reply_text(msg, reply_markup=btn, parse_mode="HTML")
        return

    if text == "💬 تواصل مع المطور صلوح":
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("💬 مراسلة صلوح على واتساب", url=WHATSAPP_URL)]])
        await update.message.reply_text("👑 يسعدنا تواصلك المباشر مع المطور صلوح المانعي:", reply_markup=btn)
        return

    # 1. روابط تيك توك المباشرة
    url_found = extract_url(text)
    if url_found and ("tiktok.com" in url_found.lower() or "douyin.com" in url_found.lower()):
        wait_msg = await update.message.reply_text("⚡️ <b>جاري سحب المقطع بأعلى دقة وبدون علامة مائية... ✨</b>", parse_mode="HTML")
        out_vid = f"{output_base}.mp4"
        data = download_tiktok_smart(url_found, out_vid)
        if data and os.path.exists(out_vid) and os.path.getsize(out_vid) > 1000:
            caption = (
                f"🎬 <b>تفضل الفيديو بدون علامة مائية يا غالي:</b>\n\n"
                f"📌 <b>{data['title'][:100]}</b>\n\n"
                f"✨ بواسطة: <b>{BOT_NAME}</b>\n"
                f"🔥 للمزيد تابعنا: <b>{TIKTOK_USER}</b>"
            )
            btn = InlineKeyboardMarkup([[InlineKeyboardButton("❤️ تابع حساب صلوح على تيك توك", url=TIKTOK_CHANNEL)]])
            with open(out_vid, "rb") as vid:
                await update.message.reply_video(video=vid, caption=caption, reply_markup=btn, parse_mode="HTML")
            await wait_msg.delete()
            try: os.remove(out_vid)
            except Exception: pass
            return
        else:
            await wait_msg.edit_text("❌ تعذر تحميل المقطع، تأكد أن الفيديو ليس خاصاً أو محذوفاً.")
            try: os.remove(out_vid)
            except Exception: pass
            return

    # 2. طلبات الشيلات والأغاني بصيغة MP3 صوت فوراً
    audio_keywords = ["شيله", "شيلة", "شيلات", "اغنيه", "اغنية", "أغنية", "صوت", "انشوده", "أنشودة", "زوامل", "زامل"]
    if any(k in text.lower() for k in audio_keywords):
        wait_msg = await update.message.reply_text("🎵 <b>جاري سحب الصوت بأعلى نقاوة MP3 فوراً... ✨</b>", parse_mode="HTML")
        clean_q = text
        for k in ["اريد", "تنزيل", "شيله", "شيلة", "اغنيه", "أغنية", "صوت", "قم بتحميل"]:
            clean_q = clean_q.replace(k, "")
        clean_q = clean_q.strip() or text

        out_audio = f"{output_base}.mp3"
        try:
            info = download_universal_media(clean_q, out_audio, is_audio=True, is_search=True)
            # فحص وجود الملف بصيغة mp3 أو أي صيغة صوتية
            actual_file = out_audio if os.path.exists(out_audio) else (glob.glob(f"{output_base}.*") or [None])[0]
            
            if actual_file and os.path.exists(actual_file) and os.path.getsize(actual_file) > 1000:
                title = info.get("title", clean_q) if info else clean_q
                caption = (
                    f"🎵 <b>تم سحب الصوت بنجاح بنقاوة كاملة:</b>\n\n"
                    f"📌 <b>{title[:100]}</b>\n\n"
                    f"✨ تم بواسطة: <b>{BOT_NAME}</b>\n"
                    f"🔥 تابع حسابنا: <b>{TIKTOK_USER}</b>"
                )
                btn = InlineKeyboardMarkup([[InlineKeyboardButton("❤️ حساب صلوح على تيك توك", url=TIKTOK_CHANNEL)]])
                with open(actual_file, "rb") as aud:
                    await update.message.reply_audio(audio=aud, caption=caption, reply_markup=btn, parse_mode="HTML")
                await wait_msg.delete()
                try: os.remove(actual_file)
                except Exception: pass
                return
        except Exception:
            pass

    # 3. طلبات الأفلام، المسلسلات، المباريات والفيديوهات
    video_keywords = ["فيلم", "فلم", "افلام", "أفلام", "مسلسل", "اهداف", "أهداف", "مباراة", "مباراه", "ملخص"]
    if any(k in text.lower() for k in video_keywords):
        wait_msg = await update.message.reply_text("🎬 <b>جاري جلب المقطع والملخص بأفضل دقة فوراً ✨</b>", parse_mode="HTML")
        clean_q = text
        for k in ["اريد", "تنزيل", "فيلم", "فلم", "مشاهدة"]:
            clean_q = clean_q.replace(k, "")
        clean_q = clean_q.strip() or text

        out_vid = f"{output_base}.mp4"
        try:
            info = download_universal_media(f"{clean_q} ملخص كامل", out_vid, is_audio=False, is_search=True)
            if os.path.exists(out_vid) and os.path.getsize(out_vid) > 1000:
                caption = (
                    f"🎬 <b>تفضل مقطع وملخص العمل المطلوب:</b>\n\n"
                    f"📌 <b>{info.get('title', clean_q)[:100]}</b>\n\n"
                    f"✨ تم الجلب بواسطة: <b>{BOT_NAME}</b>\n"
                    f"🔥 تابع حسابنا: <b>{TIKTOK_USER}</b>"
                )
                btn = InlineKeyboardMarkup([[InlineKeyboardButton("❤️ تابع حساب صلوح على تيك توك", url=TIKTOK_CHANNEL)]])
                with open(out_vid, "rb") as vid:
                    await update.message.reply_video(video=vid, caption=caption, reply_markup=btn, parse_mode="HTML")
                await wait_msg.delete()
                try: os.remove(out_vid)
                except Exception: pass
                return
        except Exception:
            pass

        # إذا كان حجم الفيلم أكبر من 50MB، يتم جلب البوستر والملخص الذكي ورابط المشاهدة دون عجز
        fb = get_media_info_fallback(clean_q)
        ai_review = ask_super_ai(f"قدم ملخص سينمائي رائع ومشوق لـ {clean_q} مع أهم الأحداث وتقييمه")
        if fb and fb.get("thumbnail"):
            caption = (
                f"🎬 <b>معلومات وملخص: {fb['title'][:100]}</b>\n\n"
                f"{ai_review[:700]}\n\n"
                f"🔗 <b>رابط المشاهدة المباشر:</b>\n{fb['url']}\n\n"
                f"✨ بواسطة: <b>{BOT_NAME}</b>"
            )
            btn = InlineKeyboardMarkup([
                [InlineKeyboardButton("🍿 مشاهدة المقطع مباشرة", url=fb['url'])],
                [InlineKeyboardButton("🔥 حساب صلوح على تيك توك", url=TIKTOK_CHANNEL)]
            ])
            await update.message.reply_photo(photo=fb["thumbnail"], caption=caption, reply_markup=btn, parse_mode="HTML")
            await wait_msg.delete()
            return

    # 4. الروابط المباشرة الأخرى (إنستغرام، يوتيوب، فيسبوك)
    if url_found:
        wait_msg = await update.message.reply_text("⚡️ <b>جاري سحب الرابط بأعلى جودة... ✨</b>", parse_mode="HTML")
        out_vid = f"{output_base}.mp4"
        try:
            info = download_universal_media(url_found, out_vid, is_audio=False, is_search=False)
            if os.path.exists(out_vid) and os.path.getsize(out_vid) > 1000:
                caption = (
                    f"🎬 <b>{info.get('title', 'فيديو')[:100]}</b>\n\n"
                    f"✨ تم التحميل عبر: <b>{BOT_NAME}</b>\n"
                    f"🔥 تابع حسابنا: <b>{TIKTOK_USER}</b>"
                )
                btn = InlineKeyboardMarkup([[InlineKeyboardButton("❤️ تابع صلوح على تيك توك", url=TIKTOK_CHANNEL)]])
                with open(out_vid, "rb") as vid:
                    await update.message.reply_video(video=vid, caption=caption, reply_markup=btn, parse_mode="HTML")
                await wait_msg.delete()
            else:
                await wait_msg.edit_text("⚠️ حجم المقطع يتجاوز حد تيليجرام (50MB).")
        except Exception:
            await wait_msg.edit_text("❌ تعذر تحميل هذا الرابط، تأكد أنه متاح للعامة.")
        finally:
            try: os.remove(out_vid)
            except Exception: pass
        return

    # 5. الذكاء الاصطناعي الأقوى للإجابة والتحليل دون أي عجز
    wait_msg = await update.message.reply_text("⚡️ <b>صلوح المانعي يجهز لك الإجابة الدقيقة فوراً... ✨</b>", parse_mode="HTML")
    reply = ask_super_ai(text)
    try:
        await wait_msg.edit_text(reply, parse_mode="HTML")
    except Exception:
        await wait_msg.edit_text(reply)

def main():
    # خادم الويب
    threading.Thread(target=start_server, daemon=True).start()
    # خيط تنظيف الذاكرة
    threading.Thread(target=auto_clean_temp_files, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"✅ {BOT_NAME} انطلق بأقوى ذكاء اصطناعي وسحب فوري...")
    app.run_polling()

if __name__ == "__main__":
    main()
