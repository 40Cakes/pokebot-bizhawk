local utils = require("utils")

dofile (utils.translatePath("data\\lua\\Memory.lua"))
dofile (utils.translatePath("data\\lua\\GameSettings.lua"))

GameSettings.initialize()

console.log("Lua Version: ".._VERSION)
package.path = ";.\\data\\lua\\?.lua;"

function getTrainer()
	local trainer = Memory.readdword(GameSettings.trainerpointer)

	trainer = {
		state = Memory.readbyte(GameSettings.trainerpointer + 199),
		mapId = Memory.readbyte(GameSettings.trainerpointer + 200),
		mapBank = Memory.readbyte(GameSettings.trainerpointer + 201),
		posX = Memory.readbyte(GameSettings.coords + 0) - 7,
		posY = Memory.readbyte(GameSettings.coords + 2) - 7
	}

	return trainer
end

last_posY = 0
last_posX = 0
last_state = 0
last_mapBank = 0
last_mapId = 0

while true do
	trainer = getTrainer()

	if (last_state ~= trainer.state) then
		last_state = trainer.state
		gui.addmessage("State: " .. trainer.state)
	end

	if (last_posX ~= trainer.posX) or (last_posY ~= trainer.posY) then
		last_posY = trainer.posY
		last_posX = trainer.posX
		gui.addmessage("X: " .. trainer.posX .. ", Y: " .. trainer.posY)
	end

	if (last_mapBank ~= trainer.mapBank) or (last_mapId ~= trainer.mapId) then
		last_mapBank = trainer.mapBank
		last_mapId = trainer.mapId
		gui.addmessage("Map: " .. trainer.mapBank .. ":" .. trainer.mapId)
	end

	emu.frameadvance()
end
