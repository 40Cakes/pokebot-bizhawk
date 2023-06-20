-- Source: https://github.com/mkdasher/PokemonBizhawkLua/blob/master/pkmgen3/GameSettings.lua

GameSettings = {
	game = 0,
	gamename = "",
	gamecolor = 0,
	rngseed = 0,
	mapbank = 0,
	mapid = 0,
	encountertable = 0,
	pstats = 0,
	estats = 0,
	rng = 0,
	rng2 = 0,
	wram = 0,
	version = 0,
	language = 0,
	trainerpointer = 0,
	coords = 0,
	roamerpokemonoffset = 0
}
GameSettings.VERSIONS = {
	RS = 1,
	E = 2,
	FRLG = 3
}
GameSettings.LANGUAGES = {
	U = 1,
	J = 2,
	F = 3,
	S = 4,
	G = 5,
	I = 6
}

function GameSettings.initialize()
	local gamecode = memory.read_u32_be(0x0000AC, "ROM")

	-- # TODO replace missing 0x0 pointers with real values
								-- RS (U) 	EMER (U) 	FRLG (U)	RS (J)		EMER (J)	FRLG (J)	RS (S)		EMER (S)	FRLG (S)
	local pstats = 				{0x3004360, 0x20244EC, 	0x2024284, 	0x3004290, 	0x2024190, 	0x20241E4,	0x0,		0x20244EC,	0x0 	} -- Trainer stats
	local pcount = 				{0x3004350, 0x20244E9, 	0x2024029, 	0x0,		0x202418D,	0x0,		0x0,		0x20244E9,	0x0 	} -- Party count
	local estats = 				{0x30045C0, 0x2024744, 	0x202402C, 	0x30044F0, 	0x20243E8, 	0x2023F8C,	0x0,		0x2024744,	0x0 	} -- Enemy stats
	local rng = 				{0x3004818, 0x3005D80, 	0x3005000, 	0x3004748, 	0x3005AE0, 	0x3005040,	0x0,		0x3005D80,	0x0 	} -- RNG address
	local coords = 				{0x30048B0, 0x2037360, 	0x2036E48, 	0x30047E0, 	0x2037000, 	0x2036D7C,	0x0,		0x2037360,	0x0 	} -- X/Y coords
	local rng2 = 				{0x0000000, 0x0000000, 	0x20386D0, 	0x0000000, 	0x0000000, 	0x203861C,	0x0000000,	0x0000000,	0x0 	} -- RNG encounter (FRLG only)
	local wram = 				{0x0000000, 0x2020000, 	0x2020000, 	0x0000000, 	0x2020000, 	0x201FF4C,	0x0,		0x2020000,	0x0 	} -- WRAM address
	local mapbank = 			{0x20392FC, 0x203BC80, 	0x203F3A8, 	0x2038FF4, 	0x203B94C, 	0x203F31C,	0x0,		0x203BC80,	0x0 	} -- Map Bank
	local mapid = 				{0x202E83C, 0x203732C, 	0x2036E10, 	0x202E59C, 	0x2036FCC, 	0x2036D44,	0x0,		0x203732C,	0x0 	} -- Map ID
	local trainerpointer = 		{0x3001FB4, 0x3005D90, 	0x300500C, 	0x3001F28, 	0x3005AF0, 	0x300504C,	0x0,		0x3005D90,	0x0 	} -- Trainer data
	local roamerpokemonoffset = {0x39D4, 	0x4188, 	0x4074, 	0x39D4, 	0x4188, 	0x4074,		0x39D4,		0x4188,		0x4074 	} -- Roamer Pokemon
	
	if gamecode == 0x41585645 then
		GameSettings.game = 1
		GameSettings.gamename = "Pokemon Ruby (U)"
		GameSettings.encountertable = 0x839D454
		GameSettings.version = GameSettings.VERSIONS.RS
		GameSettings.language = GameSettings.LANGUAGES.U
	elseif gamecode == 0x41585045 then
		GameSettings.game = 1
		GameSettings.gamename = "Pokemon Sapphire (U)"
		GameSettings.encountertable = 0x839D29C
		GameSettings.version = GameSettings.VERSIONS.RS
		GameSettings.language = GameSettings.LANGUAGES.U
	elseif gamecode == 0x42504545 then
		GameSettings.game = 2
		GameSettings.gamename = "Pokemon Emerald (U)"
		GameSettings.encountertable = 0x8552D48
		GameSettings.version = GameSettings.VERSIONS.E
		GameSettings.language = GameSettings.LANGUAGES.U
	elseif gamecode == 0x42505245 then
		GameSettings.game = 3
		GameSettings.gamename = "Pokemon FireRed (U)"
		GameSettings.encountertable = 0x83C9CB8
		GameSettings.version = GameSettings.VERSIONS.FRLG
		GameSettings.language = GameSettings.LANGUAGES.U
	elseif gamecode == 0x42504745 then
		GameSettings.game = 3
		GameSettings.gamename = "Pokemon LeafGreen (U)"
		GameSettings.encountertable = 0x83C9AF4
		GameSettings.version = GameSettings.VERSIONS.FRLG
		GameSettings.language = GameSettings.LANGUAGES.U
	elseif gamecode == 0x4158564A then
		GameSettings.game = 4
		GameSettings.gamename = "Pokemon Ruby (J)"
		GameSettings.encountertable = 0x8379304
		GameSettings.version = GameSettings.VERSIONS.RS
		GameSettings.language = GameSettings.LANGUAGES.J
	elseif gamecode == 0x4158504A then
		GameSettings.game = 4
		GameSettings.gamename = "Pokemon Sapphire (J)"
		GameSettings.encountertable = 0x83792FC
		GameSettings.version = GameSettings.VERSIONS.RS
		GameSettings.language = GameSettings.LANGUAGES.J
	elseif gamecode == 0x4250454A then
		GameSettings.game = 5
		GameSettings.gamename = "Pokemon Emerald (J)"
		GameSettings.encountertable = 0x852D9F4
		GameSettings.version = GameSettings.VERSIONS.E
		GameSettings.language = GameSettings.LANGUAGES.J
	elseif gamecode == 0x4250524A then
		GameSettings.game = 6
		GameSettings.gamename = "Pokemon FireRed (J)"
		GameSettings.encountertable = 0x8390B34
		GameSettings.version = GameSettings.VERSIONS.FRLG
		GameSettings.language = GameSettings.LANGUAGES.J
	elseif gamecode == 0x4250474A then
		GameSettings.game = 6
		GameSettings.gamename = "Pokemon LeafGreen (J)"
		GameSettings.encountertable = 0x83909A4
		GameSettings.version = GameSettings.VERSIONS.FRLG
		GameSettings.language = GameSettings.LANGUAGES.J
	elseif gamecode == 0x41585653 then
		GameSettings.game = 7
		GameSettings.gamename = "Pokemon Ruby (S)"
		GameSettings.encountertable = 0x0
		GameSettings.version = GameSettings.VERSIONS.RS
		GameSettings.language = GameSettings.LANGUAGES.S
	elseif gamecode == 0x41585053 then
		GameSettings.game = 7
		GameSettings.gamename = "Pokemon Sapphire (S)"
		GameSettings.encountertable = 0x0
		GameSettings.version = GameSettings.VERSIONS.RS
		GameSettings.language = GameSettings.LANGUAGES.S
	elseif gamecode == 0x42504553 then
		GameSettings.game = 8
		GameSettings.gamename = "Pokemon Emerald (S)"
		GameSettings.encountertable = 0x0
		GameSettings.version = GameSettings.VERSIONS.E
		GameSettings.language = GameSettings.LANGUAGES.S
	elseif gamecode == 0x42505253 then
		GameSettings.game = 9
		GameSettings.gamename = "Pokemon FireRed (S)"
		GameSettings.encountertable = 0x0
		GameSettings.version = GameSettings.VERSIONS.FRLG
		GameSettings.language = GameSettings.LANGUAGES.S
	elseif gamecode == 0x42504753 then
		GameSettings.game = 9
		GameSettings.gamename = "Pokemon LeafGreen (S)"
		GameSettings.encountertable = 0x0
		GameSettings.version = GameSettings.VERSIONS.FRLG
		GameSettings.language = GameSettings.LANGUAGES.S
	else
		GameSettings.game = 0
		GameSettings.gamename = "Unsupported game"
		GameSettings.encountertable = 0
	end

	if GameSettings.game > 0 then
		GameSettings.pstats = pstats[GameSettings.game]
		GameSettings.pcount = pcount[GameSettings.game]
		GameSettings.estats = estats[GameSettings.game]
		GameSettings.rng = rng[GameSettings.game]
		GameSettings.rng2 = rng2[GameSettings.game]
		GameSettings.wram = wram[GameSettings.game]
		GameSettings.mapbank = mapbank[GameSettings.game]
		GameSettings.mapid = mapid[GameSettings.game]
		GameSettings.trainerpointer = trainerpointer[GameSettings.game]
		GameSettings.coords = coords[GameSettings.game]
		GameSettings.roamerpokemonoffset = roamerpokemonoffset[GameSettings.game]
	end
	
	if GameSettings.game % 3 == 1 then
		GameSettings.rngseed = 0x5A0
	else
		GameSettings.rngseed = Memory.readword(GameSettings.wram)
	end
end