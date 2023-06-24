import os
import json
import math
import logging
import pandas as pd
from datetime import datetime

from CustomCatchConfig import CustomCatchConfig
from modules.Config import GetConfig
from modules.Discord import DiscordShinyPing
from modules.data.GameState import GameState
from modules.Files import ReadFile, WriteFile
from modules.Inputs import ReleaseAllInputs, PressButton, WaitFrames
from modules.Menuing import CatchPokemon, FleeBattle, PickupItems, ResetGame, SaveGame, StartMenu, BattleOpponent, \
    IsValidMove
from modules.mmf.Pokemon import GetOpponent, GetParty
from modules.mmf.Trainer import GetTrainer

log = logging.getLogger(__name__)
config = GetConfig()

os.makedirs("stats", exist_ok=True)

files = {
    "encounter_log": "stats/encounter_log.json",
    "shiny_log": "stats/shiny_log.json",
    "totals": "stats/totals.json"
}


def GetStats():
    default = {"pokemon": {},
               "totals": {"longest_phase_encounters": 0, "shortest_phase_encounters": "-", "phase_lowest_sv": 99999,
                          "phase_lowest_sv_pokemon": "", "encounters": 0, "phase_encounters": 0, "shiny_average": "-",
                          "shiny_encounters": 0}}
    try:
        totals = ReadFile(files["totals"])
        if totals:
            return json.loads(totals)
        return default
    except Exception as e:
        log.exception(str(e))
        return default


def GetEncounterLog():
    default = {"encounter_log": []}
    try:
        encounter_log = ReadFile(files["encounter_log"])
        if encounter_log:
            return json.loads(encounter_log)
        return default
    except Exception as e:
        log.exception(str(e))
        return default


def GetShinyLog():
    default = {"shiny_log": []}
    try:
        shiny_log = ReadFile(files["shiny_log"])
        if shiny_log:
            return json.loads(shiny_log)
        return default
    except Exception as e:
        log.exception(str(e))
        return default


def GetRNGState(tid: str, mon: str):
    default = {"rngState": []}
    try:
        file = ReadFile(f"stats/{tid}/{mon.lower()}.json")
        data = json.loads(file) if file else default
        return data
    except Exception as e:
        log.exception(str(e))
        return default


last_opponent_personality = None


def OpponentChanged():
    """
    This function checks if there is a different opponent since last check, indicating the game state is probably
    now in a battle
    :return: Boolean value of whether in a battle
    """
    global last_opponent_personality
    try:
        # Fixes a bug where the bot checks the opponent for up to 20 seconds if it was last closed in a battle
        if GetTrainer()["state"] == GameState.OVERWORLD:
            return False

        opponent = GetOpponent()
        if opponent:
            log.debug(
                f"Checking if opponent's PID has changed... (if {last_opponent_personality} != {opponent['personality']})")
            if last_opponent_personality != opponent["personality"]:
                log.info(
                    f"Opponent has changed! Previous PID: {last_opponent_personality}, New PID: {opponent['personality']}")
                last_opponent_personality = opponent["personality"]
                return True
        return False
    except Exception as e:
        log.exception(str(e))
        return False


def LogEncounter(pokemon: dict):
    def CommonStats():
        try:
            mon_stats = stats["pokemon"][pokemon["name"]]
            total_stats = stats["totals"]

            mon_stats["encounters"] += 1
            mon_stats["phase_encounters"] += 1

            # Update encounter stats
            phase_encounters = total_stats["phase_encounters"]
            total_encounters = total_stats["encounters"] + total_stats["shiny_encounters"]
            total_shiny_encounters = total_stats["shiny_encounters"]

            # Log lowest shiny value
            if mon_stats["phase_lowest_sv"] == "-":
                mon_stats["phase_lowest_sv"] = pokemon["shinyValue"]
            else:
                mon_stats["phase_lowest_sv"] = min(pokemon["shinyValue"], mon_stats["phase_lowest_sv"])

            if mon_stats["total_lowest_sv"] == "-":
                mon_stats["total_lowest_sv"] = pokemon["shinyValue"]
            else:
                mon_stats["total_lowest_sv"] = min(pokemon["shinyValue"], mon_stats["total_lowest_sv"])

            # Log shiny average
            if mon_stats["shiny_encounters"] > 0:
                avg = int(math.floor(mon_stats["encounters"] / mon_stats["shiny_encounters"]))
                shiny_average = f"1/{avg:,}"
            else:
                shiny_average = "-"

            if total_shiny_encounters != 0 and mon_stats["encounters"] != 0:
                avg = int(math.floor(total_encounters / total_shiny_encounters))
                total_stats["shiny_average"] = f"1/{avg:,}"
            else:
                total_stats["shiny_average"] = "-"

            log_obj = {
                "time_encountered": str(datetime.now()),
                "pokemon_obj": pokemon,
                "snapshot_stats": {
                    "phase_encounters": total_stats["phase_encounters"],
                    "species_encounters": mon_stats["encounters"],
                    "species_shiny_encounters": mon_stats["shiny_encounters"],
                    "total_encounters": total_encounters,
                    "total_shiny_encounters": total_shiny_encounters,
                    "shiny_average": shiny_average
                }
            }

            if pokemon["shiny"]:
                shiny_log = GetShinyLog()
                shiny_log["shiny_log"].append(log_obj)
                WriteFile(files["shiny_log"], json.dumps(shiny_log, indent=4, sort_keys=True))  # Save shiny log file

            encounter_log = GetEncounterLog()
            encounter_log["encounter_log"].append(log_obj)

            mon_stats["shiny_average"] = shiny_average
            encounter_log["encounter_log"] = encounter_log["encounter_log"][-100:]

            WriteFile(files["totals"], json.dumps(stats, indent=4, sort_keys=True))  # Save stats file
            WriteFile(files["encounter_log"],
                  json.dumps(encounter_log, indent=4, sort_keys=True))  # Save encounter log file

            if config["log"]:
                # Log all encounters to a CSV file per phase
                csvpath = "stats/encounters/"
                csvfile = f"Phase {total_shiny_encounters} Encounters.csv"
                pokemondata = pd.DataFrame.from_dict(pokemon, orient="index").drop(
                    ["enrichedMoves", "moves", "pp", "type"]).sort_index().transpose()
                os.makedirs(csvpath, exist_ok=True)
                header = False if os.path.exists(f"{csvpath}{csvfile}") else True
                pokemondata.to_csv(f"{csvpath}{csvfile}", mode="a", encoding="utf-8", index=False, header=header)

            #if config["discord"]["pokemon_encounter_milestones"] > 0 and \
            #    total_encounters % config["discord"]["pokemon_encounter_milestones"] == 0:

            log.info(
                f"Phase encounters: {phase_encounters} | {pokemon['name']} Phase Encounters: {mon_stats['phase_encounters']}")
            log.info(
                f"{pokemon['name']} Encounters: {mon_stats['encounters']:,} | Lowest {pokemon['name']} SV seen this phase: {mon_stats['phase_lowest_sv']}")
            log.info(
                f"Shiny {pokemon['name']} Encounters: {mon_stats['shiny_encounters']:,} | {pokemon['name']} Shiny Average: {shiny_average}")
            log.info(
                f"Total Encounters: {total_encounters:,} | Total Shiny Encounters: {total_shiny_encounters:,} | Total Shiny Average: {total_stats['shiny_average']}")
        except Exception as e:
            log.exception(str(e))

    try:
        stats = GetStats()
        # Use the correct article when describing the Pokemon
        # e.g. "A Poochyena", "An Anorith"
        article = "an" if pokemon["name"].lower()[0] in {"a", "e", "i", "o", "u"} else "a"

        log.info(f"------------------ {pokemon['name']} ------------------")
        log.debug(pokemon)
        log.info(f"Encountered {article} {pokemon['name']} at {pokemon['metLocationName']}")
        log.info(
            f"HP: {pokemon['hpIV']} | ATK: {pokemon['attackIV']} | DEF: {pokemon['defenseIV']} | SPATK: {pokemon['spAttackIV']} | SPDEF: {pokemon['spDefenseIV']} | SPE: {pokemon['speedIV']}")
        log.info(f"Shiny Value (SV): {pokemon['shinyValue']:,} (is {pokemon['shinyValue']:,} < 8 = {pokemon['shiny']})")

        # Set up pokemon stats if first encounter
        if not pokemon["name"] in stats["pokemon"]:
            stats["pokemon"].update({pokemon["name"]: {"encounters": 0, "shiny_encounters": 0, "phase_lowest_sv": "-",
                                                       "phase_encounters": 0, "shiny_average": "-",
                                                       "total_lowest_sv": "-"}})

        if pokemon["shiny"]:
            log.info("Shiny Pokemon detected!")

            # Send shiny Discord message
            if config["discord"]["enable"]:
                DiscordShinyPing(pokemon, stats)

            if stats["totals"]["shortest_phase_encounters"] == "-":
                stats["totals"]["shortest_phase_encounters"] = stats["totals"]["phase_encounters"]
            else:
                stats["totals"]["shortest_phase_encounters"] = min(stats["totals"]["shortest_phase_encounters"],
                                                                   stats["totals"]["phase_encounters"])

            stats["pokemon"][pokemon["name"]]["shiny_encounters"] += 1
            stats["totals"]["shiny_encounters"] += 1
            CommonStats()
            stats["totals"]["phase_encounters"] = 0
            stats["totals"]["phase_lowest_sv"] = "-"
            stats["totals"]["phase_lowest_sv_pokemon"] = ""

            # Reset phase stats
            for pokemon["name"] in stats["pokemon"]:
                stats["pokemon"][pokemon["name"]]["phase_lowest_sv"] = "-"
                stats["pokemon"][pokemon["name"]]["phase_encounters"] = 0

            WriteFile(files["totals"], json.dumps(stats, indent=4, sort_keys=True))  # Save stats file
        else:
            log.info("Non shiny Pokemon detected...")

            stats["totals"]["encounters"] += 1
            stats["totals"]["phase_encounters"] += 1

            if stats["totals"]["phase_encounters"] > stats["totals"]["longest_phase_encounters"]: stats["totals"][
                "longest_phase_encounters"] = stats["totals"]["phase_encounters"]
            if stats["totals"]["phase_lowest_sv"] == "-":
                stats["totals"]["phase_lowest_sv"] = pokemon["shinyValue"]
                stats["totals"]["phase_lowest_sv_pokemon"] = pokemon["name"]
            elif pokemon["shinyValue"] <= stats["totals"]["phase_lowest_sv"]:
                stats["totals"]["phase_lowest_sv"] = pokemon["shinyValue"]
                stats["totals"]["phase_lowest_sv_pokemon"] = pokemon["name"]

            CommonStats()

        log.info(f"----------------------------------------")
    except Exception as e:
        log.exception(str(e))
        return False


def EncounterPokemon(starter: bool = False):
    """
    New Pokemon encountered, record stats + decide whether to catch/battle/flee
    :param starter: Boolean value of whether in starter mode
    :return: Boolean value of whether in battle
    """
    legendary_hunt = config["bot_mode"] in ["manual", "rayquaza", "kyogre", "groudon", "southern island", "regis",
                                            "deoxys resets", "deoxys runaways", "mew"]

    log.info("Identifying Pokemon...")
    ReleaseAllInputs()

    if starter:
        WaitFrames(30)
    else:
        for _ in range(250):
            if GetTrainer()["state"] in [3, 255]:
                break

    if GetTrainer()["state"] == GameState.OVERWORLD:
        return False

    pokemon = GetParty()[0] if starter else GetOpponent()
    LogEncounter(pokemon)

    replace_battler = False

    if pokemon["shiny"]:
        if not starter and not legendary_hunt and config["catch_shinies"]:
            CatchPokemon()
        elif legendary_hunt:
            input("Pausing bot for manual intervention. (Don't forget to pause the pokebot.lua script so you can "
                  "provide inputs). Press Enter to continue...")
        return True
    else:
        if config["bot_mode"] == "manual":
            while GetTrainer()["state"] != GameState.OVERWORLD:
                WaitFrames(100)
        elif starter:
            return False

        if CustomCatchConfig(pokemon):
            CatchPokemon()

        if not legendary_hunt:
            if config["battle_others"]:
                battle_won = BattleOpponent()
                replace_battler = not battle_won
            else:
                FleeBattle()
        elif config["bot_mode"] == "deoxys resets":
            if not config["mem_hacks"]:
                # Wait until sprite has appeared in battle before reset
                WaitFrames(240)
            ResetGame()
            return False
        else:
            FleeBattle()

        if config["pickup"] and not legendary_hunt:
            PickupItems()

        # If total encounters modulo config["save_every_x_encounters"] is 0, save the game
        # Save every x encounters to prevent data loss (pickup, levels etc)
        stats = GetStats()
        total_encounters = stats["totals"]["encounters"] + stats["totals"]["shiny_encounters"]
        if config["autosave_encounters"] > 0 and total_encounters > 0 and \
                total_encounters % config["autosave_encounters"] == 0:
            SaveGame()

        if replace_battler:
            if not config["cycle_lead_pokemon"]:
                log.info("Lead Pokemon can no longer battle. Ending the script!")
                FleeBattle()
                return False
            else:
                StartMenu("pokemon")

                # Find another healthy battler
                party_pp = [0, 0, 0, 0, 0, 0]
                for i, mon in enumerate(GetParty()):
                    if mon is None:
                        continue

                    if mon["hp"] > 0 and i != 0:
                        for j, move in enumerate(mon["enrichedMoves"]):
                            if IsValidMove(move) and mon["pp"][j] > 0:
                                party_pp[i] += move["pp"]

                highest_pp = max(party_pp)
                lead_idx = party_pp.index(highest_pp)

                if highest_pp == 0:
                    log.info("Ran out of Pokemon to battle with. Ending the script!")
                    os._exit(1)

                lead = GetParty()[lead_idx]
                if lead is not None:
                    log.info(f"Replacing lead battler with {lead['speciesName']} (Party slot {lead_idx})")

                PressButton("A")
                WaitFrames(60)
                PressButton("A")
                WaitFrames(15)

                for _ in range(3):
                    PressButton("Up")
                    WaitFrames(15)

                PressButton("A")
                WaitFrames(15)

                for _ in range(lead_idx):
                    PressButton("Down")
                    WaitFrames(15)

                # Select target Pokemon and close out menu
                PressButton("A")
                WaitFrames(60)

                log.info("Replaced lead Pokemon!")

                for _ in range(5):
                    PressButton("B")
                    WaitFrames(15)
        return False
