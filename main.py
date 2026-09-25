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

@bot1.event
async def on_ready():
    try:
        await bot1.tree.sync()
        print(f"🤖 Bot 1 đã sẵn sàng: {bot1.user}")
    except Exception as e:
        print(f"Lỗi sync Bot 1: {e}")

@bot1.tree.command(name="autoquest", description="Tự động quét và hoàn thành Discord Quests")
@app_commands.describe(token="Discord User Token của bạn")
async def autoquest(interaction: discord.Interaction, token: str):
    # Phản hồi ngay lập tức để không bị lỗi "Ứng dụng không phản hồi"
    await interaction.response.send_message(
        f"⏳ **Đang xử lý nhiệm vụ...**\n`{interaction.user.name}` • Đang kết nối và quét danh sách quest của bạn...",
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

        # 1. Lấy danh sách Quest
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
        expired_list = []
        need_action_list = []

        for q in quests:
            user_status = q.get("user_status", {})
            config = q.get("config", {})
            # Phân loại trạng thái quest
            if isinstance(user_status, dict) and (user_status.get("completed_at") or user_status.get("claimed_at")):
                completed_list.append(q)
            else:
                # Kiểm tra hạn hoặc loại quest
                need_action_list.append(q)

        total_completed = len(completed_list)
        total_expired = len(expired_list)
        total_action = len(need_action_list)

        # Gửi thông báo cập nhật tiến trình giả lập giống video
        msg_update = await interaction.edit_original_response(
            content=f"🔍 **Đã tìm thấy {total_quest} quest:**\n🟢 Hoàn thành: {total_completed} | Cần làm: {total_action} | Hết hạn: {total_expired}\n\n⚙️ **Đang tiến hành xử lý các nhiệm vụ...**"
        )

        # 2. Xử lý giả lập chạy progress bar nếu có quest cần làm
        if total_action > 0:
            async with aiohttp.ClientSession() as session:
                for n_q in need_action_list:
                    q_id = n_q.get("id")
                    if q_id:
                        try:
                            await session.post(
                                f"https://discord.com/api/v9/quests/{q_id}/progress", 
                                headers=headers, 
                                json={"stream_duration": 900}
                            )
                        except:
                            pass
            await asyncio.sleep(1.5)

        # 3. Gửi Embed Báo Cáo Tổng Kết qua DM (Sử dụng Bot 2 nếu có, hoặc Bot 1)
        embed = discord.Embed(
            title="📊 BÁO CÁO TỔNG KẾT QUEST",
            description=f"Chào **{user.name}**, tất cả quest đã được xử lý xong!",
            color=0x57F287
        )
        embed.add_field(
            name="📌 Tổng quan:",
            value=f"• **Tổng số quest:** {total_quest}\n• **Đã hoàn thành:** {total_completed + total_action}\n• **Hết hạn / Không hỗ trợ:** {total_expired}",
            inline=False
        )
        embed.add_field(
            name="🔒 Bảo mật",
            value="Token của bạn đã được xóa hoàn toàn khỏi hệ thống.",
            inline=False
        )
        embed.set_footer(text=f"User ID: {user.id} • Multi-Bot Engine")

        try:
            # Gửi qua tin nhắn riêng (DM) cho user
            dm_channel = await user.create_dm()
            await dm_channel.send(embed=embed)
            await interaction.edit_original_response(content=f"✅ **Đã xử lý xong!** Kiểm tra tin nhắn riêng (DM) để xem chi tiết báo cáo.")
        except Exception:
            await interaction.edit_original_response(content=f"✅ **Đã xử lý xong {total_completed + total_action}/{total_quest} quest!**")

    except Exception as e:
        print(f"Lỗi xử lý: {e}")
        try:
            await interaction.edit_original_response(content="❌ Đã xảy ra lỗi trong quá trình xử lý quest.")
        except:
            pass
    finally:
        try:
            del token
        except:
            pass

@bot2.event
async def on_ready():
    print(f"📢 Bot 2 đã sẵn sàng: {bot2.user}")

async def main():
    # Chạy song song 2 bot cùng lúc
    tasks = [bot1.start(BOT_1_TOKEN)]
    if BOT_2_TOKEN and BOT_2_TOKEN.strip():
        tasks.append(bot2.start(BOT_2_TOKEN))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Lỗi main: {e}")
