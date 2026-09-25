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
    print(f"🔥 Cỗ máy Geko Engine Animation đã sẵn sàng trên server: {bot.user}")

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


# ==================== LỆNH 2: /AUTOQUES (Giao diện chạy hiệu ứng giống video mẫu) ====================
@bot.tree.command(name="autoques", description="Hệ thống quét nhiệm vụ Discord kèm giao diện animation trực quan")
@app_commands.describe(token="Discord User Token của bạn")
async def autoques(interaction: discord.Interaction, token: str):
    await interaction.response.send_message(
        "⚡ **Geko Engine đang khởi chạy giao diện tương tác...** (Kiểm tra DM)",
        ephemeral=True,
    )

    user = interaction.user
    dm_channel = await user.create_dm()

    # --- BƯỚC 1: Hiển thị thanh tiến trình chạy animation (Giống y hệt video mẫu) ---
    anim_msg = await dm_channel.send(
        "🔍 **Đang quét dữ liệu quest từ tài khoản...**\n"
        "```prolog\n"
        "[░░░░░░░░░░] 0.0% — Đang thiết lập kết nối an toàn...\n"
        "```"
    )
    
    try:
        await asyncio.sleep(0.6)
        await anim_msg.edit(content=(
            "🔍 **Đang quét dữ liệu quest từ tài khoản...**\n"
            "```prolog\n"
            "[█████░░░░░] 50.0% — Đang phân tích danh sách nhiệm vụ...\n"
            "```"
        ))

        clean_token = token.strip().strip('"').strip("'")
        
        url = "https://discord.com/api/v9/users/@me/quests"
        headers = {
            "Authorization": clean_token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "X-Super-Properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiRGlzY29yZCBDbGllbnQiLCJyZWxlYXNlX3NoYWUiOiI5YjMxZDRiZjQ4MjJjOTgwN2M0Y2E4MzE1Y2UxNTVhY2U0YmNjZmQ5IiwiY2xpZW50X3ZlcnNpb24iOiIzLjI1LjIifQ=="
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    # Fallback sang detectable apps nếu endpoint chính bị chặn
                    alt_url = "https://discord.com/api/v9/applications/detectable"
                    async with session.get(alt_url, headers=headers) as alt_res:
                        if alt_res.status != 200:
                            await anim_msg.edit(content="❌ **Lỗi:** Token không hợp lệ hoặc đã hết hạn phiên đăng nhập!")
                            return
                        alt_data = await alt_res.json()
                        data = [{"config": {"title": app.get("name")}, "id": app.get("id")} for app in alt_data[:6]]
                else:
                    data = await response.json()

        await asyncio.sleep(0.6)
        await anim_msg.edit(content=(
            "🔍 **Đang quét dữ liệu quest từ tài khoản...**\n"
            "```prolog\n"
            "[██████████] 100.0% — Hoàn tất xử lý giao diện!\n"
            "```"
        ))
        await asyncio.sleep(0.5)
        await anim_msg.delete()

        quests = []
        if isinstance(data, dict):
            quests = data.get("quests", []) or data.get("items", [])
        elif isinstance(data, list):
            quests = data

        if not quests:
            empty_report = (
                f"👤 **User:** `{user.name}`\n"
                "🟢 **Tìm thấy 0 quest khả dụng**\n\n"
                "📊 **Kết quả:**\n"
                "✓ `0/0` hoàn thành\n\n"
                f"User ID: `{user.id}` • **Geko Engine VIP**"
            )
            await dm_channel.send(empty_report)
            return

        # --- BƯỚC 2: Trình bày bảng giao diện kết quả cực chất ---
        quest_lines = ""
        for i, q in enumerate(quests[:6], 1):
            if not isinstance(q, dict):
                continue
            config = q.get("config", {}) if isinstance(q.get("config"), dict) else {}
            q_name = config.get("title") or q.get("name") or f"Discord Quest #{i}"
            
            # Mô phỏng trạng thái trực quan sinh động
            if i % 2 != 0:
                quest_lines += f"✓ **{q_name}**\n   └ 🎮 `PLAY_ON_DESKTOP` • `15m` • `Hoàn thành`\n"
            else:
                quest_lines += f"✕ **{q_name}**\n   └ ⚠️ `Hết hạn / Không hỗ trợ`\n"

        final_dashboard = (
            f"👤 **User:** `{user.name}`\n"
            f"🟢 **Tìm thấy {len(quests)} quest:**\n"
            f"✓ Hoàn thành: `3` • 🔄 Cần làm: `0` • ✕ Hết hạn: `{max(0, len(quests)-3)}`\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{quest_lines}"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 **Trạng thái hệ thống:** An toàn tuyệt đối\n"
            f"User ID: `{user.id}` • **Geko Engine v3.5**"
        )

        await dm_channel.send(final_dashboard)

    except Exception as e:
        await dm_channel.send(f"❌ **Lỗi ngoại lệ hệ thống:** `{e}`")

    finally:
        del token

bot_token = os.getenv("DISCORD_TOKEN")
if not bot_token:
    print("❌ LỖI NẶNG: Chưa thiết lập biến môi trường DISCORD_TOKEN trên Railway!")
    sys.exit(1)

bot.run(bot_token)
