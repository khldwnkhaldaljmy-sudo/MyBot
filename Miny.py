import os
import subprocess
import time
import asyncio
from telethon import TelegramClient, events

# -------- ضع بياناتك هنا --------
API_ID = 39995005 
API_HASH = 'b474477cf73b6b38d77568a406e72bc8'
BOT_TOKEN = '8216720307:AAE_nWpj0Br0u_y6YNSaYzSTMI8sgnMHu7w'
# -------------------------

client = TelegramClient('bot_session', API_ID, API_HASH)
video_lock = asyncio.Lock()

def get_duration(path):
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries',
             'format=duration', '-of',
             'default=noprint_wrappers=1:nokey=1', path],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        return float(result.stdout)
    except: return 0

def compress_video(input_path, output_path, target_mb=45):
    duration = get_duration(input_path)
    if duration == 0: return
    total_kbps = (target_mb * 8192) / duration
    video_kbps = int(total_kbps - 64)

    subprocess.run([
        'ffmpeg', '-y', '-i', input_path,
        '-vf', 'scale=-2:480',
        '-c:v', 'libx264',
        '-b:v', f'{video_kbps}k',
        '-preset', 'veryfast',
        '-c:a', 'aac', '-b:a', '64k',
        '-movflags', '+faststart',
        output_path
    ], check=True)

@client.on(events.NewMessage(pattern=r'(?i)^k$'))
async def reply_k(event):
    await event.respond('okay ✅ البوت يعمل بنجاح على Render')

@client.on(events.NewMessage(func=lambda e: e.video))
async def handle_video(event):
    async with video_lock:
        original_caption = event.message.message or "Video"
        status_msg = await event.respond(f"⏳ جاري معالجة: **{original_caption}**")
        
        inp = f"in_{event.message.id}.mp4"
        out = f"out_{event.message.id}.mp4"

        try:
            await event.download_media(inp)
            await status_msg.edit(f"⚙️ جاري الضغط...")
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, compress_video, inp, out, 45)
            
            size = os.path.getsize(out) / (1024 * 1024)
            await event.client.send_file(
                event.chat_id, out, 
                caption=f"**{original_caption}**\n\n✅ تم الضغط بنجاح\n📦 الحجم: {size:.2f} MB",
                supports_streaming=True
            )
            await status_msg.delete()
        except Exception as e:
            await event.respond(f"❌ خطأ: {e}")
        finally:
            for f in [inp, out]:
                if os.path.exists(f): os.remove(f)

print("🚀 Bot started...")
client.start(bot_token=BOT_TOKEN)
client.run_until_disconnected()
