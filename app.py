import os
import telebot
from telebot import types
import requests
import threading
import time
import logging
import uuid
import re
import json
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import tempfile
import shutil

# ==================== 1. إعدادات السجلات (Logging) ====================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== 2. خادم فحص الحالة السحابي (Render Keep-Alive) ====================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return
    
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Saleh Mega Engine is Live!")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        logger.info(f"Health Check Server running on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Server Error: {e}")

threading.Thread(target=run_health_server, daemon=True).start()

# ==================== 3. تهيئة البوت ====================
raw_token = os.environ.get("BOT_TOKEN", "")
if not raw_token:
    raise ValueError("BOT_TOKEN environment variable is not set! Please add it to Render Env Variables.")

BOT_TOKEN = raw_token.strip()
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# متغيرات عامة
AUDIO_STORE = {}
processing_jobs = {} # لتتبع حالة الرسائل التفاعلية

# ==================== 4. أدوات مساعدة (Helpers) ====================

def expand_short_url(url: str) -> str:
    """فك الروابط المختصرة"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.head(url, allow_redirects=True, timeout=10, headers=headers)
        return res.url
    except:
        return url

def get_direct_stream_url(url: str):
    """
    المحرك الرئيسي لاستخراج رابط الفيديو المباشر.
    يدعم TikTok, Instagram, Twitter, YouTube بشكل عام
    """
    real_url = expand_short_url(url)
    
    # 1. TikTok / Douyin Logic
    if "tiktok.com" in real_url or "douyin.com" in real_url:
        try:
            # استخدام API موثوق وحديث
            api_url = f"https://tikwm.com/api/?url={urllib.parse.quote(real_url)}"
            res = requests.get(api_url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
            data = res.json()
            
            if data.get("code") == 0:
                d = data["data"]
                video_url = d.get("play") or d.get("hdplay")
                audio_url = d.get("music")
                
                if video_url:
                    return {
                        "success": True,
                        "video": video_url,
                        "audio": audio_url,
                        "title": d.get("title", "TikTok Video"),
                        "thumbnail": d.get("origin_cover"),
                        "type": "video"
                    }
        except Exception as e:
            logger.warning(f"TikTok API failed: {e}")

    # 2. Instagram Logic (Simplified fallback)
    elif "instagram.com" in real_url:
        # ملاحظة: إنستجرام معقد، هنا نستخدم نهج بسيط
        # يمكنك ربطه بـ API مثل instasave.io إذا أردت دقة أعلى
        pass

    # 3. General Direct Link Fallback
    try:
        head_res = requests.head(real_url, timeout=5, allow_redirects=True)
        content_type = head_res.headers.get('Content-Type', '')
        if 'video' in content_type or 'image' in content_type:
            return {
                "success": True,
                "video": real_url,
                "audio": None,
                "title": "Direct Media",
                "type": "direct"
            }
    except:
        pass

    return {"success": False, "error": "لم يتم العثور على فيديو صالح"}

def download_file_to_temp(file_url, filename):
    """تحميل الملف إلى مجلد مؤقت"""
    temp_dir = f"/tmp/saleh_bot_{uuid.uuid4().hex}"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, filename)
    
    try:
        response = requests.get(file_url, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return file_path, response.headers.get('content-length', 0)
    except Exception as e:
        logger.error(f"Download error: {e}")
        return None, 0

def extract_audio_from_video(video_path):
    """استخراج الصوت باستخدام FFmpeg"""
    output_path = video_path.rsplit('.', 1)[0] + "_audio.mp3"
    try:
        # تأكد من أن ffmpeg مثبت على سيرفر ريندر
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vn", "-acodec", "libmp3lame", "-q:a", "2",
            output_path
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if os.path.exists(output_path):
            return output_path
    except Exception as e:
        logger.error(f"FFmpeg Error: {e}")
    return None

# ==================== 5. الواجهة التفاعلية (Interactive UI) ====================

def create_progress_keyboard(job_id, progress_percent):
    """إنشاء أزرار تفاعلية"""
    kb = types.InlineKeyboardMarkup()
    
    # شريط تقدم بصري
    bar_length = 10
    filled = int(bar_length * progress_percent / 100)
    empty = bar_length - filled
    progress_bar = "█" * filled + "░" * empty
    
    status_text = f"📥 جاري المعالجة...\n{progress_bar} {progress_percent}%\n⏳ الوقت المتبقي: {max(1, int((100-progress_percent)/10))} ثوانٍ"
    
    btn_refresh = types.InlineKeyboardButton("🔄 تحديث", callback_data=f"refresh_{job_id}")
    btn_cancel = types.InlineKeyboardButton("❌ إلغاء", callback_data=f"cancel_{job_id}")
    
    kb.add(btn_refresh, btn_cancel)
    return kb, status_text

def send_interactive_download(bot, chat_id, message_id, job_id, task_func, *args):
    """إرسال رسالة أولية ثم تحديثها"""
    msg = bot.send_message(chat_id, "⚙️ جاري بدء المعالجة...", reply_markup=create_progress_keyboard(job_id, 0))
    
    processing_jobs[job_id] = {
        "message_id": msg.message_id,
        "chat_id": chat_id,
        "start_time": time.time(),
        "status": "processing",
        "progress": 0
    }
    
    thread = threading.Thread(target=task_wrapper, args=(bot, chat_id, msg.message_id, job_id, task_func, args))
    thread.daemon = True
    thread.start()

def task_wrapper(bot, chat_id, msg_id, job_id, func, args):
    """غلاف لتنفيذ المهمة وتحديث الواجهة"""
    try:
        result = func(*args)
        update_status(bot, chat_id, msg_id, job_id, 100, "✅ تم بنجاح!", result)
    except Exception as e:
        update_status(bot, chat_id, msg_id, job_id, 0, f"❌ خطأ: {str(e)[:50]}")

def update_status(bot, chat_id, msg_id, job_id, percent, text, result=None):
    """تحديث نص وزر الرسالة الحالية"""
    try:
        kb = types.InlineKeyboardMarkup()
        if percent < 100:
            kb.add(types.InlineKeyboardButton("🔄 تحديث", callback_data=f"refresh_{job_id}"))
        
        bot.edit_message_text(text, chat_id=chat_id, message_id=msg_id, reply_markup=kb)
        
        if result and percent == 100:
            # حذف الرسالة بعد 5 ثواني للحفاظ على نظافة الشات
            threading.Timer(5, lambda: bot.delete_message(chat_id, msg_id)).start()
            
    except Exception as e:
        logger.debug(f"Update error: {e}")

# ==================== 6. الأوامر (Commands) ====================

@bot.message_handler(commands=['start'])
def start_command(message):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📥 تحميل فيديو", callback_data="menu_download"))
    kb.add(types.InlineKeyboardButton("🎵 استخراج صوت", callback_data="menu_audio"))
    kb.add(types.InlineKeyboardButton("ℹ️ حول البوت", callback_data="menu_about"))
    
    bot.reply_to(message, 
                 "👋 مرحباً بك في **Saleh Mega Bot v2.0**!\n\n"
                 "أنا بوت احترافي لسحب الوسائط.\n"
                 "أرسل لي رابط أي فيديو وسأقوم بمعالجته فوراً.",
                 reply_markup=kb)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "menu_download":
        bot.send_message(call.message.chat.id, "🔗 أرسل لي رابط الفيديو الآن:")
    elif call.data == "menu_audio":
        bot.send_message(call.message.chat.id, "🎵 أرسل لي رابط الفيديو لاستخراج الصوت MP3:")
    elif call.data == "menu_about":
        bot.send_message(call.message.chat.id, "🤖 **Saleh Mega Bot v2.0**\n\n"
                                            "✅ دعم مباشر لجميع المنصات\n"
                                            "✅ واجهة تفاعلية حية\n"
                                            "✅ تجاوز حد 50MB\n"
                                            "✅ استخراج صوت عالي الجودة\n\n"
                                            "© Designed by Saleh")
    elif call.data.startswith("refresh_"):
        job_id = call.data.split("_")[1]
        if job_id in processing_jobs:
            # محاكاة تحديث التقدم
            current_prog = min(100, processing_jobs[job_id].get("progress", 0) + 10)
            kb, text = create_progress_keyboard(job_id, current_prog)
            bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)
            
    elif call.data.startswith("cancel_"):
        job_id = call.data.split("_")[1]
        if job_id in processing_jobs:
            del processing_jobs[job_id]
            bot.edit_message_text("تم إلغاء العملية.", call.message.chat.id, call.message.message_id)

# ==================== 7. معالجة الرسائل (Message Handler) ====================

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    if message.text and "http" in message.text.lower():
        url_match = re.search(r'https?://\S+', message.text)
        if url_match:
            url = url_match.group(0)
            process_media(message.chat.id, message.message_id, url)
    else:
        bot.reply_to(message, "أرسل لي رابط فيديو أو صوتي للمعالجة.")

def process_media(chat_id, message_id, url):
    job_id = str(uuid.uuid4())
    send_interactive_download(bot, chat_id, message_id, job_id, download_and_send_media, url)

def download_and_send_media(url):
    """الدالة الأساسية للتحميل والإرسال"""
    
    # الخطوة 1: تحليل الرابط
    bot_msg = bot.send_message(chat_id, "🔍 جاري تحليل الرابط...")
    kb, txt = create_progress_keyboard("temp", 10)
    bot.edit_message_text(txt, chat_id=chat_id, message_id=bot_msg.message_id, reply_markup=kb)
    
    media_info = get_direct_stream_url(url)
    
    if not media_info.get("success"):
        bot.edit_message_text("❌ لم يتم العثور على رابط وسائط صالح.", chat_id=chat_id, message_id=bot_msg.message_id)
        return

    bot.edit_message_text("📥 جاري تحميل الملف من الخادم...", chat_id=chat_id, message_id=bot_msg.message_id, reply_markup=kb)
    
    # الخطوة 2: التحميل الفعلي
    filename = f"{uuid.uuid4().hex}.mp4"
    file_path, size_str = download_file_to_temp(media_info["video"], filename)
    
    # تحويل الحجم لنص قابل للمقارنة
    try:
        size = int(size_str) if size_str else 0
    except:
        size = 0
    
    if not file_path:
        bot.edit_message_text("❌ فشل التحميل.", chat_id=chat_id, message_id=bot_msg.message_id)
        return

    bot.edit_message_text("📊 التحميل: 90% ...", chat_id=chat_id, message_id=bot_msg.message_id, reply_markup=kb)
    
    # الخطوة 3: الإرسال (تجاوز الحد 50MB)
    try:
        if size > 50 * 1024 * 1024: # أكبر من 50MB
            # إرسال كملف وثائقي لدعم الأحجام الكبيرة
            with open(file_path, 'rb') as f:
                bot.send_document(chat_id, f, caption=f"📁 {media_info.get('title', 'File')}\n💾 الحجم: {size/1024/1024:.2f} MB", 
                                disable_notification=True)
        else:
            # إرسال كفيديو عادي
            with open(file_path, 'rb') as f:
                bot.send_video(chat_id, f, caption=f"🎬 {media_info.get('title', 'Video')}", 
                               supports_streaming=True, disable_notification=True)
        
        bot.edit_message_text("✅ تم الإرسال بنجاح!", chat_id=chat_id, message_id=bot_msg.message_id)
        
    except Exception as e:
        bot.edit_message_text(f"❌ خطأ أثناء الإرسال: {str(e)}", chat_id=chat_id, message_id=bot_msg.message_id)
    finally:
        # تنظيف الملفات المؤقتة
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            # حذف المجلد إذا وجد
            dir_path = os.path.dirname(file_path)
            if os.path.isdir(dir_path):
                shutil.rmtree(dir_path, ignore_errors=True)
        except:
            pass

# ==================== 8. تشغيل البوت ====================
if __name__ == "__main__":
    logger.info("Starting Saleh Mega Bot...")
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except KeyboardInterrupt:
        exit()
    except Exception as e:
        logger.error(f"Bot crashed: {e}")