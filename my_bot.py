import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

# Cargar variables desde el archivo .env
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
VOICE_CHANNEL_ID = int(os.getenv("VOICE_CHANNEL_ID"))
AUDIO_FILE = os.getenv("AUDIO_FILE")
NOTIFY_USER_IDS = list(map(int, os.getenv("NOTIFY_USER_IDS").split(",")))  # Convierte a lista de números


# Intents necesarios
intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.members = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

    # El bot se une automáticamente al canal de voz
    guild = bot.get_guild(GUILD_ID)
    if guild:
        channel = guild.get_channel(VOICE_CHANNEL_ID)
        if channel:
            await channel.connect()
            print(f"Bot conectado al canal de voz: {channel.name}")

@bot.event
async def on_voice_state_update(member, before, after):
    """Detecta cuando un usuario entra al canal y notifica a los demás."""
    if member.bot:
        return  # Ignora si es otro bot

    vc = discord.utils.get(bot.voice_clients, guild=member.guild)

    # Verifica que el usuario NO estaba en el canal antes y AHORA sí está en el canal objetivo
    if before.channel is None and after.channel and after.channel.id == VOICE_CHANNEL_ID:
        if vc is None or not vc.is_connected():
            # Si el bot no está en el canal, lo conecta
            vc = await after.channel.connect()

        # Reproduce sonido de alerta en el canal de voz
        if not vc.is_playing():
            vc.play(discord.FFmpegPCMAudio(AUDIO_FILE))
            while vc.is_playing():
                await asyncio.sleep(1)

        # Notificar a los usuarios que no están en el canal
        await notify_users(member.guild, member)

async def notify_users(guild, joined_member):
    """Envía un mensaje privado a los usuarios que no están en el canal de voz."""
    voice_channel = guild.get_channel(VOICE_CHANNEL_ID)

    if not voice_channel:
        return  # Si el canal de voz no existe, no hace nada

    connected_users = {member.id for member in voice_channel.members}  # Usuarios en el canal

    for user_id in NOTIFY_USER_IDS:
        if user_id not in connected_users:  # Solo notifica a los que no están en el canal
            user = await bot.fetch_user(user_id)
            if user:
                try:
                    await user.send(f"🔊 {joined_member.display_name} se ha conectado al canal de voz **{voice_channel.name}** en **{guild.name}**.")
                    print(f"Notificación enviada a {user.display_name}")
                except discord.Forbidden:
                    print(f"No puedo enviar mensaje a {user.display_name} (DMs bloqueados)")

bot.run(TOKEN)