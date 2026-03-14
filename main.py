import discord
import os
import asyncio
import random
from discord.ext import commands, tasks
from dotenv import load_dotenv
from itertools import cycle

# Carregar variáveis de ambiente
load_dotenv()
TOKEN = os.getenv('TOKEN')

# Configuração de Status
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
        # Intents necessários para XP e Moderação
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.presences = True 
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        print("\n" + "="*30)
        print("     OBLIVION CORE SYSTEM")
        print("="*30)
        
        # 1. Carregar Extensões (Cogs)
        if os.path.exists('./cogs'):
            for filename in os.listdir('./cogs'):
                if filename.endswith('.py') and not filename.startswith('__'):
                    ext_name = f'cogs.{filename[:-3]}'
                    try:
                        await self.load_extension(ext_name)
                        print(f' ✅ [COG] {filename[:-3].upper()} carregado.')
                    except Exception as e:
                        print(f' ❌ [ERRO] {filename}: {e}')
        
        # 2. Registar Views Persistentes (Sem crashar se o Cog falhar)
        try:
            # Import dinâmico dentro da função para evitar erro de circularidade
            from cogs.recompensas import DailyView
            self.add_view(DailyView(None)) 
            print(" ✅ [VIEW] DailyView persistente ativada.")
        except Exception as e:
            print(f" ⚠ [AVISO] DailyView não registada: {e}")

        # 3. Sincronizar Comandos Slash
        try:
            await self.tree.sync()
            print(" ✅ [SLASH] Comandos sincronizados.")
        except Exception as e:
            print(f" ❌ [ERRO] Falha na sincronização: {e}")
            
        print("="*30 + "\n")
        
        # Iniciar o loop de status
        self.change_status.start()

    @tasks.loop(seconds=20)
    async def change_status(self):
        await self.wait_until_ready()
        
        # Tenta contar membros de todos os servidores
        try:
            membros = sum(g.member_count for g in self.guilds if g.member_count)
            
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
        except:
            pass

    async def on_ready(self):
        print(f'🚀 SISTEMA OPERACIONAL: {self.user.name}')
        print(f'🆔 ID: {self.user.id}')
        print(f'🟢 Status: Totalmente Funcional\n')

# Inicialização do Bot
bot = Theoblivionsmp()

async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Bot desligado manualmente.")