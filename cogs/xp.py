import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import os
import random
from datetime import datetime, timedelta

# --- CONFIGS ---
PATH_PLAYERS = "players.json"
COR_XP = 0x9b59b6
ID_CARGO_PLAYER = 1337596948940722306

class SistemaXP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}
        if not os.path.exists(PATH_PLAYERS):
            with open(PATH_PLAYERS, "w") as f:
                json.dump({}, f)

    @app_commands.command(name="xp_status", description="Verifica se o sistema de XP está ativo")
    async def xp_status(self, it: discord.Interaction):
        await it.response.send_message("✅ Sistema de XP carregado e operacional!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SistemaXP(bot))