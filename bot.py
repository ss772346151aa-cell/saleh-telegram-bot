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
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import yt_dlp

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)

# ==================== إعدادات وهوية البوت الإمبراطوري ====================
BOT_TOKEN = "9157081412:AAF-LegdEK1zKi_ZUCPOarhFXwphmPpqFUE"
BOT_NAME = "بوت صلوح المانعي الإمبراطوري ⚡️👑"
TIKTOK_CHANNEL = "https://www.tiktok.com/@almanay22"
TIKTOK_USER = "@almanay22"
WHATSAPP_NUMBER = "967782953692"
WHATSAPP_URL = f"https://wa.me/{WHATSAPP_NUMBER}"
CHANNEL_URL = "https://t.me/saleh_down_bot"
MAX_FILE_SIZE = 49 * 1024 * 1024  # حد تيليجرام 50MB
# =======================================================================

# 1. خادم الويب المصغر لإبقاء Render في وضع النشاط 24/7
class SimpleHealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Saleh Ultimate Imperial Bot is Online 24/7!")

def start_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHealthServer)
    server.serve_forever()

def auto_clean_temp_files():
    """تنظيف المخلفات المؤقتة كل 15 دقيقة للحفاظ على سرعة السيرفر"""
    while True:
        time.sleep(900)
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
    """محرك تيك توك فائق التطور لسحب الفيديو بدون علامة مائية"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

    # المحاولة 1: TikWM المباشر
    try:
        api_url = f"https://www.tikwm.com/api/?url={urllib.parse.quote(url)}"
        res = requests.get(api_url, headers=headers, timeout=10).json()
        if res.get("code") == 0 and "data" in res:
            dl_url = res["data"].get("play") or res["data"].get("wmplay")
            music_url = res["data"].get("music")
            title = res["data"].get("title", "مقطع تيك توك حصري")
            if dl_url.startswith("/"):
                dl_url = "https://www.tikwm.com" + dl_url
            v_data = requests.get(dl_url, headers=headers, timeout=30).content
            with open(output_path, "wb") as f:
                f.write(v_data)
            return {"title": title, "path": output_path, "music": music_url}
    except Exception as e:
        logging.warning(f"TikWM engine issue: {e}")

    # المحاولة 2: Loover Tiklydown
    try:
        api_url2 = f"https://api.tiklydown.eu.org/api/download?url={urllib.parse.quote(url)}"
        res2 = requests.get(api_url2, headers=headers, timeout=10).json()
        if "video" in res2:
            dl_url = res2["video"].get("noWatermark") or res2["video"].get("watermark")
            title = res2.get("title", "مقطع تيك توك حصري")
            music_url = res2.get("music", {}).get("playUrl")
            v_data = requests.get(dl_url, headers=headers, timeout=30).content
            with open(output_path, "wb") as f:
                f.write(v_data)
            return {"title": title, "path": output_path, "music": music_url}
    except Exception as e:
        logging.warning(f"Tiklydown engine issue: {e}")

    # المحاولة 3: yt-dlp الاحتياطي
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
            return {"title": info.get("title", "مقطع تيك توك"), "path": output_path, "music": None}
    except Exception as e:
        logging.error(f"yt-dlp engine issue: {e}")

    return None

def download_universal_media(target: str, output_path: str, is_audio=False, is_search=False):
    """تنزيل وتحويل الوسائط الشامل من يوتيوب، إنستغرام، فيسبوك، وX"""
    query = f"ytsearch1:{target}" if is_search else target
    ydl_opts = {
        "outtmpl": output_path,
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "max_filesize": MAX_FILE_SIZE,
        "extractor_args": {
            "youtube": {"player_client": ["android", "ios", "mweb"]}
        },
        "user_agent": "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36",
    }
    if is_audio:
        ydl_opts["format"] = "bestaudio/best"
    else:
        ydl_opts["format"] = "best[ext=mp4][filesize<45M]/best[filesize<45M]/worst[ext=mp4]/worst"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=True)
        if "entries" in info and len(info["entries"]) > 0:
            return info["entries"][0]
        return info

def ask_imperial_ai(prompt: str) -> str:
    """محرك ذكاء اصطناعي تفاعلي سريع ومبتكر"""
    p = prompt.lower().strip()
    if any(w in p for w in ["مرحبا", "هلا", "السلام", "أهلاً", "اهلا"]):
        return (
            "يا هلا ومية مرحبا يا غالي! نورت البوت الإمبراطوري 🌹👑\n\n"
            f"أنا المساعد الذكي الخارق لـ <b>صلوح المانعي</b>.\n"
            f"تابع حسابنا المعتمد على تيك توك للمزيد من الإبداع: <b>{TIKTOK_USER}</b>\n\n"
            "✨ فقط أرسل أي رابط (تيك توك، ريلز، يوتيوب) أو اكتب اسم أي فيلم أو أغنية، وسأتولى الباقي فوراً!"
        )
    if any(w in p for w in ["من انت", "من أنت", "مين انت", "عرف عن نفسك"]):
        return (
            f"👑 <b>أنا {BOT_NAME}</b>\n\n"
            "المنصة الأقوى على تيليجرام لتحميل مقاطع الوسائط، استخراج الصوتيات، تحليل الأعمال السينمائية، ومتابعة الرياضة ⚡️\n"
            f"تحت إدارة وتطوير: <b>صلوح المانعي</b>."
        )

    try:
        url = "https://text.pollinations.ai/" + urllib.parse.quote(
            f"أنت المساعد الذكي لصلوح المانعي، أجب باحترافية، وود ومرح، ونسق الإجابة بنقاط مريحة وإيموجي باللغة العربية: {prompt}"
        )
        res = requests.get(url, timeout=4)
        if res.status_code == 200 and len(res.text.strip()) > 3:
            return res.text.strip()
    except Exception:
        pass

    return f"طلبك بخصوص <b>{prompt}</b> في صميم اهتمامنا يا غالي! جاري توفير أفضل نتيجة تليق بك دائماً 🌸✨"

# ==================== الأوامر والتعامل مع الرسائل ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    msg = (
        f"👑 <b>أهلاً وسهلاً بك يا أغلى الناس {name}!</b>\n"
        f"في <b>{BOT_NAME}</b> — المنظومة الترفيهية والتقنية المتكاملة ⚡️\n\n"
        "🚀 <b>قدرات البوت الخارقة تحت أمرك:</b>\n"
        "• 📥 <b>سحب تيك توك:</b> بدون علامة مائية وفائق السرعة.\n"
        "• 🎥 <b>ريلز وإنستغرام وفيسبوك:</b> تنزيل مباشر بنقاوة كاملة.\n"
        "• 🎵 <b>صوتيات MP3 وشيلات:</b> تحويل فوري لأي مقطع إلى صوت نقي.\n"
        "• 🍿 <b>أفلام وملخصات كروية:</b> بحث ذكي وعرض حي بالمحادثة.\n\n"
        f"🌟 <b>حسابنا الرسمي على تيك توك لمتابعة كل جديد:</b>\n"
        f"👉 <code>{TIKTOK_CHANNEL}</code>\n\n"
        "👇 <i>استخدم القائمة السريعة أدناه أو أرسل رابطك فوراً:</i>"
    )
    inline_kb = [
        [InlineKeyboardButton("🔥 حساب صلوح المانعي على تيك توك 🔥", url=TIKTOK_CHANNEL)],
        [InlineKeyboardButton("💬 واتساب صلوح", url=WHATSAPP_URL), InlineKeyboardButton("📢 قناة التحديثات", url=CHANNEL_URL)]
    ]
    reply_kb = [
        [KeyboardButton("🔥 حساب تيك توك الرسمي"), KeyboardButton("🎬 اقتراح فيلم سينمائي")],
        [KeyboardButton("🎵 استخراج شيلة / أغنية"), KeyboardButton("⚽ ملخص مباريات اليوم")],
        [KeyboardButton("💬 تواصل مع المطور صلوح"), KeyboardButton("💡 كيف يعمل البوت؟")]
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

    # معالجة تفاعلية لأزرار الكيبورد السريع
    if text == "🔥 حساب تيك توك الرسمي":
        msg = (
            f"🎬 <b>الحساب الرسمي لصلوح المانعي على تيك توك:</b>\n\n"
            f"المحتوى الأقوى والحصري أولاً بأول 🌟\n"
            f"🔗 {TIKTOK_CHANNEL}"
        )
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("✨ فتح حساب التيك توك مباشرة ✨", url=TIKTOK_CHANNEL)]])
        await update.message.reply_text(msg, reply_markup=btn, parse_mode="HTML")
        return

    if text == "💬 تواصل مع المطور صلوح":
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("💬 مراسلة صلوح على واتساب", url=WHATSAPP_URL)]])
        await update.message.reply_text("👑 يسعدنا تواصلك مع المطور صلوح المانعي لجميع الاستفسارات والخدمات:", reply_markup=btn)
        return

    if text == "💡 كيف يعمل البوت؟":
        msg = (
            "🛠 <b>طريقة استخدام البوت بأبسط شكل:</b>\n\n"
            "1️⃣ <b>تنزيل الفيديوهات:</b> فقط انسخ أي رابط من تيك توك أو إنستغرام أو يوتيوب وألصقه هنا مباشرة.\n"
            "2️⃣ <b>الأفلام والمباريات:</b> اكتب اسم الفيلم أو المباراة مثل (اهداف الكلاسيكو) وسيتم سحب المقطع فوراً.\n"
            "3️⃣ <b>الأغاني والصوتيات:</b> اكتب (اغنية كذا) أو (شيلة كذا) لجلب الملف الصوتي.\n"
            "4️⃣ <b>الدردشة:</b> اسأل البوت عن أي شيء وسيجيبك بذكاء متقدم!"
        )
        await update.message.reply_text(msg, parse_mode="HTML")
        return

    if text == "🎬 اقتراح فيلم سينمائي":
        reply = ask_imperial_ai("اقترح لي فيلم سينمائي أسطوري عالي التقييم مع نبذة مشوقة عنه بدون حرق")
        await update.message.reply_text(reply, parse_mode="HTML")
        return

    if text == "⚽ ملخص مباريات اليوم":
        reply = ask_imperial_ai("ما هي أهم مواعيد وقمم مباريات اليوم في الدوريات الأوروبية والعربية والعالمية؟")
        await update.message.reply_text(reply, parse_mode="HTML")
        return

    # 1. روابط تيك توك وسحبها بدون علامة مائية
    url_found = extract_url(text)
    if url_found and ("tiktok.com" in url_found.lower() or "douyin.com" in url_found.lower()):
        wait_msg = await update.message.reply_text(
            "⚡️ <b>جاري سحب المقطع بأعلى دقة وبدون علامة مائية... ✨</b>", 
            parse_mode="HTML"
        )
        out_vid = f"{output_base}.mp4"
        data = download_tiktok_smart(url_found, out_vid)
        if data and os.path.exists(out_vid) and os.path.getsize(out_vid) > 1000:
            caption = (
                f"🎬 <b>تفضل الفيديو بدون علامة مائية يا غالي:</b>\n\n"
                f"📌 <b>{data['title'][:100]}</b>\n\n"
                f"✨ بواسطة: <b>{BOT_NAME}</b>\n"
                f"🔥 تابع حسابنا: <b>{TIKTOK_USER}</b>"
            )
            btn = InlineKeyboardMarkup([
                [InlineKeyboardButton("❤️ تابع حساب صلوح على تيك توك", url=TIKTOK_CHANNEL)],
                [InlineKeyboardButton("💬 واتساب صلوح", url=WHATSAPP_URL)]
            ])
            with open(out_vid, "rb") as vid:
                await update.message.reply_video(video=vid, caption=caption, reply_markup=btn, parse_mode="HTML", supports_streaming=True)
            await wait_msg.delete()
            try: os.remove(out_vid)
            except Exception: pass
            return
        else:
            await wait_msg.edit_text("❌ تعذر تحميل المقطع، تأكد أن الفيديو عام وغير محذوف.")
            try: os.remove(out_vid)
            except Exception: pass
            return

    # 2. روابط المنصات الأخرى (إنستغرام، يوتيوب، فيسبوك، X)
    if url_found:
        wait_msg = await update.message.reply_text(
            "⚡️ <b>جاري التحميل والتجهيز لك بأفضل نقاوة فوراً ✨</b>", 
            parse_mode="HTML"
        )
        out_vid = f"{output_base}.mp4"
        try:
            info = download_universal_media(url_found, out_vid, is_audio=False, is_search=False)
            if os.path.exists(out_vid) and os.path.getsize(out_vid) > 1000:
                caption = (
                    f"🎬 <b>{info.get('title', 'فيديو بجودة عالية')[:100]}</b>\n\n"
                    f"✨ تم الجلب عبر: <b>{BOT_NAME}</b>\n"
                    f"🔥 تابع حسابنا على تيك توك: <b>{TIKTOK_USER}</b>"
                )
                btn = InlineKeyboardMarkup([[InlineKeyboardButton("❤️ تابع صلوح على تيك توك", url=TIKTOK_CHANNEL)]])
                with open(out_vid, "rb") as vid:
                    await update.message.reply_video(video=vid, caption=caption, reply_markup=btn, parse_mode="HTML")
                await wait_msg.delete()
            else:
                await wait_msg.edit_text("⚠️ حجم المقطع يتجاوز 50MB (الحد الأقصى للإرسال المباشر).")
        except Exception:
            await wait_msg.edit_text("❌ تعذر تحميل الرابط، تأكد من أن الرابط متاح للعامة.")
        finally:
            try: os.remove(out_vid)
            except Exception: pass
        return

    # 3. طلبات البحث الصريحة (أغاني، شيلات، أفلام، أهداف)
    media_words = ["اغنيه", "أغنية", "فيلم", "فلم", "افلام", "أفلام", "مسلسل", "اهداف", "أهداف", "مباراة", "مباراه", "ملخص", "شيلة", "شيله"]
    if any(w in text.lower() for w in media_words):
        wait_msg = await update.message.reply_text(
            "⚡️ <b>جاري البحث وسحب أفضل مقطع متوفر لك فوراً ✨</b>", 
            parse_mode="HTML"
        )
        clean_q = text.replace("قم بتنزيل", "").replace("تنزيل", "").replace("اريد", "").strip()
        out_vid = f"{output_base}.mp4"
        try:
            is_audio_req = any(w in text.lower() for w in ["اغنيه", "أغنية", "شيلة", "شيله", "صوت"])
            info = download_universal_media(clean_q, out_vid, is_audio=is_audio_req, is_search=True)
            if os.path.exists(out_vid) and os.path.getsize(out_vid) > 1000:
                caption = (
                    f"🎬 <b>{info.get('title', clean_q)[:100]}</b>\n\n"
                    f"🍿 تم الجلب خصيصاً عبر: <b>{BOT_NAME}</b>\n"
                    f"🔥 تابعنا على تيك توك: <b>{TIKTOK_USER}</b>"
                )
                btn = InlineKeyboardMarkup([[InlineKeyboardButton("❤️ تابع حساب صلوح على تيك توك", url=TIKTOK_CHANNEL)]])
                
                if is_audio_req:
                    with open(out_vid, "rb") as aud:
                        await update.message.reply_audio(audio=aud, caption=caption, reply_markup=btn, parse_mode="HTML")
                else:
                    with open(out_vid, "rb") as vid:
                        await update.message.reply_video(video=vid, caption=caption, reply_markup=btn, parse_mode="HTML")
                await wait_msg.delete()
                try: os.remove(out_vid)
                except Exception: pass
                return
            else:
                ai_text = ask_imperial_ai(clean_q)
                await wait_msg.edit_text(f"⚠️ <b>المقطع يتجاوز حد تيليجرام (50MB).</b>\n\n{ai_text}", parse_mode="HTML")
        except Exception:
            ai_text = ask_imperial_ai(text)
            await wait_msg.edit_text(ai_text, parse_mode="HTML")
        finally:
            try: os.remove(out_vid)
            except Exception: pass
        return

    # 4. المحادثة والذكاء الاصطناعي العام
    wait_msg = await update.message.reply_text(
        "⚡️ <b>صلوح المانعي يبحث لك الآن عن أفضل محتوى ✨</b>", 
        parse_mode="HTML"
    )
    reply = ask_imperial_ai(text)
    try:
        await wait_msg.edit_text(reply, parse_mode="HTML")
    except Exception:
        await wait_msg.edit_text(reply)

def main():
    # 1. إطلاق خادم الويب
    threading.Thread(target=start_server, daemon=True).start()
    # 2. إطلاق خيط التنظيف التلقائي للحفاظ على سرعة الذاكرة
    threading.Thread(target=auto_clean_temp_files, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"✅ {BOT_NAME} انطلق بكامل مميزاته وقدراته الخارقة 24/7...")
    app.run_polling()

if __name__ == "__main__":
    main()
