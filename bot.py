import logging
import random
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "বট সচল আছে! নিচের 'Get Number' বাটন বা সঠিক কমান্ড ব্যবহার করুন।"
    )

# সব ধরণের মেসেজ এবং বাটন ক্লিক হ্যান্ডেল করার ফাংশন
async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
        
    text = update.message.text.strip()
    
    # যদি মেসেজটি স্ল্যাশ দিয়ে শুরু হয় (যেমন: /382671XXX 5 বা অন্য কোনো আইডি ও সংখ্যা)
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
        # যদি সাধারণ কোনো টেক্সট বা বাটন টেক্সট হয় যাতে স্ল্যাশ বা নম্বর নেই
        if text == "Get Number":
            await update.message.reply_text("দয়া করে নির্দিষ্ট সার্ভিস বা রেঞ্জ সিলেক্ট করুন।")

if __name__ == "__main__":
    TOKEN = "8998738234:AAGpV1zS4miYRC9AxNpSHvJNyWPgkfI9-U4"

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    
    # সব ধরনের টেক্সট মেসেজ ও বাটন ক্লিক রিসিভ করার জন্য ইউনিভার্সাল হ্যান্ডলার
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))
    app.add_handler(MessageHandler(filters.COMMAND, handle_all_messages))

    print("Bot is running...")
    app.run_polling()
