import asyncio
import logging
from pathlib import Path

import discord
from discord.ext import commands

from src.config import Config
from src.config.targets import TargetManager

logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
target_manager = TargetManager()


@bot.event
async def on_ready():
    logger.info(f"Discord bot logged in as {bot.user.name}")
    logger.info(f"Guild ID: {Config.DISCORD_GUILD_ID}")


@bot.command(name='start')
async def start(ctx: commands.Context):
    """Affiche le menu de démarrage pour les nouveaux clients."""
    embed = discord.Embed(
        title="🐀 GnawLead - Système de Leads Automatisé",
        description="Bienvenue dans le nid. Utilisez les commandes ci-dessous pour gérer vos campagnes.",
        color=discord.Color.green()
    )
    embed.add_field(name="!generate <mots-clés>", value="Lance un scraping sur Reddit/Twitter", inline=False)
    embed.add_field(name="!status", value="Vérifie l'état du pipeline en cours", inline=False)
    embed.add_field(name="!export", value="Télécharge le dernier CSV de leads chauds", inline=False)
    await ctx.send(embed=embed)


@bot.command(name='generate')
@commands.has_any_role("admin", "owner")
async def generate(ctx: commands.Context, *, keywords: str):
    """Déclenche le pipeline de scraping (rôle admin requis)."""
    keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
    if not keyword_list:
        await ctx.send("❌ Mots-clés invalides. Usage: !generate mot1,mot2")
        return

    msg = await ctx.send(f"🐀 Queue qui frétille. Lancement de la traque pour : `{keywords}`...")
    try:
        # Import local pour éviter la dépendance circulaire
        from src.main import run_pipeline
        leads = await run_pipeline(keywords=keyword_list)
        await msg.edit(content=f"✅ Traque terminée. {len(leads)} leads chauds enrichis.")
    except Exception as e:
        logger.exception("Pipeline failed")
        await msg.edit(content=f"❌ Échec du pipeline: {e}")


@bot.command(name='status')
async def status(ctx: commands.Context):
    """État rapide du nid."""
    campaigns = target_manager.list_campaigns()
    active = sum(
        1 for c in campaigns
        if target_manager.targets.get('campaigns', {}).get(c, {}).get('active')
    )
    exports = sorted(Path(Config.EXPORTS_DIR).glob("*.csv"), key=lambda p: p.stat().st_mtime)
    last = exports[-1].name if exports else "aucun"
    await ctx.send(f"📊 Campagnes: {active}/{len(campaigns)} actives | Dernier export: `{last}`")


@bot.command(name='export')
async def export_cmd(ctx: commands.Context):
    """Envoie le dernier CSV généré."""
    exports = sorted(Path(Config.EXPORTS_DIR).glob("*.csv"), key=lambda p: p.stat().st_mtime)
    if not exports:
        await ctx.send("❌ Aucun export disponible. Lance !generate d'abord.")
        return
    await ctx.send(file=discord.File(str(exports[-1])))


@bot.command(name='addcampaign')
@commands.has_any_role("admin", "owner")
async def add_campaign(ctx: commands.Context, name: str, *, keywords: str):
    """Ajoute une campagne. Usage: !addcampaign nom mot1,mot2,mot3"""
    keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
    target_manager.add_campaign(name, keyword_list, ['reddit', 'twitter'], limit=50)
    await ctx.send(f"✅ Campagne `{name}` ajoutée avec {len(keyword_list)} mots-clés.")


@bot.command(name='togglecampaign')
@commands.has_any_role("admin", "owner")
async def toggle_campaign(ctx: commands.Context, name: str):
    """Active/désactive une campagne."""
    target_manager.toggle_campaign(name)
    await ctx.send(f"✅ Campagne `{name}` basculée.")


@bot.command(name='listcampaigns')
async def list_campaigns(ctx: commands.Context):
    """Liste toutes les campagnes."""
    campaigns = target_manager.list_campaigns()
    if not campaigns:
        await ctx.send("❌ Aucune campagne configurée.")
        return

    embed = discord.Embed(title="📋 Campagnes de Traque", color=discord.Color.blue())
    for name in campaigns:
        campaign = target_manager.targets.get('campaigns', {}).get(name, {})
        state = "✅" if campaign.get('active') else "❌"
        embed.add_field(
            name=f"{state} {name}",
            value=f"{len(campaign.get('keywords', []))} keywords | {', '.join(campaign.get('platforms', []))}",
            inline=False
        )
    await ctx.send(embed=embed)


@generate.error
@add_campaign.error
@toggle_campaign.error
async def command_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send("⛔ Rôle `admin` requis pour cette commande.")
    else:
        logger.exception(f"Erreur commande: {error}")
        await ctx.send("❌ Erreur interne, check les logs.")


def run_bot():
    if not Config.DISCORD_BOT_TOKEN:
        raise RuntimeError("DISCORD_BOT_TOKEN manquant dans .env")
    bot.run(Config.DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_bot()
