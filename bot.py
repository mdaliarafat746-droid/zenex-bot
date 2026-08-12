import logging
import requests
import json
import os
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import sys
import io
import re

# কনসোল এনকোডিং ঠিক রাখা
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

BOT_TOKEN = "8807397397:AAHa3vHLOeyMnc5Y2JditjN9OKZnxmLzLMM"
PANEL_1_KEY = "ZNX_5GJKQ6O8MT1F20MSW2G9K4V9"
ADMIN_CHAT_ID = 6470943912  
TARGET_GROUP_CHAT_ID = -1005155008461  # আপনার নির্দিষ্ট গ্রুপ আইডি

sent_otps_cache = set()

def extract_pure_code(full_text):
    text = str(full_text).strip()
    match = re.search(r'\b\d{4,8}\b', text)
    if match:
        return match.group(0)
    return text

def get_country_info_by_range_or_text(range_str, country_field, raw_text=""):
    r_str = str(range_str)
    c_field = str(country_field).lower()
    combined = f"{r_str} {c_field} {str(raw_text).lower()}".strip()
    
    if r_str.startswith("992") or "tajikistan" in combined or "tj" in c_field:
        return "🇹🇯", "TJ"
    elif r_str.startswith("261") or "madagascar" in combined or "mg" in c_field:
        return "🇲🇬", "MG"
    elif r_str.startswith("380") or "ukraine" in combined or "ua" in c_field:
        return "🇺🇦", "UA"
    elif r_str.startswith("224") or "guinea" in combined or "gn" in c_field:
        return "🇬🇳", "GN"
    elif r_str.startswith("228") or "togo" in combined or "tg" in c_field:
        return "🇹🇬", "TG"
    elif r_str.startswith("237") or "cameroon" in combined or "cm" in c_field:
        return "🇨🇲", "CM"
    elif r_str.startswith("225") or "ivory" in combined or "ci" in c_field or "côte" in combined:
        return "🇨🇮", "CI"
    elif r_str.startswith("880") or "bangladesh" in combined or "bd" in c_field:
        return "🇧🇩", "BD"
    elif r_str.startswith("374") or "armenia" in combined or "am" in c_field:
        return "🇦🇲", "AM"
    elif r_str.startswith("966") or "saudi" in combined or "sa" in c_field:
        return "🇸🇦", "SA"
    else:
        return "🌍", "TG"

# অটো ওটিপি চেকার (সরাসরি আপনার গ্রুপে পাঠাবে)
async def auto_otp_checker(context: ContextTypes.DEFAULT_TYPE):
    try:
        res1 = requests.get('https://api.zenexnetwork.com/v1/numsuccess/info', headers={'mapikey': PANEL_1_KEY}, timeout=3).json()
        if res1.get('meta', {}).get('code') == 200:
            otps_list = res1.get('data', {}).get('otps', [])
            
            for item in otps_list:
                num = str(item.get('number')).strip()
                raw_otp = str(item.get('otp', '')).strip()
                if not raw_otp:
                    continue
                    
                otp_text = extract_pure_code(raw_otp)
                service = str(item.get('service', 'Facebook')).strip()
                
                api_id = str(item.get('id', item.get('_id', ''))).strip()
                if api_id and api_id != '':
                    unique_signature = f"id_{api_id}"
                else:
                    unique_signature = f"num_{num}_otp_{otp_text}_srv_{service}"
                
                if unique_signature in sent_otps_cache:
                    continue
                
                sent_otps_cache.add(unique_signature)
                if len(sent_otps_cache) > 1000:
                    sent_otps_cache.pop()
                    
                country = item.get('country', 'TOGO')
                flag, c_code = get_country_info_by_range_or_text(num, country)
                
                masked_num = num[:-2] + "**" if len(num) > 2 else num
                
                msg_text = (
                    f"<b>FAST SMS OTP x TNE</b>                                      <i>admin</i>\n"
                    f"{flag} <b>{c_code}</b> | 📱 <code>{masked_num}</code> | 🟢 <i>{service}</i>"
                )
                
                keyboard = [
                    [
                        InlineKeyboardButton("📢 Channel", url="https://t.me/your_channel_link"),
                        InlineKeyboardButton(f"🔑 {otp_text}", callback_data="dummy_otp")
                    ],
                    [
                        InlineKeyboardButton("📞 Get Number", callback_data="get_new_number_action")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await context.bot.send_message(
                    chat_id=TARGET_GROUP_CHAT_ID, 
                    text=msg_text, 
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
    except Exception as e:
        print("Error in auto_otp_checker:", e)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return

    # এখানে স্ক্রিনশটের মতো 'GET NUMBER' এবং 'LIVE TRAFFIC' বাটন যুক্ত করা হয়েছে
    keyboard = [
        [KeyboardButton("📞 Get API Number"), KeyboardButton("⚙️ Set Range")],
        [KeyboardButton("📱 GET NUMBER"), KeyboardButton("🔴 LIVE TRAFFIC")],
        [KeyboardButton("🛠️ Select Service"), KeyboardButton("👤 Account Profile")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    welcome_text = (
        f"👋 **Welcome to Automated OTP Gateway!**\n\n"
        f"✨ Fast, secure, and reliable virtual number & OTP management service.\n"
        f"📌 Please choose an option from the menu below to get started:"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    if update.effective_chat.type != "private":
        return

    text = update.message.text.strip()

    # যদি কেউ '🔴 LIVE TRAFFIC' বাটনে ক্লিক করে
    if text == "🔴 LIVE TRAFFIC":
        traffic_text = (
            "<b>🔴LIVE Live Traffic (Last 1 Hours)</b>\n\n"
            "📘 <b>FACEBOOK</b> | 🇿🇼 <b>Zimbabwe Fire</b> | <code>44.0%</code>\n"
            "⬛ <b>TikTok</b> | 🇳🇴 <b>Norway</b> | <code>32.0%</code>\n"
            "📘 <b>FACEBOOK</b> | 🇹🇿 <b>Tanzania</b> | <code>24.0%</code>"
        )
        await update.message.reply_text(traffic_text, parse_mode="HTML")
        return

    if text == "📱 GET NUMBER" or text == "📱 Get Number" or text == "📞 Get API Number":
        loading_msg = await update.message.reply_text("⌛ **Fetching numbers from panel...**", parse_mode="Markdown")
        
        try:
            resp = requests.post(
                'https://api.zenexnetwork.com/v1/getnum',
                headers={'mapikey': PANEL_1_KEY, 'Content-Type': 'application/json'},
                json={"range": "228", "is_national": False, "remove_plus": False},
                timeout=5
            ).json()
            
            if resp.get('meta', {}).get('code') == 200:
                data_obj = resp.get('data', {})
                numbers_list = data_obj.get('numbers', [])
                full_num_single = data_obj.get('full_number')
                
                nums_to_show = []
                if numbers_list:
                    for n in numbers_list:
                        n_str = str(n).replace("+", "").strip()
                        nums_to_show.append(n_str)
                elif full_num_single:
                    n_str = str(full_num_single).replace("+", "").strip()
                    nums_to_show.append(n_str)
                
                if nums_to_show:
                    num_lines = "\n".join([f"+{n}" for n in nums_to_show])
                    result_msg = (
                        f"✅ **API NUMBERS SUCCESSFULLY ASSIGNED**\n\n"
                        f"🌍 Country: 🇹🇬 `TOGO (TG)`\n"
                        f"📌 Range: `228967XXX` | Service: `All`\n"
                        f"⏳ Status: `Waiting for incoming OTP...`\n\n"
                        f"{num_lines}\n\n"
                        f"💡 *Tap any number above to copy instantly!*"
                    )
                    await loading_msg.edit_text(result_msg, parse_mode="Markdown")
                else:
                    await loading_msg.edit_text("❌ No numbers found in response.", parse_mode="Markdown")
            else:
                await loading_msg.edit_text("❌ Stock Exhausted or API Error.", parse_mode="Markdown")
        except Exception as e:
            await loading_msg.edit_text(f"⚠️ Error: {str(e)}", parse_mode="Markdown")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer("Working...")
    except:
        pass

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.job_queue.run_repeating(auto_otp_checker, interval=1, first=1)
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(button_click))
    
    print("Bot is running successfully...")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
