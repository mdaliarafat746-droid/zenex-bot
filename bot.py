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

# মূল হ্যান্ডলার ফাংশন
async def handle_bot_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
        
    text = update.message.text.strip()
    
    # ১. যদি বাটন থেকে শুধু "Get Number" লেখাটি আসে
    if text == "📱 Get Number" or text.lower() == "get number":
        # এখানে আপনি চাইলে নির্দিষ্ট কোনো ডিফল্ট নম্বর বা রেঞ্জ সেট করে দিতে পারেন
        # অথবা ব্যবহারকারীকে বলতে পারেন কী করতে হবে
        generated_num = random.randint(1, 10) # উদাহরণস্বরূপ ১ থেকে ১০ এর মধ্যে
        await update.message.reply_text(
            f"📱 আপনার জেনারেট করা র‍্যান্ডম নম্বরটি হলো: *{generated_num}*",
            parse_mode="Markdown"
        )
        return

    # ২. যদি স্ল্যাশযুক্ত কমান্ড বা আইডি ও লিমি트 আসে (যেমন: /382671XXX 5 বা /range 1 50)
    match_number = re.match(r"^/([^\s]+)\s+(\d+)$", text)
    if match_number:
        service_name = match_number.group(1)
        max_limit = int(match_number.group(2))
        
        generated_num = random.randint(1, max_limit)
        
        await update.message.reply_text(
            f"🌐 সার্ভিস/আইডি: `{service_name}`\n"
            f"🎲 প্রাপ্ত র‍্যান্ডম নম্বর: *{generated_num}*",
            parse_mode="Markdown"
        )
        return

    # ৩. সাধারণ /range কমান্ড বা অন্য কিছু যদি আসে
    match_range = re.match(r"^/range\s+(\d+)\s+(\d+)$", text)
    if match_range:
        min_v = int(match_range.group(1))
        max_v = int(match_range.group(2))
        chosen = random.randint(min_v, max_v)
        await update.message.reply_text(
            f"🎯 রেঞ্জ ({min_v} - {max_v}) এর মধ্যে নম্বর: *{chosen}*",
            parse_mode="Markdown"
        )
        return

    # অন্য কোনো সাধারণ লেখা আসলে
    await update.message.reply_text(f"রিসিভ হয়েছে: {text}")

if __name__ == "__main__":
    TOKEN = "8998738234:AAGpV1zS4miYRC9AxNpSHvJNyWPgkfI9-U4"

    app = ApplicationBuilder().token(TOKEN).build()

    # সকল ধরনের টেক্সট ও কমান্ড মেসেজ ধরার ফিল্টার
    app.add_handler(MessageHandler(filters.TEXT | filters.COMMAND, handle_bot_actions))

    print("Bot is running...")
    app.run_polling()
