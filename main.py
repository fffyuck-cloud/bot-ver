import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
import random
import string
from datetime import datetime
import os
import sys

# ================== CẤU HÌNH ==================
TOKEN = os.environ.get("TOKEN")
VERIFY_CHANNEL_ID = 1548735130057711636  # ID kênh verify
VERIFIED_ROLE_NAME = "VERIFIED"      # Role sau khi verify
UNVERIFIED_ROLE_NAME = "UNVERIFIED"  # Role khi mới vào server

GIF_URL = "https://i.pinimg.com/originals/ca/9f/e9/ca9fe9e1c1aad2d7767cf7dfb9396540.gif"

MAU_CHINH = 0x000000      # ⚫ Đen
MAU_THANH_CONG = 0x000000 # ⚫ Đen
MAU_LOI = 0x000000        # ⚫ Đen

# ================== ĐỌC TOKEN TỪ FILE ==================
def load_token():
    """Đọc token từ file token.txt"""
    if not os.path.exists("token.txt"):
        print("=" * 50)
        print("❌ KHÔNG TÌM THẤY FILE token.txt!")
        print("👉 Tạo file token.txt cùng thư mục với bot.py")
        print("   Bên trong file chỉ dán token bot vào.")
        print("=" * 50)
        sys.exit(1)

    with open("token.txt", "r", encoding="utf-8") as f:
        token = f.read().strip()

    if not token:
        print("❌ File token.txt đang trống! Dán token bot vào trong file.")
        sys.exit(1)

    return token


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


# ================== HÀM TÌM ROLE ==================
def get_verified_role(guild: discord.Guild):
    return discord.utils.get(guild.roles, name=VERIFIED_ROLE_NAME)


def get_unverified_role(guild: discord.Guild):
    return discord.utils.get(guild.roles, name=UNVERIFIED_ROLE_NAME)


# ================== EMBED FULL ĐEN ==================
def create_verify_embed():
    now = datetime.now().strftime("%H:%M • %d/%m/%Y")
    embed = discord.Embed(
        title="╭「 ⚫ HỆ THỐNG XÁC MINH 」╮",
        description=(
            "```\n"
            "      Chào mừng bạn đến với server!\n"
            "      Để mở khóa toàn bộ kênh chat,\n"
            "      bạn cần hoàn tất xác minh.\n"
            "```\n"
        ),
        color=MAU_CHINH
    )
    embed.add_field(
        name="📌 __Hướng dẫn__",
        value=(
            "> 1️⃣ Nhấn nút **✅ Xác Minh** bên dưới\n"
            "> 2️⃣ Nhập đúng mã **captcha** hiện ra\n"
            "> 3️⃣ Hoàn tất! Kênh chat tự động mở 🔓"
        ),
        inline=False
    )
    embed.add_field(
        name="⚠️ __Lưu ý__",
        value=(
            "> • Nhập captcha **không phân biệt** hoa/thường\n"
            "> • Nhập sai? Bấm nút và thử lại nhé!\n"
            "> • Không verify = **không thấy kênh chat**"
        ),
        inline=False
    )
    embed.set_image(url=GIF_URL)
    embed.set_footer(text=f"🛡️ Hệ thống chống bot • {now}")
    return embed


def create_welcome_embed(member: discord.Member):
    embed = discord.Embed(
        title=f"👋 Chào mừng {member.name}!",
        description=(
            f"> Bạn vừa vào server **{member.guild.name}**\n"
            f"> Hãy vào <#{VERIFY_CHANNEL_ID}> để **xác minh** nhé!\n\n"
            f"```\nKhông xác minh bạn sẽ không thấy kênh chat!\n```"
        ),
        color=MAU_CHINH
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_image(url=GIF_URL)
    embed.set_footer(text="🔒 Xác minh để mở khóa server")
    return embed


# ================== SETUP QUYỀN KÊNH TỰ ĐỘNG ==================
async def setup_permissions(guild: discord.Guild, status_msg=None):
    """Chặn UNVERIFIED ở tất cả kênh, chỉ mở kênh verify"""
    unverified = get_unverified_role(guild)
    if not unverified:
        if status_msg:
            await status_msg.edit(content=f"❌ Chưa có role **{UNVERIFIED_ROLE_NAME}**! Restart bot để tự tạo.")
        return

    verify_channel = guild.get_channel(VERIFY_CHANNEL_ID)
    if not verify_channel:
        if status_msg:
            await status_msg.edit(content="❌ Không tìm thấy kênh verify! Kiểm tra lại VERIFY_CHANNEL_ID.")
        return

    blocked, opened = 0, 0
    await status_msg.edit(content="⏳ Đang cấu hình quyền kênh...")

    for channel in guild.channels:
        try:
            if channel.id == VERIFY_CHANNEL_ID:
                await channel.set_permissions(
                    unverified,
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True
                )
                opened += 1
            else:
                await channel.set_permissions(
                    unverified,
                    view_channel=False
                )
                blocked += 1
        except discord.Forbidden:
            pass

    result = (
        f"✅ **Cấu hình hoàn tất!**\n\n"
        f"> 🔓 Mở kênh verify: **{opened}** kênh\n"
        f"> 🔒 Chặn UNVERIFIED: **{blocked}** kênh\n\n"
        f"```\nGiờ role UNVERIFIED chỉ thấy kênh verify thôi!\n```"
    )
    await status_msg.edit(content=result)


# ================== MODAL CAPTCHA ==================
class CaptchaModal(Modal, title="⚫ Xác Minh Thành Viên"):
    def __init__(self, captcha_code):
        super().__init__()
        self.captcha_code = captcha_code
        self.captcha_input = TextInput(
            label=f"Nhập mã: {captcha_code}",
            placeholder="Gõ mã captcha vào đây...",
            required=True,
            max_length=6
        )
        self.add_item(self.captcha_input)

    async def on_submit(self, interaction: discord.Interaction):
        if self.captcha_input.value.strip().upper() == self.captcha_code:
            verified = get_verified_role(interaction.guild)
            unverified = get_unverified_role(interaction.guild)

            if verified is None:
                await interaction.response.send_message(
                    "❌ Không tìm thấy role VERIFIED! Liên hệ Admin.",
                    ephemeral=True
                )
                return

            try:
                await interaction.user.add_roles(verified, reason="Đã xác minh thành công")
                if unverified and unverified in interaction.user.roles:
                    await interaction.user.remove_roles(unverified, reason="Đã xác minh thành công")

                success = discord.Embed(
                    title="✅ XÁC MINH THÀNH CÔNG!",
                    description=(
                        f"> Chào mừng **{interaction.user.name}** đến với server!\n\n"
                        f"```\nToàn bộ kênh chat đã được mở khóa cho bạn!\n```\n"
                        f"> 🎉 Chúc bạn vui vẻ!"
                    ),
                    color=MAU_THANH_CONG
                )
                success.set_thumbnail(url=interaction.user.display_avatar.url)
                success.set_image(url=GIF_URL)
                success.set_footer(text="🔓 Đã mở khóa toàn bộ quyền truy cập")
                await interaction.response.send_message(embed=success, ephemeral=True)
            except discord.Forbidden:
                await interaction.response.send_message(
                    "❌ Bot không đủ quyền gán role! Kéo role bot lên cao hơn.",
                    ephemeral=True
                )
        else:
            fail = discord.Embed(
                title="❌ SAI CAPTCHA!",
                description="> Mã bạn nhập **không đúng**!\n> Bấm nút **✅ Xác Minh** và thử lại nhé.",
                color=MAU_LOI
            )
            await interaction.response.send_message(embed=fail, ephemeral=True)


# ================== NÚT VERIFY ==================
class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Xác Minh Ngay",
        emoji="✅",
        style=discord.ButtonStyle.green,
        custom_id="verify_button"
    )
    async def verify_button(self, interaction: discord.Interaction, button: Button):
        verified = get_verified_role(interaction.guild)
        if verified and verified in interaction.user.roles:
            warn = discord.Embed(
                title="⚠️ BẠN ĐÃ XÁC MINH RỒI!",
                description="> Tài khoản của bạn đã được xác minh trước đó.",
                color=MAU_CHINH
            )
            await interaction.response.send_message(embed=warn, ephemeral=True)
            return

        captcha_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        await interaction.response.send_modal(CaptchaModal(captcha_code))


# ================== KHI THÀNH VIÊN MỚI VÀO ==================
@bot.event
async def on_member_join(member: discord.Member):
    if member.bot:
        return

    guild = member.guild
    unverified = get_unverified_role(guild)

    if unverified:
        try:
            await member.add_roles(unverified, reason="Thành viên mới chưa xác minh")
            print(f"✅ Đã add UNVERIFIED cho: {member.name}")
        except discord.Forbidden:
            print(f"❌ Không đủ quyền add role cho: {member.name}")

    channel = guild.get_channel(VERIFY_CHANNEL_ID)
    if channel:
        try:
            await channel.send(embed=create_welcome_embed(member))
        except discord.Forbidden:
            pass


# ================== SỰ KIỆN BOT KHỞI ĐỘNG ==================
@bot.event
async def on_ready():
    print(f"🤖 Bot đã online: {bot.user}")
    bot.add_view(VerifyView())

    for guild in bot.guilds:
        if not get_verified_role(guild):
            try:
                await guild.create_role(name=VERIFIED_ROLE_NAME, color=0x000000, reason="Tự tạo role verify")
                print(f"✅ Đã tạo role '{VERIFIED_ROLE_NAME}': {guild.name}")
            except discord.Forbidden:
                print(f"❌ Không đủ quyền tạo role: {guild.name}")

        if not get_unverified_role(guild):
            try:
                await guild.create_role(name=UNVERIFIED_ROLE_NAME, color=0x2B2D31, reason="Tự tạo role chưa verify")
                print(f"✅ Đã tạo role '{UNVERIFIED_ROLE_NAME}': {guild.name}")
            except discord.Forbidden:
                print(f"❌ Không đủ quyền tạo role: {guild.name}")

    channel = bot.get_channel(VERIFY_CHANNEL_ID)
    if channel:
        already_sent = False
        async for msg in channel.history(limit=10):
            if msg.author == bot.user:
                already_sent = True
                break
        if not already_sent:
            await channel.send(embed=create_verify_embed(), view=VerifyView())
            print(f"✅ Đã gửi tin nhắn verify vào: {channel.name}")


# ================== LỆNH !SETUP ==================
@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    """Tự động chặn UNVERIFIED ở mọi kênh, chỉ mở kênh verify"""
    msg = await ctx.send("⏳ Đang chuẩn bị cấu hình...")
    await setup_permissions(ctx.guild, status_msg=msg)


# ================== LỆNH !HELP ==================
@bot.command()
async def help(ctx):
    """Hiện danh sách lệnh"""
    if ctx.author.guild_permissions.administrator:
        desc = (
            "╭「 📋 **LỆNH ADMIN** 」╮\n"
            "> 🔧 `!setup` — Tự chặn UNVERIFIED ở mọi kênh (chỉ mở kênh verify)\n"
            "> 📨 `!resend` — Gửi lại tin nhắn verify\n"
            "> 🔍 `!checkrole` — Xem trạng thái 2 role verify\n"
            "> 👤 `!unverify @user` — Gỡ verify của thành viên\n"
            "> ✅ `!verify @user` — Verify hộ thành viên\n\n"
            "╭「 🌐 **LỆNH MỌI NGƯỜI** 」╮\n"
            "> ❓ `!help` — Xem danh sách lệnh này\n"
            "> 🔒 Bấm nút **Xác Minh** trong kênh verify để mở khóa!"
        )
    else:
        desc = (
            "╭「 🌐 **LỆNH** 」╮\n"
            "> ❓ `!help` — Xem danh sách lệnh\n"
            "> 🔒 Vào kênh verify và bấm **✅ Xác Minh** để mở khóa server!"
        )

    embed = discord.Embed(
        title="╭「 🤖 HƯỚNG DẪN SỬ DỤNG BOT 」╮",
        description=desc,
        color=MAU_CHINH
    )
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.set_image(url=GIF_URL)
    embed.set_footer(text=f"Được yêu cầu bởi {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)


# ================== LỆNH ADMIN KHÁC ==================
@bot.command()
@commands.has_permissions(administrator=True)
async def resend(ctx):
    """Gửi lại tin nhắn verify"""
    channel = bot.get_channel(VERIFY_CHANNEL_ID)
    await channel.send(embed=create_verify_embed(), view=VerifyView())
    ok = discord.Embed(
        title="✅ Thành công!",
        description=f"> Đã gửi lại tin nhắn verify vào <#{VERIFY_CHANNEL_ID}>",
        color=MAU_CHINH
    )
    await ctx.send(embed=ok)


@bot.command()
@commands.has_permissions(administrator=True)
async def checkrole(ctx):
    """Kiểm tra 2 role verify"""
    verified = get_verified_role(ctx.guild)
    unverified = get_unverified_role(ctx.guild)

    embed = discord.Embed(
        title="🔍 TRẠNG THÁI ROLE XÁC MINH",
        color=MAU_CHINH
    )
    embed.add_field(
        name=f"✅ Role {VERIFIED_ROLE_NAME}",
        value=f"> Tồn tại: **{'Có' if verified else '❌ Chưa'}**\n> Số người: **{len(verified.members) if verified else 0}**",
        inline=True
    )
    embed.add_field(
        name=f"🔴 Role {UNVERIFIED_ROLE_NAME}",
        value=f"> Tồn tại: **{'Có' if unverified else '❌ Chưa'}**\n> Số người: **{len(unverified.members) if unverified else 0}**",
        inline=True
    )
    embed.set_image(url=GIF_URL)
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(administrator=True)
async def unverify(ctx, member: discord.Member):
    """Gỡ verify của thành viên"""
    verified = get_verified_role(ctx.guild)
    unverified = get_unverified_role(ctx.guild)

    if verified and verified in member.roles:
        await member.remove_roles(verified)
    if unverified:
        await member.add_roles(unverified)

    embed = discord.Embed(
        title="🔴 ĐÃ GỠ VERIFY",
        description=f"> Thành viên: {member.mention}\n> Đã trả role **{UNVERIFIED_ROLE_NAME}** — phải xác minh lại!",
        color=MAU_LOI
    )
    embed.set_image(url=GIF_URL)
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(administrator=True)
async def verify(ctx, member: discord.Member):
    """Verify hộ thành viên"""
    verified = get_verified_role(ctx.guild)
    unverified = get_unverified_role(ctx.guild)

    if verified:
        await member.add_roles(verified)
    if unverified and unverified in member.roles:
        await member.remove_roles(unverified)

    embed = discord.Embed(
        title="✅ ĐÃ VERIFY HỘ",
        description=f"> Thành viên: {member.mention}\n> Người verify: {ctx.author.mention}",
        color=MAU_THANH_CONG
    )
    embed.set_image(url=GIF_URL)
    await ctx.send(embed=embed)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="⛔ KHÔNG ĐỦ QUYỀN!",
            description="> Lệnh này chỉ dành cho **Admin**!",
            color=MAU_LOI
        )
        await ctx.send(embed=embed, delete_after=5)


# ================== CHẠY BOT ==================
if __name__ == "__main__":
    TOKEN = load_token()
    bot.run(TOKEN)
