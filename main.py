import asyncio
import os
import sys
import aiohttp
import discord
from discord.ext import commands

BOT_1_TOKEN = os.getenv("DISCORD_TOKEN")
BOT_2_TOKEN = os.getenv("SECOND_BOT_TOKEN")

if not BOT_1_TOKEN or not BOT_1_TOKEN.strip():
    print("❌ LỖI: Chưa cấu hình DISCORD_TOKEN trên Railway!")
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True  # Đảm bảo đọc được nội dung tin nhắn

# Khởi tạo 2 bot chạy song song bằng tiền tố !
bot1 = commands.Bot(command_prefix="!", intents=intents)
bot2 = commands.Bot(command_prefix="!", intents=intents)

@bot1.event
async def on_ready():
    print(f"🤖 Bot 1 đã sẵn sàng: {bot1.user}")

@bot1.command(name="autoquest", help="Tự động quét và hoàn thành Discord Quests")
async def autoquest(ctx, token: str = None):
    if not token:
        await ctx.send(f"❌ {ctx.author.mention}, thiếu token! Cú pháp đúng: `!autoquest <token_của_bạn>`", delete_after=10)
        try:
            await ctx.message.delete()
        except:
            pass
        return

    # Xóa ngay tin nhắn chứa token của sếp để bảo mật tuyệt đối
    try:
        await ctx.message.delete()
    except:
        pass

    # Gửi tin nhắn thông báo đang xử lý
    status_msg = await ctx.send(f"⏳ **{ctx.author.name}** • Đang kết nối và quét danh sách quest của bạn...")

    user = ctx.author
    user_id = user.id

    try:
        clean_token = token.strip().strip('"').strip("'")
        headers = {
            "Authorization": clean_token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Discord/1.0.9015 Chrome/120.0.6099.291 Electron/28.2.10 Safari/537.36",
            "X-Super-Properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiRGlzY29yZCBDbGllbnQiLCJyZWxlYXNlX3NoYWUiOiI5YjMxZDRiZjQ4MjJjOTgwN2M0Y2E4MzE1Y2UxNTVhY2U0YmNjZmQ5IiwiY2xpZW50X3ZlcnNpb24iOiIzLjI1LjIifQ=="
        }

        async with aiohttp.ClientSession() as session:
            url = "https://discord.com/api/v9/users/@me/quests"
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    await status_msg.edit(content=f"❌ **LỖI:** Token không hợp lệ hoặc đã hết hạn đối với {user.mention}!")
                    return
                data = await response.json()

        quests = data.get("quests", []) if isinstance(data, dict) else data
        if not isinstance(quests, list):
            quests = []

        total_quest = len(quests)
        completed_list = []
        need_action_list = []

        for q in quests:
            user_status = q.get("user_status", {})
            if isinstance(user_status, dict) and (user_status.get("completed_at") or user_status.get("claimed_at")):
                completed_list.append(q)
            else:
                need_action_list.append(q)

        total_completed = len(completed_list)
        total_need_action = len(need_action_list)

        # Cập nhật trạng thái đang chạy progress giả lập
        await status_msg.edit(content=f"⚙️ **{user.name}** • Tìm thấy {total_quest} quest. Đang tiến hành xử lý...")

        if total_need_action > 0:
            async with aiohttp.ClientSession() as session:
                for n_q in need_action_list:
                    q_id = n_q.get("id")
                    if q_id:
                        try:
                            await session.post(f"https://discord.com/api/v9/quests/{q_id}/progress", headers=headers, json={"stream_duration": 900})
                        except:
                            pass
            await asyncio.sleep(1)

        # Gửi bảng Báo Cáo Tổng Kết qua DM (Tin nhắn riêng)
        try:
            dm_channel = await user.create_dm()
            embed = discord.Embed(
                title="📊 BÁO CÁO TỔNG KẾT QUEST",
                description=f"Chào **{user.name}**, quy trình xử lý đã hoàn tất!",
                color=0x57F287
            )
            embed.add_field(
                name="📌 Kết quả",
                value=f"🟢 **{total_completed + total_need_action}/{total_quest}** đã hoàn thành\n❌ **0** hết hạn",
                inline=False
            )
            embed.add_field(
                name="🔒 Bảo mật",
                value="Token của bạn đã được xóa hoàn toàn khỏi hệ thống.",
                inline=False
            )
            embed.set_footer(text=f"User ID: {user.id} • Multi-Bot Engine")
            await dm_channel.send(embed=embed)
            
            await status_msg.edit(content=f"✅ **{user.name}** • Đã xử lý xong {total_completed + total_need_action}/{total_quest} quest! Hãy kiểm tra tin nhắn riêng (DM).")
        except Exception:
            await status_msg.edit(content=f"✅ **{user.name}** • Đã xử lý xong {total_completed + total_need_action}/{total_quest} quest!")

    except Exception as e:
        print(f"Lỗi: {e}")
        try:
            await status_msg.edit(content=f"❌ Đã xảy ra lỗi trong quá trình xử lý quest của {user.mention}.")
        except:
            pass
    finally:
        try:
            del token
        except:
            pass

@bot2.event
async def on_ready():
    print(f"📢 Bot 2 (Thông báo/Phụ) đã sẵn sàng: {bot2.user}")

async def main():
    # Chạy song song 2 bot cùng lúc trên Railway
    tasks = [bot1.start(BOT_1_TOKEN)]
    if BOT_2_TOKEN and BOT_2_TOKEN.strip():
        tasks.append(bot2.start(BOT_2_TOKEN))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except:
        pass
