import logging
import requests
import json
import os
import sys
import re
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8') if 'io' in globals() else sys.stdout
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

BOT_TOKEN = "8998738234:AAGpV1zS4miYRC9AxNpSHvJNyWPgkfI9-U4"
PANEL_1_KEY = "ZNX_5GJKQ6O8MT1F20MSW2G9K4V9"
TARGET_GROUP_CHAT_ID = -1005155008461

sent_otps_cache = set()

def extract_pure_code(full_text):
    text = str(full_text).strip()
    match = re.search(r'\b\d{4,8}\b', text)
    return match.group(0) if match else text

def get_auto_country_info(number_str):
    clean_num = re.sub(r'\D', '', str(number_str))
    
    country_map = [
        ("374", "🇦🇲", "ARMENIA", "AM"),
        ("261", "🇲🇬", "MADAGASCAR", "MG"),
        ("992", "🇹🇯", "TAJIKISTAN", "TJ"),
        ("380", "🇺🇦", "UKRAINE", "UA"),
        ("224", "🇬🇳", "GUINEA", "GN"),
        ("228", "🇹🇬", "TOGO", "TG"),
        ("237", "🇨🇲", "CAMEROON", "CM"),
        ("225", "🇨🇮", "IVORY COAST", "CI"),
        ("880", "🇧🇩", "BANGLADESH", "BD"),
        ("966", "🇸🇦", "SAUDI ARABIA", "SA"),
        ("258", "🇲🇿", "MOZAMBIQUE", "MZ"),
        ("7",   "🇷🇺", "RUSSIA", "RU"),
        ("91",  "🇮🇳", "INDIA", "IN"),
        ("1",   "🇺🇸", "USA", "US"),
        ("44",  "🇬🇧", "UK", "GB")
    ]
    
    for prefix, flag, name, short in country_map:
        if clean_num.startswith(prefix):
            return flag, f"{name} ({short})"
            
    if len(clean_num) >= 3:
        return "🌍", f"INT (+{clean_num[:3]})"
    return "🌍", "INTERNATIONAL"

async def auto_otp_checker(context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get('https://api.zenexnetwork.com/v1/numsuccess/info', headers={'mapikey': PANEL_1_KEY}, timeout=5)
        if response.status_code == 200:
            res1 = response.json()
            if res1.get('meta', {}).get('code') == 200:
                for item in res1.get('data', {}).get('otps', []):
                    num = str(item.get('number')).strip()
                    raw_otp = str(item.get('otp', '')).strip()
                    if not raw_otp:
                        continue
                    
                    otp_text = extract_pure_code(raw_otp)
                    service = str(item.get('service', 'Facebook')).strip()
                    api_id = str(item.get('id', item.get('_id', ''))).strip()
                    
                    unique_signature = f"id_{api_id}" if api_id else f"num_{num}_otp_{otp_text}_srv_{service}"
                    if unique_signature in sent_otps_cache:
                        continue
                    
                    sent_otps_cache.add(unique_signature)
                    if len(sent_otps_cache) > 1000:
                        sent_otps_cache.pop()
                    
                    flag, c_name = get_auto_country_info(num)
                    
                    masked_num = num[:-2] + "**" if len(num) > 2 else num
                    msg_text = f"<b>FAST SMS OTP x TNE</b>                                      <i>admin</i>\n{flag} <b>{c_name.split(' ')[0]}</b> | 📱 <code>{masked_num}</code> | 🟢 <i>{service}</i>"
                    
                    try:
                        await context.bot.send_message(chat_id=TARGET_GROUP_CHAT_ID, text=msg_text, parse_mode="HTML")
                    except Exception as e:
                        print("Send Error:", e)
    except Exception as e:
        print("API Error:", e)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    
    keyboard = [
        [KeyboardButton("📞 Get API Number"), KeyboardButton("⚙️ Set Range")],
        [KeyboardButton("📱 Get Number"), KeyboardButton("🔴 LIVE TRAFFIC")],
        [KeyboardButton("🛠️ Select Service"), KeyboardButton("👤 Account Profile")],
        [KeyboardButton("📩 Live OTP Inbox")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "👋 **Welcome to Automated OTP Gateway!**\n\n📌 Please choose an option below:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    if update.effective_chat.type != "private":
        return

    text = update.message.text.strip()

    if text == "🔴 LIVE TRAFFIC":
        traffic_text = (
            "<b>🔴LIVE Live Traffic (Last 1 Hours)</b>\n\n"
            "📘 <b>FACEBOOK</b> | 🇿🇼 <b>Zimbabwe Fire</b> | <code>44.0%</code>\n"
            "⬛ <b>TikTok</b> | 🇳🇴 <b>Norway</b> | <code>32.0%</code>\n"
            "📘 <b>FACEBOOK</b> | 🇹🇿 <b>Tanzania</b> | <code>24.0%</code>"
        )
        await update.message.reply_text(traffic_text, parse_mode="HTML")
        return

    if "Get Number" in text or text == "📞 Get API Number":
        loading_msg = await update.message.reply_text("⌛ **Fetching numbers from panel...**", parse_mode="Markdown")
        try:
            resp = requests.post(
                'https://api.zenexnetwork.com/v1/getnum',
                headers={'mapikey': PANEL_1_KEY, 'Content-Type': 'application/json'},
                json={},
                timeout=5
            )
            
            resp_json = resp.json()
            print("API Response:", resp_json)
            
            if resp_json.get('meta', {}).get('code') == 200:
                data_obj = resp_json.get('data', {})
                nums = data_obj.get('numbers', [])
                full_num = data_obj.get('full_number')
                
                all_nums = []
                if nums:
                    all_nums.extend([str(n).replace("+", "").strip() for n in nums])
                elif full_num:
                    all_nums.append(str(full_num).replace("+", "").strip())
                
                if all_nums:
                    first_num = all_nums[0]
                    flag, c_name = get_auto_country_info(first_num)
                    num_lines = "\n".join([f"+{n}" for n in all_nums])
                    
                    result_msg = (
                        f"✅ **API NUMBERS SUCCESSFULLY ASSIGNED**\n\n"
                        f"🌍 Country: {flag} `{c_name}`\n"
                        f"⏳ Status: `Waiting for incoming OTP...`\n\n"
                        f"{num_lines}\n\n"
                        f"💡 *Tap any number above to copy instantly!*"
                    )
                    await loading_msg.edit_text(result_msg, parse_mode="Markdown")
                else:
                    await loading_msg.edit_text("❌ No numbers found in panel stock.", parse_mode="Markdown")
            else:
                err_msg = resp_json.get('meta', {}).get('message', 'Stock Exhausted or API Error.')
                await loading_msg.edit_text(f"❌ {err_msg}", parse_mode="Markdown")
        except Exception as e:
            print("Error:", e)
            await loading_msg.edit_text("⚠️ Error connecting to API server.", parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.job_queue.run_repeating(auto_otp_checker, interval=3, first=1)
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
