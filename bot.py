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
        "স্বাগতম! নম্বর পেতে নিচের ফরম্যাটে কমান্ড ব্যবহার করুন:\n"
        "উদাহরণ: /number 382671XXX 5\n"
        "অথবা সরাসরি রেঞ্জের জন্য: /range 1 50"
    )

# Custom range random number command (যদি কেউ সরাসরি রেঞ্জ দিতে চায়)
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


# ইনলাইন বাটন থেকে আসা কমান্ড হ্যান্ডেল করার জন্য (যেমন: /382671XXX 5 বা /number ID count)
async def handle_number_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # যদি ব্যবহারকারী দুটি আর্গুমেন্ট দেয় (যেমন: আইডি এবং কত সংখ্যা পর্যন্ত বা রেঞ্জ)
        if len(context.args) >= 2:
            service_name = context.args[0]
            max_limit = int(context.args[1])
            
            # ১ থেকে ব্যবহারকারীর দেওয়া সংখ্যাটির মধ্যে র‍্যান্ডম নম্বর জেনারেট করবে
            generated_num = random.randint(1, max_limit)
            
            await update.message.reply_text(
                f"🌐 সার্ভিস/আইডি: `{service_name}`\n"
                f"🎲 প্রাপ্ত র‍্যান্ডম নম্বর: *{generated_num}*",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "বট সক্রিয় আছে! দয়া করে সঠিক ফরম্যাটে কমান্ড দিন।"
            )
    except ValueError:
        await update.message.reply_text("নম্বর প্রসেস করতে সমস্যা হয়েছে। দয়া করে সঠিক সংখ্যা দিন।")

if __name__ == "__main__":
    # আপনার টেলিগ্রাম বটের টোকেন এখানে বসাবেন বা এনভায়রনমেন্ট ভ্যারিয়েবল ব্যবহার করবেন
    TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("range", random_range))
    
    # আপনার স্ক্রিনশটের বাটনগুলোর ফরম্যাট হ্যান্ডেল করার জন্য জেনেরিক হ্যান্ডলার (যে কোনো টেক্সট বা আইডি দিয়ে কমান্ড আসলে তা ধরতে পারবে)
    # অথবা আপনার যদি নির্দিষ্ট কোনো কমান্ড বা ফাংশন থাকে তা এখানে যোগ করা হয়েছে
    app.add_handler(CommandHandler("number", handle_number_request))

    print("Bot is running...")
    app.run_polling()
