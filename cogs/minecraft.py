import discord
from discord.ext import commands
from discord import app_commands
import aiohttp

# Lista começa com alguns, mas vai crescer sozinha!
nick_cache = ["PipocaMaia", "Notch", "jeb_", "Dinnerbone", "Technoblade", "Dream"]

class SistemasUnificados(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Função de autocomplete que lê a lista dinâmica
    async def nick_autocomplete(self, interaction: discord.Interaction, current: str):
        return [
            app_commands.Choice(name=nick, value=nick)
            for nick in nick_cache if current.lower() in nick.lower()
        ][:25]

    @app_commands.command(
        name="minecraft_skin",
        description="Mostra a skin de um jogador do Minecraft (Premium)"
    )
    @app_commands.describe(nick="Nick do jogador para pesquisar")
    @app_commands.autocomplete(nick=nick_autocomplete)
    async def minecraft_skin(self, interaction: discord.Interaction, nick: str):
        await interaction.response.defer()

        # 1. Procurar UUID na Mojang
        mojang_api = f"https://api.mojang.com/users/profiles/minecraft/{nick}"
        async with aiohttp.ClientSession() as session:
            async with session.get(mojang_api) as resp:
                if resp.status != 200:
                    return await interaction.followup.send(f"❌ O jogador **{nick}** não foi encontrado ou não é original.", ephemeral=True)
                
                data = await resp.json()
                uuid = data["id"]
                nome_correto = data["name"] # Pega o nick com as letras maiúsculas corretas

        # --- SISTEMA DE CACHE DINÂMICO ---
        # Se o nick não estiver na lista, adiciona-o para aparecer no próximo autocomplete!
        if nome_correto not in nick_cache:
            nick_cache.append(nome_correto)
            # Mantém a lista limpa (apaga os mais antigos se passar de 100)
            if len(nick_cache) > 100: nick_cache.pop(0)

        # 2. URLs de alta qualidade (Render 3D)
        head_url = f"https://mc-heads.net/avatar/{uuid}/100"
        # Usamos o 'player' em vez de 'body' para um render 3D mais bonito
        body_render = f"https://mc-heads.net/player/{uuid}/400"
        
        embed = discord.Embed(
            title=f"👤 Perfil de {nome_correto}",
            url=f"https://namemc.com/profile/{nome_correto}",
            color=0x2f3136 # Cor escura elegante
        )
        
        embed.set_thumbnail(url=head_url)
        embed.set_image(url=body_render)
        
        embed.add_field(name="🔗 Nick Original", value=f"`{nome_correto}`", inline=True)
        embed.add_field(name="🆔 UUID", value=f"`{uuid}`", inline=True)
        
        # Detalhe extra: Link direto para a skin plana (textura)
        embed.add_field(name="🖼️ Textura", value=f"[Ver Skin Plana](https://mc-heads.net/skin/{uuid})", inline=False)
        
        embed.set_footer(text="Oblivion SMP • mc-heads.net", icon_url="https://static.wikia.nocookie.net/minecraft_gamepedia/images/2/2d/Grass_Block_JE2.png")

        # 3. Botões interativos
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Baixar Skin", url=f"https://mc-heads.net/download/{uuid}", style=discord.ButtonStyle.link, emoji="📥"))
        view.add_item(discord.ui.Button(label="Ver no NameMC", url=f"https://namemc.com/profile/{nome_correto}", style=discord.ButtonStyle.link, emoji="🌐"))

        await interaction.followup.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(SistemasUnificados(bot))