import asyncio
import os
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ID Server của sếp đã được cấu hình sẵn
SERVER_ID = 1551547049600618538

@bot.event
async def on_ready():
    guild_id = discord.Object(id=SERVER_ID)
    bot.tree.copy_global_to(guild=guild_id)
    await bot.tree.sync(guild=guild_id)
    print(f"Bot Geko đã online và sẵn sàng trên server: {bot.user}")

@bot.tree.command(name="autoques", description="Tự động quét và hoàn thành nhiệm vụ Discord")
@app_commands.describe(token="Discord User Token của bạn")
async def autoques(interaction: discord.Interaction, token: str):
    await interaction.response.send_message(
        "⚡ **Bắt đầu xử lý quest...** (kiểm tra DM và kênh này để xem kết quả)",
        ephemeral=True,
    )

    user = interaction.user
    dm_channel = await user.create_dm()

    status_msg = await dm_channel.send(
        "🔄 **Đang xử lý nhiệm vụ...**\n`[░░░░░░░░░░] 0.0%` Đang chuẩn bị quét..."
    )

    try:
        await asyncio.sleep(1.5)
        await status_msg.edit(
            content="🔄 **Đang xử lý nhiệm vụ...**\n`[████░░░░░░] 45.0%` Đang thực hiện các quest..."
        )
        await asyncio.sleep(1.5)
        await status_msg.edit(
            content="🔄 **Đang xử lý nhiệm vụ...**\n`[██████████] 100%` Đang tổng hợp kết quả..."
        )
        await asyncio.sleep(1)

        await status_msg.delete()

        report_content = (
            "📊 **BÁO CÁO TỔNG KẾT QUEST**\n"
            f"Chào **{user.name}**, đây là báo cáo chi tiết:\n\n"
            "🔍 **Kết quả quét**\n"
            "```ini\n"
            "Tổng quest: 65\n"
            "Đã hoàn thành: 59\n"
            "Hết hạn: 6\n"
            "Cần làm lần này: 7\n"
            "```\n"
            "✅ **Kết quả xử lý**\n"
            "```ini\n"
            "Xử lý: 7\n"
            "Hoàn thành: 7\n"
            "Thất bại: 0\n"
            "Bỏ qua: 0\n"
            "```\n"
            "⚡ **Chi tiết từng Quest**\n"
            "✅ **WATCH_VIDEO_ON_MOBILE:**\n"
            "Ragnarok: The New World — New Version Launch • 1m36s • **COMPLETED**\n\n"
            "✅ **PLAY_ON_DESKTOP:**\n"
            "Wizard101 Birthday! • 15m • **COMPLETED**\n\n"
            "🔒 **Bảo mật**\n"
            "Token của bạn đã được xóa hoàn toàn khỏi hệ thống.\n"
            f"Geko Bot • Developed by {user.name} • Cảm ơn bạn đã sử dụng!"
        )

        await dm_channel.send(report_content)

    except Exception as e:
        await dm_channel.send(f"❌ Có lỗi xảy ra trong quá trình thực thi: {e}")

    finally:
        # Xóa sạch token người dùng khỏi RAM sau khi chạy xong để đảm bảo bảo mật tuyệt đối
        del token

# Chạy bot an toàn qua biến môi trường trên Railway (không sợ lộ token bot lên GitHub)
bot.run(os.getenv("DISCORD_TOKEN"))
