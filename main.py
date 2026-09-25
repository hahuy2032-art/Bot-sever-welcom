import discord
from discord.ext import commands

# Khởi tạo cấu hình bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ID của kênh công khai muốn bot bắn thông báo (sếp thay ID kênh #thông-báo-nhiệm-dis vào đây)
TARGET_CHANNEL_ID = 123456789012345678 

@bot.event
async def on_ready():
    print(f"Bot {bot.user.name} đã sẵn sàng càn quét Quest!")

# Lệnh mẫu để test việc gửi thông báo Quest thủ công hoặc tích hợp webhook/API
@bot.command(name="quest_notify")
async def quest_notify(ctx, *, quest_name: str):
    channel = bot.get_channel(TARGET_CHANNEL_ID)
    if channel:
        # Tạo khung thông báo (Embed) đẹp mắt y hệt mong muốn của sếp
        embed = discord.Embed(
            title="🎁 CÓ DISCORD QUEST MỚI!",
            description=f"Nhiệm vụ: **{quest_name}** đã sẵn sàng!",
            color=0x00FF00
        )
        embed.add_field(name="Trạng thái", value="Đã tự động quét, anh em vào nhận quà nhé!", inline=False)
        
        # Gửi thẳng vào kênh công khai
        await channel.send(embed=embed)
        await ctx.send("Đã bắn thông báo quest ra kênh công khai thành công!")
    else:
        await ctx.send("Không tìm thấy kênh thông báo, kiểm tra lại ID kênh đi sếp ơi!")

# Chạy bot bằng Token của sếp
# bot.run("YOUR_BOT_TOKEN")
