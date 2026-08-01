import logging
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "স্বাগতম! কাস্টম রেঞ্জ থেকে র‍্যান্ডম নম্বর পেতে এই কমান্ডটি ব্যবহার করুন:\n"
        "উদাহরণ: /range 1 100 (১ থেকে ১০০ এর মধ্যে নম্বর পেতে)"
    )

# Custom range random number command
async def random_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # ব্যবহারকারী যে দুটি সংখ্যা পাঠাবে তা চেক করা
        if len(context.args) < 2:
            await update.message.reply_text(
                "দয়া করে সঠিক নিয়মে রেঞ্জ দিন। যেমন:\n/range 1 50"
            )
            return

        min_val = int(context.args[0])
        max_val = int(context.args[1])

        if min_val > max_val:
            await update.message.reply_text(
                "প্রথম সংখ্যাটি ছোট এবং দ্বিতীয় সংখ্যাটি বড় হতে হবে!"
            )
            return

        # রেঞ্জের মধ্য থেকে র‍্যান্ডম নম্বর জেনারেট করা
        chosen_number = random.randint(min_val, max_val)
        
        await update.message.reply_text(
            f"🎯 রেঞ্জ ({min_val} - {max_val}) এর মধ্যে আপনার নম্বরটি হলো: *{chosen_number}*",
            parse_mode="Markdown"
        )

    except ValueError:
        await update.message.reply_text("দয়া করে শুধু পূর্ণসংখ্যা ব্যবহার করুন! যেমন: /range 1 10")

if __name__ == "__main__":
    # আপনার টেলিগ্রাম বটের টোকেন এখানে বসাবেন বা এনভায়রনমেন্ট ভ্যারিয়েবল ব্যবহার করবেন
    TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("range", random_range))

    print("Bot is running...")
    app.run_polling()
