import os
import logging
import discord
from discord.ext import commands

# =========================================================
# CONFIG
# =========================================================

TOKEN = os.getenv("DISCORD_TOKEN")

# Channel ticket panel của m
TICKET_CHANNEL_ID = 1552922576584577034

# Nếu có role Supporter thì điền ID vào đây.
# Không có thì để 0.
STAFF_ROLE_ID = 0

if not TOKEN:
    raise RuntimeError("❌ Thiếu DISCORD_TOKEN trên Railway!")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

log = logging.getLogger("ticket-bot")


# =========================================================
# INTENTS
# =========================================================

intents = discord.Intents.default()
intents.guilds = True
intents.members = True


# =========================================================
# BOT
# =========================================================

class TicketBot(commands.Bot):

    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents
        )

    async def setup_hook(self):
        # Menu vẫn hoạt động sau khi Railway restart
        self.add_view(TicketMenu())
        self.add_view(CloseTicket())

        await self.tree.sync()

        log.info("✅ Slash commands synced")


bot = TicketBot()


# =========================================================
# LOẠI TICKET
# =========================================================

TICKET_TYPES = {

    "report": {
        "emoji": "🚨",
        "name": "Tố cáo người vi phạm",
        "prefix": "bao-cao",
        "description": (
            "Báo cáo thành viên vi phạm nội quy "
            "của server."
        )
    },

    "developer": {
        "emoji": "🛠️",
        "name": "Tuyển dụng người phát triển server",
        "prefix": "developer",
        "description": (
            "Ứng tuyển Developer hoặc trao đổi "
            "về việc phát triển server."
        )
    },

    "feedback": {
        "emoji": "💡",
        "name": "Góp ý server",
        "prefix": "gop-y",
        "description": (
            "Gửi góp ý, ý tưởng hoặc phản hồi "
            "cho server."
        )
    }
}


# =========================================================
# STAFF ROLE
# =========================================================

def get_staff_role(guild):

    if STAFF_ROLE_ID == 0:
        return None

    return guild.get_role(STAFF_ROLE_ID)


# =========================================================
# TÌM TICKET ĐANG MỞ
# =========================================================

def find_existing_ticket(guild, user_id):

    for channel in guild.text_channels:

        if not channel.topic:
            continue

        if channel.topic.startswith(
            f"ticket-owner:{user_id}"
        ):
            return channel

    return None


# =========================================================
# TẠO TICKET
# =========================================================

async def create_ticket(interaction, ticket_type):

    guild = interaction.guild
    user = interaction.user

    if not guild:
        await interaction.response.send_message(
            "❌ Chỉ sử dụng trong server.",
            ephemeral=True
        )
        return

    # Kiểm tra ticket cũ
    old_ticket = find_existing_ticket(
        guild,
        user.id
    )

    if old_ticket:
        await interaction.response.send_message(
            f"❌ Bạn đang có ticket: {old_ticket.mention}",
            ephemeral=True
        )
        return

    info = TICKET_TYPES[ticket_type]

    # =====================================================
    # PERMISSION
    # =====================================================

    overwrites = {

        guild.default_role:
            discord.PermissionOverwrite(
                view_channel=False
            ),

        user:
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True
            ),

        guild.me:
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
                manage_messages=True
            )
    }

    staff_role = get_staff_role(guild)

    if staff_role:

        overwrites[staff_role] = (
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True
            )
        )

    # =====================================================
    # CATEGORY
    # =====================================================

    panel_channel = guild.get_channel(
        TICKET_CHANNEL_ID
    )

    category = None

    if isinstance(
        panel_channel,
        discord.TextChannel
    ):
        category = panel_channel.category

    # =====================================================
    # CHANNEL NAME
    # =====================================================

    username = user.display_name.lower()

    username = "".join(
        c for c in username
        if c.isalnum() or c in "-_"
    )

    if not username:
        username = str(user.id)

    channel_name = (
        f"{info['prefix']}-{username}"
    )[:100]

    # =====================================================
    # CREATE CHANNEL
    # =====================================================

    try:

        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=(
                f"ticket-owner:{user.id}"
                f"|type:{ticket_type}"
            ),
            reason="Ticket System"
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            (
                "❌ Bot không có quyền tạo channel.\n"
                "Cấp cho bot quyền **Manage Channels**."
            ),
            ephemeral=True
        )
        return

    except Exception as e:

        log.exception(
            "Lỗi tạo ticket: %s",
            e
        )

        await interaction.response.send_message(
            "❌ Không thể tạo ticket.",
            ephemeral=True
        )
        return

    # =====================================================
    # EMBED TICKET
    # =====================================================

    embed = discord.Embed(
        title=(
            f"{info['emoji']} "
            f"{info['name']}"
        ),
        description=(
            f"Xin chào {user.mention}! 👋\n\n"
            f"{info['description']}\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "📌 **Hãy trình bày vấn đề rõ ràng.**\n"
            "📎 Có thể gửi ảnh/video/bằng chứng nếu cần.\n"
            "⏳ Đội ngũ hỗ trợ sẽ phản hồi sớm nhất có thể.\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔒 Ticket này là riêng tư."
        ),
        color=discord.Color.blurple()
    )

    embed.set_footer(
        text="Support Center • Ticket System"
    )

    mention = user.mention

    if staff_role:
        mention += f" {staff_role.mention}"

    await ticket_channel.send(
        content=mention,
        embed=embed,
        view=CloseTicket()
    )

    await interaction.response.send_message(
        (
            "✅ **Đã tạo ticket!**\n"
            f"👉 {ticket_channel.mention}"
        ),
        ephemeral=True
    )

    log.info(
        "Ticket created: %s | %s",
        user,
        ticket_type
    )


# =========================================================
# DROPDOWN
# =========================================================

class TicketSelect(discord.ui.Select):

    def __init__(self):

        options = [

            discord.SelectOption(
                label="Tố cáo người vi phạm",
                description="Báo cáo thành viên vi phạm nội quy.",
                emoji="🚨",
                value="report"
            ),

            discord.SelectOption(
                label="Tuyển dụng người phát triển server",
                description="Ứng tuyển Developer / phát triển server.",
                emoji="🛠️",
                value="developer"
            ),

            discord.SelectOption(
                label="Góp ý server",
                description="Gửi góp ý hoặc ý tưởng cho server.",
                emoji="💡",
                value="feedback"
            )
        ]

        super().__init__(
            placeholder="📩 Chọn một chủ đề để mở ticket...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_select_menu"
        )

    async def callback(self, interaction):

        await create_ticket(
            interaction,
            self.values[0]
        )


# =========================================================
# MENU
# =========================================================

class TicketMenu(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

        self.add_item(
            TicketSelect()
        )


# =========================================================
# NÚT ĐÓNG TICKET
# =========================================================

class CloseTicket(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="Đóng ticket",
        emoji="🔒",
        style=discord.ButtonStyle.danger,
        custom_id="close_ticket"
    )
    async def close(
        self,
        interaction,
        button
    ):

        channel = interaction.channel

        if not isinstance(
            channel,
            discord.TextChannel
        ):
            return

        if not channel.topic:
            await interaction.response.send_message(
                "❌ Đây không phải ticket.",
                ephemeral=True
            )
            return

        if not channel.topic.startswith(
            "ticket-owner:"
        ):
            await interaction.response.send_message(
                "❌ Đây không phải ticket của bot.",
                ephemeral=True
            )
            return

        try:

            owner_id = int(
                channel.topic
                .split("|")[0]
                .replace(
                    "ticket-owner:",
                    ""
                )
            )

        except Exception:

            owner_id = 0

        is_owner = (
            interaction.user.id == owner_id
        )

        is_staff = False

        if isinstance(
            interaction.user,
            discord.Member
        ):

            if interaction.user.guild_permissions.manage_channels:
                is_staff = True

            staff_role = get_staff_role(
                interaction.guild
            )

            if (
                staff_role
                and staff_role in interaction.user.roles
            ):
                is_staff = True

        if not is_owner and not is_staff:

            await interaction.response.send_message(
                "❌ Bạn không có quyền đóng ticket.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "🔒 Đang đóng ticket...",
            ephemeral=True
        )

        await channel.delete(
            reason="Ticket closed"
        )


# =========================================================
# PANEL
# =========================================================

def panel_embed():

    embed = discord.Embed(
        title="🎫  HỖ TRỢ SERVER",
        description=(
            "Chào mừng bạn đến với **Trung tâm hỗ trợ**! 👋\n\n"
            "Chọn **một chủ đề** bên dưới để mở ticket "
            "riêng cho bạn.\n"
            "Đội ngũ hỗ trợ sẽ phản hồi trong thời gian "
            "sớm nhất.\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "🚨 **TỐ CÁO NGƯỜI VI PHẠM**\n"
            "Báo cáo thành viên vi phạm nội quy server.\n\n"

            "🛠️ **TUYỂN DỤNG NGƯỜI PHÁT TRIỂN SERVER**\n"
            "Ứng tuyển hoặc trao đổi về phát triển server.\n\n"

            "💡 **GÓP Ý SERVER**\n"
            "Đóng góp ý tưởng và phản hồi cho server.\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "⚠️ **LƯU Ý**\n"
            "• Không spam ticket.\n"
            "• Không tạo ticket đùa.\n"
            "• Mô tả vấn đề càng rõ càng tốt.\n"
            "• Tôn trọng đội ngũ hỗ trợ."
        ),
        color=discord.Color.from_rgb(
            88, 101, 242
        )
    )

    embed.set_footer(
        text="💙 Support Center • Ticket System"
    )

    return embed


# =========================================================
# TỰ ĐẶT PANEL VÀO CHANNEL
# =========================================================

async def ensure_panel():

    channel = bot.get_channel(
        TICKET_CHANNEL_ID
    )

    if not channel:

        log.error(
            "❌ Không tìm thấy channel %s",
            TICKET_CHANNEL_ID
        )

        return

    if not isinstance(
        channel,
        discord.TextChannel
    ):

        log.error(
            "❌ ID này không phải Text Channel."
        )

        return

    # Tìm panel cũ của bot
    try:

        async for message in channel.history(
            limit=100
        ):

            if (
                message.author.id == bot.user.id
                and len(message.components) > 0
            ):

                try:

                    await message.edit(
                        embed=panel_embed(),
                        view=TicketMenu()
                    )

                    log.info(
                        "✅ Panel ticket đã có sẵn."
                    )

                    return

                except Exception:
                    pass

    except Exception:

        log.exception(
            "❌ Không thể đọc lịch sử channel."
        )

    # Không có panel -> tạo
    try:

        await channel.send(
            embed=panel_embed(),
            view=TicketMenu()
        )

        log.info(
            "✅ Đã tạo panel ticket."
        )

    except discord.Forbidden:

        log.error(
            "❌ Bot không có quyền gửi message/embed."
        )

    except Exception:

        log.exception(
            "❌ Lỗi tạo panel."
        )


# =========================================================
# READY
# =========================================================

@bot.event
async def on_ready():

    log.info(
        "🤖 Bot online: %s",
        bot.user
    )

    log.info(
        "🌐 Servers: %s",
        len(bot.guilds)
    )

    await ensure_panel()


# =========================================================
# RUN
# =========================================================

async def main():

    await bot.start(TOKEN)


if __name__ == "__main__":

    import asyncio

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        pass
