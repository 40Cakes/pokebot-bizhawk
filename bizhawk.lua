-- bizhawk.lua - this script runs in Bizhawk emulator
-- it enables external applications to retrieve data
-- from Pokemon games as well as press and hold buttons

-- These were an immense help with this project:
-- https://github.com/mkdasher/PokemonBizhawkLua/
-- https://github.com/besteon/Ironmon-Tracker/
-- https://github.com/Gikkman/bizhawk-communication

local utils = require("./data/lua/utils")

enable_input = true -- Toggle inputs to the emulator, useful for testing
write_files = false -- Toggle output of data to files (press L+R in emulator to save files to testing/ folder)

dofile (utils.translatePath("data\\lua\\Memory.lua"))
dofile (utils.translatePath("data\\lua\\GameSettings.lua"))

-- Initialize game settings before loading other files
GameSettings.initialize()

console.log("Lua Version: ".._VERSION)
package.path = utils.translatePath(";.\\data\\lua\\?.lua;")

json = require "json"
PokemonNames = require "PokemonNames"

console.log("Detected game: " .. GameSettings.gamename)

-- Function to read Pokemon data from an address
-- Pokemon data structure: https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_data_structure_(Generation_III)
function readMonData(address)
	local mon = {}
	mon.personality = Memory.readdword(address + 0)
	mon.magicWord = mon.personality ~ Memory.readdword(address + 4)
	mon.otId = Memory.readdword(address + 4)
	mon.language = Memory.readbyte(address + 18)
	local flags = Memory.readbyte(address + 19)
	mon.isBadEgg = flags & 1
	mon.hasSpecies = (flags >> 1) & 1
	mon.isEgg = (flags >> 2) & 1
	mon.markings = Memory.readbyte(address + 27)
	mon.status = Memory.readdword(address + 80)
	mon.level = Memory.readbyte(address + 84)
	mon.mail = Memory.readdword(address + 85)
	mon.hp = Memory.readword(address + 86)
	mon.maxHP = Memory.readword(address + 88)
	mon.attack = Memory.readword(address + 90)
	mon.defense = Memory.readword(address + 92)
	mon.speed = Memory.readword(address + 94)
	mon.spAttack = Memory.readword(address + 96)
	mon.spDefense = Memory.readword(address + 98)

	local key = mon.otId ~ mon.personality
	local substructSelector = {
		[ 0] = {0, 1, 2, 3},
		[ 1] = {0, 1, 3, 2},
		[ 2] = {0, 2, 1, 3},
		[ 3] = {0, 3, 1, 2},
		[ 4] = {0, 2, 3, 1},
		[ 5] = {0, 3, 2, 1},
		[ 6] = {1, 0, 2, 3},
		[ 7] = {1, 0, 3, 2},
		[ 8] = {2, 0, 1, 3},
		[ 9] = {3, 0, 1, 2},
		[10] = {2, 0, 3, 1},
		[11] = {3, 0, 2, 1},
		[12] = {1, 2, 0, 3},
		[13] = {1, 3, 0, 2},
		[14] = {2, 1, 0, 3},
		[15] = {3, 1, 0, 2},
		[16] = {2, 3, 0, 1},
		[17] = {3, 2, 0, 1},
		[18] = {1, 2, 3, 0},
		[19] = {1, 3, 2, 0},
		[20] = {2, 1, 3, 0},
		[21] = {3, 1, 2, 0},
		[22] = {2, 3, 1, 0},
		[23] = {3, 2, 1, 0},
	}

	local pSel = substructSelector[mon.personality % 24]
	local ss0 = {}
	local ss1 = {}
	local ss2 = {}
	local ss3 = {}

	for i = 0, 2 do
		ss0[i] = Memory.readdword(address + 32 + pSel[1] * 12 + i * 4) ~ key
		ss1[i] = Memory.readdword(address + 32 + pSel[2] * 12 + i * 4) ~ key
		ss2[i] = Memory.readdword(address + 32 + pSel[3] * 12 + i * 4) ~ key
		ss3[i] = Memory.readdword(address + 32 + pSel[4] * 12 + i * 4) ~ key
	end

	mon.species = (ss0[0] & 0xFFFF) + 1
	mon.speciesName = PokemonNames[mon.species]
	mon.heldItem = ss0[0] >> 16
	mon.experience = ss0[1]
	mon.ppBonuses = ss0[2] & 0xFF
	mon.friendship = (ss0[2] >> 8) & 0xFF

	mon.moves = {
		ss1[0] & 0xFFFF,
		ss1[0] >> 16,
		ss1[1] & 0xFFFF,
		ss1[1] >> 16
	}
	mon.pp = {
		ss1[2] & 0xFF,
		(ss1[2] >> 8) & 0xFF,
		(ss1[2] >> 16) & 0xFF,
		ss1[2] >> 24
	}

	mon.hpEV = ss2[0] & 0xFF
	mon.attackEV = (ss2[0] >> 8) & 0xFF
	mon.defenseEV = (ss2[0] >> 16) & 0xFF
	mon.speedEV = ss2[0] >> 24
	mon.spAttackEV = ss2[1] & 0xFF
	mon.spDefenseEV = (ss2[1] >> 8) & 0xFF
	mon.cool = (ss2[1] >> 16) & 0xFF
	mon.beauty = ss2[1] >> 24
	mon.cute = ss2[2] & 0xFF
	mon.smart = (ss2[2] >> 8) & 0xFF
	mon.tough = (ss2[2] >> 16) & 0xFF
	mon.sheen = ss2[2] >> 24

	mon.pokerus = ss3[0] & 0xFF
	mon.metLocation = (ss3[0] >> 8) & 0xFF
	flags = ss3[0] >> 16
	mon.metLevel = flags & 0x7F
	mon.metGame = (flags >> 7) & 0xF
	mon.pokeball = (flags >> 11) & 0xF
	mon.otGender = (flags >> 15) & 0x1
	flags = ss3[1]
	mon.hpIV = flags & 0x1F
	mon.attackIV = (flags >> 5) & 0x1F
	mon.defenseIV = (flags >> 10) & 0x1F
	mon.speedIV = (flags >> 15) & 0x1F
	mon.spAttackIV = (flags >> 20) & 0x1F
	mon.spDefenseIV = (flags >> 25) & 0x1F
	mon.altAbility = (flags >> 31) & 1
	flags = ss3[2]
	mon.coolRibbon = flags & 7
	mon.beautyRibbon = (flags >> 3) & 7
	mon.cuteRibbon = (flags >> 6) & 7
	mon.smartRibbon = (flags >> 9) & 7
	mon.toughRibbon = (flags >> 12) & 7
	mon.championRibbon = (flags >> 15) & 1
	mon.winningRibbon = (flags >> 16) & 1
	mon.victoryRibbon = (flags >> 17) & 1
	mon.artistRibbon = (flags >> 18) & 1
	mon.effortRibbon = (flags >> 19) & 1
	mon.marineRibbon = (flags >> 20) & 1
	mon.landRibbon = (flags >> 21) & 1
	mon.skyRibbon = (flags >> 22) & 1
	mon.countryRibbon = (flags >> 23) & 1
	mon.nationalRibbon = (flags >> 24) & 1
	mon.earthRibbon = (flags >> 25) & 1
	mon.worldRibbon = (flags >> 26) & 1
	mon.eventLegal = (flags >> 27) & 0x1F
	return mon
end

-- Function to read trainer data
-- Trainer data structure: https://bulbapedia.bulbagarden.net/wiki/Save_data_structure_(Generation_III)
function getTrainer()
	local trainer = Memory.readdword(GameSettings.trainerpointer)

	trainer = { -- # TODO add items in bag
		--gender = Memory.readbyte(trainer + 8),
		tid = Memory.readword(trainer + 10),
		sid = Memory.readword(trainer + 12),
		state = Memory.readbyte(GameSettings.trainerpointer + 199), -- TODO Test this on RS and FRLG
		mapId = Memory.readbyte(GameSettings.trainerpointer + 200), -- TODO Test this on RS and FRLG
		mapBank = Memory.readbyte(GameSettings.trainerpointer + 201), -- TODO Test this on RS and FRLG
		posX = Memory.readbyte(GameSettings.coords + 0) - 7,
		posY = Memory.readbyte(GameSettings.coords + 2) - 7,
		roamerMapId = Memory.readbyte(GameSettings.mapbank + 7)
	}

	return trainer
end

-- Function to get data of all Pokemon in the player's party
function getParty()
	local party = {}
	local start = GameSettings.pstats
	local partyCount = GameSettings.pcount

	for i = 1, Memory.readbyte(partyCount) do
		party[i] = readMonData(start)
		start = start + 100 -- Pokemon data structure is 100 bytes
	end

	return party
end

-- Function to get data related to the emulator itself
function getEmu()
	local emu_info = {
		frameCount = emu.framecount(),
		emuFPS = client.get_approx_framerate(),
		detectedGame = GameSettings.gamename,
		rngState = Memory.readdword(GameSettings.rng),
		language = GameSettings.language
	}

	return emu_info
end

-- Main function to write data to memory mapped files
function mainLoop()
	trainer = getTrainer()
	party = getParty()
	opponent = readMonData(GameSettings.estats)

	comm.mmfWrite("bizhawk_trainer_info", json.encode({["trainer"] = trainer}) .. "\x00")
	comm.mmfWrite("bizhawk_party_info", json.encode({["party"] = party}) .. "\x00")
	comm.mmfWrite("bizhawk_opponent_info", json.encode({["opponent"] = opponent}) .. "\x00")

	if write_files then
		check_input = joypad.get()
		if check_input["L"] and check_input["R"] then
			trainer_info_file = io.open(
				utils.translatePath("testing\\trainer_info.json"), "w"
			)
			trainer_info_file:write(json.encode({["trainer"] = trainer}))
			trainer_info_file:close()
			
			party_info_file = io.open(
				utils.translatePath("testing\\party_info.json"), "w"
			)
			party_info_file:write(json.encode({["party"] = party}))
			party_info_file:close()

			opponent_info_file = io.open(
				utils.translatePath("testing\\opponent_info.json"), "w"
			)
			opponent_info_file:write(json.encode({["opponent"] = opponent}))
			opponent_info_file:close()
		end
	end
end

-- Release all keys after starting script
if enable_input then
	input = joypad.get()
	input["A"], input["B"], input["L"], input["R"], input["Up"], input["Down"], input["Left"], input["Right"], input["Select"], input["Start"], input["Screenshot"] = false, false, false, false, false, false, false, false, false, false, false
	joypad.set(input)
end

-- Allocate memory mapped file sizes
comm.mmfWrite("bizhawk_screenshot", string.rep("\x00", 24576))
comm.mmfSetFilename("bizhawk_screenshot")
comm.mmfScreenshot()

comm.mmfWrite("bizhawk_press_input", string.rep("\x00", 256))
comm.mmfWrite("bizhawk_hold_input", string.rep("\x00", 256))
comm.mmfWrite("bizhawk_trainer_info", string.rep("\x00", 4096))
comm.mmfWrite("bizhawk_party_info", string.rep("\x00", 8192))
comm.mmfWrite("bizhawk_opponent_info", string.rep("\x00", 4096))
comm.mmfWrite("bizhawk_emu_info", string.rep("\x00", 4096))

-- Create memory mapped input files for Python script to write to
comm.mmfWrite("bizhawk_press_input", json.encode(input) .. "\x00")
comm.mmfWrite("bizhawk_hold_input", json.encode(input) .. "\x00")

last_posY = 0
last_posX = 0
last_state = 0
last_mapBank = 0
last_mapId = 0

while true do
	if enable_input then
		for button, _ in pairs (input) do
			input[button] = false
		end

		local press_success, press_result = pcall(json.decode, comm.mmfRead("bizhawk_press_input", 256))
		if press_success then
			input_press = press_result
		end
		local hold_success, hold_result = pcall(json.decode, comm.mmfRead("bizhawk_hold_input", 256))
		if hold_success then
			input_hold = hold_result
		end

		if input_press then
			for button, press in pairs (input_press) do
				if press and (press ~= 0) then
					input[button] = true
				elseif input_hold[button] then
					input[button] = true
				else
					input[button] = false
				end
			end
		end

		joypad.set(input)
	end
	
	if input["Screenshot"] then
		comm.mmfScreenshot()
	end

	emu_info = getEmu()
	comm.mmfWrite("bizhawk_emu_info", json.encode({["emu"] = emu_info}) .. "\x00")
	-- Save screenshot and other data to memory mapped files, as FPS is higher, reduce the number of reads and writes to memory
	fps = emu_info.emuFPS
	if fps > 70 and fps <= 120  then -- Copy screenshot to memory every nth frame if running at higher than 1x to reduce memory writes
		if (emu_info.frameCount % 2 == 0) then
			mainLoop()
		end
	elseif fps > 120 and fps <= 240 then 
		if (emu_info.frameCount % 3 == 0) then
			mainLoop()
		end	
	elseif fps > 240 and fps <= 480 then 
		if (emu_info.frameCount % 4 == 0) then
			mainLoop()
		end	
	elseif fps > 480 then 
		if (emu_info.frameCount % 5 == 0) then
			mainLoop()
		end
	else
		mainLoop()
	end

	-- Frame advance
	emu.frameadvance()
end
