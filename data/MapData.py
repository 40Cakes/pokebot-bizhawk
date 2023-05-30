from enum import IntEnum # https://docs.python.org/3/library/enum.html

# https://bulbapedia.bulbagarden.net/wiki/List_of_locations_by_index_number_(Generation_III)

class MapBank(IntEnum):
    OVERWORLD = 0
    LITTLEROOT_TOWN = 1
    OLDALE_TOWN = 2
    DEWFORD_TOWN = 3
    DUNGEONS = 24
    SPECIAL = 26

class MapID(IntEnum):
    # Dungeons
    REGIROCK_CAVE = 6
    REGICE_CAVE = 67
    REGISTEEL_CAVE = 68
    RAYQUAZA_PILLAR = 85
    KYOGRE_CAVE = 103
    GROUDON_CAVE = 105
    # Special
    LATI_ISLAND = 10
    MEW_ISLAND = 57
    DEOXYS_ISLAND = 58
    HO_OH_ROCK = 75
    LUGIA_ROCK = 87
