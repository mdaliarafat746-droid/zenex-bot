import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

BOT_TOKEN = "8998738234:AAGpV1zS4miYRC9AxNpSHvJNyWPgkfI9-U4"
API_KEY = "ZNX_5GJKQ6O8MT1F20MSW2G9K4V9"

ADMIN_CHAT_ID = "6470943912"  

notified_otps = set()

def get_country_info_by_range_or_text(range_str, text):
    combined = f"{range_str} {text}".lower()
    
    if "992" in range_str:
        return "🇲🇦", "MA"
    elif "261" in range_str:
        return "🇲🇬", "MG"
    elif "380" in range_str:
        return "🇺🇦", "UA"
    elif "224" in range_str:
        return "🇬🇳", "GN"
    elif "228" in range_str:
        return "🇹🇬", "TG"
    elif "237" in range_str:
        return "🇨🇲", "CM"
    
    if "malaysia" in combined:
        return "🇲🇾", "MY"
    elif "morocco" in combined:
        return "🇲🇦", "MA"
    elif "russian" in combined or "russia" in combined:
        return "🇷🇺", "RU"
    elif "sudan" in combined:
        return "🇸🇩", "SD"
    elif "tanzania" in combined:
        return "🇹🇿", "TZ"
    elif "zimbabwe" in combined:
        return "🇿🇼", "ZW"
    elif "algeria" in combined:
        return "🇩🇿", "DZ"
    elif "bolivia" in combined:
        return "🇧🇴", "BO"
    elif "madagascar" in combined:
        return "🇲🇬", "MG"
    elif "egypt" in combined:
        return "🇪🇬", "EG"
    elif "togo" in combined:
        return "🇹🇬", "TG"
    elif "india" in combined:
        return "🇮🇳", "IN"
    elif "ghana" in combined:
        return "🇬🇭", "GH"
    elif "brazil" in combined:
        return "🇧🇷", "BR"
    else:
        return "🌐", "GLOBAL"

async def auto_otp_checker(context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get(
            'https://api.zenexnetwork.com/v1/numsuccess/info',
            headers={'mapikey': API_KEY},
            timeout=10
        )
        res_data = response.json()
        
        if res_data.get('meta', {}).get('code') == 200:
            otps_list = res_data.get('data', {}).get('otps', [])
            
            for item in otps_list:
                nid = item.get('nid')
                if nid and nid not in notified_otps:
                    notified_otps.add(nid)
                    if len(notified_otps) > 1000:
                        notified_otps.pop()
                    
                    num = item.get('number')
                    otp_text = item.get('otp')
                    country = item.get('country', 'Unknown')
                    service = item.get('service', 'Facebook')
                    
                    flag, c_code = get_country_info_by_range_or_text("", country)
                    
                    alert_msg = (
                        f"⚔️ **{service} Received.**\n"
                        f"❓ {flag} {c_code}\n"
                        f"📞 `{num}`\n"
                        f"👥 Earned: +$0.0030\n"
                        f"💰 Balance: $0.0180\n\n"
                        f"🔑 `{otp_text}`"
                    )
                    
                    await context.bot.send_message(
                        chat_id=ADMIN_CHAT_ID,
                        text=alert_msg,
                        parse_mode="Markdown"
                    )
    except Exception as e:
        pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("📱 Get Number"), KeyboardButton("📩 Check Live OTP")],
        [KeyboardButton("💰 Balance"), KeyboardButton("👤 Profile")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "স্বাগতম! Zenex অটো-ওটিপি প্যানেলে আপনাকে স্বাগতম:",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📱 Get Number":
        loading_msg = await update.message.reply_text("প্যানেল থেকে রেঞ্জ ও শর্ট নেম লোড করা হচ্ছে...")
        
        try:
            response = requests.get(
                'https://api.zenexnetwork.com/v1/active-ranges',
                headers={'mapikey': API_KEY},
                timeout=10
            )
            res_data = response.json()
            
            if res_data.get('success') == True:
                active_ranges = res_data.get('data', {}).get('active_ranges', [])
                
                keyboard = []
                for item in active_ranges:
                    rng = str(item.get('range', ''))
                    srv = item.get('service', 'Facebook')
                    
                    raw_info = f"{item.get('country', '')} {item.get('region', '')} {item.get('location', '')} {srv}"
                    flag, c_code = get_country_info_by_range_or_text(rng, raw_info)
                    
                    mode_type = None
                    for key in ['mode', 'type', 'category', 'sub_service', 'tag', 'status', 'label']:
                        if item.get(key) and str(item.get(key)).strip() != "":
                            mode_type = item.get(key)
                            break
                    
                    if not mode_type:
                        mode_type = "New Fb" if "new" in str(item).lower() else "PC Clone"

                    btn_text = f"{flag} {c_code} | {rng} | {srv} ({mode_type})"
                    keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"get3_{rng}_{c_code}")])
                
                keyboard.append([InlineKeyboardButton("🔙 Close", callback_data="close_menu")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await loading_msg.edit_text(
                    "⚡ **ACTIVE RANGES & COUNTRY CODES**\n\n_আপনার পছন্দের রেঞ্জটি সিলেক্ট করুন:_",
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
            else:
                await loading_msg.edit_text("❌ প্যানেল থেকে রেঞ্জ লোড করতে ব্যর্থ হয়েছে।")
                
        except Exception as e:
            await loading_msg.edit_text(f"কানেকশন এরর: {e}")
            
    elif text == "📩 Check Live OTP":
        loading_msg = await update.message.reply_text("প্যানেল থেকে ইনকামিং ওটিপি চেক করা হচ্ছে...")
        try:
            response = requests.get(
                'https://api.zenexnetwork.com/v1/numsuccess/info',
                headers={'mapikey': API_KEY},
                timeout=10
            )
            res_data = response.json()
            if res_data.get('meta', {}).get('code') == 200:
                otps_list = res_data.get('data', {}).get('otps', [])
                if len(otps_list) > 0:
                    msg = "📥 **Live OTP Payloads:**\n\n"
                    for item in otps_list:
                        num = item.get('number')
                        otp_text = item.get('otp')
                        country = item.get('country')
                        flag, c_code = get_country_info_by_range_or_text("", country)
                        msg += f"📞 নম্বর: `{num}`\n{flag} কোড: {c_code}\n💬 এসএমএস: __{otp_text}__\n-----------------------------------\n"
                    await loading_msg.edit_text(msg, parse_mode="Markdown")
                else:
                    await loading_msg.edit_text("📭 কোনো নতুন OTP আসেনি।")
            else:
                await loading_msg.edit_text("❌ ওটিপি ফেচ করতে সমস্যা হয়েছে।")
        except Exception as e:
            await loading_msg.edit_text(f"এরর: {e}")
            
    elif text == "💰 Balance":
        await update.message.reply_text("Zenex API কানেকশন সক্রিয় রয়েছে।")
    elif text == "👤 Profile":
        await update.message.reply_text(f"আপনার টেলিগ্রাম আইডি: {update.effective_user.id}")
    else:
        await update.message.reply_text(f"আপনি সিলেক্ট করেছেন: {text}")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data_code = query.data

    if data_code.startswith("get3_"):
        parts = data_code.split("_")
        range_value = parts[1]
        c_code = parts[2] if len(parts) > 2 else "GLOBAL"
        
        await query.edit_message_text(text="🔄 প্যানেল থেকে একসাথে ৩টি নম্বর অ্যাসাইন করা হচ্ছে, দয়া করে অপেক্ষা করুন...")

        assigned_numbers = []
        detected_c_code = c_code
        
        try:
            for _ in range(3):
                response = requests.post(
                    'https://api.zenexnetwork.com/v1/getnum',
                    headers={
                        'mapikey': API_KEY,
                        'Content-Type': 'application/json'
                    },
                    json={
                        "range": range_value,
                        "is_national": False,
                        "remove_plus": False
                    },
                    timeout=10
                )
                res = response.json()
                if res.get('meta', {}).get('code') == 200:
                    num_data = res.get('data', {})
                    assigned_numbers.append(num_data.get('full_number'))
                    if num_data.get('country'):
                        _, detected_c_code = get_country_info_by_range_or_text(range_value, num_data.get('country'))

            if len(assigned_numbers) > 0:
                flag, final_c_code = get_country_info_by_range_or_text(range_value, detected_c_code)
                
                keyboard = [
                    [InlineKeyboardButton("🔄 Next Number", callback_data=f"get3_{range_value}_{c_code}"), 
                     InlineKeyboardButton("🌐 Country", callback_data="back_to_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                result_msg = (
                    f"{flag} **[{final_c_code}] Number Assigned**\n\n"
                    f"💰 Per OTP : 0.30 TK\n\n"
                )
                for num in assigned_numbers:
                    result_msg += f"{flag} `{num}`  📋\n"

                await query.edit_message_text(result_msg, parse_mode="Markdown", reply_markup=reply_markup)
            else:
                await query.edit_message_text("❌ দুঃখিত, বর্তমানে এই রেঞ্জে কোনো নম্বর স্টক নেই।")
                
        except Exception as e:
            await query.edit_message_text(f"এরর: {e}")

    elif data_code == "back_to_menu":
        await query.message.delete()
        await query.message.reply_text("মূল মেনু থেকে '📱 Get Number' এ ক্লিক করুন।")

    elif data_code == "close_menu":
        await query.message.delete()

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    job_queue = app.job_queue
    job_queue.run_repeating(auto_otp_checker, interval=5, first=3)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(button_click))

    print("Zenex Auto-OTP Bot is running with background sync...")
    app.run_polling()

if __name__ == '__main__':
    main()
