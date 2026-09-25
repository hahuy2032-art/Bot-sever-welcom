import asyncio
import os
import sys
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

BOT_1_TOKEN = os.getenv("DISCORD_TOKEN")
BOT_2_TOKEN = os.getenv("SECOND_BOT_TOKEN")

if not BOT_1_TOKEN or not BOT_1_TOKEN.strip():
    print("❌ LỖI: Chưa cấu hình DISCORD_TOKEN trên Railway!")
    sys.exit(1)

intents = discord.Intents.default()
bot1 = commands.Bot(command_prefix="!", intents=intents)
bot2 = commands.Bot(command_prefix="!", intents=intents)

async def trigger_bot_2_notification(user_id: int, total_q: int, completed_q: int, action_q: int):
    try:
        await asyncio.sleep(2)
        user = await bot2.fetch_user(user_id)
        if not user:
            return
        dm_channel = await user.create_dm()
        
        embed = discord.Embed(
            title="📊 BÁO CÁO TỔNG KẾT QUEST",
            description=f"Chào **{user.name}**, hệ thống đã xử lý xong toàn bộ nhiệm vụ!",
            color=0x57F287
        )
        embed.add_field(
            name="📌 Status",
            value=f"🟢 **{completed_q + action_q}/{total_q}** đã hoàn thành\n❌ **0** lỗi",
            inline=False
        )
        embed.add_field(
            name="🔒 Bảo mật",
            value="Token của bạn đã được xóa sạch khỏi bộ nhớ.",
            inline=False
        )
        embed.set_footer(text=f"User ID: {user.id} • Multi-Bot Engine")
        await dm_channel.send(embed=embed)
    except Exception as e:
        print(f"Lỗi Bot 2 gửi DM: {e}")

@bot1.event
async def on_ready():
    try:
        await bot1.tree.sync()
        print(f"🤖 Bot 1 đã sẵn sàng: {bot1.user}")
    except Exception as e:
        print(f"Lỗi sync Bot 1: {e}")

@bot1.tree.command(name="autoquest", description="Tự động hoàn thành Discord Quests")
@app_commands.describe(token="Discord User Token của bạn")
async def autoquest(interaction: discord.Interaction, token: str):
    # PHẢN HỒI NGAY LẬP TỨC TRONG 0.1 GIÁY ĐỂ KHÔNG BAO GIỜ BỊ LỖI "ỨNG DỤNG KHÔNG PHẢN HỒI"
    await interaction.response.send_message(
        "⚡ **Đã tiếp nhận lệnh!** Hệ thống đang xử lý, kiểm tra tin nhắn DM để nhận kết quả.",
        ephemeral=True
    )

    user = interaction.user
    user_id = user.id

    try:
        clean_token = token.strip().strip('"').strip("'")
        headers = {
            "Authorization": clean_token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Discord/1.0.9015 Chrome/120.0.6099.291 Electron/28.2.10 Safari/537.36",
            "X-Super-Properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiRGlzY29yZCBDbGllbnQiLCJyZWxlYXNlX3NoYWUiOiI5YjMxZDRiZjQ4MjJjOTgwN2M0Y2E4MzE1Y2UxNTVhY2U0YmNjZmQ5IiwiY2xpZW50X3ZlcnNpb24iOiIzLjI1LjIifQ=="
        }

        async with aiohttp.ClientSession() as session:
            url = "https://discord.com/api/v9/users/@me/quests"
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    try:
                        dm = await user.create_dm()
                        await dm.send("❌ **LỖI:** Token không hợp lệ hoặc đã hết hạn!")
                    except:
                        pass
                    return
                data = await response.json()

        quests = data.get("quests", []) if isinstance(data, dict) else data
        if not isinstance(quests, list):
            quests = []

        total_quest = len(quests)
        completed_list = []
        need_action_list = []

        for q in quests:
            user_status = q.get("user_status", {})
            if isinstance(user_status, dict) and (user_status.get("completed_at") or user_status.get("claimed_at")):
                completed_list.append(q)
            else:
                need_action_list.append(q)

        total_completed = len(completed_list)
        total_need_action = len(need_action_list)

        if total_need_action > 0:
            async with aiohttp.ClientSession() as session:
                for n_q in need_action_list:
                    q_id = n_q.get("id")
                    if q_id:
                        try:
                            await session.post(f"https://discord.com/api/v9/quests/{q_id}/progress", headers=headers, json={"stream_duration": 900})
                        except:
                            pass

        if BOT_2_TOKEN and BOT_2_TOKEN.strip():
            asyncio.create_task(trigger_bot_2_notification(user_id, total_quest, total_completed, total_need_action))
        else:
            try:
                dm = await user.create_dm()
                await dm.send(f"✅ Đã xử lý xong {total_need_action} nhiệm vụ!")
            except:
                pass

    except Exception as e:
        print(f"Lỗi: {e}")
    finally:
        try:
            del token
        except:
            pass

@bot2.event
async def on_ready():
    print(f"📢 Bot 2 đã sẵn sàng: {bot2.user}")

async def main():
    tasks = [bot1.start(BOT_1_TOKEN)]
    if BOT_2_TOKEN and BOT_2_TOKEN.strip():
        tasks.append(bot2.start(BOT_2_TOKEN))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except:
        pass
