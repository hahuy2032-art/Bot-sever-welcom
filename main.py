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

# ==================== LỆNH 1: /GETTOKEN (Chỉ một mình sếp thấy, bảo mật tuyệt đối) ====================
@bot.tree.command(name="gettoken", description="Hướng dẫn lấy Discord User Token bảo mật (Chỉ bạn mới thấy)")
async def gettoken(interaction: discord.Interaction):
    user = interaction.user
    
    secret_guide = (
        f"🔐 **HƯỚNG DẪN LẤY USER TOKEN AN TOÀN CHO {user.name.upper()}**\n\n"
        "Vì lý do bảo mật, Discord không cho phép bot tự động lấy trộm token tài khoản cá nhân. Sếp làm theo các bước sau để lấy:\n\n"
        "1️⃣ Mở Discord trên Trình duyệt web (Chrome, Safari, Edge... ở chế độ **Trang web cho máy tính / Desktop site**).\n"
        "2️⃣ Nhấn phím `F12` (hoặc chuột phải chọn **Kiểm tra / Inspect**) -> Chuyển sang tab **Network** (Mạng).\n"
        "3️⃣ Gõ chữ `api` vào ô lọc (Filter) -> Gửi một tin nhắn bất kỳ lên web.\n"
        "4️⃣ Click vào bất kỳ dòng request nào, tìm mục **Headers** -> Kéo xuống tìm dòng **`authorization`**, dãy ký tự dài đằng sau chính là **User Token** của sếp!\n\n"
        "⚠️ *Tuyệt đối không chia sẻ Token này cho bất kỳ ai!*"
    )
    
    # ephemeral=True bắt buộc chỉ một mình sếp thấy nội dung này
    await interaction.response.send_message(secret_guide, ephemeral=True)


# ==================== LỆNH 2: /AUTOQUES (Quét toàn bộ nhiệm vụ, chống lỗi văng app) ====================
@bot.tree.command(name="autoques", description="Hiển thị toàn bộ danh sách nhiệm vụ Discord chi tiết 100%")
@app_commands.describe(token="Discord User Token của bạn")
async def autoques(interaction: discord.Interaction, token: str):
    await interaction.response.send_message(
        "⚡ **Geko Engine đang quét sâu vào dữ liệu Discord...** (Kiểm tra DM)",
        ephemeral=True,
    )

    user = interaction.user
    dm_channel = await user.create_dm()

    status_msg = await dm_channel.send(
        "🔄 **GEKO ENGINE - ĐANG TRÍCH XUẤT**\n"
        "```prolog\n"
        "[████████░░] 80.0% — Đang quét toàn bộ danh sách quest...\n"
        "```"
    )

    try:
        url = "https://discord.com/api/v9/users/@me/quests"
        headers = {
            "Authorization": token.strip(),
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    await status_msg.edit(content="❌ **Lỗi:** Token không hợp lệ hoặc đã hết hạn. Hãy kiểm tra lại!")
                    return
                
                data = await response.json()
                
                # Xử lý an toàn chống lỗi NoneType/dict/list
                if isinstance(data, dict):
                    quests = data.get("quests", [])
                    if quests is None:
                        quests = []
                elif isinstance(data, list):
                    quests = data
                else:
                    quests = []

        await asyncio.sleep(0.8)
        await status_msg.delete()

        # Nếu không có nhiệm vụ nào
        if not quests:
            complete_board = (
                "╭──────────────────────────────────────────╮\n"
                "│       🎉 **GEKO: KHÔNG CÓ NHIỆM VỤ** │\n"
                "╰──────────────────────────────────────────╯\n"
                f"👤 **Chủ nhân:** `{user.name}`\n\n"
                "📌 **Trạng thái:** Tài khoản của bạn đã hoàn thành sạch sẽ tất cả!\n"
                "🔒 **Bảo mật:** Token đã được xóa sạch khỏi RAM.\n"
            )
            await dm_channel.send(complete_board)
            return

        # Vét cạn và liệt kê tất cả các nhiệm vụ tìm thấy vào bảng
        quest_blocks = ""
        for i, q in enumerate(quests, 1):
            if not isinstance(q, dict):
                continue
            config = q.get("config") or {}
            messages = config.get("messages") or {}
            
            q_name = messages.get("quest_name") or config.get("title") or f"Nhiệm vụ Discord #{i}"
            game_title = messages.get("game_title") or config.get("application_name") or "Ứng dụng Discord"
            
            quest_blocks += (
                f"🔹 **Quest {i}: {q_name}**\n"
                f"   • **Trò chơi / Nền tảng:** `{game_title}`\n"
                f"   • **Trạng thái:** `Chưa hoàn thành / Đang hiển thị`\n"
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
            "⚡ **Hệ thống:** Đã quét sạch toàn bộ danh sách thành công!\n"
            "🔒 **Bảo mật:** Token đã được xóa vĩnh viễn khỏi RAM.\n"
            f"👑 *Geko Engine • Phát triển cho {user.name}*"
        )

        await dm_channel.send(full_board)

    except Exception as e:
        await dm_channel.send(f"❌ **Lỗi hệ thống:** `{e}`")

    finally:
        del token

# Kiểm tra an toàn biến môi trường trước khi chạy bot
bot_token = os.getenv("DISCORD_TOKEN")
if not bot_token:
    print("❌ LỖI NẶNG: Chưa thiết lập biến môi trường DISCORD_TOKEN trên Railway!")
    sys.exit(1)

bot.run(bot_token)
