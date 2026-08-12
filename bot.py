def get_country_info_by_range_or_text(range_str, country_field, raw_text=""):
    r_str = str(range_str).strip().replace("+", "")
    c_field = str(country_field).strip().upper()
    
if not c_field or len(c_field) > 3:
    c_field = "INT"

    # কমন কান্ট্রি কোড ও ফ্ল্যাগের অটোম্যাপ ডিকশনারি
    # প্রিফিক্স বড় থেকে ছোট সাজানো হয়েছে যাতে সঠিক কোড আগে ম্যাচ করে
    prefix_map = {
        "880": ("🇧🇩", "BD", "BANGLADESH"),
        "91":  ("🇮🇳", "IN", "INDIA"),
        "1":   ("🇺🇸", "US", "UNITED STATES"),
        "44":  ("🇬🇧", "GB", "UNITED KINGDOM"),
        "7":   ("🇷🇺", "RU", "RUSSIA"),
        "992": ("🇹🇯", "TJ", "TAJIKISTAN"),
        "261": ("🇲🇬", "MG", "MADAGASCAR"),
        "380": ("🇺🇦", "UA", "UKRAINE"),
        "224": ("🇬🇳", "GN", "GUINEA"),
        "228": ("🇹🇬", "TG", "TOGO"),
        "237": ("🇨🇲", "CM", "CAMEROON"),
        "225": ("🇨🇮", "CI", "IVORY COAST"),
        "236": ("🇨🇫", "CF", "CENTRAL AFRICA"),
        "229": ("🇧🇯", "BJ", "BENIN"),
        "60":  ("🇲🇾", "MY", "MALAYSIA"),
        "212": ("🇲🇦", "MA", "MOROCCO"),
        "249": ("🇸🇩", "SD", "SUDAN"),
        "255": ("🇹🇿", "TZ", "TANZANIA"),
        "263": ("🇿🇼", "ZW", "ZIMBABWE"),
        "213": ("🇩🇿", "DZ", "ALGERIA"),
        "591": ("🇧🇴", "BO", "BOLIVIA"),
        "20":  ("🇪🇬", "EG", "EGYPT"),
        "233": ("🇬🇭", "GH", "GHANA"),
        "55":  ("🇧🇷", "BR", "BRAZIL")
    }
    
    # প্রথমে প্রিফিক্স দিয়ে খোঁজা
    for prefix, (flag, code, name) in sorted(prefix_map.items(), key=lambda x: len(x[0]), reverse=True):
        if r_str.startswith(prefix):
            return flag, code, name
            
    # যদি প্যানেল থেকে সরাসরি শর্ট কোড বা কান্ট্রি নাম দেয় (যেমন: MG, TZ)
    if len(c_field) == 2:
        # জেনেরিক ফ্ল্যাগ জেনারেটর (ISO 2-letter code থেকে ইমোজি ফ্ল্যাগ তৈরি)
        flag = ''.join([chr(ord(char) + 127397) for char in c_field])
        return flag, c_field, c_field
        
    return "🌍", c_field if c_field else "INT", "INTERNATIONAL"
