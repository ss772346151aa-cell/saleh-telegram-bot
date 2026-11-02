import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# إعدادات السجلات (Logs) لرؤية الأخطاء في سيرفر Render
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /start"""
    update.message.reply_text("👋 مرحباً! أنا بوتك الذكي الجديد.\n"
                              "أنا أعمل الآن من السيرفر بنجاح!")

def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /help"""
    update.message.reply_text("يمكنك استخدام الأوامر التالية:\n"
                              "/start - لبدء المحادثة\n"
                              "/help - لعرض المساعدة")

def main():
    # ضع التوكين الخاص بك هنا مباشرة إذا لم يكن لديك ملف config.py
    # أو استورده من ملف config كما شرحنا سابقاً
    TOKEN = "8973911507:AAHP-19kh9IZTjdZiJF6muixl8vvOxvrwKU" 

    # إنشاء التطبيق
    application = Application.builder().token(TOKEN).build()

    # إضافة الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # بدء البوت (هذا الأمر هو الذي يمنع البرنامج من الخروج)
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()