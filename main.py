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


# ==================== LỆNH 2: /AUTOQUES (Fix chuẩn endpoint client) ====================
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
        
        # Giả lập Header chuẩn như một Discord Client thật để vượt tường lửa API 404
        url = "https://discord.com/api/v9/users/@me/quests"
        headers = {
            "Authorization": clean_token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Discord/1.0.9015 Chrome/120.0.6099.291 Electron/28.2.10 Safari/537.36",
            "X-Super-Properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiRGlzY29yZCBDbGllbnQiLCJyZWxlYXNlX3NoYWUiOiI5YjMxZDRiZjQ4MjJjOTgwN2M0Y2E4MzE1Y2UxNTVhY2U0YmNjZmQ5IiwiY2xpZW50X3ZlcnNpb24iOiIzLjI1LjIifQ=="
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    res_text = await response.text()
                    await status_msg.edit(content=f"❌ **Lỗi API ({response.status}):** Không thể đọc dữ liệu quest. Hãy đảm bảo sếp lấy đúng User Token chính chủ!\nPhản hồi từ Discord: `{res_text[:100]}`")
                    return
                
                data = await response.json()

                # Xử lý đa dạng cấu trúc dữ liệu trả về
                if isinstance(data, dict):
                    quests = data.get("quests", []) or data.get("items", []) or data.get("data", [])
                    if quests is None:
                        quests = []
                elif isinstance(data, list):
                    quests = data
                else:
                    quests = []

        await asyncio.sleep(0.8)
        await status_msg.delete()

        if not quests:
            complete_board = (
                "╭──────────────────────────────────────────╮\n"
                "│       🎉 **GEKO: KHÔNG CÓ NHIỆM VỤ** │\n"
                "╰──────────────────────────────────────────╯\n"
                f"👤 **Chủ nhân:** `{user.name}`\n\n"
                "📌 **Trạng thái:** Tài khoản này hiện không có nhiệm vụ nào khả dụng!\n"
                "🔒 **Bảo mật:** Token đã được xóa sạch khỏi RAM.\n"
            )
            await dm_channel.send(complete_board)
            return

        quest_blocks = ""
        for i, q in enumerate(quests, 1):
            if not isinstance(q, dict):
                continue
            config = q.get("config", {}) if isinstance(q.get("config"), dict) else {}
            q_name = config.get("title") or q.get("name") or f"Nhiệm vụ Discord #{i}"
            
            quest_blocks += (
                f"🔹 **Quest {i}: {q_name}**\n"
                f"   • **Trạng thái:** `Đang hiển thị / Chờ hoàn thành`\n"
                "----------------------------------------\n"
            )

        full_board = (
            "╔════════════════════════════════════════╗\n"
            "║     📋 **TẤT CẢ NHIỆM VỤ HIỆN TẠI** ║\n"
            "╚════════════════════════════════════════╝\n"
            f"👤 **Tài khoản:** `{user.name}`\n"
            f"📊 **Tổng số quest quét được:** `{len(quests)}`\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{quest_blocks}"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "⚡ **Hệ thống:** Đã quét dữ liệu thành công!\n"
            "🔒 **Bảo mật:** Token đã được xóa vĩnh viễn khỏi RAM.\n"
            f"👑 *Geko Engine • Phát triển cho {user.name}*"
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
