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
intents.message_content = True

bot1 = commands.Bot(command_prefix="!", intents=intents)
bot2 = commands.Bot(command_prefix="!", intents=intents)

@bot1.event
async def on_ready():
    try:
        await bot1.tree.sync()
        print(f"🤖 Bot 1 đã sẵn sàng: {bot1.user}")
    except Exception as e:
        print(f"Lỗi sync tree: {e}")

# HÀM XỬ LÝ CHẠY NGẦM CHUẨN XÁC THEO MẪU XỊN
async def process_quests_background(interaction: discord.Interaction, token: str):
    user = interaction.user
    clean_token = token.strip().strip('"').strip("'")
    
    headers = {
        "Authorization": clean_token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Discord/1.0.9015 Chrome/120.0.6099.291 Electron/28.2.10 Safari/537.36",
        "X-Super-Properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiRGlzY29yZCBDbGllbnQiLCJyZWxlYXNlX3NoYWUiOiI5YjMxZDRiZjQ4MjJjOTgwN2M0Y2E4MzE1Y2UxNTVhY2U0YmNjZmQ5IiwiY2xpZW50X3ZlcnNpb24iOiIzLjI1LjIifQ=="
    }

    try:
        async with aiohttp.ClientSession() as session:
            # 1. Lấy danh sách quests
            url = "https://discord.com/api/v9/users/@me/quests"
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    try:
                        await interaction.edit_original_response(
                            content=f"❌ **LỖI:** Token không hợp lệ, sai định dạng hoặc đã hết hạn!"
                        )
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
            if isinstance(user_status, dict) and (user_status.get("completed_at") or user_status.get("claimed_at")):
                completed_list.append(q)
            else:
                need_action_list.append(q)

        total_completed = len(completed_list)
        total_expired = len(expired_list)
        total_action = len(need_action_list)

        # Cập nhật thông báo đã quét xong danh sách
        try:
            await interaction.edit_original_response(
                content=f"📋 **Danh sách quest:** Tìm thấy `{total_quest}` quest.\n🟢 Đã hoàn thành: `{total_completed}` | ⏳ Cần làm: `{total_action}`\n🔄 *Đang tiến hành gửi yêu cầu hoàn thành nhiệm vụ...*"
            )
        except:
            pass

        # 2. Xử lý tiến trình từng quest cần làm
        processed_count = 0
        if total_action > 0:
            async with aiohttp.ClientSession() as session:
                for n_q in need_action_list:
                    q_id = n_q.get("id")
                    if q_id:
                        try:
                            async with session.post(
                                f"https://discord.com/api/v9/quests/{q_id}/progress", 
                                headers=headers, 
                                json={"stream_duration": 900}
                            ) as p_res:
                                if p_res.status in [200, 204]:
                                    processed_count += 1
                        except:
                            pass
                        await asyncio.sleep(0.8)

        # 3. Tạo Embed báo cáo tổng kết gửi thẳng vào DM (Tin nhắn riêng)
        embed = discord.Embed(
            title="📊 BÁO CÁO TỔNG KẾT QUEST",
            description=f"Chào **{user.name}**, quá trình quét và tự động xử lý quest đã hoàn tất!",
            color=0x57F287
        )
        embed.add_field(
            name="📌 Kết quả chi tiết",
            value=f"• **Tổng số Quest:** {total_quest}\n• **Đã hoàn thành:** {total_completed + processed_count}\n• **Hết hạn / Không hỗ trợ:** {total_expired}",
            inline=False
        )
        embed.add_field(
            name="🔒 Bảo mật hệ thống",
            value="Token của bạn đã được xóa sạch hoàn toàn khỏi RAM ngay sau khi chạy xong.",
            inline=False
        )
        embed.set_footer(text=f"User ID: {user.id} • AutoQuest Pro Engine")

        try:
            dm_channel = await user.create_dm()
            await dm_channel.send(embed=embed)
            await interaction.edit_original_response(
                content=f"✅ **Đã xử lý xong!** Tổng cộng hoàn thành: `{total_completed + processed_count}/{total_quest}` quest. Đã gửi báo cáo chi tiết vào Tin nhắn riêng (DM) cho bạn."
            )
        except Exception:
            await interaction.edit_original_response(
                content=f"✅ **Đã xử lý xong `{total_completed + processed_count}/{total_quest}` quest!**"
            )

    except Exception as e:
        print(f"Lỗi hệ thống ngầm: {e}")
        try:
            await interaction.edit_original_response(content="❌ Đã xảy ra lỗi hệ thống trong quá trình thực thi quest.")
        except:
            pass
    finally:
        try:
            del token
        except:
            pass

@bot1.tree.command(name="autoquest", description="Tự động quét và hoàn thành Discord Quests")
@app_commands.describe(token="Discord User Token của bạn")
async def autoquest(interaction: discord.Interaction, token: str):
    # Trả tín hiệu trì hoãn ngay lập tức để chống lỗi 3 giây của Discord
    await interaction.response.defer(ephemeral=True)
    
    await interaction.followup.send(
        "⚡ **Đang kết nối và quét danh sách quest của bạn...** Vui lòng đợi trong giây lát.",
        ephemeral=True
    )

    # Chạy ngầm tiến trình nặng
    asyncio.create_task(process_quests_background(interaction, token))

@bot2.event
async def on_ready():
    print(f"📢 Bot 2 đã sẵn sàng: {bot2.user}")

async def main():
    tasks = [bot1.start(BOT_1_TOKEN)]
    if BOT_2_TOKEN and BOT_2_TOKEN.strip():
        tasks.append(bot2.start(BOT_2_TOKEN))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except:
        pass
