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

CARGOS_VIPS_XP = {
    "GEN 1": 1440494650728255538,
    "GEN 2": 1440494651147685949,
    "GEN 3": 1440494652166901822,
    "GEN X": 1477066277251186852
}

def pegar_rank(nivel):
    if nivel < 10: return "🌱 Recruta"
    if nivel < 25: return "🏹 Sobrevivente"
    if nivel < 50: return "🛡️ Veterano"
    if nivel < 80: return "⚔️ Elite"
    return "👑 Lenda do Oblivion"

class SistemaDeExperiencia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}
        self.dados = self.carregar_dados()
        self.salvar_periodicamente.start()

    def carregar_dados(self):
        if not os.path.exists(PATH_PLAYERS): return {}
        try:
            with open(PATH_PLAYERS, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}

    @tasks.loop(minutes=5)
    async def salvar_periodicamente(self):
        with open(PATH_PLAYERS, "w", encoding="utf-8") as f:
            json.dump(self.dados, f, indent=4)

    def calcular_mult(self, member, p_data):
        mult = 1.0
        roles_ids = [r.id for r in member.roles]
        if any(rid in CARGOS_VIPS_XP.values() for rid in roles_ids) or member.guild_permissions.administrator:
            mult = 2.0
        
        prestigio = p_data.get("prestigio", 0)
        mult += (prestigio * 0.5)

        if "booster_ate" in p_data:
            try:
                if datetime.now() < datetime.fromisoformat(p_data["booster_ate"]):
                    mult *= 2
            except: pass
        return mult

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild: return
        if not any(r.id == ID_CARGO_PLAYER for r in message.author.roles): return
        if len(message.content) < 4: return

        uid = str(message.author.id)
        agora = datetime.now()

        if uid in self.cooldowns and agora < self.cooldowns[uid] + timedelta(seconds=60):
            return

        if uid not in self.dados:
            self.dados[uid] = {"xp": 0, "nivel": 1, "prestigio": 0, "notificar_lvl": True}

        p = self.dados[uid]
        mult = self.calcular_mult(message.author, p)
        
        xp_ganho = random.randint(15, 25) * mult
        p["xp"] = p.get("xp", 0) + xp_ganho
        self.cooldowns[uid] = agora

        nivel_atual = p.get("nivel", 1)
        prox_lvl_xp = nivel_atual * 500

        if p["xp"] >= prox_lvl_xp:
            p["xp"] -= prox_lvl_xp
            p["nivel"] = nivel_atual + 1
            
            if p.get("notificar_lvl", True):
                emb = discord.Embed(
                    title="🎊 NOVO NÍVEL!",
                    description=f"{message.author.mention} subiu para o **Nível {p['nivel']}**!\nPatente: **{pegar_rank(p['nivel'])}**.",
                    color=COR_XP
                )
                emb.set_thumbnail(url=message.author.display_avatar.url)
                try:
                    await message.channel.send(embed=emb, delete_after=20)
                except: pass

    @app_commands.command(name="prestigio", description="Reseta o nível para bónus de XP.")
    async def prestigiar(self, it: discord.Interaction):
        uid = str(it.user.id)
        if uid not in self.dados or self.dados[uid].get("nivel", 1) < 100:
            return await it.response.send_message("❌ Precisas de **Nível 100**!", ephemeral=True)

        p = self.dados[uid]
        p["nivel"] = 1
        p["xp"] = 0
        p["prestigio"] = p.get("prestigio", 0) + 1
        await it.response.send_message(f"⭐ **ASCENSÃO!** {it.user.mention} agora é Prestígio {p['prestigio']}!")

async def setup(bot):
    await bot.add_cog(SistemaDeExperiencia(bot))