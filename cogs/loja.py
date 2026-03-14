import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
import io
import json
import random
import string
from datetime import datetime, timedelta

# --- CONFIGS ---
ID_CANAL_LOGS_STAFF = 1481124593971236947 
COR_SUCESSO = 0x2ecc71
COR_ALERTA = 0xf1c40f
COR_ERRO = 0xe74c3c
COR_PRINCIPAL = 0x9b59b6

CARGOS_IDS = {
    "GEN 1": 1440494650728255538,
    "GEN 2": 1440494651147685949,
    "GEN 3": 1440494652166901822,
    "GEN X": 1477066277251186852,
    "APOIO HOST": 1161390337831477400
}

def gerar_id_pedido():
    return f"OBV-{''.join(random.choices(string.digits, k=4))}"

# --- MODAL DE RECUSA ---
class MotivoRecusaModal(discord.ui.Modal, title="✖️ Invalidação de Pagamento"):
    motivo = discord.ui.TextInput(
        label="Motivo da Rejeição",
        style=discord.TextStyle.paragraph,
        placeholder="Ex: Comprovativo ilegível...",
        required=True
    )

    def __init__(self, cliente, embed_log, id_pedido):
        super().__init__()
        self.cliente = cliente
        self.embed_log = embed_log
        self.id_pedido = id_pedido

    async def on_submit(self, interaction: discord.Interaction):
        self.embed_log.title = f"❌ PAGAMENTO REJEITADO [{self.id_pedido}]"
        self.embed_log.color = COR_ERRO
        self.embed_log.clear_fields() 
        self.embed_log.add_field(name="🚫 Motivo Oficial", value=self.motivo.value, inline=False)
        await interaction.response.edit_message(embed=self.embed_log, view=None)
        
        if self.cliente:
            try:
                emb = discord.Embed(title="⚠️ Atualização do Pedido", color=COR_ERRO)
                emb.description = f"Olá, o teu pedido **{self.id_pedido}** foi invalidado.\n\n**Motivo:** {self.motivo.value}"
                await self.cliente.send(embed=emb)
            except: pass

# --- FEEDBACK ---
class AvaliacaoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

    async def registrar_voto(self, interaction: discord.Interaction, n):
        canal = interaction.client.get_channel(ID_CANAL_LOGS_STAFF)
        if canal:
            await canal.send(f"🌟 **FEEDBACK:** {interaction.user.mention} deu **{n}/5 estrelas**!")
        await interaction.response.edit_message(content=f"✅ Feedback de {n} estrelas enviado! Obrigado.", view=None)
        self.stop()

    @discord.ui.button(label="1", style=discord.ButtonStyle.danger, emoji="⭐")
    async def s1(self, it, bt): await self.registrar_voto(it, 1)
    @discord.ui.button(label="2", style=discord.ButtonStyle.secondary, emoji="⭐")
    async def s2(self, it, bt): await self.registrar_voto(it, 2)
    @discord.ui.button(label="3", style=discord.ButtonStyle.secondary, emoji="⭐")
    async def s3(self, it, bt): await self.registrar_voto(it, 3)
    @discord.ui.button(label="4", style=discord.ButtonStyle.primary, emoji="⭐")
    async def s4(self, it, bt): await self.registrar_voto(it, 4)
    @discord.ui.button(label="5", style=discord.ButtonStyle.success, emoji="⭐")
    async def s5(self, it, bt): await self.registrar_voto(it, 5)

# --- PAINEL STAFF ---
class PainelAprovacao(discord.ui.View):
    def __init__(self, cliente_id, itens_comprados, id_pedido):
        super().__init__(timeout=None)
        self.cliente_id = cliente_id
        self.itens = itens_comprados
        self.id_pedido = id_pedido

    @discord.ui.button(label="Confirmar e Notificar", style=discord.ButtonStyle.success, emoji="✅")
    async def aprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        guild = interaction.guild
        cliente = guild.get_member(self.cliente_id)
        
        vips_cog = interaction.client.get_cog("Vips")
        log_entrega = []

        for item in self.itens:
            if "GEN" in item and vips_cog:
                nivel_num = item.replace("GEN ", "").strip()
                if nivel_num == "X": nivel_num = "4"
                try:
                    nova_data = await vips_cog.adicionar_vip_automatico(cliente, nivel_num, 30)
                    log_entrega.append(f"✅ {item} (Até {nova_data.strftime('%d/%m/%Y')})")
                except Exception as e:
                    log_entrega.append(f"❌ Erro no Registro VIP: {e}")
            elif item in CARGOS_IDS:
                cargo = guild.get_role(CARGOS_IDS[item])
                if cargo and cliente:
                    await cliente.add_roles(cargo)
                    log_entrega.append(f"✅ Cargo {item} entregue")
                else:
                    log_entrega.append(f"⚠️ Cargo {item} não encontrado")

        embed = interaction.message.embeds[0]
        embed.title = f"✅ PAGAMENTO CONFIRMADO [{self.id_pedido}]"
        embed.color = COR_SUCESSO
        embed.add_field(name="⚡ Resumo da Entrega", value="\n".join(log_entrega) if log_entrega else "Nada a entregar.", inline=False)
        embed.set_footer(text=f"Aprovado por: {interaction.user.display_name}")
        await interaction.edit_original_response(embed=embed, view=None)

        if cliente:
            try:
                emb_recibo = discord.Embed(title="🎊 Compra Validada!", color=COR_SUCESSO)
                emb_recibo.description = (
                    f"Olá {cliente.mention}, o teu pedido **{self.id_pedido}** foi aprovado.\n\n"
                    f"**Itens Ativados:**\n`{', '.join(self.itens)}`\n\n"
                    "**Dica:** Usa `/vip` para ver o teu tempo restante e itens pendentes!"
                )
                await cliente.send(embed=emb_recibo)
            except: pass

    @discord.ui.button(label="Recusar", style=discord.ButtonStyle.danger, emoji="✖️")
    async def recusar(self, interaction: discord.Interaction, button: discord.ui.Button):
        cliente = interaction.guild.get_member(self.cliente_id)
        await interaction.response.send_modal(MotivoRecusaModal(cliente, interaction.message.embeds[0], self.id_pedido))

# --- CARRINHO ---
class ConfirmacaoCompra(discord.ui.View):
    def __init__(self, rs, eur, itens, alvo_id):
        super().__init__(timeout=600)
        self.rs, self.eur, self.itens = rs, eur, itens
        self.alvo_id = alvo_id
        self.id_pedido = gerar_id_pedido()

    @discord.ui.button(label="🔑 Ver Chave PIX", style=discord.ButtonStyle.secondary)
    async def pix(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"**Chave PIX:** `theoblivionsmp.chave@gmail.com` \n**ID Pedido:** `{self.id_pedido}`\n\n*Nota: Deves incluir o ID do pedido na descrição do pagamento.*", ephemeral=True)

    @discord.ui.button(label="📤 Enviar Comprovativo", style=discord.ButtonStyle.success, emoji="📎")
    async def upload_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("📸 **Envia a imagem do comprovativo no chat agora.**", ephemeral=True)
        
        def check(m): return m.author == interaction.user and m.attachments
        try:
            msg = await interaction.client.wait_for("message", check=check, timeout=300)
            canal_logs = interaction.client.get_channel(ID_CANAL_LOGS_STAFF)
            if not canal_logs:
                return await interaction.followup.send("❌ Erro: Canal de logs não encontrado.", ephemeral=True)

            img_name = f"{self.id_pedido}.png"
            img_data = await msg.attachments[0].read()
            arquivo = discord.File(io.BytesIO(img_data), filename=img_name)

            log_emb = discord.Embed(title=f"🔔 NOVO PEDIDO [{self.id_pedido}]", color=COR_ALERTA)
            log_emb.add_field(name="👤 Pagante", value=f"{interaction.user.mention} ({interaction.user.id})")
            log_emb.add_field(name="🎯 Destinatário", value=f"<@{self.alvo_id}>")
            log_emb.add_field(name="💰 Valor Total", value=f"**R$ {self.rs:.2f} | {self.eur:.2f}€**")
            log_emb.add_field(name="📦 Itens Escolhidos", value=f"```\n{', '.join(self.itens)}\n```", inline=False)
            log_emb.set_image(url=f"attachment://{img_name}")

            await canal_logs.send(embed=log_emb, file=arquivo, view=PainelAprovacao(self.alvo_id, self.itens, self.id_pedido))
            
            try: await msg.delete()
            except: pass

            final_emb = discord.Embed(title="🚀 Pedido Enviado!", color=COR_SUCESSO, description=f"O teu pedido **{self.id_pedido}** está em análise.\nReceberás uma DM assim que for aprovado.")
            await interaction.followup.send(embed=final_emb, view=AvaliacaoView(), ephemeral=True)

        except asyncio.TimeoutError:
            await interaction.followup.send("❌ Tempo esgotado. Tenta novamente.", ephemeral=True)

# --- COG LOJA ---
class SistemasUnificados(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="loja", description="Abre o Mercado Negro.")
    @app_commands.describe(jogador="O jogador que vai receber os itens (Vazio = Tu)")
    async def loja(self, interaction: discord.Interaction, jogador: discord.Member = None):
        alvo = jogador or interaction.user
        
        embed = discord.Embed(title="◣ MERCADO NEGRO: OBLIVION ◥", color=0x2b2d31)
        embed.description = (
            f"Olá {interaction.user.mention}, seleciona o que desejas comprar.\n"
            f"🎯 **Itens para:** {alvo.mention}\n\n"
            "⚠️ **Atenção:** VIPs são acumulativos no tempo!"
        )
        embed.set_image(url="https://media.tenor.com/C7YIu5_rY3IAAAAC/marvel-rivals-adam-warlock.gif")
        
        select = discord.ui.Select(placeholder="🛒 Adicionar ao carrinho...", options=[
            discord.SelectOption(label="🛡️ Apoio Host", description="R$ 10,00 | 1.50€", value="item|APOIO HOST|10|1.5"),
            discord.SelectOption(label="🧬 GEN 1", description="R$ 12,00 | 2.00€", value="vip|GEN 1|12|2"),
            discord.SelectOption(label="🌀 GEN 2", description="R$ 25,00 | 4.00€", value="vip|GEN 2|25|4"),
            discord.SelectOption(label="🌌 GEN 3", description="R$ 50,00 | 8.00€", value="vip|GEN 3|50|8"),
            discord.SelectOption(label="☣️ GEN X", description="R$ 90,00 | 15.00€", value="vip|GEN X|90|15"),
            discord.SelectOption(label="❤️ Vida Extra", description="R$ 10,00 | 1.50€", value="item|Vida Adulto|10|1.5"),
            discord.SelectOption(label="📜 Reset de Lore", description="R$ 20,00 | 3.50€", value="item|Reset Lore|20|3.5"),
        ], max_values=5)

        async def callback(inter: discord.Interaction):
            vips, outros = [], []
            for v in select.values:
                tipo, nome, rs, eur = v.split('|')
                if tipo == "vip": vips.append({"n": nome, "r": float(rs), "e": float(eur)})
                else: outros.append({"n": nome, "r": float(rs), "e": float(eur)})
            
            final_nomes, tr, te = [], 0.0, 0.0
            if vips:
                v_top = max(vips, key=lambda x: x['r'])
                final_nomes.append(v_top['n'])
                tr += v_top['r']
                te += v_top['e']
            
            for i in outros:
                final_nomes.append(i['n'])
                tr += i['r']
                te += i['e']

            res_emb = discord.Embed(title="🛒 REVISÃO DO CARRINHO", color=COR_PRINCIPAL)
            res_emb.description = f"**Destinatário:** {alvo.mention}\n**Itens:** `{', '.join(final_nomes)}`"
            res_emb.add_field(name="Total a Pagar", value=f"**R$ {tr:.2f}** ou **{te:.2f}€**")
            
            await inter.response.send_message(embed=res_emb, view=ConfirmacaoCompra(tr, te, final_nomes, alvo.id), ephemeral=True)

        select.callback = callback
        view = discord.ui.View()
        view.add_item(select)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(SistemasUnificados(bot))