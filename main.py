import os
import asyncio
from pyrogram import Client, filters, enums
from motor.motor_asyncio import AsyncIOMotorClient
from flask import Flask
from threading import Thread

# --- Web Server ---
web_app = Flask('')
@web_app.route('/')
def home(): return "Rose-Clone Bot is Online!"

def run_web():
    web_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# --- Config ---
API_ID = 35881078
API_HASH = "c7a3d1f7c484275a3e6c648d7e8cea15"
BOT_TOKEN = "8784127770:AAF9mwfcFrpJQNZ62-Ndf__VOovSxb0fFcU"
MONGO_URI = "mongodb+srv://mostofa7077:Mostofa123@cluster0.x08t0rs.mongodb.net/?appName=Cluster0"
ADMIN_ID = 6830289510 

app = Client("RoseCloneBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
db = AsyncIOMotorClient(MONGO_URI)["RoseCloneDB"]["filters"]

# --- ১. ফিল্টার সেভ করার কমান্ড (এখানে ৩ সেকেন্ড পর ডিলিট হবে) ---
@app.on_message(filters.command("filter") & filters.user(ADMIN_ID))
async def add_filter(client, message):
    if message.reply_to_message:
        if len(message.command) < 2:
            msg = await message.reply("❌ **ব্যবহার:** `/filter keyword` (replying to a msg)")
            await asyncio.sleep(3)
            return await msg.delete()
        
        keyword = message.command[1].lower()
        reply_msg = message.reply_to_message
        content = reply_msg.text.markdown if reply_msg.text else (reply_msg.caption.markdown if reply_msg.caption else "")
        
        data = {
            "chat_id": message.chat.id,
            "keyword": keyword,
            "content": content,
            "file_id": reply_msg.photo.file_id if reply_msg.photo else (reply_msg.video.file_id if reply_msg.video else None),
            "type": "photo" if reply_msg.photo else ("video" if reply_msg.video else "text")
        }
    else:
        if len(message.command) < 3:
            msg = await message.reply("❌ **ব্যবহার:** `/filter keyword text` or reply to a msg.")
            await asyncio.sleep(3)
            return await msg.delete()
        
        keyword = message.command[1].lower()
        content = message.text.markdown.split(None, 2)[2]
        data = {"chat_id": message.chat.id, "keyword": keyword, "content": content, "file_id": None, "type": "text"}

    # ডাটাবেজে সেভ/আপডেট
    await db.update_one({"chat_id": message.chat.id, "keyword": keyword}, {"$set": data}, upsert=True)
    
    # কমান্ড এবং কনফার্মেশন মেসেজ ৩ সেকেন্ড পর ডিলিট হবে
    confirm_msg = await message.reply(f"✅ Filter **'{keyword}'** has been saved!")
    await asyncio.sleep(3)
    try:
        await message.delete()      # আপনার দেওয়া /filter কমান্ড ডিলিট
        await confirm_msg.delete()  # বটের দেওয়া Saved মেসেজ ডিলিট
    except: pass

# --- ২. অটো রিপ্লাই ইঞ্জিন (এই রিপ্লাইগুলো ডিলিট হবে না) ---
@app.on_message(filters.text & (filters.group | filters.private) & ~filters.command)
async def auto_reply(client, message):
    query = message.text.lower().strip()
    
    # সরাসরি কি-ওয়ার্ড দিয়ে ডাটাবেস চেক
    filter_data = await db.find_one({"chat_id": message.chat.id, "keyword": query})
    
    if filter_data:
        content = filter_data["content"]
        # {mention} হ্যান্ডেল করা
        if "{mention}" in content:
            user = message.from_user
            mention = f"[{user.first_name}](tg://user?id={user.id})"
            content = content.replace("{mention}", mention)
        
        try:
            if filter_data.get("type") == "photo":
                await message.reply_photo(filter_data["file_id"], caption=content)
            elif filter_data.get("type") == "video":
                await message.reply_video(filter_data["file_id"], caption=content)
            else:
                # টেক্সট রিপ্লাই (বোল্ড এবং লিংক প্রিভিউ সহ)
                await message.reply_text(content, disable_web_page_preview=False)
        except Exception as e:
            print(f"Reply Error: {e}")

# --- ৩. ফিল্টার ডিলিট করার কমান্ড (৩ সেকেন্ড পর ডিলিট হবে) ---
@app.on_message(filters.command("stop") & filters.user(ADMIN_ID))
async def stop_filter(client, message):
    if len(message.command) < 2: return
    keyword = message.command[1].lower()
    await db.delete_one({"chat_id": message.chat.id, "keyword": keyword})
    
    del_msg = await message.reply(f"🗑 Stopped filter: **{keyword}**")
    await asyncio.sleep(3)
    try:
        await message.delete()
        await del_msg.delete()
    except: pass

if __name__ == "__main__":
    Thread(target=run_web).start()
    print("🚀 Rose-Clone Filter Bot is Starting...")
    app.run()
    
