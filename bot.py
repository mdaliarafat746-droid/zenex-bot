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
ADMIN_CHAT_ID = 6470943912  

sent_otps_cache = set()
number_to_user_map = {}
user_target_ranges = {}
user_target_services = {}
waiting_for_range = {}
all_bot_users = set()

def load_hot_ranges():
    if os.path.exists("hot_ranges.txt"):
        try:
            with open("hot_ranges.txt", "r", encoding="utf-8") as f:
                lines = []
                for line in f:
                    cleaned = line.strip().replace("XXX", "").replace("xxx", "")
                    if cleaned:
                        lines.append(cleaned)
                return lines
        except:
            return []
    return []

def extract_pure_code(full_text):
    text = str(full_text).strip()
    match = re.search(r'\b\d{4,8}\b', text)
    if match:
        return match.group(0)
    return text

def get_country_info_by_range_or_text(range_str, country_field, raw_text=""):
    c_field = str(country_field).strip().upper()
    r_str = str(range_str).strip().replace("+", "")
    
    # যদি প্যানেল থেকে সরাসরি ২ অক্ষরের শর্ট কোড দেয় (যেমন: BD, IN, US, PK, ID ইত্যাদি)
    if len(c_field) == 2 and c_field.isalpha():
        # অটোমেটিক যেকোনো ISO 2-letter কোড থেকে ফ্ল্যাগ ইমোজি তৈরি
        flag = ''.join([chr(ord(char) + 127397) for char in c_field])
        return flag, c_field, c_field
        
    # যদি কান্ট্রি ফিল্ড না থাকে, তবে ফোন নাম্বারের প্রিফিক্স থেকে আন্দাজ করে অটো ফ্ল্যাগ ও শর্ট কোড বের করা
    # কিছু কমন প্রিফিক্স ম্যাপিং যা অটোমেটিক কাজ করবে
    prefix_to_iso = {
        "880": "BD", "91": "IN", "1": "US", "44": "GB", "7": "RU", 
        "992": "TJ", "261": "MG", "380": "UA", "224": "GN", "228": "TG", 
        "237": "CM", "225": "CI", "236": "CF", "229": "BJ", "60": "MY", 
        "212": "MA", "249": "SD", "255": "TZ", "263": "ZW", "213": "DZ", 
        "591": "BO", "20": "EG", "233": "GH", "55": "BR", "92": "PK",
        "62": "ID", "84": "VN", "63": "PH", "90": "TR", "98": "IR"
    }
    
    for prefix, iso in sorted(prefix_to_iso.items(), key=lambda x: len(x[0]), reverse=True):
        if r_str.startswith(prefix):
            flag = ''.join([chr(ord(char) + 127397) for char in iso])
            return flag, iso, iso

    return "🌍", c_field if c_field else "INT", "INTERNATIONAL"

def get_service_display(service_name, raw_item):
    srv = str(service_name).lower()
    raw_item_str = str(raw_item).lower()
    
    if "clone" in raw_item_str or "cl" in raw_item_str or "pc" in raw_item_str:
        return "💻 PC Clone"
    elif "instagram" in srv or "ig" in srv or "insta" in raw_item_str:
        return "📸 Instagram"
    elif "new" in srv or "newfb" in srv or "new_fb" in raw_item_str:
        return "📘 New FB"
    else:
        return "📘 FACEBOOK"

async def auto_otp_checker(context: ContextTypes.DEFAULT_TYPE):
    try:
        res1 = requests.get('https://api.zenexnetwork.com/v1/numsuccess/info', headers={'mapikey': PANEL_1_KEY}, timeout=3).json()
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
                    f"📌 **Service:** `{label_text}`\n"
                    f"🔑 **OTP Code:** `{otp_text}`\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"⚡ _Status: Successfully Delivered_"
                )
                
                await context.bot.send_message(
                    chat_id=target_chat_id, 
                    text=msg_text, 
                    parse_mode="Markdown"
                )
    except:
        pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    all_bot_users.add(chat_id)

    keyboard = [
        [KeyboardButton("📞 Get API Number"), KeyboardButton("⚙️ Set Range")],
        [KeyboardButton("📱 Get Number"), KeyboardButton("🛠️ Select Service")],
        [KeyboardButton("📩 Live OTP Inbox"), KeyboardButton("👤 Account Profile")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    welcome_text = (
        f"👋 **Welcome to Automated OTP Gateway!**\n\n"
        f"✨ Fast, secure, and reliable virtual number & OTP management service.\n"
        f"📌 Please choose an option from the menu below to get started:"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)

async def bot_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id != ADMIN_CHAT_ID:
        return
    total_users = len(all_bot_users)
    await update.message.reply_text(f"📊 **Total Unique Users:** `{total_users}`", parse_mode="Markdown")

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id != ADMIN_CHAT_ID:
        return
    message_text = " ".join(context.args)
    if not message_text:
        await update.message.reply_text("⚠️ Please provide a message.", parse_mode="Markdown")
        return
    
    status_msg = await update.message.reply_text("📢 **Broadcasting...**", parse_mode="Markdown")
    success, fail = 0, 0
    for uid in all_bot_users:
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 **ANNOUNCEMENT**\n\n{message_text}", parse_mode="Markdown")
            success += 1
        except:
            fail += 1
    await status_msg.edit_text(f"✅ **Done!** Sent: `{success}`, Failed: `{fail}`", parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    chat_id = update.effective_chat.id
    all_bot_users.add(chat_id)

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
        if text.startswith("📞") or text.startswith("📱") or text.startswith("🛠️") or text.startswith("📩") or text.startswith("👤") or text.startswith("⚙️"):
            waiting_for_range[chat_id] = False
            await update.message.reply_text("❌ **Range setting cancelled.** Please click buttons normally.", parse_mode="Markdown")
            return

        user_target_ranges[chat_id] = text
        waiting_for_range[chat_id] = False
        await update.message.reply_text(
            f"✅ **Target Range Successfully Set:** `{text}`\n\nNow click on **'📞 Get API Number'** to fetch numbers.",
            parse_mode="Markdown"
        )
        return

    if text == "🛠️ Select Service":
        keyboard = [
            [InlineKeyboardButton("📘 New FB", callback_data="srv_NewFB"), InlineKeyboardButton("📸 Instagram", callback_data="srv_Instagram")],
            [InlineKeyboardButton("💻 PC Clone", callback_data="srv_PCClone"), InlineKeyboardButton("🌐 All Services", callback_data="srv_All")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        current_srv = user_target_services.get(chat_id, "All")
        await update.message.reply_text(
            f"🛠️ **Select Your Desired Service:**\n"
            f"📌 Current Selected Service: `{current_srv}`\n\n"
            f"👇 Click a button below to change:",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        return

    if text == "📞 Get API Number":
        if chat_id not in user_target_ranges or not user_target_ranges[chat_id]:
            await update.message.reply_text("Please click '⚙️ Set Range' first to set your target range!", parse_mode="Markdown")
            return
        
        range_value = user_target_ranges[chat_id]
        selected_service = user_target_services.get(chat_id, "All")
        
        loading_msg = await update.message.reply_text("⌛ **Getting number...**", parse_mode="Markdown")
        
        assigned_numbers = []
        detected_c_code = ""
        
        try:
            for _ in range(2):
                resp = requests.post(
                    'https://api.zenexnetwork.com/v1/getnum',
                    headers={'mapikey': PANEL_1_KEY, 'Content-Type': 'application/json'},
                    json={"range": range_value, "is_national": False, "remove_plus": False},
                    timeout=5
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
                numbers_block = "".join([f"📱 `+{str(num).replace('+', '')}`\n" for num in assigned_numbers])
                
                keyboard = [[InlineKeyboardButton("🔄 Change Number", callback_data=f"chg_{range_value}_{final_c_code}")] ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                result_msg = (
                    f"✅ **API NUMBERS SUCCESSFULLY ASSIGNED**\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"🌍 **Country:** {flag} **{full_country_name}** (`{final_c_code}`)\n"
                    f"📌 **Range:** `{range_value}` | **Service:** `{selected_service}`\n"
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
        loading_msg = await update.message.reply_text("⌛ **Getting active ranges...**", parse_mode="Markdown")
        all_ranges = []
        try:
            r1 = requests.get('https://api.zenexnetwork.com/v1/active-ranges', headers={'mapikey': PANEL_1_KEY}, timeout=5).json()
            if r1.get('success') == True:
                for r in r1.get('data', {}).get('active_ranges', []):
                    r['panel_type'] = 'panel1'
                    all_ranges.append(r)
        except:
            pass
        
        if len(all_ranges) > 0:
            hot_list = load_hot_ranges()

            keyboard = []
            for item in all_ranges[:30]:
                rng = str(item.get('range', '')).strip()
                api_country = item.get('country', '')
                flag, c_code, _ = get_country_info_by_range_or_text(rng, api_country, str(item))
                srv = str(item.get('service', 'Facebook'))
                type_label = get_service_display(srv, item)
                
                fire_tag = ""
                for hot in hot_list:
                    if rng.startswith(hot) or hot.startswith(rng):
                        fire_tag = " 🔥"
                        break
                
                keyboard.append([InlineKeyboardButton(f"{flag} {rng}XXX | {type_label}{fire_tag}", callback_data=f"get3_{rng}_{c_code}")])
            
            keyboard.append([InlineKeyboardButton("❌ Close Menu", callback_data="close_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await loading_msg.edit_text(f"⚡ **LIVE ACTIVE RANGES**\n📂 **Available Slots:** `{len(all_ranges)}`\n\n👇 _Select your preferred range below:_", parse_mode="Markdown", reply_markup=reply_markup)
        else:
            await loading_msg.edit_text("❌ **No active ranges found.**", parse_mode="Markdown")
            
    elif text == "📩 Live OTP Inbox":
        loading_msg = await update.message.reply_text("⌛ **Checking inbox...**", parse_mode="Markdown")
        try:
            msg = "📥 **Active Inbox Payloads:**\n\n"
            res1 = requests.get('https://api.zenexnetwork.com/v1/numsuccess/info', headers={'mapikey': PANEL_1_KEY}, timeout=5).json()
            if res1.get('meta', {}).get('code') == 200:
                for item in res1.get('data', {}).get('otps', [])[:5]:
                    num = str(item.get('number'))
                    if number_to_user_map.get(num) == chat_id:
                        otp_text = extract_pure_code(item.get('otp', ''))
                        flag, c_code, _ = get_country_info_by_range_or_text(num, item.get('country', ''))
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
            f"🛠️ **Preferred Service:** `{user_target_services.get(chat_id, 'All')}`\n"
            f"📊 **Account Status:** `Active / Premium`\n"
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

    try:
        await query.answer()
    except:
        pass

    if data_code.startswith("srv_"):
        selected_srv = data_code.split("_")[1]
        user_target_services[chat_id] = selected_srv
        await query.edit_message_text(
            f"✅ **Service Successfully Updated!**\n\n"
            f"📌 Current Target Service: `{selected_srv}`\n"
            f"Now you can get numbers using this service filter.",
            parse_mode="Markdown"
        )
        return

    if data_code.startswith("get3_") or data_code.startswith("chg_"):
        parts = data_code.split("_")
        range_value = parts[1]
        c_code = parts[2] if len(parts) > 2 else ""
        selected_service = user_target_services.get(chat_id, "All")
        
        await query.edit_message_text(text="⌛ **Getting number...**", parse_mode="Markdown")

        assigned_numbers = []
        detected_c_code = c_code
        
        try:
            for _ in range(2):
                resp = requests.post(
                    'https://api.zenexnetwork.com/v1/getnum',
                    headers={'mapikey': PANEL_1_KEY, 'Content-Type': 'application/json'},
                    json={"range": range_value, "is_national": False, "remove_plus": False},
                    timeout=5
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
                numbers_block = "".join([f"📱 `+{str(num).replace('+', '')}`\n" for num in assigned_numbers])
                
                keyboard = [[InlineKeyboardButton("🔄 Change Number", callback_data=f"chg_{range_value}_{final_c_code}")] ]
                if data_code.startswith("get3_"):
                    keyboard.append([InlineKeyboardButton("🌐 Back to Country Menu", callback_data="back_to_menu")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                result_msg = (
                    f"✅ **API NUMBERS SUCCESSFULLY ASSIGNED**\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"🌍 **Country:** {flag} **{full_country_name}** (`{final_c_code}`)\n"
                    f"📌 **Range:** `{range_value}` | **Service:** `{selected_service}`\n"
                    f"⏳ **Status:** `Waiting for incoming OTP...`\n\n"
                    f"{numbers_block}\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"💡 _Tap any number above to copy instantly!_"
                )
                await query.edit_message_text(result_msg, parse_mode="Markdown", reply_markup=reply_markup)
            else:
                await query.edit_message_text("❌ **Stock Exhausted:** No numbers available.", parse_mode="Markdown")
        except:
            await query.edit_message_text("⚠️ **Gateway Timeout:** Failed to fetch numbers.", parse_mode="Markdown")

    elif data_code == "back_to_menu":
        try:
            loading_msg = query.message
            all_ranges = []
            r1 = requests.get('https://api.zenexnetwork.com/v1/active-ranges', headers={'mapikey': PANEL_1_KEY}, timeout=5).json()
            if r1.get('success') == True:
                for r in r1.get('data', {}).get('active_ranges', []):
                    r['panel_type'] = 'panel1'
                    all_ranges.append(r)
            
            if len(all_ranges) > 0:
                hot_list = load_hot_ranges()

                keyboard = []
                for item in all_ranges[:30]:
                    rng = str(item.get('range', '')).strip()
                    api_country = item.get('country', '')
                    flag, c_code, _ = get_country_info_by_range_or_text(rng, api_country, str(item))
                    srv = str(item.get('service', 'Facebook'))
                    type_label = get_service_display(srv, item)
                    
                    fire_tag = ""
                    for hot in hot_list:
                        if rng.startswith(hot) or hot.startswith(rng):
                            fire_tag = " 🔥"
                            break
                    
                    keyboard.append([InlineKeyboardButton(f"{flag} {rng}XXX | {type_label}{fire_tag}", callback_data=f"get3_{rng}_{c_code}")])
                
                keyboard.append([InlineKeyboardButton("❌ Close Menu", callback_data="close_menu")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                await loading_msg.edit_text(f"⚡ **LIVE ACTIVE RANGES**\n📂 **Available Slots:** `{len(all_ranges)}`\n\n👇 _Select your preferred range below:_", parse_mode="Markdown", reply_markup=reply_markup)
            else:
                await loading_msg.edit_text("❌ **No active ranges found.**", parse_mode="Markdown")
        except:
            await query.message.delete()

    elif data_code == "close_menu":
        try:
            await query.message.delete()
        except:
            pass

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.job_queue.run_repeating(auto_otp_checker, interval=1, first=1)
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", bot_stats))
    app.add_handler(CommandHandler("broadcast", broadcast_message))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(button_click))
    
    print("Bot is running successfully...")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
