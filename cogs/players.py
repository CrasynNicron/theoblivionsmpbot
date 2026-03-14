import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import math
from datetime import datetime

# --- CONFIGS ---
COR_PRINCIPAL = 0x9b59b6
COR_VIP = 0xf1c40f
ID_CARGO_PLAYER = 1337596948940722306

BADGES_AUTOMATICAS = {
    "⚖️": 1154890661523365938, # Staff
    "✨": 1163902575637168158, # Booster
    "💸": 1161390337831477400  # Host
}

DESC_BADGES_FIXAS = {
    "⚖️": "Membro da Equipa de Staff do Oblivion.",
    "✨": "Apoiante do servidor (Server Booster).",
    "💸": "Doador ou Host do projeto.",
    "👑": "Lenda viva do SMP.",
    "⭐": "Ranking de Prestígio (Reset de Nível)."
}

CARGOS_VIPS = {
    "GEN 1": 1440494650728255538,
    "GEN 2": 1440494651147685949,
    "GEN 3": 1440494652166901822,
    "GEN X": 1477066277251186852
}

def get_rank_name(nivel):
    if nivel < 10: return "🌱 Recruta"
    if nivel < 25: return "🏹 Sobrevivente"
    if nivel < 50: return "🛡️ Veterano"
    return "👑 Lenda do Oblivion"

# --- MODAIS E VIEWS ---

class EditarPerfilModal(discord.ui.Modal, title="🎨 Personalizar Personagem"):
    bio = discord.ui.TextInput(label="Bio do Personagem", style=discord.TextStyle.paragraph, max_length=150, required=True)
    img_perfil = discord.ui.TextInput(label="URL da Imagem de Perfil (VIP)", placeholder="Link PNG/JPG...", required=False)

    def __init__(self, cog, p_data, eh_vip):
        super().__init__()
        self.cog, self.p_data, self.eh_vip = cog, p_data, eh_vip
        self.bio.default = p_data.get("bio", "Um simples sobrevivente.")
        if eh_vip: self.img_perfil.default = p_data.get("img_custom", "")

    async def on_submit(self, interaction: discord.Interaction):
        uid = str(interaction.user.id)
        if uid in self.cog.dados:
            self.cog.dados[uid]["bio"] = self.bio.value
            if self.eh_vip: self.cog.dados[uid]["img_custom"] = self.img_perfil.value
            self.cog.guardar_dados()
            await interaction.response.send_message("✨ Perfil atualizado!", ephemeral=True)

class PerfilView(discord.ui.View):
    def __init__(self, cog, p_data, alvo, eh_vip):
        super().__init__(timeout=60)
        self.cog, self.p_data, self.alvo, self.eh_vip = cog, p_data, alvo, eh_vip

    @discord.ui.button(label="Editar Perfil", style=discord.ButtonStyle.secondary, emoji="⚙️")
    async def editar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.alvo.id:
            return await interaction.response.send_message("❌ Só podes editar o teu perfil!", ephemeral=True)
        await interaction.response.send_modal(EditarPerfilModal(self.cog, self.p_data, self.eh_vip))

class TopPaginationView(discord.ui.View):
    def __init__(self, cog, sorted_list, user_pos, total_count, per_page=10):
        super().__init__(timeout=60)
        self.cog, self.sorted_list, self.user_pos, self.total_count, self.per_page = cog, sorted_list, user_pos, total_count, per_page
        self.current_page, self.max_pages = 0, math.ceil(len(sorted_list) / per_page)

    def create_embed(self):
        start = self.current_page * self.per_page
        slice_data = self.sorted_list[start:start+self.per_page]
        lb = ""
        for i, (uid, data) in enumerate(slice_data, start + 1):
            user = self.cog.bot.get_user(int(uid))
            nome = user.display_name if user else f"Sobrevivente ({uid})"
            prestigio = f" [S{data.get('prestigio', 0)}]" if data.get('prestigio', 0) > 0 else ""
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"**#{i}**"
            lb += f"{medal} **{nome}**{prestigio} — `LVL {data.get('nivel', 1)}`\n└ `{int(data.get('xp', 0))}/{data.get('nivel', 1)*500} XP`\n\n"
        
        embed = discord.Embed(title="🏆 RANKING OBLIVION SMP", description=lb or "Sem dados.", color=COR_PRINCIPAL)
        embed.set_footer(text=f"Página {self.current_page+1}/{self.max_pages} • Pos: #{self.user_pos}")
        return embed

    @discord.ui.button(label="Anterior", style=discord.ButtonStyle.gray, emoji="⬅️")
    async def prev(self, it: discord.Interaction, b: discord.ui.Button):
        if self.current_page > 0: self.current_page -= 1; await it.response.edit_message(embed=self.create_embed())

    @discord.ui.button(label="Próximo", style=discord.ButtonStyle.gray, emoji="➡️")
    async def next(self, it: discord.Interaction, b: discord.ui.Button):
        if self.current_page < self.max_pages - 1: self.current_page += 1; await it.response.edit_message(embed=self.create_embed())

# --- COG PRINCIPAL ---
class Players(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "players.json"
        self.badges_path = "badges_info.json"
        self.dados = self.carregar_dados(self.db_path)
        self.badges_desc = self.carregar_dados(self.badges_path)

    def carregar_dados(self, path):
        if not os.path.exists(path): return {}
        try:
            with open(path, "r", encoding="utf-8") as f: return json.load(f)
        except: return {}

    def guardar_dados(self):
        with open(self.db_path, "w", encoding="utf-8") as f: json.dump(self.dados, f, indent=4)
        with open(self.badges_path, "w", encoding="utf-8") as f: json.dump(self.badges_desc, f, indent=4)

    def get_player(self, user_id):
        uid = str(user_id)
        if uid not in self.dados:
            self.dados[uid] = {"vidas": 6, "kills": 0, "deaths": 0, "nivel": 1, "xp": 0, "bio": "Um simples sobrevivente.", "img_custom": None, "badges": [], "streak": 0, "prestigio": 0}
            self.guardar_dados()
        return self.dados[uid]

    def check_vip_status(self, member):
        roles_ids = [r.id for r in member.roles]
        is_gen_vip = any(rid in CARGOS_VIPS.values() for rid in roles_ids)
        is_badge_vip = any(rid in BADGES_AUTOMATICAS.values() for rid in roles_ids)
        is_admin = member.guild_permissions.administrator
        eh_especial = is_gen_vip or is_badge_vip or is_admin
        tem_vida_extra = any(rid in [CARGOS_VIPS["GEN 2"], CARGOS_VIPS["GEN 3"], CARGOS_VIPS["GEN X"]] for rid in roles_ids)
        return eh_especial, (2 if eh_especial else 1), (1 if tem_vida_extra else 0)

    @app_commands.command(name="playerinfo", description="Exibe o teu perfil completo.")
    async def playerinfo(self, it: discord.Interaction, jogador: discord.Member = None):
        alvo = jogador or it.user
        if ID_CARGO_PLAYER not in [r.id for r in alvo.roles]:
            return await it.response.send_message("❌ Não é um Jogador.", ephemeral=True)

        self.dados = self.carregar_dados(self.db_path)
        p = self.get_player(alvo.id)
        eh_vip, mult_base, extra_v = self.check_vip_status(alvo)
        v_max = 6 + extra_v
        
        mult_final = float(mult_base) + (p.get("prestigio", 0) * 0.5)
        boost_status = f"{mult_final}x"
        
        agora = datetime.now()
        if "booster_ate" in p:
            if agora < datetime.fromisoformat(p["booster_ate"]):
                mult_final *= 2
                boost_status = f"🔥 {mult_final}x (Booster Ativo)"

        xp_at, xp_nx = p.get("xp", 0), p.get("nivel", 1) * 500
        porcentagem = int((xp_at / xp_nx) * 100) if xp_nx > 0 else 0
        barra = "🟦" * int(porcentagem / 10) + "⬜" * (10 - int(porcentagem / 10))

        roles_ids = [r.id for r in alvo.roles]
        badges_finais = [e for e, rid in BADGES_AUTOMATICAS.items() if rid in roles_ids] + p.get("badges", [])
        if p.get("prestigio", 0) > 0: badges_finais.append("⭐")
        
        embed = discord.Embed(color=COR_VIP if eh_vip else COR_PRINCIPAL)
        embed.set_author(name=f"PERFIL: {alvo.display_name.upper()}", icon_url=alvo.display_avatar.url)
        
        prestigio_txt = f" | ⭐ **S{p.get('prestigio', 0)}**" if p.get("prestigio", 0) > 0 else ""
        
        embed.description = (
            f"### 👤 {alvo.mention}\n"
            f"🎖️ **Rank:** `{get_rank_name(p['nivel'])}`{prestigio_txt}\n"
            f"🏅 **Badges:** {' '.join(badges_finais) or '—'}\n"
            f"📝 *{p['bio']}*\n\n"
            f"❤️ **Vitalidade:** ` {p['vidas']} / {v_max} `\n" + ("❤️" * p["vidas"] + "🖤" * (v_max - p["vidas"]))
        )
        
        embed.add_field(name="📊 Experiência", value=f"**Lvl {p['nivel']}** (`{int(xp_at)}/{xp_nx}`)\n{barra} `{porcentagem}%`", inline=False)
        embed.add_field(name="⚡ Multiplicador", value=f"`{boost_status}`", inline=True)
        embed.add_field(name="⚔️ Combate", value=f"K: `{p['kills']}` | D: `{p['deaths']}`", inline=True)
        
        img_url = p.get("img_custom") if (eh_vip and p.get("img_custom")) else alvo.display_avatar.url
        embed.set_thumbnail(url=img_url)
        await it.response.send_message(embed=embed, view=PerfilView(self, p, alvo, eh_vip), ephemeral=True)

    @app_commands.command(name="top", description="Ranking global.")
    async def top(self, it: discord.Interaction):
        self.dados = self.carregar_dados(self.db_path)
        if not self.dados: return await it.response.send_message("Vazio.", ephemeral=True)
        sort = sorted(self.dados.items(), key=lambda x: (x[1].get('prestigio', 0), x[1].get('nivel', 1), x[1].get('xp', 0)), reverse=True)
        pos = next((i for i, (u, _) in enumerate(sort, 1) if u == str(it.user.id)), "N/A")
        await it.response.send_message(embed=TopPaginationView(self, sort, pos, len(sort)).create_embed(), view=TopPaginationView(self, sort, pos, len(sort)))

async def setup(bot):
    await bot.add_cog(Players(bot))