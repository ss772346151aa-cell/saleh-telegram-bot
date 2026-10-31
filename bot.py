import os, glob, logging, threading
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from helpers import (
    start_server, auto_clean_temp_files, track_user, load_users,
    extract_url, trim_video_to_size, download_tiktok_smart,
    search_and_download_audio_robust, download_universal_media,
    ask_super_ai, MAX_SAFE_BYTES, USERS_FILE
)

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

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
        "2️⃣ <b>شيلات وأغاني MP3:</b> اكتب اسم أي شيلة (مثل: <code>شيلة عبيد الدوعاني</code> أو <code>شيلة فهد بن فصلا</code>) وسيتم البحث عنها وجلبها لك فوراً بصوت MP3 نقي!\n"
        "3️⃣ <b>أفلام ومباريات:</b> اكتب اسم الفيلم أو المباراة وسيصلك المقطع فوراً مع قص تلقائي للأحجام الضخمة.\n"
        "4️⃣ <b>الدردشة:</b> اسأل البوت عن أي شيء وسيجيبك بذكاء متطور!"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user)
    name = update.effective_user.first_name
    msg = (
        f"👑 <b>أهلاً وسهلاً بك يا {name} في {BOT_NAME}!</b>\n\n"
        "• 📥 <b>سحب تيك توك:</b> فوري وبدون علامة مائية.\n"
        "• 🎵 <b>شيلات وأغاني MP3:</b> بحث فوري واستخراج صوتي نقي 320kbps.\n"
        "• 🎬 <b>أفلام وملخصات:</b> دقة فائقة وقص ذكي.\n\n"
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
        [KeyboardButton("⚽ ملخص مباريات اليوم"), KeyboardButton("💬 تواصل مع المطور صلوح")],
        [KeyboardButton("📞 مشاركة رقم هاتفي مع المطور", request_contact=True)]
    ]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(inline_kb), parse_mode="HTML")
    await update.message.reply_text("⚡️ أزرار التحكم السريع مدمجة في شاشتك دائماً:", reply_markup=ReplyKeyboardMarkup(reply_kb, resize_keyboard=True))

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التقاط رقم الهاتف إذا وافق المستخدم على مشاركته وحفظه فوراً"""
    contact = update.message.contact
    if contact and contact.phone_number:
        track_user(update.effective_user, phone_number=contact.phone_number)
        await update.message.reply_text("✅ شكراً لك يا غالي! تم تسجيل رقمك في سجل أعضاء البوت بنجاح 🌹")

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

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    users = load_users()
    today_str = datetime.now().strftime("%Y-%m-%d")
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    total = len(users)
    active_today = [u for u in users.values() if u.get("last_active", "").startswith(today_str)]
    active_yesterday = [u for u in users.values() if u.get("last_active", "").startswith(yesterday_str)]
    joined_today = [u for u in users.values() if u.get("first_join", "").startswith(today_str)]

    report = (
        "📊 <b>تقرير إحصائيات البوت:</b>\n\n"
        f"👥 <b>إجمالي المستخدمين:</b> <code>{total}</code>\n"
        f"⚡️ <b>المتفاعلون اليوم ({today_str}):</b> <code>{len(active_today)}</code> شخص\n"
        f"⏳ <b>المتفاعلون البارحة ({yesterday_str}):</b> <code>{len(active_yesterday)}</code> شخص\n"
        f"🆕 <b>المشتركون الجدد اليوم:</b> <code>{len(joined_today)}</code> شخص\n\n"
        "👇 <i>لعرض تفاصيل كل مستخدم وأرقام الهواتف أرسل:</i> <code>/users</code>"
    )
    await update.message.reply_text(report, parse_mode="HTML")

async def users_detail_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    users = load_users()
    if not users:
        await update.message.reply_text("لا يوجد زوار مسجلون بعد.")
        return

    text = "📋 <b>قائمة الزوار ومعلوماتهم الكاملة:</b>\n\n"
    for idx, (uid, u) in enumerate(list(users.items())[-20:], 1):
        prem = "⭐️ نعم" if u.get("is_premium") else "لا"
        phone = u.get("phone", "غير متوفر")
        text += (
            f"<b>{idx}. {u.get('first_name', '')} {u.get('last_name', '')}</b>\n"
            f"• 🆔 الآيدي: <code>{uid}</code>\n"
            f"• 👤 اليوزر: {u.get('username')}\n"
            f"• 📞 الهاتف: <code>{phone}</code>\n"
            f"• 🌐 لغة الجهاز: <code>{u.get('language_code')}</code>\n"
            f"• ⭐️ بريميوم: {prem}\n"
            f"• 🕒 أول دخول: {u.get('first_join')}\n"
            f"• ⚡️ آخر ظهور: {u.get('last_active')}\n"
            f"• 🔄 عدد التفاعلات: {u.get('interactions')} مرة\n"
            "---------------------------\n"
        )
    await update.message.reply_text(text, parse_mode="HTML")
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "rb") as f:
            await update.message.reply_document(document=f, caption="📁 ملف بيانات المستخدمين والهواتف كاملاً (JSON)")

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
        await update.message.reply_text("🎬 أرسل اسم الفيلم الآن وسأجلب لك مقطعه وملخصه فوراً!")
        return
    if text == "🎵 طلب شيلة MP3":
        await update.message.reply_text("🎵 أرسل اسم أي شيلة أو أغنية الآن (مثل: شيلة عبيد الدوعاني أو شيلة فهد بن فصلا) وسأحضرها لك صوت فوراً!")
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
                await update.message.reply_video(video=vid, caption=cap, reply_markup=btn, parse_mode="HTML")
            await wait.delete()
            if os.path.exists(out_vid): os.remove(out_vid)
            return
        await wait.edit_text("❌ تعذر تحميل المقطع، تأكد أن الفيديو متاح للعامة.")
        return

    # 2. البحث القوي للشيلات والأغاني بصيغة MP3 صوت فوراً
    audio_triggers = ["شيله", "شيلة", "شيلات", "اغنيه", "اغنية", "أغنية", "صوت", "زامل", "زوامل", "انشوده", "أنشودة"]
    if any(k in text.lower() for k in audio_triggers):
        wait = await update.message.reply_text("🎵 <b>جاري البحث في المنصات وسحب الشيلة بنقاوة MP3 فوراً... ✨</b>", parse_mode="HTML")
        res = search_and_download_audio_robust(text, output_base)
        if res and os.path.exists(res["path"]) and os.path.getsize(res["path"]) > 1000:
            cap = f"🎵 <b>{res['title'][:100]}</b>\n\n✨ تم الجلب بواسطة: <b>{BOT_NAME}</b>\n🔥 تابع حسابنا: <b>{TIKTOK_USER}</b>"
            btn = InlineKeyboardMarkup([[InlineKeyboardButton("❤️ تابع حساب صلوح", url=TIKTOK_CHANNEL)]])
            with open(res["path"], "rb") as aud:
                await update.message.reply_audio(audio=aud, caption=cap, reply_markup=btn, parse_mode="HTML")
            await wait.delete()
            try: os.remove(res["path"])
            except Exception: pass
            return
        else:
            await wait.edit_text("⚠️ لم يتم العثور على الشيلة بهذا الاسم بالتحديد، جرب كتابة اسم الشاعر أو المنشد وسأحضرها لك فوراً!")
            return

    # 3. الأفلام والمقاطع الكبيرة مع القص التلقائي
    if any(k in text.lower() for k in ["فيلم", "فلم", "افلام", "اهداف", "مباراة", "ملخص"]) or bool(url_found):
        wait = await update.message.reply_text("🎬 <b>جاري سحب المقطع بأعلى دقة متوفرة... ✨</b>", parse_mode="HTML")
        target = url_found if url_found else text.replace("فيلم", "").replace("تنزيل", "").strip()
        out_raw = f"{output_base}_raw.mp4"
        out_trim = f"{output_base}_final.mp4"
        try:
            info = download_universal_media(target, out_raw, is_search=not bool(url_found))
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

    # 4. الذكاء الاصطناعي للإجابة على أي طلب آخر
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
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))

    print(f"✅ {BOT_NAME} يعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
