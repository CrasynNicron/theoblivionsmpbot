import discord
import os
import asyncio
from discord.ext import commands, tasks
from dotenv import load_dotenv
from itertools import cycle

# IMPORTANTE: Precisamos importar a View aqui para o bot a reconhecer no arranque
# Assume que o teu ficheiro se chama recompensas.py dentro da pasta cogs
from cogs.recompensas import DailyView 

load_dotenv()
TOKEN = os.getenv('TOKEN')

status_frases = cycle([
    "Explorando o Oblivion SMP",
    "A observar as sombras...",
    "The Oblivion SMP © 2026",
])

class Theoblivionsmp(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        print("--- Carregando Módulos ---")
        
        # 1. Registar a View Persistente (O segredo para o botão nunca parar)
        self.add_view(DailyView(None)) 
        
        # 2. Carregar os Cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f'✦ Módulo carregado: {filename}')
                except Exception as e:
                    print(f'⚠ Erro ao carregar {filename}: {e}')
        
        await self.tree.sync()
        print("--- Slash Commands Sincronizados ---")
        
        # Iniciar a task de status
        self.change_status.start()

    @tasks.loop(seconds=30)
    async def change_status(self):
        await self.wait_until_ready()
        try:
            await self.change_presence(activity=discord.Game(next(status_frases)))
        except Exception as e:
            print(f"Erro ao mudar status: {e}")

    async def on_ready(self):
        print(f'Sincronização concluída: {self.user.name} está online.')

# Inicia o bot
bot = Theoblivionsmp()
bot.run(TOKEN)