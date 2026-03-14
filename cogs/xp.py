import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import random
from datetime import datetime, timedelta

# --- CONFIGS ---
PATH_PLAYERS = "players.json"
COR_XP = 0x9b59b6
ID_CARGO_PLAYER = 1337596948940722306

CARGOS_VIPS = {
    "GEN 1": 1440494650728255538,
    "GEN 2": 1440494651147685949,
    "GEN 3": 1440494652166901822,
    "GEN X": 1477066277251186852
}

def get_rank_name(nivel):
    if nivel < 10: return "🌱 Recruta"
    if nivel < 25: return "🏹 Sobrevivente"
    if nivel < 50: return "🛡️ Veterano"
    if nivel < 80: return "⚔️ Elite"
    return "👑 Lenda do Oblivion"

class XPSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}

    def carregar_dados(self):
        if not os.path.exists(PATH_PLAYERS): return {}
        try:
            with open(PATH_PLAYERS, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}

    def guardar_dados(self, dados):
        with open(PATH_PLAYERS, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4)

    def check_mult(self, member, p_data):
        mult = 1.0
        roles_ids = [r.id for r in member.roles]
        if any(rid in CARGOS_VIPS.values() for rid in roles_ids) or member.guild_permissions.administrator:
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
        if ID_CARGO_PLAYER not in [r.id for r in message.author.roles]: return
        if len(message.content) < 4: return

        uid = str(message.author.id)
        agora = datetime.now()

        if uid in self.cooldowns and agora < self.cooldowns[uid] + timedelta(seconds=60):
            return

        dados = self.carregar_dados()
        if uid not in dados: return 

        p = dados[uid]
        mult = self.check_mult(message.author, p)
        
        xp_ganho = random.randint(15, 25) * mult
        p["xp"] = p.get("xp", 0) + xp_ganho
        self.cooldowns[uid] = agora

        nivel_atual = p.get("nivel", 1)
        prox_lvl_xp = nivel_atual * 500

        if p["xp"] >= prox_lvl_xp:
            p["nivel"] = nivel_atual + 1
            p["xp"] = 0
            
            # Notificação Profissional
            if p.get("notificar_lvl", True):
                embed = discord.Embed(
                    title="🎊 NOVO NÍVEL ALCANÇADO",
                    description=f"{message.author.mention} subiu para o **Nível {p['nivel']}**!\nAgora és um **{get_rank_name(p['nivel'])}**.",
                    color=COR_XP
                )
                embed.set_thumbnail(url=message.author.display_avatar.url)
                if p.get("prestigio", 0) > 0:
                    embed.set_footer(text=f"Bónus de Prestígio S{p['prestigio']} ativo! ⭐")
                
                await message.channel.send(embed=embed, delete_after=20)

        self.guardar_dados(dados)

    @app_commands.command(name="prestigio", description="Reseta o teu nível para ganhar bónus permanente de XP.")
    async def prestigiar(self, it: discord.Interaction):
        dados = self.carregar_dados()
        uid = str(it.user.id)
        
        if uid not in dados or dados[uid].get("nivel", 1) < 100:
            return await it.response.send_message("❌ Precisas de atingir o **Nível 100** para subir de Prestígio!", ephemeral=True)

        p = dados[uid]
        p["nivel"] = 1
        p["xp"] = 0
        p["prestigio"] = p.get("prestigio", 0) + 1
        self.guardar_dados(dados)

        embed = discord.Embed(
            title="⭐ ASCENSÃO DE PRESTÍGIO",
            description=f"Parabéns {it.user.mention}!\n\nAgora és **Prestígio {p['prestigio']}**.\nO teu multiplicador base aumentou em **+0.5x** para sempre!",
            color=discord.Color.gold()
        )
        await it.response.send_message(embed=embed)

    @app_commands.command(name="notificacoes", description="Ativa ou desativa avisos de Level Up no chat.")
    async def toggle_notif(self, it: discord.Interaction):
        dados = self.carregar_dados()
        uid = str(it.user.id)
        if uid not in dados: return await it.response.send_message("Perfil não encontrado.", ephemeral=True)
        
        atual = dados[uid].get("notificar_lvl", True)
        dados[uid]["notificar_lvl"] = not atual
        self.guardar_dados(dados)
        
        status = "ATIVADAS" if not atual else "DESATIVADAS"
        await it.response.send_message(f"🔔 As tuas notificações de nível foram **{status}**.", ephemeral=True)

# --- ESTA FUNÇÃO TEM DE ESTAR FORA DA CLASSE (SEM ESPAÇOS À ESQUERDA) ---
async def setup(bot):
    await bot.add_cog(XPSystem(bot))