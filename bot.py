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
ADMIN_CHAT_ID = 6470943912  
OTP_GROUP_CHAT_ID = -1003857083035  

PANEL_API_KEY = "MTPXMVWZJWL"
BASE_URL = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api"

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
    
    if len(c_field) == 2 and c_field.isalpha():
        flag = ''.join([chr(ord(char) + 127397) for char in c_field])
        return flag, c_field, c_field
        
    prefix_to_iso = {
        "374": "AM", "880": "BD", "91": "IN", "1": "US", "44": "GB", "7": "RU", 
        "992": "TJ", "261": "MG", "380": "UA", "224": "GN", "228": "TG", 
        "237": "CM", "225": "CI", "236": "CF", "229": "BJ", "60": "MY", 
        "212": "MA", "249": "SD", "255": "TZ", "263": "ZW", "213": "DZ", 
        "591": "BO", "20": "EG", "233": "GH", "55": "BR", "92": "PK",
        "62": "ID", "84": "VN", "63": "PH", "90": "TR", "98": "IR", "977": "NP"
    }
    
    for prefix, iso in sorted(prefix_to_iso.items(), key=lambda x: len(x[0]), reverse=True):
        if r_str.startswith(prefix):
            flag = ''.join([chr(ord(char) + 127397) for char in iso])
            return flag, iso, iso

    return "🌍", c_field if c_field else "INT", "INTERNATIONAL"

async def auto_otp_checker(context: ContextTypes.DEFAULT_TYPE):
    try:
        res1 = requests.get(f'{BASE_URL}/success-otp', headers={'mauthapi': PANEL_API_KEY}, timeout=3).json()
        if res1.get('meta', {}).get('code') == 200:
            otps_list = res1.get('data', {}).get('otps', [])
            
            for item in otps_list:
                num = str(item.get('number')).strip()
                if num not in number_to_user_map:
                    continue
                
                target_chat_id = number_to_user_map[num]
                raw_msg = str(item.get('message', '')).strip()
                otp_text = extract_pure_code(raw_msg)
                
                otp_id = str(item.get('otp_id', '')).strip()
                unique_signature = f"id_{otp_id}" if otp_id else f"num_{num}_otp_{otp_text}"
                
                if unique_signature in sent_otps_cache:
                    continue
                
                sent_otps_cache.add(unique_signature)
                if len(sent_otps_cache) > 1000:
                    sent_otps_cache.pop()
                    
                flag, c_code, _ = get_country_info_by_range_or_text(num, "")
                
                msg_text = (
                    f"🔔 **NEW VERIFICATION CODE RECEIVED**\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"🌍 **Country:** {flag} `{c_code}`\n"
                    f"📱 **Number:** `+{num}`\n"
                    f"🔑 **OTP Message:** `{raw_msg}`\n"
                    f"⚡ **Extracted Code:** `{otp_text}`\n"
                    f"━━━━━━━━━━━━━━━━━━━"
                )
                
                try:
                    await context.bot.send_message(chat_id=target_chat_id, text=msg_text, parse_mode="Markdown")
                except:
                    pass
                
                try:
                    await context.bot.send_message(chat_id=OTP_GROUP_CHAT_ID, text=msg_text, parse_mode="Markdown")
                except:
                    pass
    except:
        pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    all_bot_users.add(chat_id)

    keyboard = [
        [KeyboardButton("📞 Get API Number"), KeyboardButton("⚙️ Set Range")],
        [KeyboardButton("📱 Get Number"), KeyboardButton("🛠️ Select Service")],
        [KeyboardButton("📊 Live Traffic"), KeyboardButton("📩 Live OTP Inbox")],
        [KeyboardButton("👤 Account Profile")]
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
    text = update.message.text.strip()
    chat_id = update.effective_chat.id
    all_bot_users.add(chat_id)

    if text == "⚙️ Set Range":
        waiting_for_range[chat_id] = True
        current_set = user_target_ranges.get(chat_id, "None")
        await update.message.reply_text(
            f"✍️ Please send or type your target range number/rid now (e.g., `22501`).\n"
            f"📌 Current Saved Range: `{current_set}`",
            parse_mode="Markdown"
        )
        return

    if waiting_for_range.get(chat_id, False):
        if text.startswith("📞") or text.startswith("📱") or text.startswith("🛠️") or text.startswith("📩") or text.startswith("👤") or text.startswith("⚙️") or text.startswith("📊"):
            waiting_for_range[chat_id] = False
            await update.message.reply_text("❌ **Range setting cancelled.** Please click buttons normally.", parse_mode="Markdown")
            return

        user_target_ranges[chat_id] = text.replace("XXX", "").replace("xxx", "").strip()
        waiting_for_range[chat_id] = False
        await update.message.reply_text(
            f"✅ **Target Range/RID Successfully Set:** `{text}`\n\nNow click on **'📞 Get API Number'** to fetch numbers.",
            parse_mode="Markdown"
        )
        return

    if text == "🛠️ Select Service":
        keyboard = [
            [InlineKeyboardButton("WHATSAPP", callback_data="srv_WhatsApp"), InlineKeyboardButton("INSTAGRAM", callback_data="srv_Instagram")],
            [InlineKeyboardButton("FACEBOOK", callback_data="srv_Facebook"), InlineKeyboardButton("MICROSOFT", callback_data="srv_Microsoft")],
            [InlineKeyboardButton("🌐 All Services", callback_data="srv_All")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        current_srv = user_target_services.get(chat_id, "All")
        await update.message.reply_text(
            f"🛠️ **Select a service:**\n"
            f"📌 Current Selected Service: `{current_srv}`\n\n"
            f"👇 Click a button below to change:",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        return

    # শুধুমাত্র ফেসবুক লাইভ ট্রাফিক দেখানোর লজিক
    if text == "📊 Live Traffic":
        loading_msg = await update.message.reply_text("⌛ **Fetching Facebook Live Traffic...**", parse_mode="Markdown")
        try:
            res = requests.get(f'{BASE_URL}/liveaccess', headers={'mauthapi': PANEL_API_KEY}, timeout=5).json()
            if res.get('meta', {}).get('code') == 200:
                services_list = res.get('data', {}).get('services', [])
                
                traffic_text = ""
                found_fb = False
                
                for s_item in services_list:
                    sid = str(s_item.get('sid', '')).strip().upper()
                    if sid == "FACEBOOK":
                        found_fb = True
                        ranges = s_item.get('ranges', [])
                        traffic_text = f"🔥 **10 Minute LIVE Traffic (FACEBOOK)**\n\n"
                        traffic_text += f"📘 **FACEBOOK ({len(ranges)})**\n"
                        for r in ranges[:10]: # সর্বোচ্চ ১০টি দেশের ট্রাফিক দেখাবে
                            flag, c_code, _ = get_country_info_by_range_or_text(r, "")
                            traffic_text += f"  {flag} {c_code} : ACTIVE 🟢\n"
                        break
                
                if not found_fb:
                    traffic_text = "🔥 **10 Minute LIVE Traffic (FACEBOOK)**\n\n❌ **No traffic data found for Facebook right now.**"
                else:
                    traffic_text += "\n🕒 Updated just now"
                
                keyboard = [
                    [InlineKeyboardButton("Explore Facebook Range", callback_data="srv_menu_FACEBOOK")],
                    [InlineKeyboardButton("Close", callback_data="close_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await loading_msg.edit_text(traffic_text, parse_mode="Markdown", reply_markup=reply_markup)
            else:
                await loading_msg.edit_text("❌ **Failed to load live traffic.**", parse_mode="Markdown")
        except Exception as e:
            await loading_msg.edit_text(f"⚠️ **Error:** `{e}`", parse_mode="Markdown")
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
                    f'{BASE_URL}/getnum',
                    headers={'mauthapi': PANEL_API_KEY, 'Content-Type': 'application/json'},
                    json={"rid": range_value},
                    timeout=5
                ).json()
                
                if resp.get('meta', {}).get('code') == 200:
                    num_data = resp.get('data', {})
                    full_num = str(num_data.get('full_number') or num_data.get('number') or num_data.get('copy')).strip()
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
                    f"📌 **Range/RID:** `{range_value}` | **Service:** `{selected_service}`\n"
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
        loading_msg = await update.message.reply_text("⌛ **Getting active services...**", parse_mode="Markdown")
        services_list = []
        try:
            r1 = requests.get(f'{BASE_URL}/liveaccess', headers={'mauthapi': PANEL_API_KEY}, timeout=5).json()
            if r1.get('meta', {}).get('code') == 200:
                services_list = r1.get('data', {}).get('services', [])
        except:
            pass
        
        if len(services_list) > 0:
            allowed_services = ["WHATSAPP", "FACEBOOK", "INSTAGRAM", "MICROSOFT"]
            keyboard = []
            for s_item in services_list:
                sid = str(s_item.get('sid', 'UNKNOWN')).strip().upper()
                if sid in allowed_services:
                    keyboard.append([InlineKeyboardButton(f"{sid}", callback_data=f"srv_menu_{sid}")])
            
            keyboard.append([InlineKeyboardButton("Close", callback_data="close_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await loading_msg.edit_text("📌 **Select a service:**", parse_mode="Markdown", reply_markup=reply_markup)
        else:
            await loading_msg.edit_text("❌ **No active services found.**", parse_mode="Markdown")
            
    elif text == "📩 Live OTP Inbox":
        loading_msg = await update.message.reply_text("⌛ **Checking inbox...**", parse_mode="Markdown")
        try:
            msg = "📥 **Active Inbox Payloads:**\n\n"
            res1 = requests.get(f'{BASE_URL}/success-otp', headers={'mauthapi': PANEL_API_KEY}, timeout=5).json()
            if res1.get('meta', {}).get('code') == 200:
                for item in res1.get('data', {}).get('otps', []):
                    num = str(item.get('number'))
                    if number_to_user_map.get(num) == chat_id:
                        raw_msg = item.get('message', '')
                        otp_text = extract_pure_code(raw_msg)
                        flag, c_code, _ = get_country_info_by_range_or_text(num, "")
                        msg += f"{flag} `{c_code}` | `+{num}`\n🔑 Code: `{otp_text}`\n──────────────────\n"
            if len(msg) <= 30:
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

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data_code = query.data
    chat_id = query.message.chat.id
    all_bot_users.add(chat_id)

    try:
        await query.answer()
    except:
        pass

    if data_code.startswith("srv_") and not data_code.startswith("srv_menu_"):
        selected_srv = data_code.split("_")[1]
        user_target_services[chat_id] = selected_srv
        await query.edit_message_text(
            f"✅ **Service Successfully Updated!**\n\n"
            f"📌 Current Target Service: `{selected_srv}`\n"
            f"Now you can get numbers using this service filter.",
            parse_mode="Markdown"
        )
        return

    if data_code.startswith("srv_menu_"):
        chosen_sid = data_code.replace("srv_menu_", "")
        try:
            r1 = requests.get(f'{BASE_URL}/liveaccess', headers={'mauthapi': PANEL_API_KEY}, timeout=5).json()
            if r1.get('meta', {}).get('code') == 200:
                services_list = r1.get('data', {}).get('services', [])
                hot_list = load_hot_ranges()
                keyboard = []
                count = 0
                
                for s_item in services_list:
                    if str(s_item.get('sid', '')).strip().upper() == chosen_sid:
                        ranges = s_item.get('ranges', [])
                        for rng_raw in ranges:
                            rng = str(rng_raw).replace("XXX", "").replace("xxx", "").strip()
                            flag, c_code, _ = get_country_info_by_range_or_text(rng, "")
                            
                            fire_tag = ""
                            for hot in hot_list:
                                if rng.startswith(hot) or hot.startswith(rng):
                                    fire_tag = " 🔥"
                                    break
                            
                            keyboard.append([InlineKeyboardButton(f"{flag} {rng_raw} | {chosen_sid}{fire_tag}", callback_data=f"get3_{rng}_{c_code}")])
                            count += 1
                            if count >= 30:
                                break
                        break
                
                keyboard.append([InlineKeyboardButton("🔙 Back to Services", callback_data="back_to_services")])
                keyboard.append([InlineKeyboardButton("Close", callback_data="close_menu")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(f"📌 **Ranges for {chosen_sid}:**", parse_mode="Markdown", reply_markup=reply_markup)
        except:
            await query.edit_message_text("❌ **Error loading ranges.**", parse_mode="Markdown")
        return

    if data_code == "back_to_services":
        try:
            r1 = requests.get(f'{BASE_URL}/liveaccess', headers={'mauthapi': PANEL_API_KEY}, timeout=5).json()
            if r1.get('meta', {}).get('code') == 200:
                services_list = r1.get('data', {}).get('services', [])
                allowed_services = ["WHATSAPP", "FACEBOOK", "INSTAGRAM", "MICROSOFT"]
                keyboard = []
                for s_item in services_list:
                    sid = str(s_item.get('sid', 'UNKNOWN')).strip().upper()
                    if sid in allowed_services:
                        keyboard.append([InlineKeyboardButton(f"{sid}", callback_data=f"srv_menu_{sid}")])
                
                keyboard.append([InlineKeyboardButton("Close", callback_data="close_menu")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text("📌 **Select a service:**", parse_mode="Markdown", reply_markup=reply_markup)
        except:
            await query.message.delete()
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
                    f'{BASE_URL}/getnum',
                    headers={'mauthapi': PANEL_API_KEY, 'Content-Type': 'application/json'},
                    json={"rid": range_value},
                    timeout=5
                ).json()
                
                if resp.get('meta', {}).get('code') == 200:
                    num_data = resp.get('data', {})
                    full_num = str(num_data.get('full_number') or num_data.get('number') or num_data.get('copy')).strip()
                    if full_num:
                        assigned_numbers.append(full_num)
                        number_to_user_map[full_num] = chat_id
                        _, detected_c_code, _ = get_country_info_by_range_or_text(full_num, num_data.get('country', ''))

            if len(assigned_numbers) > 0:
                flag, final_c_code, full_country_name = get_country_info_by_range_or_text(range_value, detected_c_code)
                numbers_block = "".join([f"📱 `+{str(num).replace('+', '')}`\n" for num in assigned_numbers])
                
                keyboard = [[InlineKeyboardButton("🔄 Change Number", callback_data=f"chg_{range_value}_{final_c_code}")] ]
                if data_code.startswith("get3_"):
                    keyboard.append([InlineKeyboardButton("🔙 Back to Services", callback_data="back_to_services")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                result_msg = (
                    f"✅ **API NUMBERS SUCCESSFULLY ASSIGNED**\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"🌍 **Country:** {flag} **{full_country_name}** (`{final_c_code}`)\n"
                    f"📌 **Range/RID:** `{range_value}` | **Service:** `{selected_service}`\n"
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

    elif data_code == "close_menu":
        try:
            await query.message.delete()
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
