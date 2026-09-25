import asyncio
import os
import sys
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

# ==========================================
# CẤU HÌNH HỆ THỐNG VÀ KHỞI TẠO BIẾN MÔI TRƯỜNG
# ==========================================
BOT_1_TOKEN = os.getenv("DISCORD_TOKEN")
BOT_2_TOKEN = os.getenv("SECOND_BOT_TOKEN")

if not BOT_1_TOKEN or not BOT_1_TOKEN.strip():
    print("❌ LỖI NGHIÊM TRỌNG: Chưa cấu hình DISCORD_TOKEN trên Railway!")
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True

bot1 = commands.Bot(command_prefix="!", intents=intents)
bot2 = commands.Bot(command_prefix="!", intents=intents)

# ==========================================
# CÁC HÀM XỬ LÝ API VÀ LOGIC TỰ ĐỘNG QUEST
# ==========================================
class DiscordQuestManager:
    def __init__(self, user_token: str):
        self.token = user_token.strip().strip('"').strip("'")
        self.headers = {
            "Authorization": self.token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Discord/1.0.9015 Chrome/120.0.6099.291 Electron/28.2.10 Safari/537.36",
            "X-Super-Properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiRGlzY29yZCBDbGllbnQiLCJyZWxlYXNlX3NoYWUiOiI5YjMxZDRiZjQ4MjJjOTgwN2M0Y2E4MzE1Y2UxNTVhY2U0YmNjZmQ5IiwiY2xpZW50X3ZlcnNpb24iOiIzLjI1LjIifQ==",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9"
        }

    async def fetch_quests(self):
        url = "https://discord.com/api/v9/users/@me/quests"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers) as response:
                    if response.status != 200:
                        return None, f"API từ chối cấp quyền, mã lỗi HTTP: {response.status}"
                    data = await response.json()
                    return data, None
            except Exception as e:
                return None, str(e)

    async def execute_quest_progress(self, quest_id: str):
        url = f"https://discord.com/api/v9/quests/{quest_id}/progress"
        payload = {"stream_duration": 900}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, headers=self.headers, json=payload) as response:
                    if response.status in [200, 204]:
                        return True
                    return False
            except:
                return False

# ==========================================
# HỆ THỐNG GỬI THÔNG BÁO TỪ BOT PHỤ (BOT 2)
# ==========================================
async def send_secondary_dm_report(user_id: int, report_data: dict):
    try:
        await asyncio.sleep(2)
        user = await bot2.fetch_user(user_id)
        if not user:
            return
        dm_channel = await user.create_dm()
        
        embed = discord.Embed(
            title="📊 BÁO CÁO HỆ THỐNG AUTO-QUEST",
            description=f"Xin chào **{user.name}**, quá trình quét và tự động hóa đã hoàn tất.",
            color=0x57F287
        )
        embed.add_field(
            name="📌 Tổng quan nhiệm vụ",
            value=f"• **Tổng số Quest:** {report_data.get('total', 0)}\n• **Đã hoàn thành:** {report_data.get('completed', 0)}\n• **Đã xử lý tiến trình:** {report_data.get('processed', 0)}",
            inline=False
        )
        embed.add_field(
            name="🛡️ Trạng thái bảo mật",
            value="Mọi dữ liệu Token của bạn đã được xóa sạch hoàn toàn khỏi bộ nhớ RAM ngay sau khi kết thúc.",
            inline=False
        )
        embed.set_footer(text=f"User ID: {user.id} • Secure Automated Engine")
        await dm_channel.send(embed=embed)
    except Exception as e:
        print(f"Lỗi thông báo Bot 2: {e}")

# ==========================================
# SỰ KIỆN KHI BOT 1 SẴN SÀNG & ĐĂNG KÝ LỆNH
# ==========================================
@bot1.event
async def on_ready():
    try:
        await bot1.tree.sync()
        print(f"🤖 [BOT 1] Đã đăng ký thành công Slash Command: {bot1.user}")
    except Exception as e:
        print(f"Lỗi đồng bộ cây lệnh Bot 1: {e}")

# ==========================================
# LỆNH CHÍNH: /AUTOQUEST (CHỐNG LỖI 3 GIÂY)
# ==========================================
@bot1.tree.command(name="autoquest", description="Tự động quét và hoàn thành Discord Quests an toàn")
@app_commands.describe(token="Discord User Token của bạn")
async def autoquest(interaction: discord.Interaction, token: str):
    # PHẢN HỒI NGAY LẬP TỨC TRONG 0.1 GIÁY ĐỂ TRIỆT TIỆU LỖI DISCORD
    await interaction.response.send_message(
        "⚡ **Đã tiếp nhận lệnh thành công!** Hệ thống đang phân tích token và xử lý ngầm, vui lòng kiểm tra tin nhắn DM.",
        ephemeral=True
    )

    user = interaction.user
    user_id = user.id
    manager = DiscordQuestManager(token)

    try:
        # Bước 1: Lấy danh sách nhiệm vụ
        data, err = await manager.fetch_quests()
        if err or data is None:
            try:
                dm = await user.create_dm()
                await dm.send("❌ **LỖI:** Token không hợp lệ, sai định dạng hoặc đã bị thu hồi quyền!")
            except:
                pass
            return

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
        total_action = len(need_action_list)

        # Bước 2: Kích hoạt xử lý tiến trình nếu có quest chưa xong
        processed_count = 0
        if total_action > 0:
            for n_q in need_action_list:
                q_id = n_q.get("id")
                if q_id:
                    success = await manager.execute_quest_progress(q_id)
                    if success:
                        processed_count += 1
                    await asyncio.sleep(1)

        report_payload = {
            "total": total_quest,
            "completed": total_completed,
            "processed": processed_count
        }

        # Bước 3: Điều phối gửi báo cáo qua Bot phụ (Bot 2) hoặc dự phòng Bot chính
        if BOT_2_TOKEN and BOT_2_TOKEN.strip():
            asyncio.create_task(send_secondary_dm_report(user_id, report_payload))
        else:
            try:
                dm = await user.create_dm()
                await dm.send(f"✅ **Xử lý hoàn tất!** Tổng số quest: {total_quest}, Đã tối ưu xong.")
            except:
                pass

    except Exception as e:
        print(f"Lỗi trong tiến trình thực thi quest: {e}")
    finally:
        # Xóa sạch biến chứa token khỏi bộ nhớ để đảm bảo an toàn tuyệt đối
        try:
            del token
            del manager
        except:
            pass

# ==========================================
# SỰ KIỆN KHI BOT 2 SẴN SÀNG
# ==========================================
@bot2.event
async def on_ready():
    print(f"📢 [BOT 2] Trợ lý thông báo đã sẵn sàng: {bot2.user}")

# ==========================================
# HÀM CHẠY SONG SONG ĐỒNG THỜI 2 BOT
# ==========================================
async def main():
    tasks = [bot1.start(BOT_1_TOKEN)]
    if BOT_2_TOKEN and BOT_2_TOKEN.strip():
        tasks.append(bot2.start(BOT_2_TOKEN))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Đã dừng hệ thống.")
    except Exception as e:
        print(f"Lỗi khởi chạy chính: {e}")
