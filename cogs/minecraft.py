import discord
from discord.ext import commands
from discord import app_commands
import aiohttp

# Lista de nicks para autocomplete (podes adicionar dinamicamente)
nick_cache = ["PipocaMaia", "Notch", "jeb_"]

class SistemasUnificados(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Função de autocomplete
    async def nick_autocomplete(self, interaction: discord.Interaction, current: str):
        return [
            app_commands.Choice(name=nick, value=nick)
            for nick in nick_cache if current.lower() in nick.lower()
        ][:25]  # Limite do Discord

    @app_commands.command(
        name="minecraft_skin",
        description="Mostra a skin de um jogador do Minecraft"
    )
    @app_commands.describe(nick="Nick do jogador")
    @app_commands.autocomplete(nick=nick_autocomplete)
    async def minecraft_skin(self, interaction: discord.Interaction, nick: str):
        await interaction.response.defer()

        # Verificar se o jogador existe
        mojang_api = f"https://api.mojang.com/users/profiles/minecraft/{nick}"
        async with aiohttp.ClientSession() as session:
            async with session.get(mojang_api) as resp:
                if resp.status != 200:
                    await interaction.followup.send(f"❌ Jogador `{nick}` não encontrado ou não é premium.")
                    return
                data = await resp.json()

        uuid = data["id"]

        # URLs das skins
        head_skin = f"https://mc-heads.net/avatar/{uuid}/100"
        body_skin_Lado = f"https://mc-heads.net/body/{uuid}/400"
        Full_body_front = f"https://mc-heads.net/player/{uuid}/400"
        full_skin = f"https://mc-heads.net/skin/{uuid}"
        

        # Embed
        embed = discord.Embed(
            title=f"🎮 Skin de {nick}",
            description="Aqui está a skin completa!",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=head_skin)
        embed.set_image(url=body_skin)
        embed.add_field(name="🆔 UUID", value=f"`{uuid}`", inline=False)
        embed.add_field(name="🔗 NameMC", value=f"[Clique aqui](https://namemc.com/profile/{nick})", inline=False)
        embed.set_footer(text="Sistema de skins Minecraft")

        # Botões interativos
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Download Skin", url=f"https://mc-heads.net/download/{uuid}", style=discord.ButtonStyle.green))
        view.add_item(discord.ui.Button(label="Ver NameMC", url=f"https://namemc.com/profile/{nick}", style=discord.ButtonStyle.gray))

        await interaction.followup.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(SistemasUnificados(bot))
