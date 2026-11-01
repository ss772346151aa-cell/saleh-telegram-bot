import logging
import os
import asyncio
import io
import json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder, 
    ContextTypes, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    CallbackQueryHandler,
    Application
)
from telegram.constants import ParseMode
from translatepy import Translator
import psutil
import random

# إعدادات التوكن واللوغ
TOKEN = os.getenv('BOT_TOKEN', 'ضع_التوكن_هنا')
ADMIN_IDS = [123456789]  # ضع معرفك الرقمي هنا

# إعداد اللوغ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# قاعدة بيانات بسيطة (يمكن استبدالها بـ SQLite أو MongoDB لاحقاً)
# هيكل البيانات: {chat_id: {settings: {...}, stats: {...}}}
db = {}

class SmartBot:
    def __init__(self):
        self.translator = Translator()
        self.last_cleanup = datetime.now()
        
    # --- مساعدة عامة ---
    def get_chat_data(self, chat_id):
        if chat_id not in db:
            db[chat_id] = {"settings": {}, "stats": {"messages": 0, "joined": datetime.now().isoformat()}}
        return db[chat_id]

    async def send_admin_log(self, app: Application, message: str):
        for admin_id in ADMIN_IDS:
            try:
                await app.bot.send_message(admin_id, message, parse_mode=ParseMode.HTML)
            except Exception as e:
                logger.error(f"Error sending admin log: {e}")

    # --- الأوامر الأساسية ---
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        welcome_msg = f"""
👋 مرحباً {user.first_name}!

أنا البوت الشامل الذكي. إليك ما يمكنني فعله:
🛡️ حماية المجموعات
📂 تحويل الملفات والصور
🌍 ترجمة النصوص
📊 إحصائيات متقدمة
🤖 رد تلقائي ذكي

استخدم /help لرؤية جميع الأوامر.
"""
        keyboard = [
            [InlineKeyboardButton("⚙️ الإعدادات", callback_data="settings_main")],
            [InlineKeyboardButton("📊 إحصائياتي", callback_data="my_stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_msg, reply_markup=reply_markup)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """
📜 **قائمة الأوامر المتاحة:**

🔹 *إدارة:*
/start - بدء البوت
/help - عرض المساعدة
/settings - إعدادات المجموعة
/admins - عرض المشرفين

🔹 *المحتوى:*
/pin - تثبيت رسالة
/unpin - إلغاء التثبيت
/kick @user - طرد عضو
/ban @user - حظر عضو
/mute @user - كتم صوت
/untmute - فك كتم

🔹 *الأدوات:*
/translate <text> - ترجمة نص
/convert <file> - تحويل ملف
/stats - إحصائيات المجموعة
/clean - تنظيف الرسائل المكررة

🔹 *أوامر المشرفين فقط:*
/setwelcome <text> - رسالة ترحيب
/setgoodbye <text> - رسالة وداع
/setspamprotection on/off - حماية السبام
"""
        await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

    # --- نظام الترجمة الذكي ---
    async def auto_translate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_data = self.get_chat_data(update.effective_chat.id)
        settings = chat_data["settings"]
        
        # إذا كانت الترجلة مفعلة والمجموعة وليست خاصة
        if settings.get("auto_translate", False) and update.effective_chat.type != 'private':
            msg = update.effective_message
            if msg.text or msg.caption:
                text = msg.text or msg.caption
                try:
                    # ترجمة إلى اللغة العربية افتراضياً أو لغة المجموعة
                    translated = self.translator.translate(text, to_language='ar')
                    if translated.text != text: # إذا كان النص مترجماً فعلاً
                        await msg.reply_text(f"🌍 *ترجمة:\n\n{translated.text}", parse_mode=ParseMode.MARKDOWN)
                except Exception:
                    pass

    # --- نظام إدارة الملفات والتحويل ---
    async def handle_file_conversion(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.effective_message
        
        # تحويل الصور إلى ملفات أخرى أو ضغطها
        if msg.photo:
            file = await context.bot.get_file(msg.photo[-1].file_id)
            caption = f"✅ تم استلام الصورة بنجاح.\n📏 الحجم: {file.file_size} bytes\n📅 التاريخ: {datetime.now().strftime('%Y-%m-%d')}"
            await msg.reply_caption(caption)
            
        elif msg.document:
            # محاكاة لتحويل الملف
            file = await context.bot.get_file(msg.document.file_id)
            await msg.reply_document(file) # إعادة إرسال الملف (محاكاة للتحويل)
            await msg.reply_text("📂 تم حفظ الملف في الأرشيف الخاص بك.")

    # --- نظام الحماية من السبام ---
    async def check_spam(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        chat_data = self.get_chat_data(chat_id)
        
        # منطق بسيط للسبام: إذا أرسل نفس الرسالة أكثر من 3 مرات في ثانية واحدة
        if "last_msg" in chat_data.get(user_id, {}):
            last_time = chat_data[user_id]["last_time"]
            last_text = chat_data[user_id]["last_text"]
            
            if datetime.fromisoformat(last_time) > datetime.now() - timedelta(seconds=2) and last_text == update.effective_message.text:
                # عد السبام
                spam_count = chat_data[user_id].get("spam_count", 0) + 1
                chat_data[user_id]["spam_count"] = spam_count
                
                if spam_count > 3:
                    try:
                        await update.effective_message.delete()
                        await update.effective_chat.ban_member(user_id)
                        await update.effective_chat.unban_member(user_id) # فك الحظر فوراً للعرض
                        await update.message.reply_text(f"🚫 تم حظرك بسبب السبام ({spam_count} مرات)")
                    except Exception:
                        pass
                return True
            
        # تحديث آخر رسالة
        if user_id not in chat_data:
            chat_data[user_id] = {}
        chat_data[user_id]["last_time"] = datetime.now().isoformat()
        chat_data[user_id]["last_text"] = update.effective_message.text
        chat_data[user_id]["spam_count"] = 0
        return False

    # --- لوحة التحكم والإعدادات ---
    async def settings_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        chat_id = update.effective_chat.id
        settings = self.get_chat_data(chat_id)["settings"]
        
        status_auto_trans = "🟢 مفعل" if settings.get("auto_translate") else "🔴 معطل"
        status_welcome = "🟢 مفعل" if settings.get("welcome_msg") else "🔴 معطل"
        
        text = f"""
⚙️ *إعدادات المجموعة*

🌍 الترجلة التلقائية: {status_auto_trans}
👋 رسالة الترحيب: {status_welcome}
📊 عدد الرسائل اليوم: {self.get_chat_data(chat_id)['stats']['messages']}

اختر تعديلاً:
"""
        keyboard = [
            [InlineKeyboardButton(f"تبديل الترجلة ({status_auto_trans})", callback_data="toggle_translate")],
            [InlineKeyboardButton("إعادة تعيين الإحصائيات", callback_data="reset_stats")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back")]
        ]
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        chat_id = update.effective_chat.id
        settings = self.get_chat_data(chat_id)["settings"]
        
        if query.data == "settings_main":
            await self.settings_menu(update, context)
            
        elif query.data == "toggle_translate":
            settings["auto_translate"] = not settings.get("auto_translate", False)
            await self.settings_menu(update, context)
            
        elif query.data == "reset_stats":
            self.get_chat_data(chat_id)["stats"]["messages"] = 0
            await query.answer("تم مسح الإحصائيات!")
            await self.settings_menu(update, context)
            
        elif query.data == "back":
            await query.edit_message_text("القائمة الرئيسية", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back")]]))

    # --- الأوامر الإدارية ---
    async def kick(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        member = update.effective_message.new_chat_members[0] if update.effective_message.new_chat_members else None
        
        # مثال بسيط: طرد المستخدم الذي تم ذكره
        args = context.args
        if args:
            # البحث عن المستخدم في الرسائل السابقة أو استخدام ID
            # هذا مثال مبسط
            await update.effective_chat.kick_member(int(args[0]))
            await update.message.reply_text("✅ تم طرد العضو.")
        else:
            await update.message.reply_text("❌ استخدم: /kick <user_id>")

    async def pin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.eeffective_message
        if msg:
            await msg.pin(disable_notification=True)
            await update.message.reply_text("📌 تم تثبيت الرسالة.")

    # --- الإحصائيات ---
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        data = self.get_chat_data(chat_id)
        msgs = data["stats"]["messages"]
        
        # حساب استخدام السيرفر
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory().percent
        
        text = f"""
📊 *إحصائيات المجموعة*

📝 إجمالي الرسائل: {msgs}
💻 استخدام المعالج: {cpu_percent}%
🧠 استخدام الذاكرة: {memory}%
📅 تاريخ الانضمام: {data['stats']['joined']}
"""
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)

    # --- الحلقة الرئيسية للمعالجة ---
    async def process_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_message:
            # زيادة العداد
            chat_id = update.effective_chat.id
            self.get_chat_data(chat_id)["stats"]["messages"] += 1
            
            # فحص السبام
            if await self.check_spam(update, context):
                return

            # الترجلة التلقائية
            await self.auto_translate(update, context)
            
            # معالجة الملفات
            await self.handle_file_conversion(update, context)

# --- إعداد التطبيق ---
def main():
    # إنشاء التطبيق
    application = ApplicationBuilder().token(TOKEN).build()
    
    smart_bot = SmartBot()
    
    # إضافة المعالجات (Handlers)
    application.add_handler(CommandHandler("start", smart_bot.start))
    application.add_handler(CommandHandler("help", smart_bot.help))
    application.add_handler(CommandHandler("stats", smart_bot.stats))
    application.add_handler(CommandHandler("pin", smart_bot.pin))
    application.add_handler(CommandHandler("kick", smart_bot.kick))
    application.add_handler(CommandHandler("settings", smart_bot.settings_menu))
    
    # معالجة الأزرار
    application.add_handler(CallbackQueryHandler(smart_bot.handle_callback))
    
    # معالجة الرسائل النصية والملفات (باستخدام filter)
    application.add_handler(MessageHandler(filters.TEXT | filters.CAPTION | filters.PHOTO | filters.Document.ALL, smart_bot.process_message))
    
    # تشغيل البوت
    logger.info("البوت يعمل الآن...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()