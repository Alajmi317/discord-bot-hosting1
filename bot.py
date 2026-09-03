#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ================= CONFIGURATION =================
BOT_TOKEN = "MTU0Mjk1MjczMTAzMzk5NzM3Mw.GCm2kq.JjbqI7wmYQ6NKtRMlJ68EOyqiG5mcW9IvDojMM"

# قائمة معرفات الرتب المسموح لها (Roles)
ALLOWED_ROLE_IDS = [
    1528443463312478319,  # الرتبة الأولى
    1528502123266965676,  # الرتبة الثانية
    1528443292990312458,  # الرتبة الثالثة
]

# ================= IMPORTS =================
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio
import ipaddress
from datetime import datetime

# ================= BOT SETUP =================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ================= PERMISSION CHECK (BY ROLE) =================
def has_allowed_role(interaction: discord.Interaction) -> bool:
    """Check if user has any of the allowed roles."""
    if not interaction.guild:
        return False
    
    member = interaction.guild.get_member(interaction.user.id)
    if not member:
        return False
    
    for role_id in ALLOWED_ROLE_IDS:
        role = discord.utils.get(member.roles, id=role_id)
        if role:
            return True
    
    return False

# ================= HELPER FUNCTIONS =================
def is_ip_valid(ip: str) -> bool:
    """Validate IP address format."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

async def get_ip_info(ip: str) -> dict:
    """Fetch public IP information from ip-api.com."""
    url = f"http://ip-api.com/json/{ip}?fields=status,message,country,regionName,city,isp,org,as,timezone,lat,lon"
    
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('status') == 'success':
                        return {'success': True, 'data': data}
                    else:
                        return {'success': False, 'error': data.get('message', 'Unknown error')}
                else:
                    return {'success': False, 'error': f'API returned status code: {response.status}'}
        except asyncio.TimeoutError:
            return {'success': False, 'error': 'Request timed out. Please try again.'}
        except Exception as e:
            return {'success': False, 'error': f'An error occurred: {str(e)}'}

# ================= TOOL 1: IP INFORMATION =================
async def tool_ip_information(interaction: discord.Interaction):
    """Tool: Get public information about an IP address."""
    embed = discord.Embed(
        title="🌐 معلومات الـ IP",
        description="يرجى إدخال عنوان الـ IP الذي تريد البحث عنه:",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="مثال",
        value="`8.8.8.8`\n`192.168.1.1`",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)
    
    def check(m):
        return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id
    
    try:
        msg = await bot.wait_for('message', timeout=60.0, check=check)
        ip = msg.content.strip()
        
        if not is_ip_valid(ip):
            error_embed = discord.Embed(
                title="❌ عنوان IP غير صحيح",
                description="عنوان الـ IP الذي أدخلته غير صحيح. يرجى المحاولة مرة أخرى.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            return
        
        result = await get_ip_info(ip)
        
        if not result['success']:
            error_embed = discord.Embed(
                title="❌ خطأ",
                description=result['error'],
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            return
        
        data = result['data']
        info_embed = discord.Embed(
            title="🌐 معلومات الـ IP",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        fields = [
            ("IP", data.get('query', 'N/A'), True),
            ("الدولة", data.get('country', 'N/A'), True),
            ("المنطقة", data.get('regionName', 'N/A'), True),
            ("المدينة", data.get('city', 'N/A'), True),
            ("مزود الخدمة", data.get('isp', 'N/A'), True),
            ("المنظمة", data.get('org', 'N/A'), True),
            ("ASN", data.get('as', 'N/A'), True),
            ("المنطقة الزمنية", data.get('timezone', 'N/A'), True),
        ]
        
        lat = data.get('lat')
        lon = data.get('lon')
        if lat and lon:
            fields.append(("الموقع (تقريبي)", f"{lat:.4f}, {lon:.4f}", True))
        
        for name, value, inline in fields:
            info_embed.add_field(name=name, value=value, inline=inline)
        
        info_embed.set_footer(text="معلومات عامة فقط - موقع تقريبي")
        
        await interaction.followup.send(embed=info_embed, ephemeral=True)
        
    except asyncio.TimeoutError:
        await interaction.followup.send("⏰ انتهى الوقت! يرجى المحاولة مرة أخرى.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ خطأ: {str(e)}", ephemeral=True)

# ================= USER INFO MODAL (FORM) =================
class UserInfoModal(discord.ui.Modal, title='🔍 معلومات المستخدم'):
    """Modal for entering user ID."""
    
    user_id = discord.ui.TextInput(
        label='🆔 معرف المستخدم (User ID)',
        placeholder='مثال: 1400621970424598542',
        style=discord.TextStyle.short,
        required=True,
        min_length=17,
        max_length=20
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle the modal submission."""
        await interaction.response.defer(ephemeral=True)
        
        user_id_input = self.user_id.value.strip().replace(' ', '').replace('`', '')
        
        # التحقق من أن الإدخال أرقام
        if not user_id_input.isdigit():
            error_embed = discord.Embed(
                title="❌ معرف غير صحيح",
                description="معرف المستخدم يجب أن يكون أرقاماً فقط.\nمثال: `1400621970424598542`",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            return
        
        user_id = int(user_id_input)
        
        try:
            # جلب معلومات المستخدم (حتى لو برا السيرفر)
            user = await bot.fetch_user(user_id)
            
            # محاولة جلب معلومات العضو إذا كان في السيرفر
            member = None
            if interaction.guild:
                member = interaction.guild.get_member(user_id)
            
            # إنشاء Embed للنتائج
            info_embed = discord.Embed(
                title=f"👤 معلومات المستخدم",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            # معلومات أساسية (تظهر حتى لو المستخدم برا السيرفر)
            info_embed.add_field(name="🆔 المعرف", value=f"`{user.id}`", inline=False)
            info_embed.add_field(name="👤 اسم المستخدم", value=user.name, inline=True)
            info_embed.add_field(name="📝 الاسم المعروض", value=user.display_name, inline=True)
            
            if hasattr(user, 'global_name') and user.global_name:
                info_embed.add_field(name="🌍 الاسم العالمي", value=user.global_name, inline=True)
            
            info_embed.add_field(name="🤖 بوت", value="✅ نعم" if user.bot else "❌ لا", inline=True)
            
            # تاريخ إنشاء الحساب
            created_at = user.created_at.strftime("%Y-%m-%d %H:%M:%S")
            info_embed.add_field(name="📅 تاريخ إنشاء الحساب", value=created_at, inline=False)
            
            # معلومات إضافية إذا كان العضو في السيرفر
            if member:
                joined_at = member.joined_at.strftime("%Y-%m-%d %H:%M:%S") if member.joined_at else "N/A"
                info_embed.add_field(name="📥 تاريخ الانضمام للسيرفر", value=joined_at, inline=False)
                
                # الرتب
                roles = [role.mention for role in member.roles if role.name != "@everyone"]
                roles_text = ", ".join(roles) if roles else "لا يوجد رتب"
                info_embed.add_field(name="🎖️ الرتب", value=roles_text, inline=False)
                
                # الصلاحيات
                perms = []
                if member.guild_permissions.administrator:
                    perms.append("👑 مدير")
                if member.guild_permissions.manage_messages:
                    perms.append("📝 إدارة الرسائل")
                if member.guild_permissions.kick_members:
                    perms.append("🔨 طرد الأعضاء")
                if member.guild_permissions.ban_members:
                    perms.append("🔨 حظر الأعضاء")
                if member.guild_permissions.manage_channels:
                    perms.append("📊 إدارة القنوات")
                if member.guild_permissions.manage_roles:
                    perms.append("🎖️ إدارة الرتب")
                if member.guild_permissions.manage_nicknames:
                    perms.append("✏️ إدارة الألقاب")
                if member.guild_permissions.change_nickname:
                    perms.append("✏️ تغيير اللقب")
                if member.guild_permissions.mute_members:
                    perms.append("🔇 كتم الأعضاء")
                if member.guild_permissions.deafen_members:
                    perms.append("🔇 إسكات الأعضاء")
                if member.guild_permissions.move_members:
                    perms.append("🔊 نقل الأعضاء")
                
                if perms:
                    info_embed.add_field(name="🔑 الصلاحيات", value=", ".join(perms), inline=False)
                else:
                    info_embed.add_field(name="🔑 الصلاحيات", value="لا يوجد صلاحيات خاصة", inline=False)
                
                # الحالة
                status_emoji = {
                    discord.Status.online: "🟢",
                    discord.Status.idle: "🟡",
                    discord.Status.dnd: "🔴",
                    discord.Status.offline: "⚫"
                }
                status_text = {
                    discord.Status.online: "متصل",
                    discord.Status.idle: "غير متصل",
                    discord.Status.dnd: "مشغول",
                    discord.Status.offline: "غير ظاهر"
                }
                status = status_emoji.get(member.status, "⚫") + " " + status_text.get(member.status, "غير معروف")
                info_embed.add_field(name="📌 الحالة", value=status, inline=True)
                
                # إذا كان في مكالمة صوتية
                if member.voice and member.voice.channel:
                    info_embed.add_field(name="🔊 في مكالمة صوتية", value=f"في قناة: {member.voice.channel.name}", inline=True)
            else:
                # إذا المستخدم مو في السيرفر
                info_embed.add_field(
                    name="ℹ️ ملاحظة",
                    value="هذا المستخدم ليس في هذا السيرفر، تم جلب المعلومات الأساسية فقط.",
                    inline=False
                )
            
            # إضافة الصورة الرمزية
            avatar_url = user.display_avatar.url
            info_embed.set_thumbnail(url=avatar_url)
            info_embed.set_footer(text=f"طلب بواسطة {interaction.user.name}")
            
            await interaction.followup.send(embed=info_embed, ephemeral=True)
            
        except discord.NotFound:
            error_embed = discord.Embed(
                title="❌ المستخدم غير موجود",
                description=f"المستخدم بالمعرف `{user_id}` غير موجود.\nتأكد من أن المعرف صحيح.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        except discord.HTTPException as e:
            error_embed = discord.Embed(
                title="❌ خطأ",
                description=f"فشل في جلب معلومات المستخدم: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ خطأ",
                description=f"حدث خطأ غير متوقع: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
    
    async def on_error(self, interaction: discord.Interaction, error: Exception):
        """Handle errors in the modal."""
        await interaction.response.send_message(
            f"❌ حدث خطأ: {str(error)}",
            ephemeral=True
        )

# ================= TOOL 2: USER INFO (WITH MODAL/FORM) =================
async def tool_user_info(interaction: discord.Interaction):
    """Tool: Get user information using a modal form."""
    # فتح الـ Modal (النموذج)
    modal = UserInfoModal()
    await interaction.response.send_modal(modal)

# ================= TOOL REGISTRY =================
TOOL_REGISTRY = {
    'ip_info': tool_ip_information,
    'user_info': tool_user_info,
}

# ================= SELECT MENU OPTIONS =================
SELECT_OPTIONS = [
    discord.SelectOption(
        label="معلومات الـ IP",
        value="ip_info",
        description="الحصول على معلومات عامة عن عنوان IP",
        emoji="🌐"
    ),
    discord.SelectOption(
        label="معلومات المستخدم",
        value="user_info",
        description="الحصول على معلومات المستخدم من معرفه",
        emoji="👤"
    ),
]

# ================= SELECT MENU VIEW =================
class ToolsSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="اختر أداة...",
            options=SELECT_OPTIONS
        )
    
    async def callback(self, interaction: discord.Interaction):
        if not has_allowed_role(interaction):
            await interaction.response.send_message(
                "❌ ليس لديك صلاحية لاستخدام هذه القائمة.",
                ephemeral=True
            )
            return
        
        tool_id = self.values[0]
        tool_func = TOOL_REGISTRY.get(tool_id)
        
        if tool_func:
            await tool_func(interaction)
        else:
            await interaction.response.send_message(
                "❌ الأداة غير موجودة.",
                ephemeral=True
            )

class ToolsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ToolsSelect())

# ================= SLASH COMMANDS =================
@bot.event
async def on_ready():
    """Called when the bot is ready."""
    print(f"✅ Bot logged in as: {bot.user.name} (ID: {bot.user.id})")
    print(f"📋 Allowed Role IDs: {ALLOWED_ROLE_IDS}")
    print(f"📊 Connected to {len(bot.guilds)} guild(s)")
    
    try:
        await bot.tree.sync()
        print("✅ Slash commands synced successfully.")
    except Exception as e:
        print(f"❌ Failed to sync slash commands: {e}")
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="for /menu commands"
        ),
        status=discord.Status.online
    )

@bot.tree.command(name="menu", description="فتح قائمة الأدوات")
async def menu(interaction: discord.Interaction):
    """Open the main tools menu with role verification."""
    print(f"\n📩 Menu command used by: {interaction.user.name} (ID: {interaction.user.id})")
    
    if not has_allowed_role(interaction):
        await interaction.response.send_message(
            "❌ ليس لديك صلاحية لاستخدام هذه القائمة.",
            ephemeral=True
        )
        return
    
    embed = discord.Embed(
        title="🛠️ قائمة الأدوات",
        description="اختر أداة من القائمة أدناه.",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="📋 الأدوات المتوفرة",
        value="• **معلومات الـ IP** - الحصول على معلومات عامة عن عنوان IP\n"
              "• **معلومات المستخدم** - الحصول على معلومات المستخدم من معرفه\n"
              "• المزيد من الأدوات قريباً...",
        inline=False
    )
    embed.set_footer(text="اختر أداة من القائمة المنسدلة أدناه")
    
    await interaction.response.send_message(
        embed=embed,
        view=ToolsView(),
        ephemeral=True
    )

# ================= ERROR HANDLING =================
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Global error handler for slash commands."""
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"⏰ الأمر في فترة انتظار. حاول مرة أخرى بعد {error.retry_after:.2f} ثانية.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "❌ حدث خطأ أثناء تنفيذ الأمر.",
            ephemeral=True
        )
        print(f"Command error: {error}")

# ================= MAIN =================
if __name__ == "__main__":
    if BOT_TOKEN == "PUT_YOUR_BOT_TOKEN_HERE":
        print("❌ ERROR: Please set your bot token!")
        exit(1)
    
    if not ALLOWED_ROLE_IDS:
        print("⚠️ WARNING: ALLOWED_ROLE_IDS is empty. No one can use /menu.")
    
    print("🚀 Starting bot...")
    bot.run(BOT_TOKEN)
