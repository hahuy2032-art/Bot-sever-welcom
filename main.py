import asyncio
import os
import random
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

ADMIN_USERNAME = "huy09153"
ADMIN_TITLE = "👑 TỔNG THỐNG / TRÙM TỔNG SERVER"

# Lưu trữ level tạm thời
user_levels = {}

# Danh sách link/từ khóa cấm để kích hoạt tính năng kick
BAD_KEYWORDS = [
    "http://",
    "https://",
    "discord.gg/",
    "t.me/",
    "sex",
    "nsfw",
    "hack",
    "free nitro",
]


@bot.event
async def on_ready():
  try:
    synced = await bot.tree.sync()
    print(f"Đã đồng bộ {len(synced)} lệnh hệ thống.")
  except Exception as e:
    print(f"Lỗi sync: {e}")
  print(f"Bot {bot.user.name} đã sẵn sàng thống trị server của Sếp ĐHuy!")


# --- TÍNH NĂNG 1: TỰ ĐỘNG BẮT LINK ĐỘC / KICK & GỬI THÔNG BÁO ---
@bot.event
async def on_message(message):
  if message.author.bot:
    return

  # Bỏ qua kiểm tra cho Admin (sếp Huy)
  if message.author.name != ADMIN_USERNAME:
    content_lower = message.content.lower()
    is_bad = any(keyword in content_lower for keyword in BAD_KEYWORDS)

    if is_bad:
      try:
        await message.delete()
        await message.author.kick(reason="Gửi link độc hại / nội dung bậy bạ")

        # Gửi thông báo kick cực gắt lên khung chat
        await message.channel.send(
            f"⚡ **Đã kick thằng ngu `{message.author.name}` vì dám gửi link bậy"
            " vào lãnh địa! Cút!**"
        )
        return
      except Exception as e:
        print(f"Lỗi khi kick: {e}")

  # --- TÍNH NĂNG 2: HỆ THỐNG EXP & LEVEL (MAX 1000 CHO SẾP) ---
  user_id = message.author.id
  if user_id not in user_levels:
    user_levels[user_id] = {"exp": 0, "level": 1}

  user_levels[user_id]["exp"] += random.randint(10, 25)
  current_exp = user_levels[user_id]["exp"]
  current_level = user_levels[user_id]["level"]

  required_exp = current_level * 100
  if current_exp >= required_exp and current_level < 1000:
    user_levels[user_id]["level"] += 1
    new_lvl = user_levels[user_id]["level"]

    if message.author.name == ADMIN_USERNAME or new_lvl >= 1000:
      await message.channel.send(
          f"👑 **{message.author.mention} đã đạt cấp độ tối cao {new_lvl}/1000!"
          f" Sở hữu đặc quyền [{ADMIN_TITLE}] của Tổng Server!**"
      )
    else:
      await message.channel.send(
          f"🚀 **{message.author.mention} đã tăng lên cấp độ {new_lvl}! Cố gắng"
          " cày lên 1000 để nhận quyền lực tối cao nhé!**"
      )

  await bot.process_commands(message)


# --- TÍNH NĂNG 3: CHÀO MỪNG THÀNH VIÊN MỚI (KÈM BANNER/ẢNH ĐỘNG) ---
@bot.event
async def on_member_join(member):
  for channel in member.guild.text_channels:
    try:
      embed = discord.Embed(
          title="🔥 THÀNH VIÊN MỚI GIA NHẬP LÃNH ĐỊA 🔥",
          description=(
              f"Hé lu thành viên {member.mention} đã đến với server của bố"
              " ĐHuy!\n\n"
              "⚡ **Hãy đọc kỹ luật và nhận role trước khi quậy nhé!**"
          ),
          color=discord.Color.from_rgb(180, 0, 0),
      )
      # Chèn hình ảnh động/banner vào thông báo cho xịn sò giống server lớn
      embed.set_image(
          url="https://media1.giphy.com/media/VChsIl9WnreDJdIOyA/giphy.gif"
      )
      embed.set_footer(text="✨ Uchiha Itachi & ĐHuy Tổng Server ✨")

      await channel.send(embed=embed)
      break
    except Exception as e:
      print(f"Lỗi gửi welcome: {e}")
      continue


# --- LỆNH CHECK LEVEL CÁ NHÂN ---
@bot.tree.command(
    name="level", description="Kiểm tra cấp độ và đặc quyền Tổng Server của bạn"
)
async def check_level(interaction: discord.Interaction):
  user_id = interaction.user.id
  data = user_levels.get(user_id, {"exp": 0, "level": 1})
  lvl = data["level"]
  exp = data["exp"]

  if interaction.user.name == ADMIN_USERNAME:
    lvl = 1000
    title = ADMIN_TITLE
  else:
    title = (
        "Thành viên tập sự"
        if lvl < 500
        else "Đại tướng cấp cao Tổng Server"
    )

  embed = discord.Embed(
      title=f"📊 THÔNG TIN CẤP ĐỘ CỦA {interaction.user.name.upper()}",
      color=discord.Color.gold(),
  )
  embed.add_field(name="✨ Cấp độ hiện tại:", value=f"**{lvl} / 1000**", inline=True)
  embed.add_field(name="⚡ Tổng điểm EXP:", value=f"**{exp} XP**", inline=True)
  embed.add_field(name="🛡️ Đặc quyền danh hiệu:", value=f"**{title}**", inline=False)
  embed.set_footer(text="Hệ thống quản lý quyền lực tối cao - ĐHuy Bot")

  await interaction.response.send_message(embed=embed, ephemeral=True)


TOKEN_ENV = os.getenv("DISCORD_TOKEN")
if TOKEN_ENV:
  bot.run(TOKEN_ENV)
else:
  print("❌ Thiếu DISCORD_TOKEN!")
