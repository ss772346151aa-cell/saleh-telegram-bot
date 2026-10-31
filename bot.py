import os, glob, logging, threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from helpers import (
    start_server, auto_clean_temp_files, track_user, load_users,
    extract_url, trim_video_to_size, download_tiktok_smart,
    download_universal_media, ask_super_ai, MAX_SAFE_BYTES, USERS_FILE
)

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# تم تثبيت آيدي حسابك مباشرة
ADMIN_ID = 7206214234
BOT_TOKEN = "9157081412:AAF-LegdEK1zKi_ZUCPOarhFXwphmPpqFUE"
BOT_NAME = "بوت صلوح المانعي الذكي ⚡️👑"
TIKTOK_CHANNEL = "https://www.tiktok.com/@almanay22"
TIKTOK_USER = "@almanay22"
WHATSAPP_URL = "https://wa.me/967782953692"

def get_help():
    return (
        "📖 <b>دليل الاستخدام السريع والسهل:</b> 🚀\n\n"
        "1️⃣ <b>تنزيل تيك توك:</b> الصق رابط المقطع وسيصلك بأعلى دقة وبدون علامة مائية!\n"
        "2️⃣ <b>شيلات وأغاني MP3:</b> اكتب اسم الشيلة وسيصلك ملف صوت نقي فوراً.\n"
        "3️⃣ <b>أفلام وملخصات:</b> اكتب اسم الفيلم أو المباراة وسيقوم البوت بجلبه لك وقصه بذكاء إذا كان ضخماً.\n"
        "4️⃣ <b>الدردشة:</b> اسأل البوت عن أي موضوع وسيجيبك بدقة وذكاء!"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user)
    name = update.effective_user.first_name
    msg = (
        f"👑 <b>أهلاً وسهلاً بك يا {name} في {BOT_NAME}!</b>\n\n"
        "• 📥 <b>سحب تيك توك:</b> فوري وبدون علامة مائية.\n"
        "• 🎵 <b>شيلات وأغاني MP3:</b> صوت عالي النقاوة 320kbps.\n"
        "• 🎬 <b>أفلام وملخصات:</b> بأعلى دقة وقص ذكي.\n\n"
        f"🌟 <b>حساب تيك توك الرسمي:</b> <code>{TIKTOK_CHANNEL}</code>"
    )
    inline_kb = [
        [InlineKeyboardButton("💡 اضغط هنا لطريقة الاستخدام 💡", callback_data="help")],
        [InlineKeyboardButton("🔥 حساب صلوح على تيك توك 🔥", url=TIKTOK_CHANNEL)],
        [InlineKeyboardButton("💬 واتساب المطور", url=WHATSAPP_URL)]
    ]
    reply_kb = [
        [KeyboardButton("💡 كيف أستخدم البوت؟"), KeyboardButton("🔥 حساب تيك توك الرسمي")],
        [KeyboardButton("🎬 طلب فيلم سينمائي"), KeyboardButton("🎵 طلب شيلة MP3")],
        [KeyboardButton("⚽ ملخص مباريات اليوم"), KeyboardButton("💬 تواصل مع المطور صلوح")]
    ]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(inline_kb), parse_mode="HTML")
    await update.message.reply_text("⚡️ أزرار التحكم السريع مدمجة في شاشتك دائماً:", reply_markup=ReplyKeyboardMarkup(reply_kb, resize_keyboard=True))

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user)
    btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔥 تابع حساب صلوح", url=TIKTOK_CHANNEL)]])
    await update.message.reply_text(get_help(), reply_markup=btn, parse_mode="HTML")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "help":
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔥 تابع حساب صلوح", url=TIKTOK_CHANNEL)]])
        await query.message.reply_text(get_help(), reply_markup=btn, parse_mode="HTML")

# أمر عرض معلومات الزوار التفصيلية (خاص بصلوح فقط)
async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    users = load_users()
    today = time.strftime("%Y-%m-%d")
    total = len(users)
    active = sum(1 for u in users.values() if u.get("last_active", "").startswith(today))

    report = (
        "📊 <b>تقرير إحصائيات البوت:</b>\n\n"
        f"👥 إجمالي المستخدمين: <code>{total}</code>\n"
        f"⚡️ النشطون اليوم: <code>{active}</code>\n\n"
        "👇 <i>لعرض تفاصيل وهوية كل زائر أرسل أمر:</i> <code>/users</code>"
    )
    await update.message.reply_text(report, parse_mode="HTML")

async def users_detail_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض تفاصيل وهوية الزوار المسجلين في البوت"""
    if update.effective_user.id != ADMIN_ID: return
    users = load_users()
    if not users:
        await update.message.reply_text("لا يوجد زوار مسجلون بعد.")
        return

    text = "📋 <b>قائمة الزوار المسجلين ومعلوماتهم:</b>\n\n"
    for idx, (uid, u) in enumerate(list(users.items())[-15:], 1):  # عرض آخر 15 مستخدم
        prem = "⭐️ نعم" if u.get("is_premium") else "لا"
        text += (
            f"<b>{idx}. {u.get('first_name', '')} {u.get('last_name', '')}</b>\n"
            f"• 🆔 الآيدي: <code>{uid}</code>\n"
            f"• 👤 اليوزر: {u.get('username')}\n"
            f"• 🌐 لغة جهازه: <code>{u.get('language_code')}</code>\n"
            f"• ⭐️ بريميوم: {prem}\n"
            f"• 🕒 أول دخول: {u.get('first_join')}\n"
            f"• ⚡️ آخر ظهور: {u.get('last_active')}\n"
            f"• 🔄 التفاعلات: {u.get('interactions')} مرة\n"
            "---------------------------\n"
        )
    await update.message.reply_text(text, parse_mode="HTML")
    # إرسال ملف البيانات كاملاً لمن يحب حفظه
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "rb") as f:
            await update.message.reply_document(document=f, caption="📁 ملف بيانات المستخدمين الكامل (JSON)")

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user)
    text = update.message.text.strip()
    chat_id = update.effective_chat.id
    msg_id = update.message.message_id
    output_base = f"downloads/{chat_id}_{msg_id}"
    os.makedirs("downloads", exist_ok=True)

    if text in ["💡 كيف أستخدم البوت؟", "شرح البوت"]:
        await update.message.reply_text(get_help(), parse_mode="HTML")
        return
    if text == "🔥 حساب تيك توك الرسمي":
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("✨ فتح حساب التيك توك مباشرة ✨", url=TIKTOK_CHANNEL)]])
        await update.message.reply_text(f"🎬 <b>حساب صلوح على تيك توك:</b>\n{TIKTOK_CHANNEL}", reply_markup=btn, parse_mode="HTML")
        return
    if text == "💬 تواصل مع المطور صلوح":
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("💬 مراسلة صلوح على واتساب", url=WHATSAPP_URL)]])
        await update.message.reply_text("👑 تواصل مع المطور صلوح المانعي:", reply_markup=btn)
        return
    if text == "🎬 طلب فيلم سينمائي":
        await update.message.reply_text("🎬 أرسل اسم الفيلم الآن وسأجلب لك مقطعه فوراً!")
        return
    if text == "🎵 طلب شيلة MP3":
        await update.message.reply_text("🎵 أرسل اسم الشيلة أو الأغنية وسأستخرجها لك بصوت نقي MP3 فوراً!")
        return
    if text == "⚽ ملخص مباريات اليوم":
        reply = ask_super_ai("ما هي أهم قمم ومواعيد مباريات اليوم الكروية وأبرز النتائج؟")
        await update.message.reply_text(reply, parse_mode="HTML")
        return

    # 1. روابط تيك توك
    url_found = extract_url(text)
    if url_found and ("tiktok.com" in url_found.lower() or "douyin.com" in url_found.lower()):
        wait = await update.message.reply_text("⚡️ <b>جاري سحب المقطع بدون علامة مائية... ✨</b>", parse_mode="HTML")
        out_vid = f"{output_base}.mp4"
        data = download_tiktok_smart(url_found, out_vid)
        if data and os.path.exists(out_vid) and os.path.getsize(out_vid) > 1000:
            cap = f"🎬 <b>{data['title'][:100]}</b>\n\n✨ بواسطة: <b>{BOT_NAME}</b>\n🔥 تابعنا: <b>{TIKTOK_USER}</b>"
            btn = InlineKeyboardMarkup([[InlineKeyboardButton("❤️ تابع حساب صلوح", url=TIKTOK_CHANNEL)]])
            with open(out_vid, "rb") as v:
                await update.message.reply_video(video=v, caption=cap, reply_markup=btn, parse_mode="HTML")
            await wait.delete()
            if os.path.exists(out_vid): os.remove(out_vid)
            return
        await wait.edit_text("❌ تعذر تحميل المقطع، تأكد أن الفيديو متاح للعامة.")
        return

    # 2. الشيلات والأغاني صوت MP3
    if any(k in text.lower() for k in ["شيله", "شيلة", "اغنيه", "اغنية", "صوت", "زامل"]):
        wait = await update.message.reply_text("🎵 <b>جاري سحب الصوت بنقاوة MP3 (320kbps)... ✨</b>", parse_mode="HTML")
        q = re.sub(r'(اريد|تنزيل|شيله|شيلة|اغنيه|اغنية|صوت|تحميل)', '', text).strip() or text
        out_aud = f"{output_base}.mp3"
        try:
            info = download_universal_media(q, out_aud, is_audio=True, is_search=True)
            act = out_aud if os.path.exists(out_aud) else (glob.glob(f"{output_base}.*") or [None])[0]
            if act and os.path.exists(act) and os.path.getsize(act) > 1000:
                cap = f"🎵 <b>{info.get('title', q)[:100]}</b>\n\n✨ تم بواسطة: <b>{BOT_NAME}</b>\n🔥 تابعنا: <b>{TIKTOK_USER}</b>"
                btn = InlineKeyboardMarkup([[InlineKeyboardButton("❤️ تابع حساب صلوح", url=TIKTOK_CHANNEL)]])
                with open(act, "rb") as a:
                    await update.message.reply_audio(audio=a, caption=cap, reply_markup=btn, parse_mode="HTML")
                await wait.delete()
                if os.path.exists(act): os.remove(act)
                return
        except Exception:
            pass

    # 3. الأفلام والمقاطع الكبيرة مع القص التلقائي
    if any(k in text.lower() for k in ["فيلم", "فلم", "افلام", "اهداف", "مباراة", "ملخص"]) or bool(url_found):
        wait = await update.message.reply_text("🎬 <b>جاري سحب المقطع بأعلى دقة متوفرة... ✨</b>", parse_mode="HTML")
        target = url_found if url_found else text.replace("فيلم", "").replace("تنزيل", "").strip()
        out_raw = f"{output_base}_raw.mp4"
        out_trim = f"{output_base}_final.mp4"
        try:
            info = download_universal_media(target, out_raw, is_audio=False, is_search=not bool(url_found))
            act_raw = out_raw if os.path.exists(out_raw) else (glob.glob(f"{output_base}_raw*") or [None])[0]
            if act_raw and os.path.exists(act_raw):
                final_f = act_raw
                is_t = False
                if os.path.getsize(act_raw) > MAX_SAFE_BYTES:
                    await wait.edit_text("✂️ <b>الفيديو ضخم، جاري قص الجزء الأول بأعلى دقة (48MB)...</b>", parse_mode="HTML")
                    if trim_video_to_size(act_raw, out_trim, MAX_SAFE_BYTES):
                        final_f = out_trim
                        is_t = True
                cap = f"🎬 <b>{info.get('title', target)[:100]}</b>\n\n{'⚠️ تم قص أول جزء بأعلى دقة لمطابقة حد 48MB.' if is_t else '✨ دقة فائقة.'}\n\n👑 <b>{BOT_NAME}</b>"
                btn = InlineKeyboardMarkup([[InlineKeyboardButton("❤️ تابع حساب صلوح", url=TIKTOK_CHANNEL)]])
                with open(final_f, "rb") as v:
                    await update.message.reply_video(video=v, caption=cap, reply_markup=btn, parse_mode="HTML")
                await wait.delete()
                for f in [act_raw, out_trim]:
                    if os.path.exists(f): os.remove(f)
                return
        except Exception:
            pass

    # 4. الذكاء الاصطناعي
    wait = await update.message.reply_text("⚡️ <b>لحظات أجهز لك الرد... ✨</b>", parse_mode="HTML")
    reply = ask_super_ai(text)
    await wait.edit_text(reply, parse_mode="HTML")

def main():
    threading.Thread(target=start_server, daemon=True).start()
    threading.Thread(target=auto_clean_temp_files, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("users", users_detail_cmd))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))

    print(f"✅ {BOT_NAME} يعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
