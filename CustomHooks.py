import random
import logging

from modules.Config import GetConfig
from modules.Discord import DiscordMessage

log = logging.getLogger(__name__)
config = GetConfig()

def CustomHooks(pokemon: object, stats: object):
    """
    This function is called every time an encounter is logged, but before phase stats are reset (if shiny)
    this file is useful for custom webhooks or logging to external databases if you understand Python

    Note: this function runs in a thread and will not hold up the bot if you need to run any slow hooks
    """
    try:
        #log.info(json.dumps(pokemon, indent=4))
        #log.info(json.dumps(stats, indent=4))

        ### Your custom code goes here ###

        if config["discord"]["enable"]:
            # Discord pings
            match config["discord"]["ping_mode"]:
                case "role":
                    discord_ping = f"📢 <@&{config['discord']['ping_id']}>"
                case "user":
                    discord_ping = f"📢 <@{config['discord']['ping_id']}>"
                case _:
                    discord_ping = ""

            # Formatted IV table
            if config["discord"]["iv_format"] == "formatted":
                iv_field = "```" \
                           "╔═══╤═══╤═══╤═══╤═══╤═══╗\n" \
                           "║HP │ATK│DEF│SPA│SPD│SPE║\n" \
                           "╠═══╪═══╪═══╪═══╪═══╪═══╣\n" \
                           "║{:^3}│{:^3}│{:^3}│{:^3}│{:^3}│{:^3}║\n" \
                           "╚═══╧═══╧═══╧═══╧═══╧═══╝" \
                           "```".format(
                            pokemon['hpIV'],
                            pokemon['attackIV'],
                            pokemon['defenseIV'],
                            pokemon['spAttackIV'],
                            pokemon['spDefenseIV'],
                            pokemon['speedIV'])
            else:
                # Default to basic IV formatting
                iv_field = "HP: {} | ATK: {} | DEF: {} | SPATK: {} | SPDEF: {} | SPE: {}".format(
                            pokemon["hpIV"],
                            pokemon["attackIV"],
                            pokemon["defenseIV"],
                            pokemon["spAttackIV"],
                            pokemon["spDefenseIV"],
                            pokemon["speedIV"])

            # Discord shiny Pokemon encountered
            if config["discord"]["shiny_pokemon_encounter"] and pokemon["shiny"]:
                if not config["discord"]["shiny_pokemon_encounter_ping"]:
                    discord_ping = ""
                DiscordMessage(
                    content="Encountered a shiny {}!\n\n{}".format(
                            pokemon["name"],
                            discord_ping
                    ),
                    embed=True,
                    embed_title="Shiny encountered!",
                    embed_description="{} at {}!".format(
                                    pokemon["name"],
                                    pokemon["metLocationName"]),
                    embed_fields={
                        "Shiny Value": "{:,}".format(pokemon["shinyValue"]),
                        "IVs": iv_field,
                        "Nature": "{}".format(pokemon["nature"]),
                        "Level": "{}".format(pokemon["level"]),
                        "{} Encounters".format(pokemon["name"]): "{:,}".format(stats["pokemon"][pokemon["name"]].get("encounters", 0)),
                        "Shiny {} Encounters".format(pokemon["name"]): "{:,}".format(stats["pokemon"][pokemon["name"]].get("shiny_encounters", 0)),
                        "{} Phase Encounters".format(pokemon["name"]): "{:,}".format(stats["pokemon"][pokemon["name"]].get("phase_encounters", 0)),
                        "Phase Encounters": "{:,}".format(stats["totals"].get("phase_encounters", 0)),
                        "Phase IV Sum Records": "{:,} IV {} :arrow_up:|:arrow_down: {:,} IV {}".format(
                                                stats["totals"].get("phase_highest_iv_sum", 0),
                                                stats["totals"].get("phase_highest_iv_sum_pokemon", "N/A"),
                                                stats["totals"].get("phase_lowest_iv_sum", 0),
                                                stats["totals"].get("phase_lowest_iv_sum_pokemon", "N/A")),
                        "Phase SV Records": "{:,} SV {} :arrow_up:|:arrow_down: {:,} SV ✨{}✨".format(
                                                stats["totals"].get("phase_highest_sv", 0),
                                                stats["totals"].get("phase_highest_sv_pokemon", "N/A"),
                                                stats["totals"].get("phase_lowest_sv", 0),
                                                stats["totals"].get("phase_lowest_sv_pokemon", "N/A")),
                        "Phase Same Pokemon Streak": "{:,} {} were encountered in a row!".format(
                                                stats["totals"].get("phase_streak", 0),
                                                stats["totals"].get("phase_streak_pokemon", "N/A")),
                        "Total Encounters": "{:,}".format(stats["totals"].get("encounters", 0)),
                        "Total Shiny Encounters": "{:,}".format(stats["totals"].get("shiny_encounters", 0))},
                    embed_thumbnail="./modules/interface/sprites/pokemon/shiny/{}.png".format(
                                    pokemon["name"].lower()),
                    embed_footer=f"PokéBot ID: {config['bot_instance_id']}",
                    embed_color="ffd242")

            # Discord Pokémon encounter milestones
            if config["discord"]["pokemon_encounter_milestones"] > 0 and \
            stats["pokemon"][pokemon["name"]].get("encounters", 0) % config["discord"]["pokemon_encounter_milestones"] == 0:
                if not config["discord"]["pokemon_encounter_milestones_ping"]:
                    discord_ping = ""
                DiscordMessage(
                    webhook_url=config["discord"].get("pokemon_encounter_milestones_webhook_url", None),
                    content=f"🎉 New milestone achieved!\n\n{discord_ping}",
                    embed=True,
                    embed_description="{:,} {} encounters!".format(
                                    stats["pokemon"][pokemon["name"]].get("encounters", 0),
                                    pokemon["name"]),
                    embed_thumbnail="./modules/interface/sprites/pokemon/{}.png".format(
                                    pokemon["name"].lower()),
                    embed_footer=f"PokéBot ID: {config['bot_instance_id']}")

            # Discord shiny Pokémon encounter milestones
            if pokemon["shiny"] and \
            config["discord"]["shiny_pokemon_encounter_milestones"] > 0 and \
            stats["pokemon"][pokemon["name"]].get("shiny_encounters", -1) % config["discord"]["shiny_pokemon_encounter_milestones"] == 0:
                if not config["discord"]["shiny_pokemon_encounter_milestones_ping"]:
                    discord_ping = ""
                DiscordMessage(
                    webhook_url=config["discord"].get("shiny_pokemon_encounter_milestones_webhook_url", None),
                    content=f"🎉 New milestone achieved!\n\n{discord_ping}",
                    embed=True,
                    embed_description="{:,} shiny ✨{}✨ encounters!".format(
                                    stats["pokemon"][pokemon["name"]].get("shiny_encounters", 0),
                                    pokemon["name"]),
                    embed_thumbnail="./modules/interface/sprites/pokemon/shiny/{}.png".format(
                                    pokemon["name"].lower()),
                    embed_footer=f"PokéBot ID: {config['bot_instance_id']}")

            # Discord total encounter milestones
            if config["discord"]["total_encounter_milestones"] > 0 and \
            stats["totals"].get("encounters", -1) % config["discord"]["total_encounter_milestones"] == 0:
                if not config["discord"]["total_encounter_milestones_ping"]:
                    discord_ping = ""
                DiscordMessage(
                    webhook_url=config["discord"].get("total_encounter_milestones_webhook_url", None),
                    content=f"🎉 New milestone achieved!\n\n{discord_ping}",
                    embed=True,
                    embed_description="{:,} total encounters!".format(
                                      stats["totals"].get("encounters", 0)),
                    embed_thumbnail="./modules/interface/sprites/items/{}.png".format(
                        random.choice([
                            "Dive Ball",
                            "Great Ball",
                            "Light Ball",
                            "Luxury Ball",
                            "Master Ball",
                            "Nest Ball",
                            "Net Ball",
                            "Poké Ball",
                            "Premier Ball",
                            "Repeat Ball",
                            "Safari Ball",
                            "Smoke Ball",
                            "Timer Ball",
                            "Ultra Ball"])),
                    embed_footer=f"PokéBot ID: {config['bot_instance_id']}")

            # Discord phase encounter notifications
            if not pokemon["shiny"] and \
            config["discord"]["phase_notification"] and \
            (stats["totals"].get("phase_encounters", -1) == config["discord"]["first_phase_notification"] or
            (stats["totals"].get("phase_encounters", -1) > config["discord"]["first_phase_notification"] and
            stats["totals"].get("phase_encounters", -1) % config["discord"]["consequent_phase_notifications"] == 0)):
                if not config["discord"]["phase_notification_ping"]:
                    discord_ping = ""
                DiscordMessage(
                    webhook_url=config["discord"].get("phase_notification_webhook_url", None),
                    content="💀 The current phase has reached {} encounters!\n\n{}".format(
                            stats["totals"].get("phase_encounters", 0),
                            discord_ping),
                    embed=True,
                    embed_description="Phase Summary",
                    embed_fields={
                        "Phase Encounters": "{:,}".format(stats["totals"].get("phase_encounters", 0)),
                        "Phase IV Sum Records": "{:,} IV {} :arrow_up:|:arrow_down: {:,} IV {}".format(
                                                stats["totals"].get("phase_highest_iv_sum", 0),
                                                stats["totals"].get("phase_highest_iv_sum_pokemon", "N/A"),
                                                stats["totals"].get("phase_lowest_iv_sum", 0),
                                                stats["totals"].get("phase_lowest_iv_sum_pokemon", "N/A")),
                        "Phase SV Records": "{:,} SV {} :arrow_up:|:arrow_down: {:,} SV {}".format(
                                                stats["totals"].get("phase_highest_sv", 0),
                                                stats["totals"].get("phase_highest_sv_pokemon", "N/A"),
                                                stats["totals"].get("phase_lowest_sv", 0),
                                                stats["totals"].get("phase_lowest_sv_pokemon", "N/A")),
                        "Phase Same Pokemon Streak": "{:,} {} were encountered in a row!".format(
                                                stats["totals"].get("phase_streak", 0),
                                                stats["totals"].get("phase_streak_pokemon", "N/A")),
                        "Total Encounters": "{:,}".format(stats["totals"].get("encounters", 0)),
                        "Total Shiny Encounters": "{:,}".format(stats["totals"].get("shiny_encounters", 0))},
                    embed_footer=f"PokéBot ID: {config['bot_instance_id']}")
    except Exception as e:
        log.exception(str(e))
        log.error("Failed to run custom hooks...")
