# PokeBot for BizHawk
### An automated shiny hunting bot for Pokemon Emerald
These scripts are currently being used to complete and stream a Prof. Oak living ✨shiny✨ dex challenge in Pokemon emerald on [YouTube](https://www.youtube.com/watch?v=nVEONn19lZY) and [Twitch](https://www.twitch.tv/fortycakes). Feel free to join the [Discord](https://discord.gg/CXQDjGSeyV) to discuss the stream and get support for this bot.

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/nVEONn19lZY/0.jpg)](https://www.youtube.com/watch?v=nVEONn19lZY)

## Supported games
|  | Ruby | Sapphire | Emerald | FireRed | LeafGreen | 
|--| :--: | :--: | :--: | :--: | :--: |
| English | ❌ | ❌ | ✅ | ❌ | ❌ |
| Spanish | ❌ | ❌ | ✅ | ❌ | ❌ |
| Japanese| ❌ | ❌ | ✅ | ❌ | ❌ |

Support for all other gen 3 games are coming soon (high priority)!

# Getting started
For a guide on how to download and run this bot, check out [Wiki: Getting started](https://github.com/40Cakes/pokebot-bizhawk/wiki/Getting-started).

# Requirements
- The latest version of [Python](https://www.python.org/downloads/)
- [Bizhawk 2.9](https://github.com/TASEmulators/BizHawk/releases/tag/2.9) (and Bizhawk [prereqs](https://github.com/TASEmulators/BizHawk-Prereqs/releases))

# Video examples
These are also available in the Discord channel `#running-examples`.
- [Starters soft resetting](https://cdn.discordapp.com/attachments/1109296060003778580/1109296440020312094/NVIDIA_Share_GXbkQ9G7T3.mp4)
- [Acro bike bunny hopping](https://cdn.discordapp.com/attachments/1109296060003778580/1109302055048314930/NVIDIA_Share_YkYog0pJMB.mp4)
- [Fishing](https://cdn.discordapp.com/attachments/1109296060003778580/1109300987367276614/NVIDIA_Share_hrk4r4dS6U.mp4)
- [Rayquaza](https://cdn.discordapp.com/attachments/1109296060003778580/1109299429091070002/NVIDIA_Share_7cfLYrsoGi.mp4)
- [Groudon](https://cdn.discordapp.com/attachments/1109296060003778580/1109297364923076699/NVIDIA_Share_qBANI5g3OK.mp4)
- [Kyogre](https://cdn.discordapp.com/attachments/1109296060003778580/1109296950689398794/NVIDIA_Share_roZORZBqQ9.mp4)
- [Southern Island (other roamer)](https://cdn.discordapp.com/attachments/1109296060003778580/1109296440020312094/NVIDIA_Share_GXbkQ9G7T3.mp4)

# How it works
There are 2 components of this bot:

1.  `bizhawk.lua` is a Lua script that runs in Bizhawk's Lua console ([Bizhawk Scripting API](https://tasvideos.org/Bizhawk/LuaFunctions)).
This Lua script reads a bunch of different locations GBA memory to extract information such as:

TODO

# Notes

This project is just the result of a bored holiday, I am by no means a professional Python or LUA developer so I apologise for the very scuffed code you have just stumbled upon, this was a huge learning experience and it goes without saying that this code comes with no warranty.

- This bot is very much in ALPHA - you will almost definitely run into bugs! If you decide to run this, please provide feedback and report bugs in Discord #⁠bot-support❓ channel
- It is possible to run the bot with unthrottled speedup, most shiny hunting methods will work at unthrottled speeds but you'll be more prone to getting stuck
- Only tested and confirmed working on Windows
- Only 1 bot instance can run at a time (for now)

# Todo
See the ([Milestones page](https://github.com/40Cakes/pokebot-bizhawk/milestones)) for this repo.

# Credits
I'd like to give a huge shout out to the following projects and authors, as well as the devs of Bizhawk, all were instrumental in getting this bot working.

- https://github.com/TASEmulators/BizHawk
- https://github.com/mkdasher/PokemonBizhawkLua/
- https://github.com/besteon/Ironmon-Tracker/
- https://github.com/Gikkman/bizhawk-communication
- https://github.com/mgba-emu/mgba/blob/master/res/scripts/pokemon.lua (This bot was originally written for mGBA)
- https://github.com/jaller94/matrix-plays-pokemon