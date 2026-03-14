import discord
from discord.ext import commands
from discord import app_commands
import aiohttp


class SistemasUnificados(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @app_commands.command(name="minecraft_skin", description="Mostra a skin de um jogador do Minecraft")
    @app_commands.describe(nick="Nick do jogador")
    async def minecraft_skin(self, interaction: discord.Interaction, nick: str):

        await interaction.response.defer()

        url = f"https://api.mojang.com/users/profiles/minecraft/{nick}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:

                if resp.status != 200:
                    await interaction.followup.send("❌ Jogador não encontrado.")
                    return

                data = await resp.json()

        uuid = data["id"]

        body_skin = f"https://mc-heads.net/body/{uuid}/400"
        head_skin = f"https://mc-heads.net/avatar/{uuid}/100"

        embed = discord.Embed(
            title=f"🎮 Skin de {nick}",
            color=discord.Color.green()
        )

        embed.set_thumbnail(url=head_skin)
        embed.set_image(url=body_skin)

        embed.add_field(
            name="🆔 UUID",
            value=f"`{uuid}`",
            inline=False
        )

        embed.add_field(
            name="🔗 NameMC",
            value=f"https://namemc.com/profile/{nick}",
            inline=False
        )

        embed.set_footer(text="Sistema de skins Minecraft")

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(SistemasUnificados(bot))
