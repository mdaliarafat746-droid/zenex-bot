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

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

BOT_TOKEN = "8998738234:AAGpV1zS4miYRC9AxNpSHvJNyWPgkfI9-U4"
PANEL_1_KEY = "ZNX_5GJKQ6O8MT1F20MSW2G9K4V9"
ADMIN_CHAT_ID = "6470943912"  

NID_FILE = "notified_nids.json"

def load_nids():
    if os.path.exists(NID_FILE):
        try:
            with open(NID_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    current_time = time.time()
                    return {item: current_time for item in data}
                elif isinstance(data, dict):
                    return data
        except:
            return {}
    return {}

def save_nids(nids_dict):
    try:
        with open(NID_FILE, "w", encoding="utf-8") as f:
            json.dump(nids_dict, f)
    except Exception as e:
        print(f"NID Save Error: {e}")

sent_otps_cache = load_nids()
processed_in_memory = set()

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
        return "🇹🇯", "TJ", "TAJIKISTAN"
    elif r_str.startswith("261") or "madagascar" in combined or "mg" in c_field:
        return "🇲🇬", "MG", "MADAGASCAR"
    elif r_str.startswith("380") or "ukraine" in combined or "ua" in c_field:
        return "🇺🇦", "UA", "UKRAINE"
    elif r_str.startswith("224") or "guinea" in combined or "gn" in c_field:
        return "🇬🇳", "GN", "GUINEA"
    elif r_str.startswith("228") or "togo" in combined or "tg" in c_field:
        return "🇹🇬", "TG", "TOGO"
    elif r_str.startswith("237") or "cameroon" in combined or "cm" in c_field:
        return "🇨🇲", "CM", "CAMEROON"
    elif r_str.startswith("225") or "ivory" in combined or "ci" in c_field or "côte" in combined:
        return "🇨🇮", "CI", "IVORY COAST"
    elif r_str.startswith("880") or "bangladesh" in combined or "bd" in c_field:
        return "🇧🇩", "BD", "BANGLADESH"
    elif r_str.startswith("236") or "central africa" in combined or "cf" in c_field:
        return "🇨🇫", "CF", "CENTRAL AFRICA"
    elif r_str.startswith("229") or "benin" in combined or "bj" in c_field:
        return "🇧🇯", "BJ", "BENIN"
    elif "malaysia" in combined or "my" in c_field:
        return "🇲🇾", "MY", "MALAYSIA"
    elif "morocco" in combined or "ma" in c_field:
        return "🇲🇦", "MA", "MOROCCO"
    elif "russia" in combined or "ru" in c_field:
        return "🇷🇺", "RU", "RUSSIA"
    elif "united kingdom" in combined or "uk" in combined or "gb" in c_field:
        return "🇬🇧", "GB", "UNITED KINGDOM"
    elif "sudan" in combined or "sd" in c_field:
        return "🇸🇩", "SD", "SUDAN"
    elif "tanzania" in combined or "tz" in c_field:
        return "🇹🇿", "TZ", "TANZANIA"
    elif "zimbabwe" in combined or "zw" in c_field:
        return "🇿🇼", "ZW", "ZIMBABWE"
    elif "algeria" in combined or "dz" in c_field:
        return "🇩🇿", "DZ", "ALGERIA"
    elif "bolivia" in combined or "bo" in c_field:
        return "🇧🇴", "BO", "BOLIVIA"
    elif "egypt" in combined or "eg" in c_field:
        return "🇪🇬", "EG", "EGYPT"
    elif "india" in combined or "in" in c_field:
        return "🇮🇳", "IN", "INDIA"
    elif "ghana" in combined or "gh" in c_field:
        return "🇬🇭", "GH", "GHANA"
    elif "brazil" in combined or "br" in c_field:
        return "🇧🇷", "BR", "BRAZIL"
    else:
        if r_str.startswith("236"):
            return "🇨🇫", "CF", "CENTRAL AFRICA"
        elif r_str.startswith("229"):
            return "🇧🇯", "BJ", "BENIN"
        return "🌍", "MZ", "MOZAMBIQUE"

def get_service_emoji(service_name):
    srv = str(service_name).lower()
    if "instagram" in srv:
        return "📸"
    elif "facebook" in srv or "fb" in srv:
        return "FB"
    elif "telegram" in srv:
        return "✈️"
    elif "whatsapp" in srv:
        return "💚"
    else:
        return "🌐"

async def auto_otp_checker(context: ContextTypes.DEFAULT_TYPE):
    try:
        res1 = requests.get('https://api.zenexnetwork.com/v1/numsuccess/info', headers={'mapikey': PANEL_1_KEY}, timeout=10).json()
        if res1.get('meta', {}).get('code') == 200:
            otps_list = res1.get('data', {}).get('otps', [])
            
            current_time = time.time()
            updated = False
            
            expired_keys = [k for k, t in sent_otps_cache.items() if current_time - t > 21600]
            for k in expired_keys:
                del sent_otps_cache[k]
                updated = True

            for item in otps_list:
                num = str(item.get('number')).strip()
                raw_otp = str(item.get('otp', '')).strip()
                otp_text = extract_pure_code(raw_otp)
                service = str(item.get('service', 'Facebook')).strip()
                
                # প্যানেল থেকে আসা ডেটার নিজস্ব ইউনিক আইডি বা সম্পূর্ণ স্ট্রাকচার দিয়ে ইউনিক ফিঙ্গারপ্রিন্ট
                api_id = str(item.get('id', item.get('_id', ''))).strip()
                if api_id and api_id != '':
                    unique_signature = f"id_{api_id}"
                else:
                    unique_signature = f"num_{num}_otp_{otp_text}_srv_{service}"
                
                # যদি ক্যাশ মেমোরি, ফাইল বা রানিং লিস্টে থাকে, তবে নিশ্চিতভাবে স্কিপ করবে
                if unique_signature in sent_otps_cache or unique_signature in processed_in_memory:
                    continue
                
                # রানিং মেমোরি এবং পার্মানেন্ট ক্যাশ দুটিতেই সাথে সাথে এন্ট্রি দেওয়া হচ্ছে
                processed_in_memory.add(unique_signature)
                sent_otps_cache[unique_signature] = current_time
                updated = True
                    
                country = item.get('country', '')
                flag, c_code, _ = get_country_info_by_range_or_text(num, country)
                srv_emoji = get_service_emoji(service)
                
                msg_text = (
                    f"{flag} **{c_code}** {srv_emoji} `+{num}`\n"
                    f"🔐 `{otp_text}`\n"
                )
                
                await context.bot.send_message(
                    chat_id=ADMIN_CHAT_ID, 
                    text=msg_text, 
                    parse_mode="Markdown"
                )
            
            if updated:
                save_nids(sent_otps_cache)
                
    except Exception as e:
        print(f"OTP Checker Error: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("📱 Get Number"), KeyboardButton("📩 Check Live OTP")],
        [KeyboardButton("👤 Profile")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("স্বাগতম! অটো-ওটিপি বোটে আপনাকে স্বাগতম:", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📱 Get Number":
        loading_msg = await update.message.reply_text("⚡ প্যানেল থেকে রেঞ্জ লোড করা হচ্ছে...")
        all_ranges = []
        
        try:
            r1 = requests.get('https://api.zenexnetwork.com/v1/active-ranges', headers={'mapikey': PANEL_1_KEY}, timeout=10).json()
            if r1.get('success') == True:
                for r in r1.get('data', {}).get('active_ranges', []):
                    r['panel_type'] = 'panel1'
                    all_ranges.append(r)
        except Exception as e:
            print(f"P1 Error: {e}")
        
        if len(all_ranges) > 0:
            keyboard = []
            for item in all_ranges[:30]:
                rng = str(item.get('range', ''))
                api_country = item.get('country', '')
                
                flag, c_code, _ = get_country_info_by_range_or_text(rng, api_country, str(item))
                srv = str(item.get('service', 'Facebook'))
                srv_emoji = get_service_emoji(srv)
                
                btn_text = f"{flag} {rng} | {srv_emoji} {srv}"
                keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"get3_{rng}_{c_code}")])
            
            keyboard.append([InlineKeyboardButton("❌ Close Menu", callback_data="close_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            header_text = f"⚡ **ACTIVE RANGES**\n📂 Total Available: `{len(all_ranges)}`\n\n_নিচের তালিকা থেকে আপনার পছন্দের রেঞ্জটি সিলেক্ট করুন:_"
            await loading_msg.edit_text(header_text, parse_mode="Markdown", reply_markup=reply_markup)
        else:
            await loading_msg.edit_text("❌ প্যানেল থেকে কোনো রেঞ্জ পাওয়া যায়নি।")
            
    elif text == "📩 Check Live OTP":
        loading_msg = await update.message.reply_text("ওটিপি চেক করা হচ্ছে...")
        try:
            msg = "📥 **Live OTP Payloads:**\n\n"
            res1 = requests.get('https://api.zenexnetwork.com/v1/numsuccess/info', headers={'mapikey': PANEL_1_KEY}, timeout=10).json()
            if res1.get('meta', {}).get('code') == 200:
                for item in res1.get('data', {}).get('otps', [])[:5]:
                    num = item.get('number')
                    otp_text = extract_pure_code(item.get('otp', ''))
                    country = item.get('country', '')
                    flag, c_code, _ = get_country_info_by_range_or_text(str(num), country)
                    srv_emoji = get_service_emoji(item.get('service', 'Facebook'))
                    msg += f"{flag} **{c_code}** {srv_emoji} `+{num}`\n🔑 `{otp_text}`\n-------------------\n"
            await loading_msg.edit_text(msg, parse_mode="Markdown")
        except Exception as e:
            await loading_msg.edit_text(f"এরর: {e}")
            
    elif text == "👤 Profile":
        await update.message.reply_text(f"আপনার টেলিগ্রাম আইডি: {update.effective_user.id}")
    else:
        pass

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data_code = query.data

    await query.answer()

    if data_code.startswith("get3_"):
        parts = data_code.split("_")
        range_value = parts[1]
        c_code = parts[2] if len(parts) > 2 else "MZ"
        
        await query.edit_message_text(text="🔄 প্যানেল থেকে নম্বর অ্যাসাইন করা হচ্ছে...")

        assigned_numbers = []
        detected_c_code = c_code
        
        try:
            for _ in range(3):
                resp = requests.post(
                    'https://api.zenexnetwork.com/v1/getnum',
                    headers={'mapikey': PANEL_1_KEY, 'Content-Type': 'application/json'},
                    json={"range": range_value, "is_national": False, "remove_plus": False},
                    timeout=10
                ).json()
                if resp.get('meta', {}).get('code') == 200:
                    num_data = resp.get('data', {})
                    full_num = num_data.get('full_number')
                    if full_num:
                        assigned_numbers.append(full_num)
                        _, detected_c_code, _ = get_country_info_by_range_or_text(str(full_num), num_data.get('country', ''))

            if len(assigned_numbers) > 0:
                flag, final_c_code, full_country_name = get_country_info_by_range_or_text(range_value, detected_c_code)
                
                numbers_block = ""
                for num in assigned_numbers:
                    clean_num = str(num).replace("+", "")
                    numbers_block += f"📱 `+{clean_num}`\n"
                
                keyboard = [
                    [InlineKeyboardButton("🔄 Change Number", callback_data=f"get3_{range_value}_{c_code}")],
                    [InlineKeyboardButton("🌐 Change Country", callback_data="back_to_menu")]
                ]
                
                reply_markup = InlineKeyboardMarkup(keyboard)

                result_msg = (
                    f"🌍 **Country:** {flag} **{full_country_name}** ({final_c_code})\n"
                    f"🎟️ **Status:** Waiting for OTP...\n\n"
                    f"{numbers_block}\n"
                    f"_👆 উপরের নম্বরের ওপর ট্যাপ করলেই খুব সহজে কপি হয়ে যাবে!_"
                )

                await query.edit_message_text(result_msg, parse_mode="Markdown", reply_markup=reply_markup)
            else:
                await query.edit_message_text("❌ দুঃখিত, বর্তমানে এই রেঞ্জে কোনো নম্বর স্টক নেই।")
                
        except Exception as e:
            await query.edit_message_text("❌ সার্ভার থেকে রেসপন্স পেতে দেরি হচ্ছে। আবার চেষ্টা করুন।")

    elif data_code == "back_to_menu":
        try:
            loading_msg = query.message
            all_ranges = []
            r1 = requests.get('https://api.zenexnetwork.com/v1/active-ranges', headers={'mapikey': PANEL_1_KEY}, timeout=10).json()
            if r1.get('success') == True:
                for r in r1.get('data', {}).get('active_ranges', []):
                    r['panel_type'] = 'panel1'
                    all_ranges.append(r)
            
            if len(all_ranges) > 0:
                keyboard = []
                for item in all_ranges[:30]:
                    rng = str(item.get('range', ''))
                    api_country = item.get('country', '')
                    flag, c_code, _ = get_country_info_by_range_or_text(rng, api_country, str(item))
                    srv = str(item.get('service', 'Facebook'))
                    srv_emoji = get_service_emoji(srv)
                    btn_text = f"{flag} {rng} | {srv_emoji} {srv}"
                    keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"get3_{rng}_{c_code}")])
                
                keyboard.append([InlineKeyboardButton("❌ Close Menu", callback_data="close_menu")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                header_text = f"⚡ **ACTIVE RANGES**\n📂 Total Available: `{len(all_ranges)}`\n\n_নিচের তালিকা থেকে আপনার পছন্দের রেঞ্জটি সিলেক্ট করুন:_"
                await loading_msg.edit_text(header_text, parse_mode="Markdown", reply_markup=reply_markup)
            else:
                await loading_msg.edit_text("❌ প্যানেল থেকে কোনো রেঞ্জ পাওয়া যায়নি।")
        except:
            await query.message.delete()

    elif data_code == "close_menu":
        await query.message.delete()

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.job_queue.run_repeating(auto_otp_checker, interval=10, first=3)
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(button_click))
    
    print("Ultimate Protected Bot is running...")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
