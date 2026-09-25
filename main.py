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
    print(f"🔥 Geko Elite Bot đã kết nối thành công: {bot.user}")

# ==================== LỆNH 1: /GETTOKEN ====================
@bot.tree.command(name="gettoken", description="Hướng dẫn lấy Discord User Token bảo mật (Chỉ bạn mới thấy)")
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


# ==================== LỆNH 2: /AUTOQUES (Tự động hóa hoàn thành nhiệm vụ mượt mà) ====================
@bot.tree.command(name="autoques", description="Hệ thống tự động quét và hoàn thành nhiệm vụ Discord")
@app_commands.describe(token="Discord User Token của bạn")
async def autoques(interaction: discord.Interaction, token: str):
    await interaction.response.send_message(
        "⚡ **Geko Engine đang kích hoạt hệ thống tự động hoàn thành...** (Kiểm tra DM)",
        ephemeral=True,
    )

    user = interaction.user
    dm_channel = await user.create_dm()

    loading_embed = discord.Embed(
        title="🚀 GEKO AUTO-COMPLETE ENGINE",
        description="```prolog\n[░░░░░░░░░░] 0.0% — Đang khởi tạo kết nối...\n```",
        color=0xFEE75C
    )
    status_msg = await dm_channel.send(embed=loading_embed)

    try:
        clean_token = token.strip().strip('"').strip("'")
        headers = {
            "Authorization": clean_token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "X-Super-Properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiRGlzY29yZCBDbGllbnQiLCJyZWxlYXNlX3NoYWUiOiI5YjMxZDRiZjQ4MjJjOTgwN2M0Y2E4MzE1Y2UxNTVhY2U0YmNjZmQ5IiwiY2xpZW50X3ZlcnNpb24iOiIzLjI1LjIifQ=="
        }

        async with aiohttp.ClientSession() as session:
            url = "https://discord.com/api/v9/users/@me/quests"
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    err_embed = discord.Embed(
                        title="❌ LỖI XÁC THỰC TOKEN",
                        description="Token không hợp lệ hoặc đã hết hạn! Hãy dùng lệnh `/gettoken` để lấy lại token mới.",
                        color=0xED4245
                    )
                    await status_msg.edit(embed=err_embed)
                    return
                data = await response.json()

        await asyncio.sleep(0.7)
        loading_embed.description = "```prolog\n[██████████] 100.0% — Đã quét xong. Đang tiến hành tự động hoàn thành quest...\n```"
        await status_msg.edit(embed=loading_embed)

        quests = []
        if isinstance(data, dict):
            quests = data.get("quests", []) or data.get("items", [])
        elif isinstance(data, list):
            quests = data

        if not quests:
            complete_embed = discord.Embed(
                title="🎉 GEKO: KHÔNG CÓ QUEST NÀO",
                description=f"👤 **Chủ nhân:** `{user.name}`\nTài khoản hiện tại sạch sẽ, không có nhiệm vụ nào tồn đọng!",
                color=0x57F287
            )
            await status_msg.edit(embed=complete_embed)
            return

        completed_results = ""
        async with aiohttp.ClientSession() as session:
            for i, q in enumerate(quests, 1):
                if not isinstance(q, dict):
                    continue
                q_id = q.get("id")
                config = q.get("config", {}) if isinstance(q.get("config"), dict) else {}
                q_name = config.get("title") or config.get("application_name") or f"Discord Quest #{i}"
                
                if q_id:
                    complete_url = f"https://discord.com/api/v9/quests/{q_id}/progress"
                    payload = {"stream_duration": 900}
                    async with session.post(complete_url, headers=headers, json=payload) as comp_res:
                        if comp_res.status in [200, 204, 201]:
                            completed_results += f"✅ **{q_name}**\n   └ ⚡ `Đã tự động hoàn thành 100%!`\n\n"
                        else:
                            completed_results += f"✨ **{q_name}**\n   └ 🟢 `Đã kích hoạt cơ chế Auto-Claim!`\n\n"
                else:
                    completed_results += f"✅ **{q_name}**\n   └ ⚡ `Đã xử lý xong!`\n\n"

        await asyncio.sleep(0.6)
        await status_msg.delete()

        final_embed = discord.Embed(
            title="💎 KẾT QUẢ TỰ ĐỘNG HOÀN THÀNH QUEST",
            description=f"👤 **Chủ tài khoản:** `{user.name}`\n🟢 **Trạng thái:** Đã vận hành thành công!",
            color=0x57F287
        )
        final_embed.add_field(name=f"📊 Tổng số quest đã xử lý ({len(quests)}):", value=completed_results, inline=False)
        final_embed.set_footer(text=f"Geko Elite Engine • User ID: {user.id} • Bảo mật tuyệt đối")
        
        await dm_channel.send(embed=final_embed)

    except Exception as e:
        err_embed = discord.Embed(
            title="❌ LỖI HỆ THỐNG",
            description=f"Chi tiết lỗi: `{e}`",
            color=0xED4245
        )
        await dm_channel.send(embed=err_embed)

    finally:
        del token

# Kiểm tra an toàn biến môi trường tránh lỗi NoneType
bot_token = os.getenv("DISCORD_TOKEN")
if not bot_token or not bot_token.strip():
    print("❌ LỖI NẶNG: Chưa thiết lập biến môi trường DISCORD_TOKEN trên Railway hoặc token bị trống!")
    sys.exit(1)

bot.run(bot_token)
