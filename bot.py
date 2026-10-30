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
CHANNEL_URL = "https://t.me/saleh_down_bot"
WHATSAPP_NUMBER = "967782953692"
WHATSAPP_URL = f"https://wa.me/{WHATSAPP_NUMBER}"
MAX_FILE_SIZE = 49 * 1024 * 1024  # حد 50 ميجا المسموح به في تيليجرام
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

def ask_ai(prompt: str) -> str:
    """محرك محادثة ذكي ومضمون لا يتوقف"""
    # 1. ردود سريعة ذكية للترحيب والتعريف
    p_lower = prompt.lower().strip()
    if any(w in p_lower for w in ["مرحبا", "هلا", "السلام", "مساء الخير", "صباح الخير", "أهلاً", "اهلا"]):
        return (
            "يا هلا ومية مرحبا يا غالي! نورتني وأسعدتني بوجودك 🌹✨\n\n"
            "أنا المساعد الذكي الخاص بـ <b>صلوح المانعي</b> 👑\n"
            "اطلب مني أي فيلم، أغنية، أهداف مباراة، أو مقطع من تيك توك ويوتيوب وسأجلبه لك فوراً كفيديو وصوت في المحادثة!"
        )
    if any(w in p_lower for w in ["من انت", "من أنت", "مين انت", "عرف عن نفسك"]):
        return (
            "أنا <b>بوت صلوح المانعي الذكي</b> ⚡️\n\n"
            "تم برمجتي لأكون رفيقك اليومي لتحميل الفيديوهات، جلب الأغاني، توفير ملخصات الأفلام والمباريات، ومساعدتك في أي معلومة تبحث عنها بأسرع وقت!"
        )
    if "كيف حالك" in p_lower:
        return "بخير وبأفضل حال دامك بخير وسعادة يا عزيزي! بشرني عنك؟ وكيف أقدر أخدمك اليوم؟ 🌸"

    # 2. محاولة توليد رد ذكي عبر واجهة سريعة
    try:
        sys_msg = (
            "أنت مساعد تيليجرام ذكي ومرح وخبير في السينما والرياضة والأغاني والتقنية تابع لصلوح المانعي. "
            "أجب بإيجاز، أسلوب شيق، وتنسيق نقاط جميل مع إيموجي باللغة العربية."
        )
        url = "https://api.airforce/chat/process"
        payload = {
            "messages": [
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": prompt}
            ],
            "model": "gpt-4o-mini"
        }
        r = requests.post(url, json=payload, timeout=7)
        if r.status_code == 200:
            res = r.json()
            if "choices" in res and len(res["choices"]) > 0:
                return res["choices"][0]["message"]["content"].strip()
    except Exception:
        pass

    # 3. رد ذكي تفاعلي في حال انقطاع واجهات الذكاء الخارجية
    return (
        f"أهلاً بك يا غالي بخصوص بحثك عن: <b>{prompt}</b> 🌟\n\n"
        f"✨ إذا كان طلبك فيديو أو أغنية أو ملخص لعمل، اكتب في بداية رسالتك كلمة مثل:\n"
        f"• <code>فيلم {prompt}</code>\n"
        f"• <code>اغنية {prompt}</code>\n"
        f"• <code>اهداف {prompt}</code>\n\n"
        f"وسأقوم بسحب المقطع فوراً وإرساله لك كملف حي قابل للتشغيل في الشات!"
    )

def download_media(query_or_url: str, output_base: str, is_search=False):
    """تنزيل من الروابط أو البحث المباشر وتنزيل أول نتيجة متوافقة"""
    target = f"ytsearch1:{query_or_url}" if is_search else query_or_url
    ydl_opts = {
        "format": "best[ext=mp4][filesize<48M]/best[filesize<48M]/best",
        "outtmpl": f"{output_base}.%(ext)s",
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
        info = ydl.extract_info(target, download=True)
        if "entries" in info and len(info["entries"]) > 0:
            return info["entries"][0]
        return info

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    msg = (
        f"👑 <b>أهلاً وسهلاً بك يا {name} في {BOT_NAME}!</b>\n\n"
        "🎬 <b>أنا أرسل لك الملفات والفيديوهات حية ومباشرة في المحادثة:</b>\n\n"
        "• 🎵 <b>الأغاني والصوتيات:</b> اكتب (اغنية كذا) وسأحملها لك فوراً.\n"
        "• 🎥 <b>الأفلام والمسلسلات:</b> اكتب اسم الفيلم أو ملخصه ليصلك المقطع مباشرة.\n"
        "• ⚽ <b>كرة القدم:</b> اكتب (اهداف مباراة كذا) لتشاهد الأهداف مباشرة.\n"
        "• 📥 <b>روابط السوشيال ميديا:</b> أرسل رابط تيك توك، يوتيوب، أو إنستغرام وسيتولى البوت تحميله.\n"
        "• 💬 <b>الدردشة والذكاء:</b> تحدث معي وسأجيبك فوراً!\n"
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

    # 1. تنزيل رابط مباشر
    if text.startswith("http://") or text.startswith("https://"):
        wait_msg = await update.message.reply_text("⚡️ <b>جاري تحميل المقطع وإرساله لك مباشرة...</b>", parse_mode="HTML")
        try:
            info = download_media(text, output_base, is_search=False)
            files = [f for f in glob.glob(f"{output_base}.*") if not f.endswith(('.webp', '.jpg', '.png'))]
            if files and os.path.getsize(files[0]) <= MAX_FILE_SIZE:
                title = info.get("title", "فيديو مباشر")
                with open(files[0], "rb") as vid:
                    await update.message.reply_video(video=vid, caption=f"🎬 <b>{title[:100]}</b>\n\n⚡️ بواسطة {BOT_NAME}", parse_mode="HTML")
                await wait_msg.delete()
            else:
                await wait_msg.edit_text("⚠️ حجم المقطع يتجاوز 50MB (الحد الأقصى للإرسال المباشر).")
        except Exception:
            await wait_msg.edit_text("❌ تعذر التحميل، تأكد من أن الرابط متاح للعامة.")
        finally:
            for f in glob.glob(f"{output_base}*"):
                try: os.remove(f)
                except Exception: pass
        return

    # 2. الكلمات الدالة على طلب وسائط (أغاني، أفلام، مباريات، أهداف، مقاطع، رعب، إلخ)
    media_words = [
        "اغنيه", "أغنية", "اغنية", "انشودة", "شيلة", "شيله", "موسيقى", 
        "فيلم", "فلم", "افلام", "أفلام", "مسلسل", "حلقة", "حلقه", "انمي", 
        "اهداف", "أهداف", "مباراة", "مباراه", "ملخص", "فيديو", "مقطع", "تنزيل", "قم بتنزيل"
    ]
    is_media = any(word in text.lower() for word in media_words)

    if is_media:
        wait_msg = await update.message.reply_text(
            "⚡️ <b>جاري البحث... صلوح المانعي يجلب لك المقطع الآن مباشرة ✨</b>", 
            parse_mode="HTML"
        )
        try:
            # تنظيف نص البحث للوصول لأفضل مقطع
            clean_search = text.replace("قم بتنزيل", "").replace("تنزيل", "").replace("اريد", "").strip()
            info = download_media(clean_search, output_base, is_search=True)
            files = [f for f in glob.glob(f"{output_base}.*") if not f.endswith(('.webp', '.jpg', '.png'))]
            
            if files and os.path.exists(files[0]) and os.path.getsize(files[0]) <= MAX_FILE_SIZE:
                title = info.get("title", text)
                caption = (
                    f"🎬 <b>{title[:120]}</b>\n\n"
                    f"🍿 تم الجلب حياً ومباشراً بواسطة: <b>{BOT_NAME}</b>\n"
                    f"💬 للتواصل: <code>+{WHATSAPP_NUMBER}</code>"
                )
                with open(files[0], "rb") as vid:
                    await update.message.reply_video(video=vid, caption=caption, parse_mode="HTML", supports_streaming=True)
                await wait_msg.delete()
                return
            else:
                # إذا كان الحجم كبيراً يتم توضيح ذلك مع جلب رد الذكاء الاصطناعي
                ai_reply = ask_ai(clean_search)
                await wait_msg.edit_text(
                    f"⚠️ <b>المقطع الكامل حجمه يتجاوز 50MB (حد تيليجرام).</b>\n\n"
                    f"{ai_reply}", 
                    parse_mode="HTML"
                )
        except Exception as e:
            logging.error(f"Media Search Error: {e}")
            ai_reply = ask_ai(text)
            await wait_msg.edit_text(ai_reply, parse_mode="HTML")
        finally:
            for f in glob.glob(f"{output_base}*"):
                try: os.remove(f)
                except Exception: pass
        return

    # 3. الدردشة والمحادثة العادية
    wait_msg = await update.message.reply_text(
        "⚡️ <b>جاري البحث... صلوح المانعي يبحث لك الآن عن أفضل محتوى ✨</b>", 
        parse_mode="HTML"
    )
    reply = ask_ai(text)
    try:
        await wait_msg.edit_text(reply, parse_mode="HTML")
    except Exception:
        await wait_msg.edit_text(reply)

def main():
    threading.Thread(target=start_server, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"✅ {BOT_NAME} يعمل الآن بالبحث الحي وتنزيل الوسائط الفوري...")
    app.run_polling()

if __name__ == "__main__":
    main()