import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

BOT_TOKEN = "8998738234:AAGpV1zS4miYRC9AxNpSHvJNyWPgkfI9-U4"

PANEL_1_KEY = "ZNX_5GJKQ6O8MT1F20MSW2G9K4V9"
PANEL_2_KEY = "MYSM6BGQ7U3"

# আপনার দেওয়া ওয়েবসাইট এবং স্ক্রিনশটের সঠিক বেস ইউআরএল
PANEL_2_BASE = "https://mnitnetwork.com/MXS47FLFXOU/tnemn/@public/api"

ADMIN_CHAT_ID = "6470943912"  
notified_otps = set()

def get_country_info_by_range_or_text(range_str, country_field, raw_text=""):
    r_str = str(range_str)
    c_field = str(country_field).lower()
    combined = f"{r_str} {c_field} {str(raw_text).lower()}".strip()
    
    if r_str.startswith("992") or "tajikistan" in combined:
        return "🇹🇯", "TJ"
    elif r_str.startswith("261") or "madagascar" in combined:
        return "🇲🇬", "MG"
    elif r_str.startswith("380") or "ukraine" in combined:
        return "🇺🇦", "UA"
    elif r_str.startswith("224") or "guinea" in combined:
        return "🇬🇳", "GN"
    elif r_str.startswith("228") or "togo" in combined:
        return "🇹🇬", "TG"
    elif r_str.startswith("237") or "cameroon" in combined:
        return "🇨🇲", "CM"
    
    if "malaysia" in combined:
        return "🇲🇾", "MY"
    elif "morocco" in combined:
        return "🇲🇦", "MA"
    elif "russian" in combined or "russia" in combined:
        return "🇷🇺", "RU"
    elif "united kingdom" in combined or "uk" in combined:
        return "🇬🇧", "UK"
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
    elif "egypt" in combined:
        return "🇪🇬", "EG"
    elif "india" in combined:
        return "🇮🇳", "IN"
    elif "ghana" in combined:
        return "🇬🇭", "GH"
    elif "brazil" in combined:
        return "🇧🇷", "BR"
    else:
        return "🌐", "GLOBAL"

async def auto_otp_checker(context: ContextTypes.DEFAULT_TYPE):
    # Panel 1 OTP Check
    try:
        res1 = requests.get('https://api.zenexnetwork.com/v1/numsuccess/info', headers={'mapikey': PANEL_1_KEY}, timeout=5).json()
        if res1.get('meta', {}).get('code') == 200:
            for item in res1.get('data', {}).get('otps', []):
                nid = item.get('nid')
                if nid and nid not in notified_otps:
                    notified_otps.add(nid)
                    num, otp_text, country, service = item.get('number'), item.get('otp'), item.get('country', ''), item.get('service', 'Facebook')
                    flag, c_code = get_country_info_by_range_or_text(str(num), country)
                    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"⚔️ **[P1] {service} Received.**\n❓ {flag} {c_code}\n📞 `{num}`\n🔑 `{otp_text}`", parse_mode="Markdown")
    except:
        pass

    # Panel 2 OTP Check
    try:
        res2 = requests.get(f'{PANEL_2_BASE}/success-otp', headers={'mauthapi': PANEL_2_KEY}, timeout=5).json()
        if res2.get('meta', {}).get('code') == 200:
            for item in res2.get('data', {}).get('otps', []):
                otp_id = item.get('otp_id')
                if otp_id and otp_id not in notified_otps:
                    notified_otps.add(otp_id)
                    num, msg_text = item.get('number'), item.get('message', '')
                    flag, c_code = get_country_info_by_range_or_text(str(num), "")
                    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"⚔️ **[P2] OTP Received.**\n❓ {flag} {c_code}\n📞 `{num}`\n💬 `{msg_text}`", parse_mode="Markdown")
    except:
        pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("📱 Get Number"), KeyboardButton("📩 Check Live OTP")],
        [KeyboardButton("💰 Balance"), KeyboardButton("👤 Profile")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("স্বাগতম! মাল্টি-প্যানেল অটো-ওটিপি বোটে আপনাকে স্বাগতম:", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📱 Get Number":
        loading_msg = await update.message.reply_text("⚡ সকল প্যানেল থেকে রেঞ্জ লোড করা হচ্ছে...")
        all_ranges = []
        
        # Panel 1 Ranges
        try:
            r1 = requests.get('https://api.zenexnetwork.com/v1/active-ranges', headers={'mapikey': PANEL_1_KEY}, timeout=5).json()
            if r1.get('success') == True:
                for r in r1.get('data', {}).get('active_ranges', []):
                    r['panel_type'] = 'panel1'
                    all_ranges.append(r)
        except Exception as e:
            print(f"P1 Error: {e}")

        # Panel 2 Ranges (Using mnitnetwork.com API)
        try:
            r2 = requests.get(f'{PANEL_2_BASE}/liveaccess', headers={'mauthapi': PANEL_2_KEY}, timeout=5).json()
            if r2.get('meta', {}).get('code') == 200:
                services_list = r2.get('data', {}).get('services', [])
                for srv_item in services_list:
                    srv_name = srv_item.get('sid', 'General')
                    ranges_arr = srv_item.get('ranges', [])
                    for rng in ranges_arr:
                        all_ranges.append({
                            'range': rng,
                            'service': srv_name,
                            'country': '',
                            'panel_type': 'panel2'
                        })
        except Exception as e:
            print(f"P2 Error: {e}")
        
        if len(all_ranges) > 0:
            keyboard = []
            for item in all_ranges[:30]:
                rng = str(item.get('range', '') or item.get('rid', ''))
                srv = item.get('service', 'Service')
                api_country = item.get('country', '')
                p_type = item.get('panel_type', 'panel1')
                
                flag, c_code = get_country_info_by_range_or_text(rng, api_country, srv)
                
                panel_tag = "P1" if p_type == 'panel1' else "P2"
                btn_text = f"[{panel_tag}] {flag} {c_code} | {rng} | {srv}"
                
                keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"get3_{rng}_{c_code}_{p_type}")])
            
            keyboard.append([InlineKeyboardButton("🔙 Close", callback_data="close_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await loading_msg.edit_text(f"⚡ **ACTIVE RANGES (Total: {len(all_ranges)})**\n\n_আপনার পছন্দের রেঞ্জটি সিলেক্ট করুন:_", parse_mode="Markdown", reply_markup=reply_markup)
        else:
            await loading_msg.edit_text("❌ কোনো প্যানেল থেকেই রেঞ্জ পাওয়া যায়নি।")
            
    elif text == "📩 Check Live OTP":
        loading_msg = await update.message.reply_text("ওটিপি চেক করা হচ্ছে...")
        try:
            msg = "📥 **Live OTP Payloads:**\n\n"
            
            res1 = requests.get('https://api.zenexnetwork.com/v1/numsuccess/info', headers={'mapikey': PANEL_1_KEY}, timeout=5).json()
            if res1.get('meta', {}).get('code') == 200:
                for item in res1.get('data', {}).get('otps', [])[:3]:
                    num, otp_text, country = item.get('number'), item.get('otp'), item.get('country', '')
                    flag, c_code = get_country_info_by_range_or_text(str(num), country)
                    msg += f"[P1] 📞 `{num}` | {flag} {c_code}\n🔑 `{otp_text}`\n-------------------\n"

            res2 = requests.get(f'{PANEL_2_BASE}/success-otp', headers={'mauthapi': PANEL_2_KEY}, timeout=5).json()
            if res2.get('meta', {}).get('code') == 200:
                for item in res2.get('data', {}).get('otps', [])[:3]:
                    num, otp_msg = item.get('number'), item.get('message', '')
                    flag, c_code = get_country_info_by_range_or_text(str(num), "")
                    msg += f"[P2] 📞 `{num}` | {flag} {c_code}\n💬 `{otp_msg}`\n-------------------\n"

            await loading_msg.edit_text(msg, parse_mode="Markdown")
        except Exception as e:
            await loading_msg.edit_text(f"এরর: {e}")
            
    elif text == "💰 Balance":
        await update.message.reply_text("API কানেকশন সক্রিয় আছে।")
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
        p_type = parts[3] if len(parts) > 3 else "panel1"
        
        await query.edit_message_text(text="🔄 নির্দিষ্ট প্যানেল থেকে নম্বর অ্যাসাইন করা হচ্ছে...")

        assigned_numbers = []
        detected_c_code = c_code
        
        try:
            for _ in range(3):
                if p_type == 'panel1':
                    resp = requests.post(
                        'https://api.zenexnetwork.com/v1/getnum',
                        headers={'mapikey': PANEL_1_KEY, 'Content-Type': 'application/json'},
                        json={"range": range_value, "is_national": False, "remove_plus": False},
                        timeout=5
                    ).json()
                    if resp.get('meta', {}).get('code') == 200:
                        num_data = resp.get('data', {})
                        full_num = num_data.get('full_number')
                        if full_num:
                            assigned_numbers.append(full_num)
                            _, detected_c_code = get_country_info_by_range_or_text(str(full_num), num_data.get('country', ''))
                else:
                    resp = requests.post(
                        f'{PANEL_2_BASE}/getnum',
                        headers={'mauthapi': PANEL_2_KEY, 'Content-Type': 'application/json'},
                        json={"rid": range_value},
                        timeout=5
                    ).json()
                    if resp.get('meta', {}).get('code') == 200:
                        num_data = resp.get('data', {})
                        full_num = num_data.get('full_number') or num_data.get('number')
                        if full_num:
                            assigned_numbers.append(full_num)
                            _, detected_c_code = get_country_info_by_range_or_text(str(full_num), num_data.get('country', ''))

            if len(assigned_numbers) > 0:
                flag, final_c_code = get_country_info_by_range_or_text(range_value, detected_c_code)
                keyboard = [
                    [InlineKeyboardButton("🔄 Next Number", callback_data=f"get3_{range_value}_{c_code}_{p_type}"), 
                     InlineKeyboardButton("🌐 Country", callback_data="back_to_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                panel_label = "Panel 1" if p_type == 'panel1' else "Panel 2"
                result_msg = (
                    f"╔══════════════════════════════╗\n"
                    f"║ {flag} **[{final_c_code}] ASSIGNED ({panel_label})** ║\n"
                    f"╚══════════════════════════════╝\n\n"
                    f"💰 **Per OTP:** 0.30 TK\n\n"
                    f"| SL | Assigned Numbers |\n"
                    f"| :---: | :--- |\n"
                )
                
                for idx, num in enumerate(assigned_numbers, 1):
                    result_msg += f"| **0{idx}** | `{num}` {flag} |\n"
                
                result_msg += "\n📌 _কপি করতে নম্বরের উপর ট্যাপ করুন।_"

                await query.edit_message_text(result_msg, parse_mode="Markdown", reply_markup=reply_markup)
            else:
                await query.edit_message_text("❌ দুঃখিত, বর্তমানে এই রেঞ্জে কোনো নম্বর স্টক নেই।")
                
        except Exception as e:
            await query.edit_message_text("❌ সার্ভার থেকে রেসপন্স পেতে দেরি হচ্ছে। আবার চেষ্টা করুন।")

    elif data_code == "back_to_menu":
        await query.message.delete()
        await query.message.reply_text("মূল মেনু থেকে '📱 Get Number' এ ক্লিক করুন।")

    elif data_code == "close_menu":
        await query.message.delete()

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.job_queue.run_repeating(auto_otp_checker, interval=10, first=3)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(button_click))
    print("Multi-Panel Auto-OTP Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
