import discord
from discord import app_commands
from discord.ext import commands

class SistemaNiveis(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="xp_check", description="Verifica se o sistema de XP ligou.")
    async def xp_check(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Sistema de Níveis carregado com sucesso!")

async def setup(bot):
    await bot.add_cog(SistemaNiveis(bot)