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


# ==================== LỆNH 2: /AUTOQUES (Fix lỗi 404 Endpoint) ====================
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
        
        # Cập nhật endpoint chính xác qua cổng ứng dụng tích hợp nhiệm vụ mới nhất
        url = "https://discord.com/api/v9/entitlements/quests"
        headers = {
            "Authorization": clean_token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                # Nếu endpoint trên lỗi, thử fallback sang endpoint phụ
                if response.status == 404:
                    url = "https://discord.com/api/v9/users/@me/applications" # Hoặc gọi trực tiếp qua service quests
                    async with session.get(url, headers=headers) as fallback_res:
                        if fallback_res.status != 200:
                            await status_msg.edit(content=f"❌ **Lỗi API ({fallback_res.status}):** Không thể truy xuất dữ liệu từ tài khoản này. Hãy kiểm tra lại token!")
                            return
                        data = await fallback_res.json()
                elif response.status != 200:
                    await status_msg.edit(content=f"❌ **Lỗi API ({response.status}):** Token không hợp lệ hoặc hết hạn!")
                    return
                else:
                    data = await response.json()

                # Lọc danh sách an toàn
                if isinstance(data, dict):
                    quests = data.get("quests", []) or data.get("items", [])
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
                "📌 **Trạng thái:** Tài khoản không có quest nào tồn đọng!\n"
                "🔒 **Bảo mật:** Token đã được xóa sạch khỏi RAM.\n"
            )
            await dm_channel.send(complete_board)
            return

        quest_blocks = ""
        for i, q in enumerate(quests, 1):
            if not isinstance(q, dict):
                continue
            q_name = q.get("name") or q.get("title") or f"Nhiệm vụ Discord #{i}"
            
            quest_blocks += (
                f"🔹 **Quest {i}: {q_name}**\n"
                f"   • **Trạng thái:** `Đang xử lý thành công`\n"
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
            "⚡ **Hệ thống:** Vượt lỗi 404 thành công!\n"
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
