import logging
import requests
import json
import os
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
            with open(NID_FILE, "r") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_nids(nids_set):
    try:
        nids_list = list(nids_set)[-3000:]
        with open(NID_FILE, "w") as f:
            json.dump(nids_list, f)
    except Exception as e:
        print(f"NID Save Error: {e}")

notified_nids = load_nids()

def extract_pure_code(full_text):
    """সম্পূর্ণ মেসেজ থেকে শুধু সংখ্যা বা ওটিপি কোডটি আলাদা করার ফাংশন"""
    text = str(full_text).strip()
    # সাধারণত ৬ বা ৪ ডিজিটের ওটিপি কোডগুলো আলাদা করার জন্য বা প্রথম সংখ্যা খোঁজার জন্য
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
        return "🌍", "INT", "INTERNATIONAL"

def format_service_name(item):
    srv = str(item.get('service', 'FACEBOOK')).upper()
    full_str = str(item).lower()
    
    if "instagram" in full_str or srv == "INSTAGRAM":
        return "⚡ INSTAGRAM"
    
    if "clone" in full_str or "pc" in full_str:
        return "💻 PC Clone"
    else:
        return "✨ New FB"

async def auto_otp_checker(context: ContextTypes.DEFAULT_TYPE):
    try:
        res1 = requests.get('https://api.zenexnetwork.com/v1/numsuccess/info', headers={'mapikey': PANEL_1_KEY}, timeout=10).json()
        if res1.get('meta', {}).get('code') == 200:
            otps_list = res1.get('data', {}).get('otps', [])
            
            updated = False
            for item in otps_list:
                num = item.get('number')
                raw_otp = item.get('otp', '')
                otp_text = extract_pure_code(raw_otp)  # শুধু সংখ্যা বা কোড ফিল্টার করা হলো
                service = item.get('service', 'Facebook')
                
                unique_signature = f"{num}_{otp_text}"
                
                if unique_signature not in notified_nids:
                    notified_nids.add(unique_signature)
                    updated = True
                        
                    country = item.get('country', '')
                    flag, c_code, _ = get_country_info_by_range_or_text(str(num), country)
                    
                    msg_text = (
                        f"⚔️ **{service} Received.**\n"
                        f"❓ {flag} {country if country else c_code}\n"
                        f"📞 `+{num}`\n"
                        f"👥 Earned: `+$0.0030`\n"
                        f"💰 Balance: `$0.0480`"
                    )
                    
                    # বাটনে শুধু নম্বর এবং শুধু কোড দেখানোর ব্যবস্থা
                    btn_label = f"📞 +{num} 🔑 {otp_text}"
                    keyboard = [[InlineKeyboardButton(btn_label, callback_data=f"copy_{otp_text}")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await context.bot.send_message(
                        chat_id=ADMIN_CHAT_ID, 
                        text=msg_text, 
                        parse_mode="Markdown",
                        reply_markup=reply_markup
                    )
            
            if updated:
                save_nids(notified_nids)
                
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
                formatted_srv = format_service_name(item)
                
                btn_text = f"{flag} {rng} | {formatted_srv}"
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
                    msg += f"[P1] 📞 `{num}` | {flag} {c_code}\n🔑 `{otp_text}`\n-------------------\n"
            await loading_msg.edit_text(msg, parse_mode="Markdown")
        except Exception as e:
            await loading_msg.edit_text(f"এরর: {e}")
            
    elif text == "👤 Profile":
        await update.message.reply_text(f"আপনার টেলিগ্রাম আইডি: {update.effective_user.id}")
    else:
        pass

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data_code = query.data

    if data_code.startswith("get3_"):
        parts = data_code.split("_")
        range_value = parts[1]
        c_code = parts[2] if len(parts) > 2 else "GLOBAL"
        
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

    elif data_code.startswith("copy_"):
        val_to_copy = data_code.split("_", 1)[1]
        await query.answer(text=f"কপি করা হয়েছে: {val_to_copy}", show_alert=True)

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
                    formatted_srv = format_service_name(item)
                    btn_text = f"{flag} {rng} | {formatted_srv}"
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
    
    print("Auto-OTP Bot is running smoothly...")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
