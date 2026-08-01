import logging
import random
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# মূল হ্যান্ডলার ফাংশন যা বাটন বা কমান্ড রিসিভ করে কাজ করবে
async def handle_number_generation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
        
    text = update.message.text.strip()
    
    # স্ল্যাশ দিয়ে শুরু হওয়া কমান্ড যেমন: `/382671XXX 5` বা `/facebook 10` চেক করা
    match = re.match(r"^/([^\s]+)\s+(\d+)$", text)
    if match:
        service_name = match.group(1)
        max_limit = int(match.group(2))
        
        # ১ থেকে ব্যবহারকারীর দেওয়া লিমিটের মধ্যে র‍্যান্ডম নম্বর জেনারেট করা
        generated_num = random.randint(1, max_limit)
        
        await update.message.reply_text(
            f"🌐 সার্ভিস/আইডি: `{service_name}`\n"
            f"🎲 প্রাপ্ত র‍্যান্ডম নম্বর: *{generated_num}*",
            parse_mode="Markdown"
        )
    else:
        # যদি সাধারণ কোনো টেক্সট বা বাটন টেক্সট হয়
        if text.lower() == "get number":
            await update.message.reply_text("দয়া করে নির্দিষ্ট সার্ভিস বা রেঞ্জের বাটনটিতে ক্লিক করুন।")

if __name__ == "__main__":
    TOKEN = "8998738234:AAGpV1zS4miYRC9AxNpSHvJNyWPgkfI9-U4"

    app = ApplicationBuilder().token(TOKEN).build()

    # সকল প্রকার টেক্সট এবং কমান্ড মেসেজ ধরার জন্য ফিল্টার
    app.add_handler(MessageHandler(filters.TEXT | filters.COMMAND, handle_number_generation))

    print("Bot is running...")
    app.run_polling()
