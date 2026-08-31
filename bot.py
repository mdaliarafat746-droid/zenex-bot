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

def extract_pure_code(full_text):
    text = str(full_text).strip()
    match = re.search(r'\b\d{4,8}\b', text)
    if match:
        return match.group(0)
    return text

def get_clean_digits(val):
    return re.sub(r'\D', '', str(val))

def get_country_info_by_range_or_text(range_str, country_field):
    c_field = str(country_field).strip().upper()
    r_str = get_clean_digits(range_str)
    
    iso_to_name = {
        "AM": "ARMENIA", "BD": "BANGLADESH", "IN": "INDIA", "US": "UNITED STATES", 
        "GB": "UNITED KINGDOM", "RU": "RUSSIA", "TJ": "TAJIKISTAN", "MG": "MADAGASCAR", 
        "UA": "UKRAINE", "GN": "GUINEA", "TG": "TOGO", "CM": "CAMEROON", 
        "CI": "IVORY COAST", "CF": "CENTRAL AFRICAN REPUBLIC", "BJ": "BENIN", "MY": "MALAYSIA", 
        "MA": "MOROCCO", "SD": "SUDAN", "TZ": "TANZANIA, UNITED REPUBLIC OF", "ZW": "ZIMBABWE", 
        "DZ": "ALGERIA", "BO": "BOLIVIA", "EG": "EGYPT", "GH": "GHANA", 
        "BR": "BRAZIL", "PK": "PAKISTAN", "ID": "INDONESIA", "VN": "VIETNAM", 
        "PH": "PHILIPPINES", "TR": "TURKEY", "IR": "IRAN", "NP": "NEPAL", "ME": "MONTENEGRO",
        "SL": "SIERRA LEONE"
    }

    if len(c_field) == 2 and c_field.isalpha():
        flag = ''.join([chr(ord(char) + 127397) for char in c_field])
        full_name = iso_to_name.get(c_field, c_field)
        return flag, c_field, full_name
        
    prefix_to_iso = {
        "374": "AM", "880": "BD", "91": "IN", "1": "US", "44": "GB", "7": "RU", 
        "992": "TJ", "261": "MG", "380": "UA", "224": "GN", "228": "TG", 
        "237": "CM", "225": "CI", "236": "CF", "229": "BJ", "60": "MY", 
        "212": "MA", "249": "SD", "255": "TZ", "263": "ZW", "213": "DZ", 
        "591": "BO", "20": "EG", "233": "GH", "55": "BR", "92": "PK",
        "62": "ID", "84": "VN", "63": "PH", "90": "TR", "98": "IR", "977": "NP",
        "382": "ME", "232": "SL"
    }
    
    for prefix, iso in sorted(prefix_to_iso.items(), key=lambda x: len(x[0]), reverse=True):
        if r_str.startswith(prefix):
            flag = ''.join([chr(ord(char) + 127397) for char in iso])
            full_name = iso_to_name.get(iso, iso)
            return flag, iso, full_name

    return "🌍", c_field if c_field else "INT", "INTERNATIONAL"

async def auto_otp_checker(context: ContextTypes.DEFAULT_TYPE):
    try:
        res1 = requests.get(f'{BASE_URL}/success-otp', headers={'mauthapi': PANEL_API_KEY}, timeout=3).json()
        if res1.get('meta', {}).get('code') == 200:
            otps_list = res1.get('data', {}).get('otps', [])
            
            for item in otps_list:
                raw_num = str(item.get('number', '')).strip()
                clean_num = get_clean_digits(raw_num)
                
                if not clean_num or clean_num not in number_to_user_map:
                    continue
                
                target_chat_id = number_to_user_map[clean_num]
                raw_msg = str(item.get('message', '')).strip()
                otp_text = extract_pure_code(raw_msg)
                
                otp_id = str(item.get('otp_id', '')).strip()
                unique_signature = f"id_{otp_id}" if otp_id else f"num_{clean_num}_otp_{otp_text}"
                
                if unique_signature in sent_otps_cache:
                    continue
                
                sent_otps_cache.add(unique_signature)
                if len(sent_otps_cache) > 1000:
                    sent_otps_cache.pop()
                    
                flag, c_code, _ = get_country_info_by_range_or_text(clean_num, "")
                
                msg_text = (
                    f"🔔 **NEW VERIFICATION CODE RECEIVED**\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"🌍 **Country:** {flag} `{c_code}`\n"
                    f"📱 **Number:** `+{clean_num}`\n"
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
            [InlineKeyboardButton("WHATSAPP", callback_data="srv_WHATSAPP"), InlineKeyboardButton("FACEBOOK", callback_data="srv_FACEBOOK")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        current_srv = user_target_services.get(chat_id, "FACEBOOK")
        await update.message.reply_text(
            f"🛠️ **Select a service:**\n"
            f"📌 Current Selected Service: `{current_srv}`\n\n"
            f"👇 Click a button below to change:",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        return

    if text == "📊 Live Traffic":
        loading_msg = await update.message.reply_text("⌛ **Loading Live Traffic...**", parse_mode="Markdown")
        try:
            res = requests.get(f'{BASE_URL}/liveaccess', headers={'mauthapi': PANEL_API_KEY}, timeout=5).json()
            if res.get('meta', {}).get('code') == 200:
                services_list = res.get('data', {}).get('services', [])
                allowed_services = ["FACEBOOK", "WHATSAPP"]
                traffic_text = "🔥 **10 Minute LIVE Traffic**\n\n"
                
                has_data = False
                for s_item in services_list:
                    sid = str(s_item.get('sid', '')).strip().upper()
                    if sid in allowed_services:
                        ranges = s_item.get('ranges', [])
                        total_ranges = len(ranges)
                        
                        traffic_text += f"📘 **{sid} {total_ranges}**\n"
                        
                        country_count = {}
                        for r_raw in ranges:
                            r_str = str(r_raw).replace("XXX", "").replace("xxx", "").strip()
                            flag, c_code, full_name = get_country_info_by_range_or_text(r_str, "")
                            c_key = (flag, full_name)
                            country_count[c_key] = country_count.get(c_key, 0) + 1
                        
                        sorted_countries = sorted(country_count.items(), key=lambda x: x[1], reverse=True)
                        
                        for (flag, full_name), count in sorted_countries:
                            status = "HIGH" if count >= 3 else "LOW"
                            status_icon = "🟢" if status == "HIGH" else "🔴"
                            traffic_text += f"{flag} {full_name} : {status} {status_icon}\n"
                        
                        traffic_text += "\n"
                        has_data = True
                
                if not has_data:
                    traffic_text = "📭 **No live traffic data available right now.**"
                
                await loading_msg.edit_text(traffic_text, parse_mode="Markdown")
            else:
                await loading_msg.edit_text("❌ **Failed to load live traffic.**", parse_mode="Markdown")
        except Exception as e:
            await loading_msg.edit_text(f"⚠️ **Error:** `{e}`", parse_mode="Markdown")
        return

    if text == "📱 Get Number":
        loading_msg = await update.message.reply_text("⌛ **Loading services...**", parse_mode="Markdown")
        try:
            res = requests.get(f'{BASE_URL}/liveaccess', headers={'mauthapi': PANEL_API_KEY}, timeout=5).json()
            if res.get('meta', {}).get('code') == 200:
                services_list = res.get('data', {}).get('services', [])
                keyboard = []
                allowed_services = ["FACEBOOK", "WHATSAPP"]
                seen_services = set()
                
                for s_item in services_list:
                    sid = str(s_item.get('sid', '')).strip().upper()
                    if sid in allowed_services and sid not in seen_services:
                        seen_services.add(sid)
                        keyboard.append([InlineKeyboardButton(sid, callback_data=f"srv_list_{sid}")])
                
                keyboard.append([InlineKeyboardButton("Close", callback_data="close_menu")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await loading_msg.edit_text("📊 **Explore Service:** Select a service below:", parse_mode="Markdown", reply_markup=reply_markup)
            else:
                await loading_msg.edit_text("❌ **Failed to load services.**", parse_mode="Markdown")
        except Exception as e:
            await loading_msg.edit_text(f"⚠️ **Error:** `{e}`", parse_mode="Markdown")
        return

    if text == "📞 Get API Number":
        if chat_id not in user_target_ranges or not user_target_ranges[chat_id]:
            await update.message.reply_text("Please click '⚙️ Set Range' first to set your target range!", parse_mode="Markdown")
            return
        
        range_value = user_target_ranges[chat_id]
        selected_service = user_target_services.get(chat_id, "FACEBOOK")
        
        loading_msg = await update.message.reply_text("⌛ **Getting 4 numbers...**", parse_mode="Markdown")
        assigned_numbers = []
        detected_c_code = ""
        
        try:
            for _ in range(4):
                resp = requests.post(
                    f'{BASE_URL}/getnum',
                    headers={'mauthapi': PANEL_API_KEY, 'Content-Type': 'application/json'},
                    json={"rid": range_value},
                    timeout=5
                ).json()
                
                if resp.get('meta', {}).get('code') == 200:
                    num_data = resp.get('data', {})
                    raw_full_num = str(num_data.get('full_number') or num_data.get('number') or num_data.get('copy')).strip()
                    clean_full_num = get_clean_digits(raw_full_num)
                    
                    if clean_full_num and clean_full_num not in assigned_numbers:
                        assigned_numbers.append(clean_full_num)
                        number_to_user_map[clean_full_num] = chat_id
                        _, detected_c_code, _ = get_country_info_by_range_or_text(clean_full_num, num_data.get('country', ''))

            if len(assigned_numbers) > 0:
                flag, final_c_code, full_country_name = get_country_info_by_range_or_text(range_value, detected_c_code)
                numbers_block = "".join([f"📱 `+{num}`\n" for num in assigned_numbers])
                
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
            
    elif text == "📩 Live OTP Inbox":
        loading_msg = await update.message.reply_text("⌛ **Checking inbox...**", parse_mode="Markdown")
        try:
            msg = "📥 **Active Inbox Payloads:**\n\n"
            res1 = requests.get(f'{BASE_URL}/success-otp', headers={'mauthapi': PANEL_API_KEY}, timeout=5).json()
            if res1.get('meta', {}).get('code') == 200:
                for item in res1.get('data', {}).get('otps', []):
                    clean_num = get_clean_digits(item.get('number', ''))
                    if number_to_user_map.get(clean_num) == chat_id:
                        raw_msg = item.get('message', '')
                        otp_text = extract_pure_code(raw_msg)
                        flag, c_code, _ = get_country_info_by_range_or_text(clean_num, "")
                        msg += f"{flag} `{c_code}` | `+{clean_num}`\n🔑 Code: `{otp_text}`\n──────────────────\n"
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
            f"🛠️ **Preferred Service:** `{user_target_services.get(chat_id, 'FACEBOOK')}`\n"
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

    if data_code.startswith("srv_") and not data_code.startswith("srv_list_"):
        selected_srv = data_code.split("_")[1]
        user_target_services[chat_id] = selected_srv
        await query.edit_message_text(
            f"✅ **Service Successfully Updated!**\n\n"
            f"📌 Current Target Service: `{selected_srv}`\n"
            f"Now you can get numbers using this service filter.",
            parse_mode="Markdown"
        )
        return

    if data_code.startswith("srv_list_"):
        chosen_sid = data_code.replace("srv_list_", "")
        try:
            res = requests.get(f'{BASE_URL}/liveaccess', headers={'mauthapi': PANEL_API_KEY}, timeout=5).json()
            if res.get('meta', {}).get('code') == 200:
                services_list = res.get('data', {}).get('services', [])
                keyboard = []
                
                for s_item in services_list:
                    sid = str(s_item.get('sid', '')).strip().upper()
                    if sid == chosen_sid:
                        ranges = s_item.get('ranges', [])
                        country_groups = {}
                        
                        for r_raw in ranges:
                            r_str = str(r_raw).replace("XXX", "").replace("xxx", "").strip()
                            flag, c_code, full_name = get_country_info_by_range_or_text(r_str, "")
                            display_name = f"{full_name} ({c_code})"
                            
                            if display_name not in country_groups:
                                country_groups[display_name] = {"flag": flag, "c_code": c_code, "ranges": []}
                            country_groups[display_name]["ranges"].append(r_str)
                        
                        sorted_countries = sorted(country_groups.items(), key=lambda x: len(x[1]["ranges"]), reverse=True)
                        
                        for c_name, info in sorted_countries:
                            total_otp = len(info["ranges"])
                            btn_text = f"{info['flag']} {c_name} - {total_otp} OTP"
                            callback_val = f"cnt_{chosen_sid}_{info['c_code']}"
                            
                            keyboard.append([InlineKeyboardButton(btn_text, callback_data=callback_val)])
                        break
                
                keyboard.append([InlineKeyboardButton("Back", callback_data="back_to_services_main")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(f"📊 **Explore Service:** 📘 {chosen_sid}\n\nSelect a country to view available ranges:", parse_mode="Markdown", reply_markup=reply_markup)
        except Exception as e:
            await query.edit_message_text(f"❌ **Error loading countries:** `{e}`", parse_mode="Markdown")
        return

    if data_code.startswith("cnt_"):
        parts = data_code.split("_")
        chosen_sid = parts[1]
        target_c_code = parts[2]
        
        try:
            res = requests.get(f'{BASE_URL}/liveaccess', headers={'mauthapi': PANEL_API_KEY}, timeout=5).json()
            if res.get('meta', {}).get('code') == 200:
                services_list = res.get('data', {}).get('services', [])
                keyboard = []
                
                for s_item in services_list:
                    sid = str(s_item.get('sid', '')).strip().upper()
                    if sid == chosen_sid:
                        ranges = s_item.get('ranges', [])
                        matched_ranges = []
                        flag = "🌍"
                        
                        for r_raw in ranges:
                            r_str = str(r_raw).replace("XXX", "").replace("xxx", "").strip()
                            f_val, c_code_val, _ = get_country_info_by_range_or_text(r_str, "")
                            if c_code_val == target_c_code:
                                flag = f_val
                                matched_ranges.append(r_str)
                        
                        range_counts = {}
                        for r in matched_ranges:
                            range_counts[r] = range_counts.get(r, 0) + 1
                            
                        sorted_ranges = sorted(range_counts.items(), key=lambda x: x[1], reverse=True)
                        
                        row = []
                        for r_val, count in sorted_ranges:
                            btn_text = f"{r_val} ({count})"
                            row.append(InlineKeyboardButton(btn_text, callback_data=f"get4_{r_val}_{target_c_code}"))
                            if len(row) == 2:
                                keyboard.append(row)
                                row = []
                        if row:
                            keyboard.append(row)
                        break
                
                keyboard.append([InlineKeyboardButton("Back", callback_data=f"srv_list_{chosen_sid}")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(f"📊 **Ranges for** 📘 {chosen_sid} - {flag} {target_c_code}\n\nClick on any range to copy it.", parse_mode="Markdown", reply_markup=reply_markup)
        except Exception as e:
            await query.edit_message_text(f"❌ **Error loading ranges:** `{e}`", parse_mode="Markdown")
        return

    if data_code == "back_to_services_main":
        try:
            res = requests.get(f'{BASE_URL}/liveaccess', headers={'mauthapi': PANEL_API_KEY}, timeout=5).json()
            if res.get('meta', {}).get('code') == 200:
                services_list = res.get('data', {}).get('services', [])
                keyboard = []
                allowed_services = ["FACEBOOK", "WHATSAPP"]
                seen_services = set()
                
                for s_item in services_list:
                    sid = str(s_item.get('sid', '')).strip().upper()
                    if sid in allowed_services and sid not in seen_services:
                        seen_services.add(sid)
                        keyboard.append([InlineKeyboardButton(sid, callback_data=f"srv_list_{sid}")])
                
                keyboard.append([InlineKeyboardButton("Close", callback_data="close_menu")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text("📊 **Explore Service:** Select a service below:", parse_mode="Markdown", reply_markup=reply_markup)
        except:
            await query.message.delete()
        return

    if data_code == "close_menu":
        try:
            await query.message.delete()
        except:
            pass

    if data_code.startswith("get4_") or data_code.startswith("chg_"):
        parts = data_code.split("_")
        range_value = parts[1]
        c_code = parts[2] if len(parts) > 2 else ""
        selected_service = user_target_services.get(chat_id, "FACEBOOK")
        
        await query.edit_message_text(text="⌛ **Getting 4 numbers...**", parse_mode="Markdown")

        assigned_numbers = []
        detected_c_code = c_code
        
        try:
            for _ in range(4):
                resp = requests.post(
                    f'{BASE_URL}/getnum',
                    headers={'mauthapi': PANEL_API_KEY, 'Content-Type': 'application/json'},
                    json={"rid": range_value},
                    timeout=5
                ).json()
                
                if resp.get('meta', {}).get('code') == 200:
                    num_data = resp.get('data', {})
                    raw_full_num = str(num_data.get('full_number') or num_data.get('number') or num_data.get('copy')).strip()
                    clean_full_num = get_clean_digits(raw_full_num)
                    
                    if clean_full_num and clean_full_num not in assigned_numbers:
                        assigned_numbers.append(clean_full_num)
                        number_to_user_map[clean_full_num] = chat_id
                        _, detected_c_code, _ = get_country_info_by_range_or_text(clean_full_num, num_data.get('country', ''))

            if len(assigned_numbers) > 0:
                flag, final_c_code, full_country_name = get_country_info_by_range_or_text(range_value, detected_c_code)
                numbers_block = "".join([f"📱 `+{num}`\n" for num in assigned_numbers])
                
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
                await query.edit_message_text(result_msg, parse_mode="Markdown", reply_markup=reply_markup)
            else:
                await query.edit_message_text("❌ **Stock Exhausted:** No numbers available.", parse_mode="Markdown")
        except:
            await query.edit_message_text("⚠️ **Gateway Timeout:** Failed to fetch numbers.", parse_mode="Markdown")

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
