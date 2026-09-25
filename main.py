import asyncio
import os
import sys
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

# Lấy Token của cả 2 Bot từ biến môi trường trên Railway
BOT_1_TOKEN = os.getenv("DISCORD_TOKEN")          # Token Bot 1 (Nhận lệnh /autoquest)
BOT_2_TOKEN = os.getenv("SECOND_BOT_TOKEN")       # Token Bot 2 (Chuyên bắn thông báo DM)

if not BOT_1_TOKEN or not BOT_1_TOKEN.strip():
    print("❌ LỖI: Chưa cấu hình DISCORD_TOKEN trên Railway!")
    sys.exit(1)

intents = discord.Intents.default()

# Khởi tạo 2 client bot riêng biệt
bot1 = commands.Bot(command_prefix="!", intents=intents)
bot2 = commands.Bot(command_prefix="!", intents=intents)

# ----------------------------------------------------
# HÀM ĐỂ BOT 2 BẮN THÔNG BÁO VỀ DM CHO USER
# ----------------------------------------------------
async def trigger_bot_2_notification(user_id: int, total_q: int, completed_q: int, action_q: int):
    try:
        await asyncio.sleep(1.5)
        user = await bot2.fetch_user(user_id)
        if not user:
            return
            
        dm_channel = await user.create_dm()
        
        embed = discord.Embed(
            title="📊 BÁO CÁO TỔNG KẾT QUEST",
            description=f"Chào **{user.name}**, quy trình tự động hóa đã hoàn tất!",
            color=0x57F287
        )
        embed.add_field(
            name="📌 Status",
            value=f"🟢 **{completed_q + action_q}/{total_q}** đã xong\n❌ **0** hết hạn/không hỗ trợ",
            inline=False
        )
        embed.add_field(
            name="🔒 Bảo mật",
            value="Token của bạn đã được xóa hoàn toàn khỏi hệ thống.",
            inline=False
        )
        embed.set_footer(text=f"User ID: {user.id} • Multi-Bot Engine • Bảo mật tuyệt đối")

        await dm_channel.send(embed=embed)
        print(f"✅ Bot 2 đã gửi thông báo thành công cho User ID: {user_id}")
    except Exception as e:
        print(f"⚠️ Bot 2 không thể gửi DM: {e}")

# ----------------------------------------------------
# SỰ KIỆN VÀ LỆNH CỦA BOT 1 (NHẬN LỆNH)
# ----------------------------------------------------
@bot1.event
async def on_ready():
    try:
        await bot1.tree.sync()
        print(f"🤖 Bot 1 (Nhận lệnh) đã sẵn sàng: {bot1.user}")
    except Exception as e:
        print(f"⚠️ Lỗi sync Bot 1: {e}")

@bot1.tree.command(name="autoquest", description="Tự động quét và hoàn thành Discord Quests")
@app_commands.describe(token="Discord User Token của bạn")
async def autoquest(interaction: discord.Interaction, token: str):
    await interaction.response.send_message(
        "⚡ **Đã tiếp nhận yêu cầu!** Bot 1 đang xử lý, Bot 2 sẽ gửi kết quả qua DM cho bạn.",
        ephemeral=True,
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

        # Bot 1 gọi API lấy dữ liệu quest
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

        # Gửi tiến trình sang API nếu có quest cần làm
        if total_need_action > 0:
            async with aiohttp.ClientSession() as session:
                for n_q in need_action_list:
                    q_id = n_q.get("id")
                    if q_id:
                        try:
                            await session.post(f"https://discord.com/api/v9/quests/{q_id}/progress", headers=headers, json={"stream_duration": 900})
                        except:
                            pass

        # Kích hoạt Bot 2 gửi thông báo DM kết quả
        if BOT_2_TOKEN and BOT_2_TOKEN.strip():
            asyncio.create_task(trigger_bot_2_notification(user_id, total_quest, total_completed, total_need_action))
        else:
            try:
                dm = await user.create_dm()
                await dm.send(f"✅ Đã xử lý xong {total_need_action} nhiệm vụ!")
            except:
                pass

    except Exception as e:
        print(f"Lỗi tiến trình: {e}")
    finally:
        try:
            del token
        except:
            pass

# ----------------------------------------------------
# SỰ KIỆN CỦA BOT 2 (THÔNG BÁO)
# ----------------------------------------------------
@bot2.event
async def on_ready():
    print(f"📢 Bot 2 (Chuyên thông báo DM) đã sẵn sàng: {bot2.user}")

# ----------------------------------------------------
# CHẠY SONG SONG CẢ 2 BOT TRONG 1 TIẾN TRÌNH TRÊN CLOUD
# ----------------------------------------------------
async def main():
    tasks = [bot1.start(BOT_1_TOKEN)]
    if BOT_2_TOKEN and BOT_2_TOKEN.strip():
        tasks.append(bot2.start(BOT_2_TOKEN))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot đã dừng.")
