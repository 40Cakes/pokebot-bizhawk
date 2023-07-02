import logging

log = logging.getLogger(__name__)

# Check your recent encounters .csv files in the stats/encounters/
# folder to see all available Pokemon fields to filter on
# return True to command the bot to catch the Pokemon
# TODO add option for a Discord webhook when a custom is caught
def CustomCatchConfig(pokemon: object):
    """
    Catch the current encounter if it matches any of the following criteria
    :param pokemon: Pokemon object of the current encounter
    """
    try:
        ### Edit below this line ###

        # Catch perfect IV Pokemon
        if pokemon["IVSum"] == 186:
            return True

        # Catch zero IV Pokemon
        if pokemon["IVSum"] == 0:
            return True

        # Catch Pokemon with 6 identical IVs of any value
        ivs = [pokemon["hpIV"],
               pokemon["attackIV"],
               pokemon["defenseIV"],
               pokemon["speedIV"],
               pokemon["spAttackIV"],
               pokemon["spDefenseIV"]]
        if all(v == ivs[0] for v in ivs):
            return True

        # Catch Pokemon with a good IV sum of greater than or equal to 170
        #if pokemon["IVSum"] >= 170:
        #    return True

        # Catch uncaught Pokemon, not yet registered in the dex
        #if pokemon["hasSpecies"] == 0:
        #    return True

        # Catch all Poochyena with a Pecha Berry
        #if pokemon["name"] == "Poochyena" and pokemon["itemName"] == "Pecha Berry":
        #    return True

        # Catch any Pokemon with perfect Atk, SpAtk and Speed
        #if pokemon["attackIV"] == 31 and pokemon["spAttackIV"] == 31 and pokemon["speedIV"] == 31:
        #    return True

        ### Edit above this line ###

        return False
    except Exception as e:
        log.exception(str(e))
        log.error("Failed to check Pokemon, due to invalid custom catch settings...")
        return False