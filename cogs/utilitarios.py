import discord
from discord import app_commands, ui
from discord.ext import commands
from mcstatus import JavaServer

# --- JANELA POP-UP (MODAL) PARA ANÚNCIOS ---
class AnuncioModal(ui.Modal, title="Painel de Anúncios - The Oblivion"):
    titulo_input = ui.TextInput(
        label="Título do Anúncio",
        placeholder="Escreve o título aqui...",
        style=discord.TextStyle.short,
        required=True
    )
    
    cor_input = ui.TextInput(
        label="Cor da Barra (Hexadecimal)",
        placeholder="Ex: #ff0000 ou deixa vazio para azul",
        style=discord.TextStyle.short,
        required=False,
        default="#3498db"
    )

    imagem_input = ui.TextInput(
        label="Link da Imagem (Opcional)",
        placeholder="https://link-da-imagem.com/foto.png",
        style=discord.TextStyle.short,
        required=False
    )
    
    mensagem_input = ui.TextInput(
        label="Conteúdo da Mensagem",
        placeholder="Escreve o conteúdo... Podes usar parágrafos (Enter).",
        style=discord.TextStyle.long,
        required=True,
        max_length=2000
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            cor_str = self.cor_input.value.replace("#", "")
            cor_hex = int(cor_str, 16)
        except:
            cor_hex = 0x3498db

        embed = discord.Embed(
            title=self.titulo_input.value,
            description=self.mensagem_input.value,
            color=cor_hex
        )
        
        if self.imagem_input.value and self.imagem_input.value.startswith("http"):
            embed.set_image(url=self.imagem_input.value)
            
        embed.set_footer(text=f"Enviado por {interaction.user.display_name} • The Oblivion SMP")
        
        await interaction.response.send_message("✅ Anúncio enviado!", ephemeral=True)
        await interaction.channel.send(embed=embed)

# --- CLASSE DO BOTÃO PIX ---
class PixView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Copiar Chave PIX", style=discord.ButtonStyle.success, emoji="📋")
    async def copiar_pix(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            content="theoblivionsmp.chave@gmail.com", 
            ephemeral=True
        )

class Utilitarios(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ip_servidor = "theoblivionsmp.servmine.com"

    # --- COMANDO ANUNCIAR (SISTEMA DE MENU) ---
    @app_commands.command(name="anunciar", description="Abre o menu para criar um anúncio personalizado.")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def anunciar(self, interaction: discord.Interaction):
        await interaction.response.send_modal(AnuncioModal())

    # --- STATUS DO SERVIDOR ---
    @app_commands.command(name="status", description="Verifica o estado atual do servidor de Minecraft.")
    async def status(self, interaction: discord.Interaction):
        await interaction.response.defer() 
        try:
            server = JavaServer.lookup(self.ip_servidor)
            status = server.status()
            embed = discord.Embed(
                title="📡 ESTADO DO SISTEMA",
                color=0x2ecc71
            )
            embed.add_field(name="Status", value="🟢 **Online**", inline=True)
            embed.add_field(name="Jogadores", value=f"👥 `{status.players.online}/{status.players.max}`", inline=True)
            embed.add_field(name="Versão", value=f"⚙️ `{status.version.name}`", inline=False)
            embed.add_field(name="Latência", value=f"📶 `{round(status.latency, 2)}ms`", inline=True)
            embed.set_thumbnail(url="https://api.mcstatus.io/v2/icon/" + self.ip_servidor)
        except Exception as e:
            embed = discord.Embed(
                title="📡 ESTADO DO SISTEMA",
                description="🔴 **O servidor encontra-se offline ou em manutenção.**",
                color=0xff0000
            )
            embed.add_field(name="IP para conexão", value=f"`{self.ip_servidor}`")

        embed.set_footer(text="The Oblivion SMP © Todos os direitos reservados!")
        await interaction.followup.send(embed=embed)

    # --- COMANDO DE PARCERIAS (TEXTO ORIGINAL MANTIDO) ---
    @app_commands.command(name="parcerias", description="Envia os requisitos de parceria.")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def parcerias(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📂 REQUISITOS DE PARCERIA",
            description=(
                "Para que possamos avançar, deves enviar o teu convite do teu projeto "
                "diretamente ao **ADM** que está a atender este ticket.\n\n"
                "O teu servidor deve obrigatoriamente cumprir as seguintes **Diretrizes de Estabilidade**:\n\n"
                "* ✅ **Conformidade:** Seguir rigorosamente os ToS do Discord.\n"
                "* 👥 **Volume:** Possuir, no mínimo, **100 membros** reais.\n"
                "* 🛠️ **Integridade:** Servidor devidamente **organizado** (canais e cargos claros).\n\n"
                "`[INFORMACAO]: Envia o convite apenas se o teu servidor cumprir estas diretrizes "
                "caso não o faca informe o Administrador mais tarde ele irá validar o seu convite.`\n\n"
                "**Do seu lado esperamos a print a comprovar que enviou o nosso convite no seu servidor, "
                "o nosso convite encontra-se aqui <#1392289933326028991>.**"
            ),
            color=0xff0000 
        )
        embed.set_footer(text="The Oblivion SMP © Todos os direitos reservados!")
        await interaction.response.send_message(embed=embed)

    # --- COMANDO DE PAGAMENTOS (TEXTO ORIGINAL MANTIDO) ---
    @app_commands.command(name="metodosdepagamento", description="Exibe a chave PIX para pagamentos.")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def pagamentos(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="💳 MÉTODOS DE PAGAMENTO",
            description=(
                "Atualmente aceitamos pagamentos via **PIX**.\n\n"
                "**🔑 CHAVE PIX (E-mail):**\n"
                "`theoblivionsmp.chave@gmail.com`"
            ),
            color=0x2ecc71
        )
        embed.set_footer(text="The Oblivion SMP © Todos os direitos reservados!")
        await interaction.response.send_message(embed=embed, view=PixView())

    # --- COMANDO DE IP (TEXTO ORIGINAL MANTIDO) ---
    @app_commands.command(name="ip", description="Mostra o IP e a versão do servidor.")
    async def ip(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎮 CONECTAR AO SERVIDOR",
            description=(
                f"**IP:** `{self.ip_servidor}`\n"
                "**Versão:** 1.20.1 \n\n"
                "Já estás na nossa Whitelist? Se não, abre um ticket em <#1150686724280811540>."
            ),
            color=0x3498db
        )
        embed.set_footer(text="The Oblivion SMP © Todos os direitos reservados!")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Utilitarios(bot))