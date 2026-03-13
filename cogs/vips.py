import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
from datetime import datetime, timedelta

# --- VIEWS PARA GERIR ENTREGAS ---

class EntregaButton(discord.ui.Button):
    def __init__(self, label, item_key, current_state):
        style = discord.ButtonStyle.success if current_state else discord.ButtonStyle.danger
        super().__init__(label=label, style=style)
        self.item_key = item_key

    async def callback(self, interaction: discord.Interaction):
        view: EntregaView = self.view
        estado_atual = view.entregas.get(self.item_key, False)
        view.entregas[self.item_key] = not estado_atual
        
        vips = view.cog.carregar_vips()
        if view.target_id in vips:
            vips[view.target_id]["checklist"] = view.entregas
            view.cog.guardar_vips(vips)
        
        new_view = EntregaView(view.cog, view.target_id, view.entregas, view.nivel)
        await interaction.response.edit_message(content=f"⚙️ A gerir entregas de <@{view.target_id}>:", view=new_view)

class EntregaView(discord.ui.View):
    def __init__(self, cog, target_id, entregas, nivel):
        super().__init__(timeout=None)
        self.cog = cog
        self.target_id = target_id
        self.entregas = entregas
        self.nivel = nivel

        itens_disponiveis = {
            "1": [("🎫 Ticket", "ticket"), ("📦 Kit Alpha", "bit"), ("🎨 Tag", "tag")],
            "2": [("❤️ Coração", "vida"), ("⚔️ Item Mod", "mod"), ("💎 Recursos", "res"), ("🎭 Cosméticos", "cos")],
            "3": [("🔱 Lendário", "lend"), ("📜 Lore", "lore"), ("💍 Curios", "curio"), ("🦁 Spawner", "spawn")],
            "4": [("🏛️ Monumento", "monu"), ("🧿 Amuleto", "amul"), ("📜 Legado", "legado")]
        }

        for n in range(1, int(nivel) + 1):
            if str(n) in itens_disponiveis:
                for label, key in itens_disponiveis[str(n)]:
                    state = self.entregas.get(key, False)
                    self.add_item(EntregaButton(label, key, state))

# --- COG PRINCIPAL ---

class Vips(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vips_file = 'vips.json'
        self.canal_logs_id = 1481124593971236947 
        if not self.verificar_vips.is_running():
            self.verificar_vips.start()

    def carregar_vips(self):
        try:
            with open(self.vips_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def guardar_vips(self, dados):
        with open(self.vips_file, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)

    CARGOS_VIP = {
        "1": {"nome": "🧬 ﹒ Gen 1", "id": 1440494650728255538, "cor": 0x3498db},
        "2": {"nome": "🌀 ﹒ Gen 2", "id": 1440494651147685949, "cor": 0x9b59b6},
        "3": {"nome": "🌌 ﹒ Gen 3", "id": 1440494652166901822, "cor": 0xf1c40f},
        "4": {"nome": "☣️ ﹒ Gen X", "id": 1477066277251186852, "cor": 0xe74c3c}
    }

    MAPA_ENTREGAS = {
        "ticket": "🎫 Prioridade em Tickets", "kit": "📦 Kit Alpha", "tag": "🎨 Tag Personalizada",
        "vida": "❤️ +1 Coração", "mod": "⚔️ Item Modificado", "res": "💎 4 Packs Recursos", "cos": "🎭 Cosméticos",
        "lend": "🔱 Item Lendário", "lore": "📜 Itens de Lore", "curio": "💍 Slot Curios", "spawn": "🦁 Spawner/Pets",
        "monu": "🏛️ Monumento Lore", "amul": "🧿 Amuleto Buff", "legado": "📜 Nome na História"
    }

    @app_commands.command(name="darvip", description="[STAFF] Atribui ou aumenta o VIP de um jogador.")
    @app_commands.default_permissions(administrator=True)
    async def darvip(self, interaction: discord.Interaction, nivel: str, user: discord.Member, dias: int = 30):
        if nivel not in self.CARGOS_VIP:
            return await interaction.response.send_message("❌ Nível inválido!", ephemeral=True)
        
        vips = self.carregar_vips()
        uid = str(user.id)
        agora = datetime.now()

        if uid in vips:
            try:
                data_atual = datetime.strptime(vips[uid]["data_expira"], "%Y-%m-%d %H:%M:%S")
                nova_data = data_atual + timedelta(days=dias)
            except: nova_data = agora + timedelta(days=dias)
        else:
            nova_data = agora + timedelta(days=dias)

        vips[uid] = {
            "nivel": nivel,
            "nome_vip": self.CARGOS_VIP[nivel]["nome"],
            "data_expira": nova_data.strftime("%Y-%m-%d %H:%M:%S"),
            "estado": "ATIVO",
            "checklist": vips.get(uid, {}).get("checklist", {})
        }
        
        self.guardar_vips(vips)
        cargo = user.guild.get_role(self.CARGOS_VIP[nivel]["id"])
        if cargo: await user.add_roles(cargo)
        await interaction.response.send_message(f"✅ VIP de {user.mention} atualizado até {nova_data.strftime('%d/%m/%Y')}")

    @app_commands.command(name="setestado", description="[STAFF] Muda o estado do VIP (ATIVO, CONGELADO, SUSPENSO).")
    @app_commands.choices(estado=[
        app_commands.Choice(name="ATIVO", value="ATIVO"),
        app_commands.Choice(name="CONGELADO", value="CONGELADO"),
        app_commands.Choice(name="SUSPENSO", value="SUSPENSO")
    ])
    @app_commands.default_permissions(manage_messages=True)
    async def setestado(self, interaction: discord.Interaction, user: discord.Member, estado: str):
        vips = self.carregar_vips()
        uid = str(user.id)
        if uid not in vips: return await interaction.response.send_message("❌ Jogador sem VIP.", ephemeral=True)
        
        vips[uid]["estado"] = estado
        self.guardar_vips(vips)
        await interaction.response.send_message(f"✅ Estado de {user.mention} alterado para **{estado}**.")

    @app_commands.command(name="removervip", description="[STAFF] Remove dias ou deleta o VIP.")
    @app_commands.describe(dias="Quantos dias remover (use 999 para deletar tudo)")
    @app_commands.default_permissions(administrator=True)
    async def removervip(self, interaction: discord.Interaction, user: discord.Member, dias: int):
        vips = self.carregar_vips()
        uid = str(user.id)
        if uid not in vips: return await interaction.response.send_message("❌ Jogador não tem VIP.", ephemeral=True)

        if dias >= 999:
            del vips[uid]
            msg = f"🚫 VIP de {user.mention} foi removido completamente."
        else:
            data_atual = datetime.strptime(vips[uid]["data_expira"], "%Y-%m-%d %H:%M:%S")
            nova_data = data_atual - timedelta(days=dias)
            vips[uid]["data_expira"] = nova_data.strftime("%Y-%m-%d %H:%M:%S")
            msg = f"⏳ Removidos {dias} dias de {user.mention}. Nova expiração: `{vips[uid]['data_expira']}`"

        self.guardar_vips(vips)
        await interaction.response.send_message(msg)

    @app_commands.command(name="vipsativos", description="[STAFF] Lista todos os jogadores com VIP ativo.")
    @app_commands.default_permissions(manage_messages=True)
    async def vipsativos(self, interaction: discord.Interaction):
        vips = self.carregar_vips()
        if not vips: return await interaction.response.send_message("Nenhum VIP registado.", ephemeral=True)
        
        emb = discord.Embed(title="📋 Lista de VIPs Ativos", color=0x2b2d31)
        for uid, d in vips.items():
            est = d.get("estado", "ATIVO")
            emb.add_field(name=f"👤 {uid}", value=f"**User:** <@{uid}>\n**Plano:** `{d['nome_vip']}`\n**Estado:** `{est}`\n**Expira:** `{d['data_expira']}`", inline=False)
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @app_commands.command(name="vip", description="Vê o teu VIP e o que falta receber.")
    async def vip(self, interaction: discord.Interaction):
        vips = self.carregar_vips()
        uid = str(interaction.user.id)
        if uid not in vips: return await interaction.response.send_message("❌ Não tens VIP!", ephemeral=True)

        d = vips[uid]
        nivel = d.get("nivel", "1")
        checklist = d.get("checklist", {})
        estado = d.get("estado", "ATIVO")
        
        try:
            data_fim = datetime.strptime(d["data_expira"], "%Y-%m-%d %H:%M:%S")
            restante = (data_fim - datetime.now()).days
        except: restante = "?"
        
        emb = discord.Embed(title=f"💎 STATUS: {d['nome_vip']}", color=self.CARGOS_VIP[nivel]["cor"])
        emb.add_field(name="⏳ Dias", value=f"`{restante}d`", inline=True)
        emb.add_field(name="🛡️ Estado", value=f"`{estado}`", inline=True)
        
        txt = ""
        niveis_map = {"1": ["ticket", "kit", "tag"], "2": ["vida", "mod", "res", "cos"], "3": ["lend", "lore", "curio", "spawn"], "4": ["monu", "amul", "legado"]}
        for n in range(1, int(nivel) + 1):
            for k in niveis_map.get(str(n), []):
                status = "✅" if checklist.get(k) else "❌"
                txt += f"{status} {self.MAPA_ENTREGAS.get(k, k)}\n"

        emb.add_field(name="📦 Entregas", value=txt or "Nada pendente.", inline=False)
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @app_commands.command(name="vipinfo", description="[STAFF] Gerir entregas de um jogador.")
    @app_commands.default_permissions(manage_messages=True)
    async def vipinfo(self, interaction: discord.Interaction, user: discord.Member):
        vips = self.carregar_vips()
        if str(user.id) not in vips: return await interaction.response.send_message("❌ Sem VIP.", ephemeral=True)
        d = vips[str(user.id)]
        view = EntregaView(self, str(user.id), d.get("checklist", {}), d.get("nivel", "1"))
        await interaction.response.send_message(f"⚙️ Gerir {user.display_name}:", view=view, ephemeral=True)

    async def adicionar_vip_automatico(self, user: discord.Member, nivel: str, dias: int):
        vips = self.carregar_vips()
        uid = str(user.id)
        agora = datetime.now()

        if uid in vips:
            try:
                data_atual = datetime.strptime(vips[uid]["data_expira"], "%Y-%m-%d %H:%M:%S")
                base_data = data_atual if data_atual > agora else agora
                nova_data = base_data + timedelta(days=dias)
            except: 
                nova_data = agora + timedelta(days=dias)
        else:
            nova_data = agora + timedelta(days=dias)

        vips[uid] = {
            "nivel": nivel,
            "nome_vip": self.CARGOS_VIP[nivel]["nome"],
            "data_expira": nova_data.strftime("%Y-%m-%d %H:%M:%S"),
            "estado": "ATIVO",
            "checklist": vips.get(uid, {}).get("checklist", {})
        }
        
        self.guardar_vips(vips)
        cargo_id = self.CARGOS_VIP[nivel]["id"]
        cargo = user.guild.get_role(cargo_id)
        if cargo: await user.add_roles(cargo)
        return nova_data

    @tasks.loop(hours=24)
    async def verificar_vips(self):
        vips = self.carregar_vips()
        agora = datetime.now()
        alterou = False
        for uid, dados in list(vips.items()):
            # Se estiver CONGELADO, não remove o VIP por tempo
            if dados.get("estado") == "CONGELADO":
                continue
                
            try:
                data_exp = datetime.strptime(dados["data_expira"], "%Y-%m-%d %H:%M:%S")
                if agora > data_exp:
                    del vips[uid]
                    alterou = True
            except: pass
        if alterou: self.guardar_vips(vips)

async def setup(bot):
    await bot.add_cog(Vips(bot))