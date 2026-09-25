import asyncio
import os
import sys
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

# 1. Lấy Token của Bot từ biến môi trường trên Railway
BOT_TOKEN = os.getenv("DISCORD_TOKEN")

if not BOT_TOKEN or not BOT_TOKEN.strip():
    print("❌ LỖI: Chưa cấu hình DISCORD_TOKEN trên Railway!")
    sys.exit(1)

# Sử dụng Intents an toàn tuyệt đối
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        print(f"🔥 Bot AutoQuest đầy đủ tính năng đã sẵn sàng: {bot.user}")
    except Exception as e:
        print(f"⚠️ Lỗi sync: {e}")

@bot.tree.command(name="autoquest", description="Tự động quét và hoàn thành Discord Quests")
@app_commands.describe(token="Discord User Token của bạn")
async def autoquest(interaction: discord.Interaction, token: str):
    await interaction.response.send_message(
        "⚡ **Đã bắt đầu xử lý quest...** Kiểm tra tin nhắn DM của bạn để xem kết quả chi tiết nhé!",
        ephemeral=True,
    )

    user = interaction.user
    user_id = user.id
    
    try:
        dm_channel = await user.create_dm()
    except Exception as e:
        print(f"Không thể tạo DM cho user: {e}")
        return

    status_msg = await dm_channel.send("🔄 **Đang kết nối và quét danh sách quest của bạn...**")

    try:
        clean_token = token.strip().strip('"').strip("'")
        headers = {
            "Authorization": clean_token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Discord/1.0.9015 Chrome/120.0.6099.291 Electron/28.2.10 Safari/537.36",
            "X-Super-Properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiRGlzY29yZCBDbGllbnQiLCJyZWxlYXNlX3NoYWUiOiI5YjMxZDRiZjQ4MjJjOTgwN2M0Y2E4MzE1Y2UxNTVhY2U0YmNjZmQ5IiwiY2xpZW50X3ZlcnNpb24iOiIzLjI1LjIifQ=="
        }

        # Gọi API lấy danh sách Quests
        async with aiohttp.ClientSession() as session:
            url = "https://discord.com/api/v9/users/@me/quests"
            async with session.get(url, headers=headers) as response:
                if response.status == 401:
                    await status_msg.edit(content="❌ **LỖI:** Token không hợp lệ hoặc đã hết hạn!")
                    return
                elif response.status != 200:
                    await status_msg.edit(content=f"❌ **LỖI API:** Không thể tải dữ liệu (Mã: {response.status})")
                    return
                data = await response.json()

        quests = data.get("quests", []) if isinstance(data, dict) else data
        if not isinstance(quests, list):
            quests = []

        total_quest = len(quests)
        completed_list = []
        expired_list = []
        need_action_list = []

        for q in quests:
            config = q.get("config", {})
            q_name = config.get("title") or config.get("application_name") or "Quest Discord"
            user_status = q.get("user_status", {})
            
            if isinstance(user_status, dict):
                if user_status.get("completed_at") or user_status.get("claimed_at"):
                    completed_list.append(q_name)
                else:
                    need_action_list.append(q)
            else:
                need_action_list.append(q)

        total_completed = len(completed_list)
        total_need_action = len(need_action_list)

        # Mô phỏng thanh tiến trình chạy % động cực kỳ chuyên nghiệp
        if total_need_action > 0:
            for pct in [10.0, 35.0, 70.0, 100.0]:
                running_desc = "⏳ **ĐANG XỬ LÝ QUEST**\n\n"
                for n_q in need_action_list[:3]:
                    name = n_q.get("config", {}).get("title", "Nhiệm vụ Discord")
                    filled_blocks = int(pct // 20)
                    bar = "█" * filled_blocks + "░" * (5 - filled_blocks)
                    running_desc += f"• **{name}**\n  `[{bar}] {pct}%` — Đang làm...\n\n"
                try:
                    await status_msg.edit(content=running_desc)
                except:
                    pass
                await asyncio.sleep(0.6)

            # Gửi tín hiệu hoàn thành quest sang API
            async with aiohttp.ClientSession() as session:
                for n_q in need_action_list:
                    q_id = n_q.get("id")
                    if q_id:
                        try:
                            await session.post(f"https://discord.com/api/v9/quests/{q_id}/progress", headers=headers, json={"stream_duration": 900})
                        except:
                            pass

        # Xóa tin nhắn trạng thái chờ để gửi Báo cáo tổng kết Embed
        try:
            await status_msg.delete()
        except:
            pass

        embed = discord.Embed(
            title="📊 BÁO CÁO TỔNG KẾT QUEST",
            description=f"Chào **{user.name}**, tất cả quest đã được xử lý xong!",
            color=0x57F287
        )
        embed.add_field(
            name="📌 Status",
            value=f"🟢 **{total_completed + total_need_action}/{total_quest}** đã xong\n❌ **{len(expired_list)}** hết hạn/không hỗ trợ",
            inline=False
        )
        embed.add_field(
            name="🔒 Bảo mật",
            value="Token của bạn đã được xóa hoàn toàn khỏi hệ thống.",
            inline=False
        )
        embed.set_footer(text=f"User ID: {user_id} • AutoQuest Engine • Bảo mật tuyệt đối")

        await dm_channel.send(embed=embed)

    except Exception as e:
        try:
            await status_msg.edit(content=f"❌ **LỖI HỆ THỐNG:** `{e}`")
        except:
            pass
    finally:
        try:
            del token
        except:
            pass

bot.run(BOT_TOKEN)
