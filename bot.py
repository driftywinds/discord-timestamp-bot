import discord
from discord.ext import commands
from discord import app_commands
import datetime
import pytz
import re
import os
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

class TimestampBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)
    
    async def setup_hook(self):
        # Sync slash commands
        await self.tree.sync()
        print(f"Synced slash commands for {self.user}")

bot = TimestampBot()

@bot.event
async def on_ready():
    print(f'{bot.user} has landed!')
    print(f'Bot is ready and can be used in DMs and servers!')

def parse_offset(offset_str: str) -> Optional[datetime.timezone]:
    """Parse UTC offset string like +05:30, -08:00, etc."""
    match = re.match(r'^([+-])(\d{1,2}):?(\d{2})$', offset_str.strip())
    if not match:
        return None
    
    sign, hours, minutes = match.groups()
    total_minutes = int(hours) * 60 + int(minutes)
    if sign == '-':
        total_minutes = -total_minutes
    
    return datetime.timezone(datetime.timedelta(minutes=total_minutes))

def parse_datetime_input(date_str: str, time_str: str = None) -> Optional[datetime.datetime]:
    """Parse date and optional time strings into datetime object."""
    try:
        # If time is not provided, assume the date string might contain time too
        if time_str is None:
            # Try parsing full datetime string
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%m/%d/%Y %H:%M:%S', 
                       '%m/%d/%Y %H:%M', '%d/%m/%Y %H:%M:%S', '%d/%m/%Y %H:%M']:
                try:
                    return datetime.datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # Try parsing just date
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                try:
                    return datetime.datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
        else:
            # Parse date and time separately
            date_part = None
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                try:
                    date_part = datetime.datetime.strptime(date_str, fmt).date()
                    break
                except ValueError:
                    continue
            
            if date_part is None:
                return None
            
            time_part = None
            for fmt in ['%H:%M:%S', '%H:%M', '%I:%M:%S %p', '%I:%M %p']:
                try:
                    time_part = datetime.datetime.strptime(time_str, fmt).time()
                    break
                except ValueError:
                    continue
            
            if time_part is None:
                return None
            
            return datetime.datetime.combine(date_part, time_part)
        
        return None
    except:
        return None

def get_timezone(timezone_str: str) -> Optional[datetime.tzinfo]:
    """Get timezone object from string."""
    try:
        return pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        tz = parse_offset(timezone_str)
        if tz is None and timezone_str.upper() == 'UTC':
            return pytz.UTC
        return tz

async def timezone_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    """Autocomplete for timezone field."""
    common_timezones = [
        "UTC", "America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles",
        "Europe/London", "Europe/Paris", "Europe/Berlin", "Europe/Rome", "Europe/Amsterdam",
        "Asia/Tokyo", "Asia/Shanghai", "Asia/Kolkata", "Asia/Dubai", "Australia/Sydney",
        "America/Toronto", "America/Mexico_City", "Pacific/Auckland"
    ]
    
    # Filter timezones based on current input
    if current:
        filtered = [tz for tz in common_timezones if current.lower() in tz.lower()]
    else:
        filtered = common_timezones[:10]  # Show first 10 if no input
    
    return [app_commands.Choice(name=tz, value=tz) for tz in filtered[:25]]  # Discord limits to 25

@bot.tree.command(name="timestamp", description="Create Discord timestamps from date, time, and timezone")
@app_commands.describe(
    date="Date in YYYY-MM-DD, MM/DD/YYYY, or DD/MM/YYYY format",
    timezone="Timezone (IANA name like America/New_York or UTC offset like +05:30)",
    time="Optional: Time in HH:MM, HH:MM:SS, or HH:MM AM/PM format"
)
@app_commands.autocomplete(timezone=timezone_autocomplete)
async def slash_timestamp(interaction: discord.Interaction, date: str, timezone: str, time: str = None):
    """Slash command version of timestamp creation."""
    await interaction.response.defer(ephemeral=False)
    
    # Parse timezone
    tz = get_timezone(timezone)
    if tz is None:
        await interaction.followup.send(
            f"❌ Unknown timezone: `{timezone}`\n"
            "Use IANA names (e.g., `America/New_York`) or UTC offsets (e.g., `+05:30`, `-08:00`)",
            ephemeral=True
        )
        return
    
    # Parse datetime
    dt = parse_datetime_input(date, time)
    if dt is None:
        await interaction.followup.send(
            "❌ Could not parse date/time. Supported formats:\n"
            "• `YYYY-MM-DD` (date only)\n"
            "• `YYYY-MM-DD` with separate time field\n"
            "• `MM/DD/YYYY` or `DD/MM/YYYY`\n"
            "• Time: `HH:MM`, `HH:MM:SS`, or `HH:MM AM/PM`",
            ephemeral=True
        )
        return
    
    # Localize the datetime to the specified timezone
    try:
        if isinstance(tz, pytz.BaseTzInfo):
            localized_dt = tz.localize(dt)
        else:
            localized_dt = dt.replace(tzinfo=tz)
    except:
        await interaction.followup.send("❌ Error applying timezone to the datetime.", ephemeral=True)
        return
    
    # Convert to Unix timestamp
    unix_timestamp = int(localized_dt.timestamp())
    
    # Create Discord timestamp formats
    formats = {
        "Short Time": f"<t:{unix_timestamp}:t>",
        "Long Time": f"<t:{unix_timestamp}:T>",
        "Short Date": f"<t:{unix_timestamp}:d>",
        "Long Date": f"<t:{unix_timestamp}:D>",
        "Short Date/Time": f"<t:{unix_timestamp}:f>",
        "Long Date/Time": f"<t:{unix_timestamp}:F>",
        "Relative": f"<t:{unix_timestamp}:R>"
    }
    
    # Create embed
    embed = discord.Embed(
        title="📅 Discord Timestamp Generated",
        description=f"**Input:** {localized_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}",
        color=0x5865F2
    )
    
    # Add timestamp formats with previews
    for name, timestamp in formats.items():
        embed.add_field(
            name=f"{name}: {timestamp}",
            value=f"`{timestamp}`",
            inline=False
        )
    
    embed.set_footer(text="💡 Copy any timestamp code above to use in your messages!")
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="timezones", description="List common timezone names for use with /timestamp")
async def slash_timezones(interaction: discord.Interaction):
    """Show common timezone names."""
    embed = discord.Embed(
        title="🌍 Common Timezone Names",
        description="Here are commonly used IANA timezone names and UTC offsets:",
        color=0x5865F2
    )
    
    embed.add_field(
        name="🇺🇸 Americas",
        value="• America/New_York (EST/EDT)\n• America/Chicago (CST/CDT)\n• America/Denver (MST/MDT)\n• America/Los_Angeles (PST/PDT)\n• America/Toronto",
        inline=True
    )
    
    embed.add_field(
        name="🇪🇺 Europe",
        value="• Europe/London (GMT/BST)\n• Europe/Paris (CET/CEST)\n• Europe/Berlin\n• Europe/Amsterdam\n• Europe/Rome",
        inline=True
    )
    
    embed.add_field(
        name="🌏 Asia/Pacific",
        value="• Asia/Tokyo (JST)\n• Asia/Shanghai (CST)\n• Asia/Kolkata (IST)\n• Australia/Sydney\n• Asia/Dubai",
        inline=True
    )
    
    embed.add_field(
        name="🕐 UTC Offsets",
        value="You can also use UTC offsets:\n`+05:30`, `-08:00`, `+00:00`, `UTC`\n\nExample: `+05:30` for India Standard Time",
        inline=False
    )
    
    embed.add_field(
        name="💡 Usage Tips",
        value="• Use `/timestamp` to create Discord timestamps\n• Start typing timezone names for autocomplete\n• Works in DMs and all server channels!",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Keep the original prefix commands for backward compatibility
@bot.command(name='timestamp', aliases=['ts'])
async def create_timestamp(ctx, *, input_text: str):
    """
    Create a Discord timestamp from date, time, and timezone.
    This is the legacy prefix command - use /timestamp for the modern slash command!
    """
    parts = input_text.strip().split()
    
    if len(parts) < 2:
        await ctx.send("❌ Please provide at least a date and timezone.\n"
                      "**Tip:** Try the new `/timestamp` slash command for a better experience!\n"
                      "Examples:\n"
                      "`!timestamp 2024-12-25 America/New_York`\n"
                      "`!timestamp 2024-12-25 15:30 +05:30`")
        return
    
    timezone_str = parts[-1]
    datetime_parts = parts[:-1]
    
    tz = get_timezone(timezone_str)
    if tz is None:
        await ctx.send(f"❌ Unknown timezone: `{timezone_str}`\n"
                      "Use IANA names (e.g., `America/New_York`) or UTC offsets (e.g., `+05:30`, `-08:00`)")
        return
    
    dt = None
    if len(datetime_parts) == 1:
        dt = parse_datetime_input(datetime_parts[0])
    elif len(datetime_parts) == 2:
        dt = parse_datetime_input(datetime_parts[0], datetime_parts[1])
    else:
        dt = parse_datetime_input(' '.join(datetime_parts))
    
    if dt is None:
        await ctx.send("❌ Could not parse date/time. Supported formats:\n"
                      "• `YYYY-MM-DD` (date only)\n"
                      "• `YYYY-MM-DD HH:MM` or `YYYY-MM-DD HH:MM:SS`\n"
                      "• `MM/DD/YYYY` or `DD/MM/YYYY`")
        return
    
    try:
        if isinstance(tz, pytz.BaseTzInfo):
            localized_dt = tz.localize(dt)
        else:
            localized_dt = dt.replace(tzinfo=tz)
    except:
        await ctx.send("❌ Error applying timezone to the datetime.")
        return
    
    unix_timestamp = int(localized_dt.timestamp())
    
    formats = {
        "Short Time": f"<t:{unix_timestamp}:t>",
        "Long Time": f"<t:{unix_timestamp}:T>",
        "Short Date": f"<t:{unix_timestamp}:d>",
        "Long Date": f"<t:{unix_timestamp}:D>",
        "Short Date/Time": f"<t:{unix_timestamp}:f>",
        "Long Date/Time": f"<t:{unix_timestamp}:F>",
        "Relative": f"<t:{unix_timestamp}:R>"
    }
    
    embed = discord.Embed(
        title="📅 Discord Timestamp Generated",
        description=f"**Input:** {localized_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}\n*Try `/timestamp` for the modern slash command experience!*",
        color=0x5865F2
    )
    
    for name, timestamp in formats.items():
        embed.add_field(
            name=f"{name}: {timestamp}",
            value=f"`{timestamp}`",
            inline=False
        )
    
    embed.set_footer(text="💡 Copy any timestamp code above to use in your messages!")
    await ctx.send(embed=embed)

@bot.command(name='timezones', aliases=['tz'])
async def list_common_timezones(ctx):
    """List common timezone names - use /timezones for the modern slash command!"""
    embed = discord.Embed(
        title="🌍 Common Timezone Names",
        description="*Try `/timezones` for the modern slash command experience!*\n\nCommon IANA timezone names:",
        color=0x5865F2
    )
    
    embed.add_field(
        name="Americas",
        value="• America/New_York\n• America/Chicago\n• America/Denver\n• America/Los_Angeles",
        inline=True
    )
    
    embed.add_field(
        name="Europe",
        value="• Europe/London\n• Europe/Paris\n• Europe/Berlin\n• Europe/Amsterdam",
        inline=True
    )
    
    embed.add_field(
        name="Asia/Pacific",
        value="• Asia/Tokyo\n• Asia/Shanghai\n• Asia/Kolkata\n• Australia/Sydney",
        inline=True
    )
    
    await ctx.send(embed=embed)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Handle slash command errors."""
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(f"Command is on cooldown. Try again in {error.retry_after:.2f} seconds.", ephemeral=True)
    else:
        await interaction.response.send_message("An error occurred while processing your command.", ephemeral=True)
        print(f"Slash command error: {error}")

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
if __name__ == "__main__":
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print("❌ Error: DISCORD_BOT_TOKEN not found in environment variables!")
        print("Please create a .env file with: DISCORD_BOT_TOKEN=your_token_here")
        exit(1)
    
    print("🤖 Starting Discord Timestamp Bot...")
    bot.run(token)