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
                
                # নম্বরগুলো সরাসরি কোড ব্লকে সাজানো হলো, যাতে সহজে ট্যাপ করেই কপি করা যায়
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
                    f"❓ **Country:** {flag} **{full_country_name}**\n"
                    f"🎟️ **Waiting for OTP**\n\n"
                    f"{numbers_block}\n"
                    f"_👆 উপরের নম্বরের ওপর ট্যাপ করলেই খুব সহজে কপি হয়ে যাবে!_"
                )

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
