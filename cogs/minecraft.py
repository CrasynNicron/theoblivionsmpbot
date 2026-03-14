import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
import os

PATH_NICKS = "nicks.json"

class SistemasUnificados(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.nick_cache = self.carregar_nicks()

    def carregar_nicks(self):
        """Carrega os nicks do ficheiro JSON para o autocomplete persistente."""
        if not os.path.exists(PATH_NICKS):
            return ["PipocaMaia", "Notch", "jeb_", "Dinnerbone"]
        try:
            with open(PATH_NICKS, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return ["PipocaMaia", "Notch", "jeb_"]

    def guardar_nicks(self):
        """Guarda a lista atualizada no JSON."""
        with open(PATH_NICKS, "w", encoding="utf-8") as f:
            json.dump(self.nick_cache, f, indent=4)

    async def nick_autocomplete(self, interaction: discord.Interaction, current: str):
        """Sugere nicks baseados no histórico de pesquisas."""
        return [
            app_commands.Choice(name=nick, value=nick)
            for nick in self.nick_cache if current.lower() in nick.lower()
        ][:25]

    @app_commands.command(
        name="minecraft_skin",
        description="Mostra a skin de um jogador do Minecraft (Premium)"
    )
    @app_commands.describe(nick="Nick do jogador para pesquisar")
    @app_commands.autocomplete(nick=nick_autocomplete)
    async def minecraft_skin(self, interaction: discord.Interaction, nick: str):
        await interaction.response.defer()

        # 1. Procurar UUID na Mojang (Necessário para as APIs de skin)
        mojang_api = f"https://api.mojang.com/users/profiles/minecraft/{nick}"
        async with aiohttp.ClientSession() as session:
            async with session.get(mojang_api) as resp:
                if resp.status != 200:
                    return await interaction.followup.send(f"❌ O jogador **{nick}** não foi encontrado ou não é original.", ephemeral=True)
                
                data = await resp.json()
                uuid = data["id"]
                nome_correto = data["name"]

        # --- ATUALIZAÇÃO DO CACHE ---
        if nome_correto not in self.nick_cache:
            self.nick_cache.append(nome_correto)
            if len(self.nick_cache) > 200: self.nick_cache.pop(0)
            self.guardar_nicks()

        # 2. Configuração das Imagens (Render 3D de Lado)
        head_url = f"https://mc-heads.net/avatar/{uuid}/100"
        body_render = f"https://mc-heads.net/body/{uuid}/400" # Este é o render de lado
        
        # Link do NameMC
        namemc_url = f"https://namemc.com/profile/{nome_correto}"
        
        embed = discord.Embed(
            title=f"👤 Perfil de {nome_correto}",
            url=namemc_url, # Clicar no título abre o NameMC
            color=0x2f3136
        )
        
        embed.set_thumbnail(url=head_url)
        embed.set_image(url=body_render)
        
        embed.add_field(name="🔗 Nick Original", value=f"`{nome_correto}`", inline=True)
        embed.add_field(name="🆔 UUID", value=f"`{uuid}`", inline=True)
        embed.add_field(name="🌐 Ver no NameMC", value=f"[Clique aqui para abrir]({namemc_url})", inline=False)
        
        embed.set_footer(
            text="The Oblivion SMP", 
            icon_url="https://cdn.discordapp.com/icons/1133021777547767949/a_6714d22f0fa7b8e0faf02468456ae843.gif?size=2048.gif"
        )

        # 3. Botões interativos com link para NameMC
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Ver no NameMC", url=namemc_url, style=discord.ButtonStyle.link, emoji="🌐"))
        view.add_item(discord.ui.Button(label="Baixar Skin", url=f"https://mc-heads.net/download/{uuid}", style=discord.ButtonStyle.link, emoji="📥"))

        await interaction.followup.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(SistemasUnificados(bot))