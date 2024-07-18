import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler, ContextTypes, JobQueue, Job
import os
from threading import Lock
from datetime import datetime, timedelta

# تفعيل التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(الlevelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تعريف الحالات
SUBSCRIBE, CODE = range(2)

# أسماء الملفات لمفاتيح الاشتراك
# File names for subscription keys
one_month_file = 'one_month_keys.txt'
three_months_file = 'three_months_keys.txt'  # New file for 3 months subscription keys
six_months_file = 'six_month_keys.txt'
one_year_file = 'one_year_keys.txt'
one_day_file = 'one_day_keys.txt'

REDIRECT_LINK = "https://dzrtalert.com/"
CHANNEL_CHAT_ID = "-1002177577143"  # Replace with your private channel chat ID
USER_SECRET_FILE = 'user_secret.txt'
CHANNEL_URL = "https://t.me/+6DGVdy4JeQQ3NTM0"  # Replace with your actual channel URL
TRIAL_CHANNEL_URL = "https://t.me/+vOe2F_58VkdiNjlk"  # Replace with your trial channel URL
ADMIN_URL = "http://t.me/IT_Support2"  # Replace with your actual admin URL


file_lock = Lock()

def load_keys(file_name):
    with file_lock:
        if os.path.exists(file_name):
            with open(file_name, 'r') as file:
                return file.read().splitlines()
        return []

one_month_keys = load_keys(one_month_file)
three_months_keys = load_keys(three_months_file)  # تحميل مفاتيح 3 أشهر
six_months_keys = load_keys(six_months_file)
one_year_keys = load_keys(one_year_file)
one_day_keys = load_keys(one_day_file)

def save_keys(file_name, keys):
    with file_lock:
        with open(file_name, 'w') as file:
            for key in keys:
                file.write(f"{key}\n")

def load_user_secrets():
    with file_lock:
        if os.path.exists(USER_SECRET_FILE):
            with open(USER_SECRET_FILE, 'r') as file:
                return file.read().splitlines()
        return []

def save_user_secrets(data):
    with file_lock:
        with open(USER_SECRET_FILE, 'w') as file:
            for line in data:
                file.write(f"{line}\n")

def user_secret_count(subscription_type):
    user_secrets = load_user_secrets()
    return sum(1 for line in user_secrets if subscription_type in line)

def user_already_has_trial(user_id):
    user_secrets = load_user_secrets()
    for line in user_secrets:
        if str(user_id) in line and "one_day_trial" in line:
            return True
    return False

def check_subscription_expiry(user_id):
    user_secrets = load_user_secrets()
    current_date = datetime.now()
    for line in user_secrets:
        parts = line.strip().split(':')
        if len(parts) >= 5 and parts[0] == str(user_id):
            start_date = datetime.strptime(parts[4], '%Y-%m-%d')
            expiry_date = start_date
            if parts[3] == "1 day":
                expiry_date += timedelta(days=1)
            elif parts[3] == "1 month":
                expiry_date += timedelta(days=30)
            elif parts[3] == "3 months":
                expiry_date += timedelta(days=90)
            elif parts[3] == "6 months":
                expiry_date += timedelta(days=180)
            elif parts[3] == "1 year":
                expiry_date += timedelta(days=365)
            if current_date <= expiry_date:
                return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    one_day_trial_count = user_secret_count("one_day_trial")
    keyboard = [
        [InlineKeyboardButton("حالة الاشتراك", callback_data='subscription_status')],
        [InlineKeyboardButton("تفعيل الاشتراك", callback_data='subscribe')],
        [InlineKeyboardButton("قنوات التنبيهات", callback_data='notification_channels')]
    ]
    if one_day_trial_count < 1000:
        keyboard.append([InlineKeyboardButton("تجربة ليوم واحد", callback_data='one_day_trial')])
    message = '''💥مرحباً بك في بوت تنبيهات DZRT💥
هذا البوت يساعدك على تتبع منتجات DZRT والحصول على إشعارات عندما تكون متوفرة قم بالدخول الى قنوات المنتجات التي تريد تلقي الإشعارات عنها، واستمتع بتجربة تسوق مميزة معنا.
للدخول الى قناة المناقشات الخاصة بمستخدمي البوت https://t.me/dzrt1_botG
للدعم الفني :
http://t.me/IT_Support2
ولشراء الاشتراكات يرجى زياره موقعنا الالكتروني https://dez-store.com
.............................................
'''
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text(message, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(message, reply_markup=reply_markup)
    return SUBSCRIBE

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user = update.effective_user  # استخدم update.effective_user لمعالجة استعلامات الاسترجاع
    if query.data == 'subscribe':
        keyboard = [
            [InlineKeyboardButton("العودة إلى القائمة الرئيسية", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="أدخل الرمز للاشتراك في :", reply_markup=reply_markup)
        return CODE
    elif query.data == 'main_menu':
        await start(update, context)
        return SUBSCRIBE
    elif query.data == 'one_day_trial':
        user_id = user.id if user.id is not None else user.username
        if not user_already_has_trial(user_id):
            nameofuser = user.username if user.username is not None else user.full_name
            add_user_secret(user_id, nameofuser, "one_day_trial", "1 day")
            keyboard = [[InlineKeyboardButton("الانضمام إلى ", url=CHANNEL_URL)]]
            keyboard.append([InlineKeyboardButton("العودة إلى القائمة الرئيسية", callback_data='main_menu')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "🎉 لقد قمت بتفعيل تجربة ليوم واحد! استخدم الزر أدناه للانضمام إلى .",
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text("لقد قمت بالفعل بتفعيل تجربة ليوم واحد.")
        return ConversationHandler.END
    elif query.data == 'subscription_status':
        user_id = user.id if user.id is not None else user.username
        user_secrets = load_user_secrets()
        subscription_info = None
        for line in user_secrets:
            parts = line.strip().split(':')
            if len(parts) >= 5 and parts[0] == str(user_id):
                subscription_info = parts
                break
        if subscription_info:
            status_message = (
                f"👤 المستخدم: {subscription_info[1]}\n"
                f"📅 نوع الاشتراك: {subscription_info[3]}\n"
                f"🔑 الرمز: {subscription_info[2]}\n"
                f"📅 تاريخ الانتهاء: {subscription_info[4]}"
            )
        else:
            status_message = "لا يوجد اشتراك مفعل."
        keyboard = [
            [InlineKeyboardButton("العودة إلى القائمة الرئيسية", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=status_message, reply_markup=reply_markup)
        return SUBSCRIBE
    elif query.data == 'notification_channels':
        user_id = user.id if user.id is not None else user.username
        if check_subscription_expiry(user_id):
            keyboard = [
                [InlineKeyboardButton("العودة إلى القائمة الرئيسية", callback_data='main_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "انتهى اشتراكك. لإعادة تفعيل اشتراكك، يرجى الذهاب إلى الرابط التالي للحصول على الرمز: "
                f"{REDIRECT_LINK}", reply_markup=reply_markup)
            return SUBSCRIBE
        else:
            keyboard = [
                [InlineKeyboardButton("كل النكهات", url=CHANNEL_URL)],
                [InlineKeyboardButton("سبايسي زيست", url="https://t.me/+Q79LQ_Ly7N5mYTdk")],
                [InlineKeyboardButton("إيدجي منت", url="https://t.me/+UNDAzzUKH-swMDlk")],
                [InlineKeyboardButton("منت فيوجن", url="https://t.me/+WI8ILPupzAA0YmVk")],
                [InlineKeyboardButton("بيربل مست", url="https://t.me/+3AD6xLsyWp8wNGRk")],
                [InlineKeyboardButton("ايسي راش", url="https://t.me/+lITpa5AOnL05Zjhk")],
                [InlineKeyboardButton("جاردن منت", url="https://t.me/+wtKwavQQ-YMxMTY8")],
                [InlineKeyboardButton("سي سايد فروست", url="https://t.me/+spJ2WAsVO8gyNWY8")],
                [InlineKeyboardButton("هايلاند بيريز", url="https://t.me/+31Q2qXn2rTI5Mjdk")],
                [InlineKeyboardButton("تمرة", url="https://t.me/+BPJZNnP61DtmYmM8")],
                [InlineKeyboardButton("سمرة", url="https://t.me/+kDifLhKNIzkyN2Vk")],
                [InlineKeyboardButton("هيلة", url="https://t.me/+mABq5-FBwrw5ZjE0")],
                [InlineKeyboardButton("العودة إلى القائمة الرئيسية", callback_data='main_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text("🎉 لديك اشتراك نشط! استخدم الأزرار أدناه للانضمام إلى القنوات.", reply_markup=reply_markup)
        return SUBSCRIBE
    return ConversationHandler.END

def check_user_secret(user_id, code):
    user_secrets = load_user_secrets()
    for line in user_secrets:
        parts = line.strip().split(':')
        if len(parts) >= 5 and parts[0] == str(user_id) and parts[2] == code:
            return True
    return False

def add_user_secret(user_id, nameofuser, code, subscription_type):
    current_date = datetime.now()
    user_secrets = load_user_secrets()
    updated = False
    for i, line in enumerate(user_secrets):
        parts = line.strip().split(':')
        if parts[0] == str(user_id):
            user_secrets[i] = f"{user_id}:{nameofuser}:{code}:{subscription_type}:{current_date.strftime('%Y-%m-%d')}"
            updated = True
            break
    if not updated:
        user_secrets.append(f"{user_id}:{nameofuser}:{code}:{subscription_type}:{current_date.strftime('%Y-%m-%d')}")
    save_user_secrets(user_secrets)

async def activate_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    code = update.message.text
    user_id = user.id if user.id is not None else user.username
    nameofuser = user.username if user.username is not None else user.full_name
    success = False
    subscription_type = ""
    if code in one_month_keys:
        one_month_keys.remove(code)
        save_keys(one_month_file, one_month_keys)
        add_user_secret(user_id, nameofuser, code, "1 month")
        subscription_type = "1 month"
        success = True
    elif code in three_months_keys:
        three_months_keys.remove(code)
        save_keys(three_months_file, three_months_keys)  # حفظ مفاتيح 3 أشهر
        add_user_secret(user_id, nameofuser, code, "3 months")
        subscription_type = "3 months"
        success = True
    
    elif code in one_year_keys:
        one_year_keys.remove(code)
        save_keys(one_year_file, one_year_keys)
        add_user_secret(user_id, nameofuser, code, "1 year")
        subscription_type = "1 year"
        success = True
    elif code in one_day_keys:
        one_day_keys.remove(code)
        save_keys(one_day_file, one_day_keys)
        add_user_secret(user_id, nameofuser, code, "1 day")
        subscription_type = "1 day"
        success = True
    if success:
        
        await update.message.reply_text("🎉 تم تفعيل الاشتراك بنجاح! استخدم الأمر /start للانضمام إلى القنوات.")
        
        # Send subscription details to the channel
        subscription_details = (
            f"👤 المستخدم: {nameofuser}\n"
            f"📅 نوع الاشتراك: {subscription_type}\n"
            f"🔑 الرمز: {code}\n"
            f"📅 تاريخ البدء: {datetime.now().strftime('%Y-%m-%d')}"
        )
        await context.bot.send_message(chat_id=CHANNEL_CHAT_ID, text=f"تم تفعيل اشتراك جديد:\n{subscription_details}")
    else:
        await update.message.reply_text(f"الرمز غير صحيح. يرجى المحاولة مرة أخرى أو التواصل مع المسؤول: {ADMIN_URL}")
    return ConversationHandler.END

async def check_subscriptions(context: ContextTypes.DEFAULT_TYPE):
    user_secrets = load_user_secrets()
    current_date = datetime.now()
    expired_users = []
    for line in user_secrets:
        parts = line.strip().split(':')
        if len(parts) >= 5:
            user_id = parts[0]
            start_date = datetime.strptime(parts[4], '%Y-%m-%d')
            expiry_date = start_date
            if parts[3] == "1 day":
                expiry_date += timedelta(days=1)
            elif parts[3] == "1 month":
                expiry_date += timedelta(days=30)
            elif parts[3] == "3 months":
                expiry_date += timedelta(days=90)
            elif parts[3] == "6 months":
                expiry_date += timedelta(days=180)
            elif parts[3] == "1 year":
                expiry_date += timedelta(days=365)
            if current_date > expiry_date:
                expired_users.append(user_id)
    
    for user_id in expired_users:
        try:
            await context.bot.send_message(chat_id=user_id, text=f"انتهى اشتراكك. يرجى زيارة {REDIRECT_LINK} لإعادة تفعيله.")
        except Exception as e:
            logger.error(f"خطأ في إرسال الرسالة إلى المستخدم {user_id}: {e}")

def main():
    application = Application.builder().token("7063252878:AAG2Zk4CTCWOBYQjIXaKNpcIwmcm3yLcBX8").build()

    # جدولة وظيفة التحقق من الاشتراكات لتعمل كل دقيقة
    job_queue = application.job_queue
    job_queue.run_repeating(check_subscriptions, interval=timedelta(minutes=1440), first=timedelta(seconds=10))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SUBSCRIBE: [CallbackQueryHandler(button)],
            CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, activate_subscription)],
        },
        fallbacks=[CommandHandler('start', start)],
    )
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()