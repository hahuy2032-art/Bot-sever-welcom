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
            # Thử gọi endpoint tổng quan user thay vì trực tiếp /quests để tránh 404
            async with session.get("https://discord.com/api/v9/users/@me", headers=headers, timeout=15) as resp:
                if resp.status != 200:
                    text_resp = await resp.text()
                    return f"❌ **LỖI XÁC THỰC (Mã {resp.status}):** Token không hợp lệ hoặc bị từ chối."

            # Gọi endpoint lấy danh sách ứng dụng / quà tặng / quest hiện hành
            async with session.get("https://discord.com/api/v9/quests/@me", headers=headers, timeout=15) as resp:
                if resp.status == 404:
                    # Endpoint phụ phòng hờ
                    async with session.get("https://discord.com/api/v9/users/@me/quests", headers=headers, timeout=15) as resp2:
                        if resp2.status != 200:
                            return "✅ **Kết nối thành công!** Tuy nhiên tài khoản hiện tại không có Quest nào khả dụng hoặc tính năng này đang tắt."
                        data = await resp2.json()
                elif resp.status != 200:
                    return f"❌ **LỖI API (Mã {resp.status})** khi quét hệ thống Quest."
                else:
                    data = await resp.json()

        quests = data.get("quests", []) if isinstance(data, dict) else data
        if not isinstance(quests, list):
            quests = []

        total_quest = len(quests)
        completed = 0
        need_action = []

        for q in quests:
            ustatus = q.get("user_status", {})
            if isinstance(ustatus, dict) and (ustatus.get("completed_at") or ustatus.get("claimed_at")):
                completed += 1
            else:
                need_action.append(q)

        if len(need_action) == 0:
            return "✅ **Đã kết nối tài khoản thành công!** Hiện tại tài khoản của sếp không có nhiệm vụ mới nào cần hoàn thành."

        processed = 0
        async with aiohttp.ClientSession() as session:
            for q in need_action:
                qid = q.get("id")
                if qid:
                    try:
                        async with session.post(
                            f"https://discord.com/api/v9/quests/{qid}/progress",
                            headers=headers,
                            json={"stream_duration": 900},
                            timeout=10
                        ) as p_resp:
                            if p_resp.status in [200, 204]:
                                processed += 1
                    except:
                        pass
                    await asyncio.sleep(1)

        return {
            "total": total_quest,
            "completed": completed + processed,
            "new_processed": processed
        }

    except Exception as e:
        return f"❌ Lỗi hệ thống ngầm: `{str(e)}`"

@tasks.loop(hours=24)
async def auto_quest_task():
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return

    result = await run_auto_quest()
    if result and isinstance(result, dict):
        embed = discord.Embed(
            title="📊 BÁO CÁO TỰ ĐỘNG HOÀN THÀNH QUEST (DAILY)",
            description="Hệ thống đã tự động quét và xử lý thành công các nhiệm vụ mới!",
            color=0x57F287
        )
        embed.add_field(name="Tổng số Quest", value=str(result["total"]), inline=True)
        embed.add_field(name="Đã hoàn thành", value=str(result["completed"]), inline=True)
        embed.add_field(name="Vừa xử lý xong", value=str(result["new_processed"]), inline=True)
        embed.set_footer(text="AutoQuest Background Automation Engine")
        
        await channel.send(content="🔔 **Phát hiện và đã tự động cày xong quest mới cho sếp!**", embed=embed)
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
        
    msg = await ctx.send("⏳ Đang tiến hành quét thủ công theo yêu cầu...")
    result = await run_auto_quest()
    if isinstance(result, dict):
        await msg.edit(content=f"✅ **Đã quét xong!** Tổng quest: `{result['total']}`, Đã xong: `{result['completed']}` (Vừa cày thêm: `{result['new_processed']}`)")
    else:
        await msg.edit(content=str(result))

bot.run(BOT_TOKEN)
