import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# تفعيل السجلات
logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ البوت يعمل بنجاح!")

def main():
    # ⚠️ استبدل التوكين هنا أو استخدم متغير بيئة
    TOKEN = 8973911507:AAHP-19kh9IZTjdZiJF6muixl8vvOxvrwKU" 
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()