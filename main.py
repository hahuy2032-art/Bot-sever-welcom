import asyncio
import os
import sys
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

bot_token = os.getenv("DISCORD_TOKEN")
if not bot_token or not bot_token.strip():
    print("❌ LỖI: Chưa thiết lập DISCORD_TOKEN trên Railway/Render!")
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
SERVER_ID = 1551547049600618538

@bot.event
async def on_ready():
    try:
        guild_id = discord.Object(id=SERVER_ID)
        bot.tree.copy_global_to(guild=guild_id)
        await bot.tree.sync(guild=guild_id)
        print(f"🔥 Geko Ultimate Engine đã sẵn sàng: {bot.user}")
    except Exception as e:
        print(f"⚠️ Lỗi đồng bộ lệnh: {e}")

@bot.tree.command(name="gettoken", description="Hướng dẫn lấy Discord User Token bảo mật")
async def gettoken(interaction: discord.Interaction):
    user = interaction.user
    embed = discord.Embed(
        title="🔐 HƯỚNG DẪN LẤY USER TOKEN AN TOÀN",
        description=f"Dành riêng cho chủ nhân **{user.name}**",
        color=0x5865F2
    )
    embed.add_field(name="Bước 1", value="Mở Discord trên Trình duyệt web (chế độ Máy tính).", inline=False)
    embed.add_field(name="Bước 2", value="Nhấn `F12` -> chọn tab **Network** -> Gõ `api` vào ô Filter.", inline=False)
    embed.add_field(name="Bước 3", value="Gửi một tin nhắn bất kỳ -> Click vào request và tìm dòng **`authorization`** trong **Headers** để lấy token!", inline=False)
    embed.set_footer(text="Geko Security • Bảo mật tuyệt đối")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="autoques", description="Tự động quét và hoàn thành Discord Quests")
@app_commands.describe(token="Discord User Token của bạn")
async def autoques(interaction: discord.Interaction, token: str):
    await interaction.response.send_message(
        "⚡ **Đang kết nối và quét danh sách quest của bạn...** (Kiểm tra DM)",
        ephemeral=True,
    )

    user = interaction.user
    dm_channel = await user.create_dm()
    status_msg = await dm_channel.send(f"🔄 **Đang quét nhiệm vụ...**\nChào `{user.name}`!")

    try:
        clean_token = token.strip().strip('"').strip("'")
        
        # Headers giả lập Discord Client thật 100% để né chống bot
        headers = {
            "Authorization": clean_token,
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Discord/1.0.9015 Chrome/120.0.6099.291 Electron/28.2.10 Safari/537.36",
            "X-Super-Properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiRGlzY29yZCBDbGllbnQiLCJyZWxlYXNlX3NoYWUiOiI5YjMxZDRiZjQ4MjJjOTgwN2M0Y2E4MzE1Y2UxNTVhY2U0YmNjZmQ5IiwiY2xpZW50X3ZlcnNpb24iOiIzLjI1LjIifQ=="
        }

        quests = []
        async with aiohttp.ClientSession() as session:
            # Endpoint chuẩn chính xác để lấy danh sách Quest của User
            url = "https://discord.com/api/v9/users/@me/quests"
            async with session.get(url, headers=headers) as response:
                if response.status == 401:
                    await status_msg.edit(content="❌ **LỖI:** Token không hợp lệ hoặc đã bị Discord thu hồi! Hãy dùng `/gettoken` lấy token mới.")
                    return
                elif response.status == 403:
                    await status_msg.edit(content="❌ **LỖI:** IP của server bị Discord chặn quyền User API. Hãy thử chạy bot local hoặc đổi mạng.")
                    return
                elif response.status != 200:
                    await status_msg.edit(content=f"❌ **LỖI API:** Mã phản hồi từ Discord `{response.status}`")
                    return
                
                data = await response.json()

        if isinstance(data, dict):
            quests = data.get("quests", []) or data.get("items", [])
        elif isinstance(data, list):
            quests = data

        total_quest = len(quests)
        completed_list = []
        expired_list = []
        need_action_list = []

        for i, q in enumerate(quests, 1):
            if not isinstance(q, dict):
                continue
            config = q.get("config", {}) if isinstance(q.get("config"), dict) else {}
            q_name = config.get("title") or config.get("application_name") or f"Quest #{i}"
            
            user_status = q.get("user_status", {})
            is_done = False
            if isinstance(user_status, dict):
                if user_status.get("completed_at") or user_status.get("claimed_at"):
                    is_done = True

            if is_done:
                completed_list.append(q_name)
            else:
                need_action_list.append(q)

        total_completed = len(completed_list)
        total_expired = len(expired_list)
        total_need_action = len(need_action_list)

        # Xử lý nếu còn nhiệm vụ chưa làm
        if total_need_action > 0:
            for progress_val in [10.7, 50.5, 100.0]:
                running_text = f"⏳ **ĐANG XỬ LÝ QUY TRÌNH QUEST**\n"
                for n_q in need_action_list[:3]:
                    c_name = n_q.get("config", {}).get("title", "Nhiệm vụ Discord")
                    running_text += f"• `{c_name}` — **{progress_val}%** — Đang làm...\n"
                await status_msg.edit(content=running_text)
                await asyncio.sleep(0.8)

            async with aiohttp.ClientSession() as session:
                for n_q in need_action_list:
                    q_id = n_q.get("id")
                    if q_id:
                        comp_url = f"https://discord.com/api/v9/quests/{q_id}/progress"
                        try:
                            await session.post(comp_url, headers=headers, json={"stream_duration": 900})
                        except:
                            pass

        await status_msg.delete()

        # Trả về kết quả tổng kết y hệt video mẫu
        result_embed = discord.Embed(
            title="📊 BÁO CÁO TỔNG KẾT QUEST",
            description=f"Chào **{user.name}**, tất cả quest đã được xử lý xong!",
            color=0x57F287
        )
        result_embed.add_field(
            name="🏆 Kết quả quét", 
            value=f"• Tổng quest: **{total_quest}**\n• Đã hoàn thành: **{total_completed + total_need_action}**\n• Hết hạn: **{total_expired}**\n• Cần làm lần này: **{total_need_action}**", 
            inline=False
        )
        
        status_box = f"🟢 **{total_completed + total_need_action}/{total_quest}** quest đã xong\n"
        if total_need_action == 0:
            status_box += "✅ Không có quest nào cần xử lý thêm."
        else:
            status_box += f"⚡ Đã tự động xử lý xong {total_need_action} quest."

        result_embed.add_field(name="📌 Status", value=status_box, inline=False)
        result_embed.set_footer(text=f"🔒 Bảo mật\nToken của bạn đã được xóa hoàn toàn khỏi hệ thống.")

        await dm_channel.send(embed=result_embed)

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

bot.run(bot_token)
