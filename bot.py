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
        "স্বাগতম! নম্বর পেতে ইনলাইন বাটন ব্যবহার করুন অথবা নিচের ফরম্যাটে কমান্ড দিন:\n"
        "উদাহরণ: /number 382671XXX 5"
    )

# `/number` কমান্ড হ্যান্ডেল করার জন্য
async def handle_number_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) >= 2:
            service_name = context.args[0]
            max_limit = int(context.args[1])
            
            generated_num = random.randint(1, max_limit)
            
            await update.message.reply_text(
                f"🌐 সার্ভিস/আইডি: `{service_name}`\n"
                f"🎲 প্রাপ্ত র‍্যান্ডম নম্বর: *{generated_num}*",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "দয়া করে সঠিক ফরম্যাটে কমান্ড দিন। যেমন: /number 382671XXX 5"
            )
    except ValueError:
        await update.message.reply_text("নম্বর প্রসেস করতে সমস্যা হয়েছে। দয়া করে সঠিক সংখ্যা দিন।")

# ইনলাইন বাটন থেকে আসা স্ল্যাশযুক্ত কমান্ড (যেমন: `/382671XXX 5`) সরাসরি হ্যান্ডেল করার জন্য
async def handle_slashed_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    match = re.match(r"^/([^\s]+)\s+(\d+)$", text)
    if match:
        service_name = match.group(1)
        max_limit = int(match.group(2))
        
        generated_num = random.randint(1, max_limit)
        
        await update.message.reply_text(
            f"🌐 সার্ভিস/আইডি: `{service_name}`\n"
            f"🎲 প্রাপ্ত র‍্যান্ডম নম্বর: *{generated_num}*",
            parse_mode="Markdown"
        )

if __name__ == "__main__":
    TOKEN = "8998738234:AAGpV1zS4miYRC9AxNpSHvJNyWPgkfI9-U4"

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("number", handle_number_request))
    
    # বাটন থেকে আসা স্ল্যাশ কমান্ড ধরার জন্য ফিল্টার
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_slashed_command))
    app.add_handler(MessageHandler(filters.Regex(r"^/[^\s]+\s+\d+$"), handle_slashed_command))

    print("Bot is running...")
    app.run_polling()
