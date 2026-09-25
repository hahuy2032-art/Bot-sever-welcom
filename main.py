import os
import logging
import discord
from discord.ext import commands


# =========================================================
# CONFIG
# =========================================================

TOKEN = os.getenv("DISCORD_TOKEN")
TICKET_CHANNEL_ID = os.getenv("TICKET_CHANNEL_ID")
STAFF_ROLE_ID = os.getenv("STAFF_ROLE_ID", "")

if not TOKEN:
    raise RuntimeError("❌ Thiếu DISCORD_TOKEN")

if not TICKET_CHANNEL_ID:
    raise RuntimeError("❌ Thiếu TICKET_CHANNEL_ID")


try:
    TICKET_CHANNEL_ID = int(TICKET_CHANNEL_ID)
except ValueError:
    raise RuntimeError("❌ TICKET_CHANNEL_ID phải là số")


try:
    STAFF_ROLE_ID = int(STAFF_ROLE_ID) if STAFF_ROLE_ID else None
except ValueError:
    STAFF_ROLE_ID = None


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

log = logging.getLogger("ticket")


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
        # Persistent menu: restart bot vẫn dùng được
        self.add_view(TicketMenu())
        self.add_view(CloseTicket())

        await self.tree.sync()

        log.info("✅ Slash commands synced")


bot = TicketBot()


# =========================================================
# TICKET TYPES
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

    if not STAFF_ROLE_ID:
        return None

    return guild.get_role(STAFF_ROLE_ID)


# =========================================================
# FIND USER TICKET
# =========================================================

def find_user_ticket(guild, user_id):

    for channel in guild.text_channels:

        if not channel.topic:
            continue

        if channel.topic.startswith(
            f"ticket-owner:{user_id}"
        ):
            return channel

    return None


# =========================================================
# CREATE TICKET
# =========================================================

async def create_ticket(
    interaction: discord.Interaction,
    ticket_type: str
):

    guild = interaction.guild
    user = interaction.user

    if not guild:

        await interaction.response.send_message(
            "❌ Chỉ dùng được trong server.",
            ephemeral=True
        )
        return

    # -----------------------------------------------------
    # CHECK OLD TICKET
    # -----------------------------------------------------

    old_ticket = find_user_ticket(
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

    # -----------------------------------------------------
    # PERMISSION
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # FIND CATEGORY
    # -----------------------------------------------------

    category = None

    # Nếu channel panel nằm trong category,
    # ticket cũng tự nằm cùng category.
    panel_channel = guild.get_channel(
        TICKET_CHANNEL_ID
    )

    if isinstance(
        panel_channel,
        discord.CategoryChannel
    ):
        category = panel_channel

    elif isinstance(
        panel_channel,
        discord.TextChannel
    ):
        category = panel_channel.category

    # -----------------------------------------------------
    # NAME
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # CREATE CHANNEL
    # -----------------------------------------------------

    try:

        ticket_channel = (
            await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=(
                    f"ticket-owner:{user.id}"
                    f"|type:{ticket_type}"
                ),
                reason="Ticket System"
            )
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
            "Create ticket error: %s",
            e
        )

        await interaction.response.send_message(
            "❌ Không thể tạo ticket.",
            ephemeral=True
        )

        return

    # -----------------------------------------------------
    # EMBED
    # -----------------------------------------------------

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
            "📎 Có thể gửi ảnh/video/bằng chứng nếu cần.\n\n"
            "⏳ Đội ngũ hỗ trợ sẽ phản hồi "
            "khi có thể.\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔒 Ticket này là riêng tư."
        ),
        color=discord.Color.blurple()
    )

    embed.set_footer(
        text="Server Support • Ticket System"
    )

    # -----------------------------------------------------
    # SEND
    # -----------------------------------------------------

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
            f"✅ Ticket đã được tạo!\n"
            f"👉 {ticket_channel.mention}"
        ),
        ephemeral=True
    )

    log.info(
        "Ticket created | %s | %s",
        user,
        ticket_type
    )


# =========================================================
# SELECT MENU
# =========================================================

class TicketSelect(discord.ui.Select):

    def __init__(self):

        options = [

            discord.SelectOption(
                label="Tố cáo người vi phạm",
                description=(
                    "Báo cáo thành viên vi phạm "
                    "nội quy server."
                ),
                emoji="🚨",
                value="report"
            ),

            discord.SelectOption(
                label="Tuyển dụng người phát triển server",
                description=(
                    "Ứng tuyển Developer / phát triển server."
                ),
                emoji="🛠️",
                value="developer"
            ),

            discord.SelectOption(
                label="Góp ý server",
                description=(
                    "Gửi góp ý hoặc ý tưởng cho server."
                ),
                emoji="💡",
                value="feedback"
            )

        ]

        super().__init__(
            placeholder=(
                "📩 Chọn một chủ đề để mở ticket..."
            ),
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_select"
        )

    async def callback(self, interaction):

        await create_ticket(
            interaction,
            self.values[0]
        )


# =========================================================
# PERSISTENT MENU
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
# CLOSE BUTTON
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
        custom_id="ticket_close"
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
            return

        if not channel.topic.startswith(
            "ticket-owner:"
        ):
            await interaction.response.send_message(
                "❌ Đây không phải ticket.",
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

            if (
                interaction.user.guild_permissions
                .manage_channels
            ):
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
# PANEL EMBED
# =========================================================

def make_panel():

    embed = discord.Embed(
        title="🎫  HỖ TRỢ SERVER",
        description=(
            "Chào mừng bạn đến với trung tâm hỗ trợ! 👋\n\n"
            "Chọn **một chủ đề** bên dưới để mở "
            "ticket riêng cho bạn.\n"
            "Đội ngũ hỗ trợ sẽ phản hồi trong thời gian "
            "sớm nhất.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🚨 **TỐ CÁO NGƯỜI VI PHẠM**\n"
            "Báo cáo thành viên vi phạm nội quy.\n\n"
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
# AUTO PANEL
# =========================================================

async def ensure_panel():

    channel = bot.get_channel(
        TICKET_CHANNEL_ID
    )

    if not channel:

        log.error(
            "❌ Không tìm thấy TICKET_CHANNEL_ID"
        )

        return

    if not isinstance(
        channel,
        discord.TextChannel
    ):

        log.error(
            "❌ TICKET_CHANNEL_ID không phải text channel"
        )

        return

    # Tìm panel cũ của bot
    try:

        async for message in channel.history(
            limit=100
        ):

            if (
                message.author.id == bot.user.id
                and message.components
            ):

                try:

                    await message.edit(
                        embed=make_panel(),
                        view=TicketMenu()
                    )

                    log.info(
                        "✅ Đã cập nhật panel ticket."
                    )

                    return

                except Exception:
                    pass

    except Exception:

        log.exception(
            "❌ Không thể kiểm tra panel cũ."
        )

    # Không có panel -> tạo mới
    try:

        await channel.send(
            embed=make_panel(),
            view=TicketMenu()
        )

        log.info(
            "✅ Đã tạo panel ticket mới."
        )

    except Exception:

        log.exception(
            "❌ Không thể gửi panel ticket."
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

    # Tự động dựng panel
    await ensure_panel()


# =========================================================
# RUN
# =========================================================

async def main():

    await bot.start(
        TOKEN
    )


if __name__ == "__main__":

    import asyncio

    try:
        asyncio.run(
            main()
        )

    except KeyboardInterrupt:
        pass
