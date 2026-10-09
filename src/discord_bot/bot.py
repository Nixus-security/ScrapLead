import discord
from discord.ext import commands
from src.config import Config
from src.config.targets import TargetManager
import logging

logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

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
async def generate(ctx: commands.Context, *, keywords: str):
    """Déclenche le pipeline de scraping."""
    await ctx.send(f"🐀 Queue qui frétille. Lancement de la traque pour : `{keywords}`...")
    # Ici, tu appelleras asyncio.create_task(run_pipeline(keywords.split(',')))
    # et tu notifieras le channel quand c'est fini.
    await ctx.send("✅ Traque terminée. Les leads chauds sont en cours d'enrichissement.")

def run_bot():
    bot.run(Config.DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    run_bot()

    target_manager = TargetManager()

@bot.command(name='addcampaign')
async def add_campaign(ctx: commands.Context, name: str, *, keywords: str):
    """Ajoute une nouvelle campagne. Usage: !addcampaign nom mot1,mot2,mot3"""
    keyword_list = [k.strip() for k in keywords.split(',')]
    target_manager.add_campaign(name, keyword_list, ['reddit', 'twitter'], limit=50)
    await ctx.send(f"✅ Campagne `{name}` ajoutée avec {len(keyword_list)} mots-clés.")

@bot.command(name='togglecampaign')
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
        campaign = target_manager.get_campaign(name)
        status = "✅" if campaign.get('active') else "❌"
        embed.add_field(
            name=f"{status} {name}",
            value=f"{len(campaign.get('keywords', []))} keywords | {', '.join(campaign.get('platforms', []))}",
            inline=False
        )
    await ctx.send(embed=embed)