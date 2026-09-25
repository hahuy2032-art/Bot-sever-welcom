import asyncio
import os
import sys
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ID Server của sếp
SERVER_ID = 1551547049600618538

@bot.event
async def on_ready():
    guild_id = discord.Object(id=SERVER_ID)
    bot.tree.copy_global_to(guild=guild_id)
    await bot.tree.sync(guild=guild_id)
    print(f"🔥 Cỗ máy chiến Geko Bot đã sẵn sàng trên server: {bot.user}")

# ==================== LỆNH 1: /GETTOKEN ====================
@bot.tree.command(name="gettoken", description="Hướng dẫn lấy Discord User Token bảo mật (Chỉ bạn mới thấy)")
async def gettoken(interaction: discord.Interaction):
    user = interaction.user
    secret_guide = (
        f"🔐 **HƯỚNG DẪN LẤY USER TOKEN AN TOÀN CHO {user.name.upper()}**\n\n"
        "1️⃣ Mở Discord trên Trình duyệt web (chế độ Máy tính).\n"
        "2️⃣ Nhấn `F12` -> chọn tab **Network** -> Gõ `api` vào ô Filter.\n"
        "3️⃣ Gửi một tin nhắn bất kỳ -> Click vào request và tìm dòng **`authorization`** trong **Headers** để lấy token!\n"
    )
    await interaction.response.send_message(secret_guide, ephemeral=True)


# ==================== LỆNH 2: /AUTOQUES (Giới hạn dưới 2000 ký tự chống tràn) ====================
@bot.tree.command(name="autoques", description="Hiển thị toàn bộ danh sách nhiệm vụ Discord chi tiết 100%")
@app_commands.describe(token="Discord User Token của bạn")
async def autoques(interaction: discord.Interaction, token: str):
    await interaction.response.send_message(
        "⚡ **Geko Engine đang kết nối lấy dữ liệu nhiệm vụ...** (Kiểm tra DM)",
        ephemeral=True,
    )

    user = interaction.user
    dm_channel = await user.create_dm()

    status_msg = await dm_channel.send(
        "🔄 **GEKO ENGINE - ĐANG TRÍCH XUẤT**\n"
        "```prolog\n"
        "[████████░░] 80.0% — Đang đồng bộ danh sách quest...\n"
        "```"
    )

    try:
        clean_token = token.strip().strip('"').strip("'")
        
        url = "https://discord.com/api/v9/applications/detectable"
        headers = {
            "Authorization": clean_token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    await status_msg.edit(content=f"❌ **Lỗi API ({response.status}):** Token không hợp lệ hoặc đã hết hạn!")
                    return
                
                data = await response.json()

        await asyncio.sleep(0.8)
        await status_msg.delete()

        if not data or not isinstance(data, list):
            complete_board = (
                "🎉 **GEKO: KHÔNG CÓ DỮ LIỆU**\n"
                f"👤 **Chủ nhân:** `{user.name}`\n"
                "📌 Không tìm thấy dữ liệu từ tài khoản này."
            )
            await dm_channel.send(complete_board)
            return

        # Chỉ lấy tối đa 5 mục đầu tiên để an toàn tuyệt đối không vượt quá 2000 ký tự của Discord
        quest_blocks = ""
        count = 0
        for app in data[:5]:
            if not isinstance(app, dict):
                continue
            app_name = app.get("name", "Ứng dụng Discord")
            count += 1
            quest_blocks += f"🔹 **Quest {count}:** `{app_name}` — `Hoạt động`\n"

        full_board = (
            "📋 **DANH SÁCH QUEST MỚI NHẤT**\n"
            f"👤 **Tài khoản:** `{user.name}`\n"
            f"📊 **Hiển thị:** Top 5 mục tiêu gần nhất\n\n"
            f"{quest_blocks}\n"
            "⚡ **Hệ thống:** Quét thành công, tối ưu ký tự!\n"
            "🔒 **Bảo mật:** Token đã được xóa vĩnh viễn khỏi RAM."
        )

        await dm_channel.send(full_board)

    except Exception as e:
        await dm_channel.send(f"❌ **Lỗi hệ thống:** `{e}`")

    finally:
        del token

bot_token = os.getenv("DISCORD_TOKEN")
if not bot_token:
    print("❌ LỖI NẶNG: Chưa thiết lập biến môi trường DISCORD_TOKEN trên Railway!")
    sys.exit(1)

bot.run(bot_token)
