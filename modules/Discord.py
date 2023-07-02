import cv2
import logging

from discord_webhook import DiscordWebhook, DiscordEmbed
from modules.Config import GetConfig

log = logging.getLogger(__name__)
config = GetConfig()


def DiscordMessage(webhook_url: str = None,
                        content: str = None,
                        embed: bool = False,
                        embed_title: str = None,
                        embed_description: str = None,
                        embed_fields: object = None,
                        embed_thumbnail: str = None,
                        embed_image: str = None,
                        embed_footer: str = None,
                        embed_color: str = "FFFFFF"):
    try:
        if not webhook_url:
            webhook_url = config["discord"]["webhook_url"]
        webhook, embed_obj = DiscordWebhook(url=webhook_url, content=content), None
        if embed:
            embed_obj = DiscordEmbed(title=embed_title, color=embed_color)
            if embed_description:
                embed_obj.description = embed_description
            if embed_fields:
                for key, value in embed_fields.items():
                    embed_obj.add_embed_field(name=key, value=value, inline=False)
            if embed_thumbnail:
                with open(embed_thumbnail, "rb") as f:
                    webhook.add_file(file=f.read(), filename='thumbnail.png')
                embed_obj.set_thumbnail(url='attachment://thumbnail.png')
            if embed_image:
                with open(embed_image, "rb") as f:
                    webhook.add_file(file=f.read(), filename='image.png')
                embed_obj.set_image(url='attachment://image.png')
            if embed_footer:
                embed_obj.set_footer(text=embed_footer)
            embed_obj.set_timestamp()
            webhook.add_embed(embed_obj)
        webhook.execute()
    except Exception as e:
        log.exception(str(e))
        pass
