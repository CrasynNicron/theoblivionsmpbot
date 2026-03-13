import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import os
import random
from datetime import datetime, timedelta

# --- CONFIGS ---
COR_RECOMPENSA = 0x2ecc71
PATH_PLAYERS = "players.json"

class Recompensas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.verificar_notificacoes.start()

    def carregar_dados(self):
        if not os.path.exists(PATH_PLAYERS): return {}
        with open(PATH_PLAYERS, "r", encoding="utf-8") as f: return json.load(f)

    def guardar_dados(self, dados):
        with open(PATH_PLAYERS, "w", encoding="utf-8") as f: json.dump(dados, f, indent=4)

    @tasks.loop(minutes=30)
    async def verificar_notificacoes(self):
        dados = self.carregar_dados()
        agora = datetime.now()
        for uid, p in dados.items():
            if p.get("notificar_daily") and "last_daily" in p:
                last = datetime.fromisoformat(p["last_daily"])
                if agora > last + timedelta(hours=24) and p.get("notificado_hoje") != agora.day:
                    user = self.bot.get_user(int(uid))
                    if user:
                        try:
                            await user.send("🎁 **Oblivion SMP:** Recompensa disponível! Não percas o teu streak.")
                            p["notificado_hoje"] = agora.day
                        except: pass
        self.guardar_dados(dados)

    @app_commands.command(name="config", description="Configura as tuas notificações.")
    @app_commands.choices(opcao=[
        app_commands.Choice(name="Ativar Notificações Daily", value="on"),
        app_commands.Choice(name="Desativar Notificações Daily", value="off")
    ])
    async def config(self, it: discord.Interaction, opcao: str):
        dados = self.carregar_dados()
        uid = str(it.user.id)
        if uid not in dados: return await it.response.send_message("Fala no chat primeiro!", ephemeral=True)
        dados[uid]["notificar_daily"] = (opcao == "on")
        self.guardar_dados(dados)
        await it.response.send_message(f"✅ Notificações: **{opcao.upper()}**", ephemeral=True)

    @app_commands.command(name="setup_daily", description="[STAFF] Envia a mensagem fixa.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_daily(self, it: discord.Interaction):
        embed = discord.Embed(
            title="🎁 Recompensa Diária - Oblivion SMP",
            description=(
                "Resgata o teu prémio e mantém o teu streak vivo!\n\n"
                "⚠️ **Regras:**\n"
                "1️⃣ Atividade no chat nas últimas **12 horas**.\n"
                "2️⃣ Resgate a cada **24 horas**.\n"
                "3️⃣ Se o bónus total passar de **3x**, o cooldown é de **5 min** enquanto o bónus durar!"
            ),
            color=COR_RECOMPENSA
        )
        await it.channel.send(embed=embed, view=DailyView(self))
        await it.response.send_message("✅ Sistema enviado!", ephemeral=True)

class DailyView(discord.ui.View):
    def __init__(self, cog=None):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Resgatar Recompensa", style=discord.ButtonStyle.success, emoji="💰", custom_id="daily_button_persistent")
    async def claim_daily(self, it: discord.Interaction, button: discord.ui.Button):
        if self.cog is None:
            self.cog = it.client.get_cog("Recompensas")

        dados = self.cog.carregar_dados()
        uid = str(it.user.id)
        agora = datetime.now()

        if uid not in dados:
            return await it.response.send_message("❌ Precisas de um perfil!", ephemeral=True)

        p = dados[uid]
        last_msg_str = p.get("last_message")
        
        if not last_msg_str or agora > datetime.fromisoformat(last_msg_str) + timedelta(hours=12):
            return await it.response.send_message("❌ Precisas de ter falado no chat nas últimas 12 horas!", ephemeral=True)

        last_daily_str = p.get("last_daily")
        streak = p.get("streak", 0)

        if last_daily_str:
            last_daily = datetime.fromisoformat(last_daily_str)
            if agora < last_daily + timedelta(hours=24):
                tempo = (last_daily + timedelta(hours=24)) - agora
                return await it.response.send_message(f"⏳ Volta em {int(tempo.total_seconds()//3600)}h!", ephemeral=True)
            
            if agora > last_daily + timedelta(hours=48):
                streak = 0
            else:
                streak += 1
        else:
            streak = 1

        sorte = random.random()
        msg = ""
        if sorte < 0.70:
            qtd = random.randint(100, 300) + (streak * 10)
            p["xp"] = p.get("xp", 0) + qtd
            msg = f"Ganhaste **{qtd} XP**!"
        else:
            # --- MUDANÇA AQUI: Duração de 10 minutos ---
            p["booster_ate"] = (agora + timedelta(minutes=10)).isoformat()
            msg = f"Ganhaste um **Booster de 2x XP** por **10 minutos**! 🔥"

        p["streak"] = streak
        p["last_daily"] = agora.isoformat()
        self.cog.guardar_dados(dados)
        
        await it.response.send_message(f"🎁 **Resgatado!** {msg}\n🔥 Streak Atual: **{streak} dias**", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Recompensas(bot))