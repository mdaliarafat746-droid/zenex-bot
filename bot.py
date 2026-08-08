async def auto_otp_checker(context: ContextTypes.DEFAULT_TYPE):
    try:
        res1 = requests.get('https://api.zenexnetwork.com/v1/numsuccess/info', headers={'mapikey': PANEL_1_KEY}, timeout=10).json()
        if res1.get('meta', {}).get('code') == 200:
            otps_list = res1.get('data', {}).get('otps', [])
            
            for item in otps_list:
                # প্যানেল থেকে ইউনিক 'nid' নেওয়া হচ্ছে
                nid = item.get('nid') or f"{item.get('number')}_{item.get('otp')}"
                
                # যদি এই nid ইতিপূর্বে নোটিফিকেশন লিস্টে না থাকে, তবেই পাঠাবে
                if nid not in notified_nids:
                    notified_nids.add(nid)
                    
                    # মেমোরি ফাপা রাখতে লিমিটেড রাখা হলো
                    if len(notified_nids) > 2000:
                        notified_nids.pop()
                        
                    num = item.get('number')
                    otp_text = item.get('otp')
                    country = item.get('country', '')
                    service = item.get('service', 'Facebook')
                    
                    flag, c_code, _ = get_country_info_by_range_or_text(str(num), country)
                    await context.bot.send_message(
                        chat_id=ADMIN_CHAT_ID, 
                        text=f"⚔️ **[P1] {service} Received.**\n❓ {flag} {c_code}\n📞 `{num}`\n🔑 `{otp_text}`", 
                        parse_mode="Markdown"
                    )
    except Exception as e:
        print(f"OTP Checker Error: {e}")
