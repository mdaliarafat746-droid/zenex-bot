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
ADMIN_CHAT_ID = 6470943912  # আপনার অ্যাডমিন টেলিগ্রাম আইডি (সংখ্যা হিসেবে)

sent_otps_cache = set()
number_to_user_map = {}
user_target_ranges = {}
waiting_for_range = {}
all_bot_users = set()  # সকল ইউজারের চ্যাট আইডি জমা রাখার জন্য

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

def get_service_display(service_name, raw_item):
    srv = str(service_name).lower()
    raw_item_str = str(raw_item).lower()
    
    if "clone" in raw_item_str or "cl" in raw_item_str:
        return "💻 PC Clone"
    elif "instagram" in srv:
        return "📸 Instagram"
    else:
        return "📘 FACEBOOK"

async def auto_otp_checker(context: ContextTypes.DEFAULT_TYPE):
    try:
        res1 = requests.get('https://api.zenexnetwork.com/v1/numsuccess/info', headers={'mapikey': PANEL_1_KEY}, timeout=10).json()
        if res1.get('meta', {}).get('code') == 200:
            otps_list = res1.get('data', {}).get('otps', [])
            
            for item in otps_list:
                num = str(item.get('number')).strip()
                if num not in number_to_user_map:
                    continue
                
                target_chat_id = number_to_user_map[num]
                
                raw_otp = str(item.get('otp', '')).strip()
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
                    
                country = item.get('country', '')
                flag, c_code, _ = get_country_info_by_range_or_text(num, country)
                label_text = get_service_display(service, item)
                
                msg_text = (
                    f"🔔 **NEW VERIFICATION CODE RECEIVED**\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"🌍 **Country:** {flag} `{c_code}`\n"
                    f"📱 **Number:** `+{num}`\n"
                    f"📌 **Type:** `{label_text}`\n"
                    f"🔑 **OTP Code:** `{otp_text}`\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"⚡ _Status: Successfully Delivered_"
                )
                
                await context.bot.send_message(
                    chat_id=target_chat_id, 
                    text=msg_text, 
                    parse_mode="Markdown"
                )
                
    except Exception as e:
        print(f"OTP Checker Error: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    all_bot_users.add(chat_id)  # ইউজার বট স্টার্ট করলে লিস্টে সেভ হবে

    keyboard = [
        [KeyboardButton("📞 Get API Number"), KeyboardButton("⚙️ Set Range")],
        [KeyboardButton("📱 Get Number"), KeyboardButton("📩 Live OTP Inbox")],
        [KeyboardButton("👤 Account Profile")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    welcome_text = (
        f"👋 **Welcome to Automated OTP Gateway!**\n\n"
        f"✨ Fast, secure, and reliable virtual number & OTP management service.\n"
        f"📌 Please choose an option from the menu below to get started:"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    # চেক করা হচ্ছে যে কমান্ডটি শুধু অ্যাডমিন দিচ্ছে কিনা
    if chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ You are not authorized to use this command!")
        return
        
    # ব্রডকাস্ট মেসেজ টেক্সট বের করা
    message_text = " ".join(context.args)
    if not message_text:
        await update.message.reply_text("⚠️ Please provide a message to broadcast. Example:\n`/broadcast Hello everyone!`", parse_mode="Markdown")
        return
        
    success_count = 0
    fail_count = 0
    
    status_msg = await update.message.reply_text("📢 **Broadcasting message to all users...**", parse_mode="Markdown")
    
    for uid in all_bot_users:
        try:
            await context.bot.send_message(
                chat_id=uid, 
                text=f"📢 **ANNOUNCEMENT**\n\n{message_text}", 
                parse_mode="Markdown"
            )
            success_count += 1
            time.sleep(0.1)  # টেলিগ্রাম ফ্লাড লিমিট এড়াতে ছোট বিরতি
        except Exception as e:
            fail_count += 1
            print(f"Failed to send broadcast to {uid}: {e}")
            
    await status_msg.edit_text(
        f"✅ **Broadcast Completed!**\n\n"
        f"📨 Successfully sent: `{success_count}` users\n"
        f"❌ Failed: `{fail_count}` users",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_id = update.effective_chat.id
    all_bot_users.add(chat_id)  # ইউজার মেসেজ পাঠালেও লিস্টে সেভ হবে

    if text == "⚙️ Set Range":
        waiting_for_range[chat_id] = True
        current_set = user_target_ranges.get(chat_id, "None")
        await update.message.reply_text(
            f"✍️ Please send or type your target range number now (e.g., `261344`).\n"
            f"📌 Current Saved Range: `{current_set}`",
            parse_mode="Markdown"
        )
        return

    if waiting_for_range.get(chat_id, False):
        user_target_ranges[chat_id] = text
        waiting_for_range[chat_id] = False
        await update.message.reply_text(
            f"✅ **Target Range Successfully Set:** `{text}`\n\nNow click on **'📞 Get API Number'** to fetch numbers from this range.",
            parse_mode="Markdown"
        )
        return

    if text == "📞 Get API Number":
        if chat_id not in user_target_ranges or not user_target_ranges[chat_id]:
            await update.message.reply_text("Please click '⚙️ Set Range' first to set your target range!", parse_mode="Markdown")
            return
        
        range_value = user_target_ranges[chat_id]
        loading_msg = await update.message.reply_text(f"🔄 **Fetching API numbers for range `{range_value}`...**", parse_mode="Markdown")
        
        assigned_numbers = []
        detected_c_code = "MZ"
        
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
                    full_num = str(num_data.get('full_number')).strip()
                    if full_num:
                        assigned_numbers.append(full_num)
                        number_to_user_map[full_num] = chat_id
                        _, detected_c_code, _ = get_country_info_by_range_or_text(full_num, num_data.get('country', ''))

            if len(assigned_numbers) > 0:
                flag, final_c_code, full_country_name = get_country_info_by_range_or_text(range_value, detected_c_code)
                
                numbers_block = ""
                for num in assigned_numbers:
                    clean_num = str(num).replace("+", "")
                    numbers_block += f"📱 `+{clean_num}`\n"
                
                keyboard = [
                    [InlineKeyboardButton("🔄 Change Number", callback_data=f"chg_{range_value}_{final_c_code}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                result_msg = (
                    f"✅ **API NUMBERS SUCCESSFULLY ASSIGNED**\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"🌍 **Country:** {flag} **{full_country_name}** (`{final_c_code}`)\n"
                    f"📌 **Range:** `{range_value}`\n"
                    f"⏳ **Status:** `Waiting for incoming OTP...`\n\n"
                    f"{numbers_block}\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"💡 _Tap any number above to copy instantly!_"
                )
                await loading_msg.edit_text(result_msg, parse_mode="Markdown", reply_markup=reply_markup)
            else:
                await loading_msg.edit_text(f"❌ **Stock Exhausted:** No numbers available for range `{range_value}` right now.", parse_mode="Markdown")
                
        except Exception as e:
            await loading_msg.edit_text(f"⚠️ **Gateway Timeout:** Failed to fetch numbers. Error: `{e}`", parse_mode="Markdown")

    elif text == "📱 Get Number":
        loading_msg = await update.message.reply_text("🔄 **Fetching active ranges from secure gateway...**", parse_mode="Markdown")
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
                
                type_label = get_service_display(srv, item)
                btn_text = f"{flag} {rng} | {type_label}"
                keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"get3_{rng}_{c_code}")])
            
            keyboard.append([InlineKeyboardButton("❌ Close Menu", callback_data="close_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            header_text = (
                f"⚡ **LIVE ACTIVE RANGES**\n"
                f"📂 **Available Slots:** `{len(all_ranges)}`\n\n"
                f"👇 _Select your preferred range below:_"
            )
            await loading_msg.edit_text(header_text, parse_mode="Markdown", reply_markup=reply_markup)
        else:
            await loading_msg.edit_text("❌ **No active ranges found in the gateway at the moment.**", parse_mode="Markdown")
            
    elif text == "📩 Live OTP Inbox":
        loading_msg = await update.message.reply_text("🔍 **Checking inbox records...**", parse_mode="Markdown")
        try:
            msg = "📥 **Active Inbox Payloads:**\n\n"
            res1 = requests.get('https://api.zenexnetwork.com/v1/numsuccess/info', headers={'mapikey': PANEL_1_KEY}, timeout=10).json()
            if res1.get('meta', {}).get('code') == 200:
                for item in res1.get('data', {}).get('otps', [])[:5]:
                    num = str(item.get('number'))
                    if number_to_user_map.get(num) == chat_id:
                        otp_text = extract_pure_code(item.get('otp', ''))
                        country = item.get('country', '')
                        flag, c_code, _ = get_country_info_by_range_or_text(num, country)
                        label_text = get_service_display(item.get('service', 'Facebook'), item)
                        msg += f"{flag} `{c_code}` | `+{num}`\n📌 `{label_text}`\n🔑 Code: `{otp_text}`\n──────────────────\n"
            if len(msg) <= 35:
                msg = "📭 **Inbox is clean!** No active verification codes found for your numbers."
            await loading_msg.edit_text(msg, parse_mode="Markdown")
        except Exception as e:
            await loading_msg.edit_text(f"⚠️ **Error occurred:** `{e}`", parse_mode="Markdown")
            
    elif text == "👤 Account Profile":
        profile_msg = (
            f"👤 **USER PROFILE INFORMATION**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 **Telegram ID:** `{chat_id}`\n"
            f"📊 **Account Status:** `Active / Premium`\n"
            f"🛡️ **Security Level:** `Encrypted`\n"
            f"━━━━━━━━━━━━━━━━━━━"
        )
        await update.message.reply_text(profile_msg, parse_mode="Markdown")
    else:
        if text.isdigit() and len(text) >= 3:
            user_target_ranges[chat_id] = text
            waiting_for_range[chat_id] = False
            await update.message.reply_text(
                f"✅ **Target Range Auto-Saved:** `{text}`\n\nNow click on **'📞 Get API Number'** to fetch numbers.",
                parse_mode="Markdown"
            )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data_code = query.data
    chat_id = query.message.chat.id
    all_bot_users.add(chat_id)

    await query.answer()

    if data_code.startswith("get3_") or data_code.startswith("chg_"):
        parts = data_code.split("_")
        range_value = parts[1]
        c_code = parts[2] if len(parts) > 2 else "MZ"
        
        await query.edit_message_text(text="🔄 **Fetching new numbers from server pool...**", parse_mode="Markdown")

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
                    full_num = str(num_data.get('full_number')).strip()
                    if full_num:
                        assigned_numbers.append(full_num)
                        number_to_user_map[full_num] = chat_id
                        _, detected_c_code, _ = get_country_info_by_range_or_text(full_num, num_data.get('country', ''))

            if len(assigned_numbers) > 0:
                flag, final_c_code, full_country_name = get_country_info_by_range_or_text(range_value, detected_c_code)
                
                numbers_block = ""
                for num in assigned_numbers:
                    clean_num = str(num).replace("+", "")
                    numbers_block += f"📱 `+{clean_num}`\n"
                
                keyboard = [
                    [InlineKeyboardButton("🔄 Change Number", callback_data=f"chg_{range_value}_{final_c_code}")]
                ]
                if data_code.startswith("get3_"):
                    keyboard.append([InlineKeyboardButton("🌐 Back to Country Menu", callback_data="back_to_menu")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)

                result_msg = (
                    f"✅ **API NUMBERS SUCCESSFULLY ASSIGNED**\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"🌍 **Country:** {flag} **{full_country_name}** (`{final_c_code}`)\n"
                    f"📌 **Range:** `{range_value}`\n"
                    f"⏳ **Status:** `Waiting for incoming OTP...`\n\n"
                    f"{numbers_block}\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"💡 _Tap any number above to copy instantly!_"
                )

                await query.edit_message_text(result_msg, parse_mode="Markdown", reply_markup=reply_markup)
            else:
                await query.edit_message_text("❌ **Stock Exhausted:** No numbers available for this range right now.", parse_mode="Markdown")
                
        except Exception as e:
            await query.edit_message_text("⚠️ **Gateway Timeout:** Failed to fetch numbers. Please try again.", parse_mode="Markdown")

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
                    
                    type_label = get_service_display(srv, item)
                    btn_text = f"{flag} {rng} | {type_label}"
                    keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"get3_{rng}_{c_code}")])
                
                keyboard.append([InlineKeyboardButton("❌ Close Menu", callback_data="close_menu")],)
                reply_markup = InlineKeyboardMarkup(keyboard)
                header_text = (
                    f"⚡ **LIVE ACTIVE RANGES**\n"
                    f"📂 **Available Slots:** `{len(all_ranges)}`\n\n"
                    f"👇 _Select your preferred range below:_"
                )
                await loading_msg.edit_text(header_text, parse_mode="Markdown", reply_markup=reply_markup)
            else:
                await loading_msg.edit_text("❌ **No active ranges found.**", parse_mode="Markdown")
        except:
            await query.message.delete()

    elif data_code == "close_menu":
        await query.message.delete()

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.job_queue.run_repeating(auto_otp_checker, interval=10, first=3)
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast_message))  # ব্রডকাস্ট কমান্ড হ্যান্ডলার
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(button_click))
    
    print("Bot is running successfully with Broadcast system...")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
