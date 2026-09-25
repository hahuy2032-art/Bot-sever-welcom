import asyncio
import os
import aiohttp
import discord
from discord.ext import commands

BOT_TOKEN = os.getenv("DISCORD_TOKEN")
USER_TOKEN = os.getenv("USER_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

async def fetch_quests():
    if not USER_TOKEN:
        return []

    clean_token = USER_TOKEN.strip().strip('"').strip("'")
    headers = {
        "Authorization": clean_token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Discord/1.0.9015 Chrome/120.0.6099.291 Electron/28.2.10 Safari/537.36"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://discord.com/api/v9/quests/@me", headers=headers, timeout=15) as resp:
                if resp.status == 404:
                    async with session.get("https://discord.com/api/v9/users/@me/quests", headers=headers, timeout=15) as resp2:
                        if resp2.status != 200:
                            return []
                        data = await resp2.json()
                elif resp.status != 200:
                    return []
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
    except Exception:
        return []

@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")

@bot.command(name="check")
async def check_command(ctx):
    # Xóa tin nhắn lệnh !check cho đỡ rác kênh nếu muốn
    try:
        await ctx.message.delete()
    except:
        pass

    msg = await ctx.send("🔍 Đang quét nhiệm vụ trên tài khoản, đợi xíu...")
    
    result = await fetch_quests()
    
    if not result:
        await msg.edit(content="⚠️ Không tìm thấy nhiệm vụ nào hoặc token có vấn đề.")
        return

    embed = discord.Embed(title="🎯 KẾT QUẢ KIỂM TRA QUEST", color=0x57F287)
    for idx, q in enumerate(result, 1):
        status = "✅ Đã xong" if q["completed"] else "⏳ Đang xử lý"
        embed.add_field(name=f"#{idx}. {q['name']}", value=f"🎮 **Game:** {q['game']}\n📌 **Trạng thái:** {status}", inline=False)
    
    await msg.edit(content=None, embed=embed)

if BOT_TOKEN:
    bot.run(BOT_TOKEN)
