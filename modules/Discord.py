import cv2
import logging

from discord_webhook import DiscordWebhook, DiscordEmbed
from modules.Inputs import WaitFrames
from modules.mmf.Screenshot import GetScreenshot
from modules.Config import GetConfig

log = logging.getLogger(__name__)
config = GetConfig()

def DiscordShinyPing(pokemon: object, stats: object):
    try:
        log.info("Sending Discord ping...")

        # Add @ ping depending on user's config
        content = ""
        if config["discord"]["shiny_ping"]:
            if config["discord"]["ping_id"] and config["discord"]["ping_mode"] == "role":
                content = f"<@&{config['discord']['ping_id']}>"
            elif config["discord"]["ping_mode"] == "user":
                content = f"<@{config['discord']['ping_id']}>"

        # Create Discord webhook
        webhook = DiscordWebhook(url=config["discord"]["webhook_url"], content=content)
        embed = DiscordEmbed(title='Shiny encountered!',
                             description=f"{pokemon['name']} at {pokemon['metLocationName']}",
                             color='ffd242')
        embed.set_footer(text=f"PokeBot ID: {config['bot_instance_id']}")
        embed.set_timestamp()
        embed.add_embed_field(name='Shiny Value', value=f"{pokemon['shinyValue']:,}")
        embed.add_embed_field(name='Nature', value=f"{pokemon['nature']}")

        # Basic IV list
        if config["discord"]["iv_format"] == "basic" or config["discord"]["iv_format"] == "":
            embed.add_embed_field(name='IVs',
                                  value=f"HP: {pokemon['hpIV']} | "
                                        f"ATK: {pokemon['attackIV']} | "
                                        f"DEF: {pokemon['defenseIV']} | "
                                        f"SPATK: {pokemon['spAttackIV']} | "
                                        f"SPDEF: {pokemon['spDefenseIV']} | "
                                        f"SPE: {pokemon['speedIV']}",
                                  inline=False)

        # Formatted IV list
        if config["discord"]["iv_format"] == "formatted":
            embed.add_embed_field(name='IVs', value=f"""
            `╔═══╤═══╤═══╤═══╤═══╤═══╗`
            `║HP │ATK│DEF│SPA│SPD│SPE║`
            `╠═══╪═══╪═══╪═══╪═══╪═══╣`
            `║{pokemon['hpIV']:^3}│{pokemon['attackIV']:^3}│{pokemon['defenseIV']:^3}│{pokemon['spAttackIV']:^3}│{pokemon['spDefenseIV']:^3}│{pokemon['speedIV']:^3}║`
            `╚═══╧═══╧═══╧═══╧═══╧═══╝`""", inline=False)
        embed.add_embed_field(name='Species Phase Encounters',
                              value=f"{stats['pokemon'][pokemon['name']]['phase_encounters']}")
        embed.add_embed_field(name='All Phase Encounters', value=f"{stats['totals']['phase_encounters']}")

        # Add shiny sprite thumbnail to embed
        with open(f"modules/interface/sprites/pokemon/shiny/{pokemon['name']}.png", "rb") as shiny:
            webhook.add_file(file=shiny.read(), filename='shiny.png')
        embed.set_thumbnail(url='attachment://shiny.png')

        # Wait 300 frames for Pokemon to appear on-screen, take screenshot
        WaitFrames(300)
        screenshot = cv2.imencode('.png', GetScreenshot())[1]

        # Attach file to embed
        webhook.add_file(file=screenshot, filename='screenshot.png')
        embed.set_image(url='attachment://screenshot.png')

        # Execute webhook
        webhook.add_embed(embed)
        webhook.execute()
    except Exception as e:
        log.exception(str(e))
        pass
