import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import sys
import io

# উইন্ডোজ টার্মিনালে ইউনিকোড এনকোডিং ঠিক রাখার জন্য
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

BOT_TOKEN = "8998738234:AAGpV1zS4miYRC9AxNpSHvJNyWPgkfI9-U4"
API_KEY = "ZNX_5GJKQ6O8MT1F20MSW2G9K4V9"

# ইতিমধ্যে যে ওটিপিগুলো পাঠানো হয়েছে তা ট্র্যাক করার জন্য সেট (যেন ডাবল মেসেজ না যায়)
notified_otps = set()

# দেশের নাম বা সার্ভিস অনুযায়ী সঠিক ফ্লাগ ইমোজি নির্ধারণ করার ফাংশন
def get_flag_by_text(text):
    text = text.lower()
    if "egypt" in text:
        return "🇪🇬"
    elif "togo" in text:
        return "🇹🇬"
    elif "uk" in text or "united kingdom" in text or "britain" in text:
        return "🇬🇧"
    elif "usa" in text or "united states" in text:
        return "🇺🇸"
    elif "india" in text:
        return "🇮🇳"
    elif "ghana" in text:
        return "🇬🇭"
    elif "brazil" in text:
        return "🇧🇷"
    else:
        return "🌐"

# ব্যাকগ্রাউন্ডে স্বয়ংক্রিয়ভাবে ওটিপি চেক করার ফাংশন (প্রতি ৫ সেকেন্ড পর পর চলবে)
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
                # যদি এই ওটিপিটি আগে পাঠানো না হয়ে থাকে
                if nid and nid not in notified_otps:
                    notified_otps.add(nid)
                    
                    num = item.get('number')
                    otp_text = item.get('otp')
                    country = item.get('country', 'Unknown')
                    op = item.get('operator', '')
                    
                    flag = get_flag_by_text(country)
                    
                    alert_msg = (
                        f"🚨 **নতুন OTP চলে এসেছে!** 🚨\n\n"
                        f"{flag} নম্বর: `{num}`\n"
                        f"📡 অপারেটর: {op}\n"
                        f"💬 কোড/এসএমএস:\n`{otp_text}`"
                    )
                    
                    # বটের ভেতর যাদের চ্যাট আইডি সেভ আছে তাদের সবাইকে বা নির্দিষ্ট গ্রুপে পাঠানোর ব্যবস্থা
                    # এখানে যদি কোনো নির্দিষ্ট চ্যাট আইডিতে পাঠাতে চান সেটি দিতে পারেন
                    # আপাতত জাস্ট সিস্টেম রান রাখছি
    except Exception as e:
        pass

# /start কমান্ড এবং মূল মেনু
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("📱 Get Number"), KeyboardButton("📩 Check Live OTP")],
        [KeyboardButton("💰 Balance"), KeyboardButton("👤 Profile")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "স্বাগতম! Zenex অটো-ওটিপি প্যানেলে আপনাকে স্বাগতম। নম্বর নিলে ওটিপি অটো চলে আসবে:",
        reply_markup=reply_markup
    )

# মেসেজ হ্যান্ডলার
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📱 Get Number":
        loading_msg = await update.message.reply_text("প্যানেল থেকে লাইভ রেঞ্জ লোড করা হচ্ছে...")
        
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
                row = []
                for item in active_ranges:
                    rng = item.get('range')
                    srv = item.get('service')
                    
                    flag = get_flag_by_text(srv)
                    btn_text = f"{flag} {srv} ({rng})"
                    
                    row.append(InlineKeyboardButton(btn_text, callback_data=f"get3_{rng}_{srv}"))
                    if len(row) == 2:
                        keyboard.append(row)
                        row = []
                
                if row:
                    keyboard.append(row)
                
                keyboard.append([InlineKeyboardButton("🔙 Close", callback_data="close_menu")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await loading_msg.edit_text(
                    "⚡ **Select Service / Range**\n\n_নম্বর নিতে নিচের রেঞ্জগুলোতে ক্লিক করুন:_",
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
            else:
                await loading_msg.edit_text("❌ প্যানেল থেকে রেঞ্জ লোড করতে ব্যর্থ হয়েছে।")
                
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
                        msg += f"📞 নম্বর: `{num}`\n🌍 দেশ: {country}\n💬 এসএমএস: __{otp_text}__\n-----------------------------------\n"
                    await loading_msg.edit_text(msg, parse_mode="Markdown")
                else:
                    await loading_msg.edit_text("📭 কোনো নতুন OTP আসেনি।")
            else:
                await loading_msg.edit_text("❌ ওটিপি ফেচ করতে সমস্যা হয়েছে।")
        except Exception as e:
            await loading_msg.edit_text(f"এরর: {e}")
            
    elif text == "💰 Balance":
        await update.message.reply_text("Zenex API কানেকশন সক্রিয় রয়েছে।")
    elif text == "👤 Profile":
        await update.message.reply_text(f"আপনার টেলিগ্রাম আইডি: {update.effective_user.id}")
    else:
        await update.message.reply_text(f"আপনি সিলেক্ট করেছেন: {text}")

# ইনলাইন বাটন ক্লিক হ্যান্ডলার
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data_code = query.data

    if data_code.startswith("get3_"):
        parts = data_code.split("_")
        range_value = parts[1]
        service_name = parts[2] if len(parts) > 2 else "Number"
        
        await query.edit_message_text(text="🔄 প্যানেল থেকে একসাথে ৩টি নম্বর অ্যাসাইন করা হচ্ছে, দয়া করে অপেক্ষা করুন...")

        assigned_numbers = []
        detected_country = service_name
        
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
                        detected_country = num_data.get('country')

            if len(assigned_numbers) > 0:
                flag = get_flag_by_text(detected_country)
                
                keyboard = [
                    [InlineKeyboardButton("🔄 Next Number", callback_data=f"get3_{range_value}_{service_name}"), 
                     InlineKeyboardButton("🌐 Country", callback_data="back_to_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                result_msg = (
                    f"{flag} **{detected_country} Number Assigned**\n\n"
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

    # JobQueue ব্যবহার করে অটো ওটিপি চেকার ব্যাকগ্রাউন্ডে চালু করা (প্রতি ৫ সেকেন্ড পর পর)
    job_queue = app.job_queue
    job_queue.run_repeating(auto_otp_checker, interval=5, first=3)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(button_click))

    print("Zenex Auto-OTP Bot is running with background sync...")
    app.run_polling()

if __name__ == '__main__':
    main()
