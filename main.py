import discord
import os
import asyncio
import random  # <-- MOVIDO PARA O TOPO (BOA PRÁTICA)
from discord.ext import commands, tasks
from dotenv import load_dotenv
from itertools import cycle

# Assume que os teus ficheiros estão na pasta /cogs
from cogs.recompensas import DailyView 

load_dotenv()
TOKEN = os.getenv('TOKEN')

# --- STATUS "BONITÕES" E DINÂMICOS ---
status_frases = cycle([
    "⚔️ Dominando o Oblivion SMP",
    "Nas sombras do vazio...",
    "🛡️ Protegendo os sobreviventes",
    "💎 Em busca de fragmentos",
    "🔥 XP em dobro no chat!",
    "🚀 Use /playerinfo",
    "👑 The Oblivion SMP © 2026",
    "👺 Cuidado com o escuro..."
])

class Theoblivionsmp(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.presences = True 
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        print("\n" + "="*30)
        print("     OBLIVION CORE SYSTEM")
        print("="*30)
        
        # 1. Carregar os Cogs Primeiro
        if os.path.exists('./cogs'):
            for filename in os.listdir('./cogs'):
                # Ignorar pastas e ficheiros que não sejam .py
                if filename.endswith('.py') and not filename.startswith('__'):
                    try:
                        await self.load_extension(f'cogs.{filename[:-3]}')
                        print(f' ✅ [COG] {filename[:-3].upper()} carregado.')
                    except Exception as e:
                        print(f' ❌ [ERRO] {filename}: {e}')
        
        # 2. Registar a View Persistente
        try:
            self.add_view(DailyView(None)) 
            print(" ✅ [VIEW] DailyView persistente ativada.")
        except Exception as e:
            print(f" ⚠ [AVISO] Não foi possível registar DailyView: {e}")

        # 3. Sincronizar Comandos
        await self.tree.sync()
        print(" ✅ [SLASH] Comandos sincronizados.")
        print("="*30 + "\n")
        
        # Iniciar a task de status
        self.change_status.start()

    @tasks.loop(seconds=20)
    async def change_status(self):
        await self.wait_until_ready()
        
        membros = sum(g.member_count for g in self.guilds)
        
        # Lógica de status aleatório ou sequencial
        if random.random() < 0.2: 
            status_txt = f"👥 {membros} Sobreviventes"
        else:
            status_txt = next(status_frases)

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching, 
                name=status_txt
            ),
            status=discord.Status.online
        )

    async def on_ready(self):
        print(f'🚀 SISTEMA OPERACIONAL: {self.user.name}')
        print(f'🆔 ID: {self.user.id}')
        print(f'🟢 Status: Totalmente Funcional\n')

# Inicia o bot
bot = Theoblivionsmp()
bot.run(TOKEN)