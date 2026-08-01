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
        "স্বাগতম! নম্বর পেতে নিচের ফরম্যাটে কমান্ড ব্যবহার করুন:\n"
        "উদাহরণ: /number 382671XXX 5\n"
        "অথবা সরাসরি রেঞ্জের জন্য: /range 1 50"
    )

# Custom range random number command
async def random_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) < 2:
            await update.message.reply_text(
                "দয়া করে সঠিক নিয়মে রেঞ্জ দিন। যেমন:\n/range 1 50"
            )
            return

        min_val = int(context.args[0])
        max_val = int(context.args[1])

        if min_val > max_val:
            await update.message.reply_text(
                "প্রথম সংখ্যাটি ছোট এবং দ্বিতীয় সংখ্যাটি বড় হতে হবে!"
            )
            return

        chosen_number = random.randint(min_val, max_val)
        
        await update.message.reply_text(
            f"🎯 রেঞ্জ ({min_val} - {max_val}) এর মধ্যে আপনার নম্বরটি হলো: *{chosen_number}*",
            parse_mode="Markdown"
        )

    except ValueError:
        await update.message.reply_text("দয়া করে শুধু পূর্ণসংখ্যা ব্যবহার করুন! যেমন: /range 1 10")

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
    # প্যাটার্ন চেক করা যেমন: /382671XXX 5
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
    app.add_handler(CommandHandler("range", random_range))
    app.add_handler(CommandHandler("number", handle_number_request))
    
    # বাটন থেকে আসা স্ল্যাশ কমান্ড ধরার জন্য ফিল্টার
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_slashed_command))
    # যদি সরাসরি বট কমান্ড হিসেবে পড়তে চায়
    app.add_handler(MessageHandler(filters.Regex(r"^/[^\s]+\s+\d+$"), handle_slashed_command))

    print("Bot is running...")
    app.run_polling()
