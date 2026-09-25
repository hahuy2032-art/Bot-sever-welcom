import asyncio
import os
import sys
import aiohttp
import discord
from discord.ext import commands, tasks

BOT_TOKEN = os.getenv("DISCORD_TOKEN")
USER_TOKEN = os.getenv("USER_TOKEN") 
CHANNEL_ID_RAW = os.getenv("CHANNEL_ID", "1552922576584577034")

if not BOT_TOKEN or not BOT_TOKEN.strip():
    print("❌ LỖI: Chưa cấu hình DISCORD_TOKEN trên Railway!")
    sys.exit(1)

if not USER_TOKEN or not USER_TOKEN.strip():
    print("❌ CẢNH BÁO: Chưa cấu hình USER_TOKEN trên hệ thống Railway!")

try:
    CHANNEL_ID = int(CHANNEL_ID_RAW)
except ValueError:
    CHANNEL_ID = 1552922576584577034

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

async def run_auto_quest():
    if not USER_TOKEN:
        return "❌ Chưa cấu hình USER_TOKEN trên hệ thống Railway!"

    clean_token = USER_TOKEN.strip().strip('"').strip("'")
    headers = {
        "Authorization": clean_token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Discord/1.0.9015 Chrome/120.0.6099.291 Electron/28.2.10 Safari/537.36",
        "X-Super-Properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiRGlzY29yZCBDbGllbnQiLCJyZWxlYXNlX3NoYWUiOiI5YjMxZDRiZjQ4MjJjOTgwN2M0Y2E4MzE1Y2UxNTVhY2U0YmNjZmQ5IiwiY2xpZW50X3ZlcnNpb24iOiIzLjI1LjIifQ=="
    }

    try:
        async with aiohttp.ClientSession() as session:
            # Lấy danh sách quests từ API chính thức
            async with session.get("https://discord.com/api/v9/quests/@me", headers=headers, timeout=15) as resp:
                if resp.status == 404:
                    async with session.get("https://discord.com/api/v9/users/@me/quests", headers=headers, timeout=15) as resp2:
                        if resp2.status != 200:
                            return "✅ **Kết nối thành công!** Không tìm thấy dữ liệu Quest nào qua API."
                        data = await resp2.json()
                elif resp.status != 200:
                    return f"❌ **LỖI API (Mã {resp.status})** khi lấy thông tin Quest."
                else:
                    data = await resp.json()

        quests = data.get("quests", []) if isinstance(data, dict) else data
        if not isinstance(quests, list):
            quests = []

        detailed_quests = []

        async with aiohttp.ClientSession() as session:
            for q in quests:
                qid = q.get("id")
                ustatus = q.get("user_status", {})
                config = q.get("config", {})
                
                # Lấy tên game/ứng dụng và tên nhiệm vụ từ cấu trúc chuẩn của Discord Quest
                app = config.get("application", {})
                game_name = app.get("name", "Unknown Game")
                
                messages = config.get("messages", {})
                quest_name = messages.get("quest_title", messages.get("game_title", game_name))

                is_completed = isinstance(ustatus, dict) and (ustatus.get("completed_at") or ustatus.get("claimed_at"))
                
                processed_now = False
                if not is_completed and qid:
                    try:
                        async with session.post(
                            f"https://discord.com/api/v9/quests/{qid}/progress",
                            headers=headers,
                            json={"stream_duration": 900},
                            timeout=10
                        ) as p_resp:
                            if p_resp.status in [200, 204]:
                                processed_now = True
                    except:
                        pass
                    await asyncio.sleep(1)

                detailed_quests.append({
                    "name": quest_name,
                    "game": game_name,
                    "completed": is_completed or processed_now
                })

        return detailed_quests

    except Exception as e:
        return f"❌ Lỗi hệ thống ngầm: `{str(e)}`"

@tasks.loop(hours=24)
async def auto_quest_task():
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return

    result = await run_auto_quest()
    if isinstance(result, list):
        if len(result) == 0:
            return
        
        embed = discord.Embed(
            title="🎯 BÁO CÁO NHIỆM VỤ DISCORD (QUESTS)",
            description="Hệ thống đã tự động quét và xử lý các nhiệm vụ mới cho sếp:",
            color=0x5865F2
        )
        
        for idx, q in enumerate(result, 1):
            status_text = "✅ Đã hoàn thành / Đã cày xong" if q["completed"] else "⏳ Đang xử lý"
            embed.add_field(
                name=f"#{idx}. {q['name']}",
                value=f"🎮 **Game:** {q['game']}\n📌 **Trạng thái:** {status_text}",
                inline=False
            )
            
        embed.set_footer(text="AutoQuest Detailed Notification Engine")
        await channel.send(content="🔔 **Cập nhật danh sách Quest mới từ tài khoản của sếp!**", embed=embed)
    elif isinstance(result, str):
        try:
            channel = bot.get_channel(CHANNEL_ID)
            if channel:
                await channel.send(result)
        except:
            pass

@bot.event
async def on_ready():
    print(f"🤖 Bot đã chạy ngầm thành công: {bot.user}")
    if not auto_quest_task.is_running():
        auto_quest_task.start()

@bot.command(name="checknow")
async def checknow(ctx):
    try:
        await ctx.message.delete()
    except:
        pass
        
    msg = await ctx.send("⏳ Đang tiến hành quét chi tiết tên nhiệm vụ và game...")
    result = await run_auto_quest()
    
    if isinstance(result, list):
        if len(result) == 0:
            await msg.edit(content="✅ Không có nhiệm vụ nào khả dụng trên tài khoản lúc này.")
            return

        embed = discord.Embed(
            title="🎯 KẾT QUẢ QUÉT NHIỆM VỤ CHI TIẾT",
            description="Danh sách các Quest hiện có trên tài khoản của sếp:",
            color=0x57F287
        )
        
        for idx, q in enumerate(result, 1):
            status_text = "✅ Đã hoàn thành / Đã cày xong" if q["completed"] else "⏳ Đang xử lý"
            embed.add_field(
                name=f"#{idx}. {q['name']}",
                value=f"🎮 **Game:** {q['game']}\n📌 **Trạng thái:** {status_text}",
                inline=False
            )
            
        await msg.edit(content=None, embed=embed)
    else:
        await msg.edit(content=str(result))

bot.run(BOT_TOKEN)
