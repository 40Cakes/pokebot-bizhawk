import numpy
import logging

class HiddenPowers:
    hidden_powers = {
        '0'  : 'Fighting',
        '1'  : 'Flying',
        '2'  : 'Poison',
        '3'  : 'Ground',
        '4'  : 'Rock',
        '5'  : 'Bug',
        '6'  : 'Ghost',
        '7'  : 'Steel',
        '8'  : 'Fire',
        '9'  : 'Water',
        '10' : 'Grass',
        '11' : 'Electric',
        '12' : 'Psychic',
        '13' : 'Ice',
        '14' : 'Dragon',
        '15' : 'Dark'
    }

def calculate_hidden_power(pokemon): #validate mon before calling
    hp = pokemon['hpIV'] % 2
    atk = pokemon['attackIV'] % 2
    def_ = pokemon['defenseIV'] % 2
    spAtk = pokemon['spAttackIV'] % 2
    spDef = pokemon['spDefenseIV'] % 2
    spe = pokemon['speedIV'] % 2

    typeIndex = int(numpy.floor(((hp+(2*atk)+(4*def_)+(8*spe)+(16*spAtk)+(32*spDef))*15)/63))
    return HiddenPowers.hidden_powers[f"{typeIndex}"]
