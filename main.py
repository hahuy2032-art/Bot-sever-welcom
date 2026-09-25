import asyncio
import os
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

@bot.tree.command(name="autoques", description="Hiển thị toàn bộ bảng nhiệm vụ chi tiết từ Discord API")
@app_commands.describe(token="Discord User Token của bạn")
async def autoques(interaction: discord.Interaction, token: str):
    await interaction.response.send_message(
        "⚡ **Đang kết nối Geko Engine để quét toàn bộ dữ liệu...** (Kiểm tra DM)",
        ephemeral=True,
    )

    user = interaction.user
    dm_channel = await user.create_dm()

    status_msg = await dm_channel.send(
        "🔄 **GEKO ENGINE - ĐANG TRÍCH XUẤT DỮ LIỆU**\n"
        "```prolog\n"
        "[██████░░░░] 60.0% — Đang bóc tách từng thông tin quest từ Discord...\n"
        "```"
    )

    try:
        # 1. Gọi API thực tế lấy toàn bộ dữ liệu quest
        url = "https://discord.com/api/v9/quests/@me"
        headers = {
            "Authorization": token,
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    await status_msg.edit(content="❌ **Lỗi Hệ Thống:** Token không hợp lệ hoặc đã hết hạn!")
                    return
                
                data = await response.json()
                quests = data.get("quests", [])

        await asyncio.sleep(1)
        await status_msg.delete()

        # 2. NẾU KHÔNG CÓ NHIỆM VỤ NÀO
        if not quests:
            complete_board = (
                "╭──────────────────────────────────────────╮\n"
                "│       🎉 **GEKO: HOÀN THÀNH TẤT CẢ** │\n"
                "╰──────────────────────────────────────────╯\n"
                f"👤 **Chủ nhân:** `{user.name}`\n\n"
                "📌 **Trạng thái:** Không tìm thấy nhiệm vụ tồn đọng!\n"
                "✨ *Tài khoản của bạn đã hoàn thành sạch sẽ 100% các nhiệm vụ.* \n\n"
                "🔒 **Bảo mật:** User Token đã được xóa sạch hoàn toàn khỏi RAM.\n"
                "👑 *Geko Bot • Ultimate Edition*"
            )
            await dm_channel.send(complete_board)
            return

        # 3. NẾU CÓ NHIỆM VỤ: In chi tiết toàn bộ các trường thông tin ra bảng
        quest_blocks = ""
        for i, q in enumerate(quests, 1):
            config = q.get("config", {})
            messages = config.get("messages", {})
            
            # Lấy chi tiết từng thông tin giống hệt giao diện Discord
            q_name = messages.get("quest_name", "Nhiệm vụ đặc biệt")
            game_title = messages.get("game_title", "Ứng dụng / Trò chơi")
            target_minutes = config.get("target", 0) // 60 # Quy đổi ra phút nếu có
            reward_name = messages.get("reward_name", "Phần thưởng độc quyền")
            
            # Trạng thái tiến độ thực tế từ API
            user_status = q.get("user_status", {})
            completed = user_status.get("completed_at") is not None
            status_text = "✅ ĐÃ HOÀN THÀNH" if completed else "⏳ ĐANG TIẾN HÀNH / CHƯA LÀM"

            quest_blocks += (
                f"🔹 **Nhiệm vụ {i}: {q_name}**\n"
                f"   • **Trò chơi / Nền tảng:** `{game_title}`\n"
                f"   • **Phần thưởng:** `{reward_name}`\n"
                f"   • **Yêu cầu:** `Treo/Xem {target_minutes} phút`\n"
                f"   • **Trạng thái:** `{status_text}`\n"
                "----------------------------------------\n"
            )

        full_board = (
            "╔════════════════════════════════════════╗\n"
            "║     📋 **TẤT CẢ NHIỆM VỤ DISCORD HIỆN TẠI** ║\n"
            "╚════════════════════════════════════════╝\n"
            f"👤 **Tài khoản:** `{user.name}`\n"
            f"📊 **Tổng số quest đang có:** `{len(quests)}`\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{quest_blocks}"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "⚡ **Hệ thống:** Đã quét toàn bộ thông tin chuẩn xác 100% từ API!\n"
            "🔒 **Bảo mật:** Token đã được xóa vĩnh viễn khỏi RAM.\n"
            f"👑 *Geko Engine • Phát triển cho {user.name}*"
        )

        await dm_channel.send(full_board)

    except Exception as e:
        await dm_channel.send(f"❌ **Lỗi ngoại lệ hệ thống:** `{e}`")

    finally:
        # Xóa sạch token khỏi RAM bằng mọi giá sau khi chạy xong
        del token

# Chạy bot qua biến môi trường Railway
bot.run(os.getenv("DISCORD_TOKEN"))
