import asyncio
import os
import sys
import aiohttp
import discord
from discord.ext import commands

# Lấy Token của Bot chính từ Railway
BOT_TOKEN = os.getenv("DISCORD_TOKEN")

if not BOT_TOKEN or not BOT_TOKEN.strip():
    print("❌ LỖI: Chưa cấu hình DISCORD_TOKEN trên Railway!")
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"🤖 Bot đã đăng nhập thành công và sẵn sàng: {bot.user}")

@bot.command(name="autoquest")
async def autoquest(ctx, *, token: str = None):
    # Tự động xóa tin nhắn chứa token của sếp ngay lập tức để bảo mật tuyệt đối
    try:
        await ctx.message.delete()
    except:
        pass

    if not token:
        await ctx.send(f"❌ {ctx.author.mention} Vui lòng nhập đúng cú pháp: `!autoquest <token_cua_ban>`")
        return

    clean_token = token.strip().strip('"').strip("'")
    
    headers = {
        "Authorization": clean_token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Discord/1.0.9015 Chrome/120.0.6099.291 Electron/28.2.10 Safari/537.36",
        "X-Super-Properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiRGlzY29yZCBDbGllbnQiLCJyZWxlYXNlX3NoYWUiOiI5YjMxZDRiZjQ4MjJjOTgwN2M0Y2E4MzE1Y2UxNTVhY2U0YmNjZmQ5IiwiY2xpZW50X3ZlcnNpb24iOiIzLjI1LjIifQ=="
    }

    status_msg = await ctx.send(f"⏳ **Đang kết nối và quét danh sách quest cho {ctx.author.mention}...**")

    try:
        async with aiohttp.ClientSession() as session:
            # 1. Gọi API lấy danh sách quest từ tài khoản Discord của sếp
            async with session.get("https://discord.com/api/v9/users/@me/quests", headers=headers, timeout=10) as resp:
                if resp.status != 200:
                    await status_msg.edit(content=f"❌ **LỖI:** Token không hợp lệ hoặc đã bị Discord thu hồi!")
                    return
                data = await resp.json()

        quests = data.get("quests", []) if isinstance(data, dict) else data
        if not isinstance(quests, list):
            quests = []

        total_quest = len(quests)
        completed = 0
        need_action = []

        for q in quests:
            ustatus = q.get("user_status", {})
            if isinstance(ustatus, dict) and (ustatus.get("completed_at") or ustatus.get("claimed_at")):
                completed += 1
            else:
                need_action.append(q)

        await status_msg.edit(content=f"📋 Tìm thấy **{total_quest}** quest. Đã xong: **{completed}** | Cần chạy: **{len(need_action)}**. Đang xử lý tự động...")

        # 2. Tiến hành giả lập stream để cày quest
        processed = 0
        if len(need_action) > 0:
            async with aiohttp.ClientSession() as session:
                for q in need_action:
                    qid = q.get("id")
                    if qid:
                        try:
                            async with session.post(
                                f"https://discord.com/api/v9/quests/{qid}/progress",
                                headers=headers,
                                json={"stream_duration": 900},
                                timeout=5
                            ) as p_resp:
                                if p_resp.status in [200, 204]:
                                    processed += 1
                        except:
                            pass
                        await asyncio.sleep(0.5)

        # 3. Gửi báo cáo tổng kết qua Tin nhắn riêng (DM) cho an toàn
        embed = discord.Embed(
            title="📊 BÁO CÁO HOÀN THÀNH QUEST",
            description=f"Đã xử lý xong cho **{ctx.author.name}**!",
            color=0x57F287
        )
        embed.add_field(name="Tổng số Quest", value=str(total_quest), inline=True)
        embed.add_field(name="Đã hoàn thành", value=str(completed + processed), inline=True)
        embed.set_footer(text="AutoQuest Single Engine")

        try:
            dm = await ctx.author.create_dm()
            await dm.send(embed=embed)
            await status_msg.edit(content=f"✅ **Đã hoàn tất!** Tổng cộng xong `{completed + processed}/{total_quest}` quest. Đã gửi bảng báo cáo chi tiết vào Tin nhắn riêng (DM) của bạn.")
        except:
            await status_msg.edit(content=f"✅ **Đã hoàn tất `{completed + processed}/{total_quest}` quest!**")

    except Exception as e:
        await status_msg.edit(content=f"❌ Lỗi hệ thống: `{str(e)}`")

bot.run(BOT_TOKEN)
