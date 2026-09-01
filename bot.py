async def auto_otp_checker(context: ContextTypes.DEFAULT_TYPE):
    try:
        res = requests.get(f'{BASE_URL}/success-otp', headers={'mauthapi': PANEL_API_KEY}, timeout=5)
        res1 = res.json()
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
                selected_service = user_target_services.get(target_chat_id, "FACEBOOK")
                
                # ইউজারের ইনবক্সের জন্য সম্পূর্ণ তথ্য
                user_msg_text = (
                    f"🔔 **NEW VERIFICATION CODE RECEIVED**\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"🌍 Country: {flag} `{c_code}`\n"
                    f"📱 Number: `+{clean_num}`\n"
                    f"📌 Service: 📘 `{selected_service}`\n"
                    f"🔑 OTP Code: `{otp_text}`\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"⚡ *Status: Successfully Delivered*"
                )
                
                # নাম্বার ফরম্যাট: যেমন 26134** এবং শেষে ৪ ডিজিট
                if len(clean_num) >= 8:
                    prefix_part = clean_num[:5] # যেমন 26134
                    suffix_part = clean_num[-4:] # শেষ ৪ ডিজিট
                    masked_num = f"{prefix_part}**{suffix_part}"
                else:
                    masked_num = clean_num[:2] + "**" + clean_num[-2:]
                
                # স্ক্রিনশটের মতো একই লাইনে গ্রুপের মেসেজ ফরম্যাট
                group_msg_text = (
                    f"{flag} **{c_code}** | 📘 `{masked_num}` ➔ 🔑 `{otp_text}`"
                )
                
                # ইনলাইন বাটন (স্ক্রিনশটের মতো ডানপাশে ওটিপি কোড এবং নিচে Get Number)
                keyboard = [
                    [
                        InlineKeyboardButton("📢 Channel", url="https://t.me/your_channel_link"),
                        InlineKeyboardButton(f"🔑 {otp_text}", callback_data="noop")
                    ],
                    [InlineKeyboardButton("📞 Get Number", url="https://t.me/personal40bot")]
                ]
                group_reply_markup = InlineKeyboardMarkup(keyboard)
                
                # ইউজারের ইনবক্সে পাঠানো
                try:
                    await context.bot.send_message(chat_id=target_chat_id, text=user_msg_text, parse_mode="Markdown")
                except Exception as e:
                    print(f"Failed to send user message: {e}")
                
                # গ্রুপে পাঠানো
                try:
                    await context.bot.send_message(
                        chat_id=OTP_GROUP_CHAT_ID, 
                        text=group_msg_text, 
                        parse_mode="Markdown", 
                        reply_markup=group_reply_markup
                    )
                except Exception as e:
                    print(f"Failed to send group message: {e}")
    except Exception as e:
        print(f"Checker Error: {e}")
