import cv2
import json
import logging

import flask
from flask import Flask, abort, jsonify, make_response, request
from flask_cors import CORS

from modules.Config import GetConfig
from modules.CatchBlockList import GetBlockList, BlockListManagement
from modules.Files import ReadFile
from modules.Stats import GetEncounterLog, GetEncounterRate, GetShinyLog, GetStats
from modules.mmf.Emu import GetEmu
from modules.mmf.Pokemon import GetParty
from modules.mmf.Screenshot import GetScreenshot
from modules.mmf.Trainer import GetTrainer

config = GetConfig()

PokedexList = json.loads(ReadFile("./modules/data/pokedex.json"))


def httpServer():
    """Run Flask server to make bot data available via HTTP GET"""
    try:
        log = logging.getLogger("werkzeug")
        log.setLevel(logging.ERROR)

        server = Flask(__name__, static_folder="./interface")
        CORS(server)

        @server.route("/dashboard", methods=["GET"])
        def Dashboard():
            return flask.render_template("dashboard.html")

        @server.route("/dashboard/pokedex", methods=["GET"])
        def DashboardPokedex():
            return flask.render_template("pokedex.html")

        @server.route("/dashboard/debug", methods=["GET"])
        def DashboardDebug():
            return flask.render_template("debug.html")

        @server.route("/trainer", methods=["GET"])
        def Trainer():
            trainer = GetTrainer()
            if trainer:
                return jsonify(trainer)
            abort(503)

        @server.route("/party", methods=["GET"])
        def Party():
            party = GetParty()
            if party:
                return jsonify(party)
            abort(503)

        @server.route("/encounter", methods=["GET"])
        def Encounter():
            encounter_logs = GetEncounterLog()["encounter_log"]
            if len(encounter_logs) > 0 and encounter_logs[-1]["pokemon_obj"]:
                encounter = encounter_logs.pop()["pokemon_obj"]
                stats = GetStats()
                if stats:
                    try:
                        encounter["stats"] = stats["pokemon"][encounter["name"]]
                        return jsonify(encounter)
                    except:
                        abort(503)
                return jsonify(encounter)
            abort(503)

        @server.route("/encounter_rate", methods=["GET"])
        def EncounterRate():
            try:
                return jsonify({"encounter_rate": GetEncounterRate()})
            except:
                return jsonify({"encounter_rate": "-"})
            abort(503)

        @server.route("/emu", methods=["GET"])
        def Emu():
            emu = GetEmu()
            if emu:
                return jsonify(emu)
            abort(503)

        @server.route("/stats", methods=["GET"])
        def Stats():
            stats = GetStats()
            if stats:
                return jsonify(stats)
            abort(503)

        @server.route("/encounter_log", methods=["GET"])
        def EncounterLog():
            recent_encounter_log = GetEncounterLog()["encounter_log"][-25:]
            if recent_encounter_log:
                encounter_log = {"encounter_log": recent_encounter_log}
                return jsonify(encounter_log)
            abort(503)

        @server.route("/shiny_log", methods=["GET"])
        def ShinyLog():
            shiny_log = GetShinyLog()
            if shiny_log:
                return jsonify(shiny_log)
            abort(503)

        # TODO Missing route_list
        # @server.route("/routes", methods=["GET"])
        # def Routes():
        #     if route_list:
        #         return route_list
        #     else:
        #         abort(503)

        @server.route("/pokedex", methods=["GET"])
        def Pokedex():
            if PokedexList:
                return PokedexList
            abort(503)

        # @server.route("/config", methods=["POST"])
        # def Config():
        #    response = jsonify({})
        #    return response

        @server.route("/updateblocklist", methods=["POST"])
        def UpdateBlockList():
           data = request.json
           pkmName = data.get('pokemonName')
           sprite = data.get('spriteLoaded')
           catch = True
           if '-disabled' in sprite:
             catch = False
           else: catch = True
           BlockListManagement(pkmName, catch)
           return "OK", 200

        @server.route("/blocked", methods=["GET"])
        def Blocked():
            block_list = GetBlockList()
            return block_list

        @server.route("/screenshot.png", methods=["GET"])
        def Screenshot():
            screenshot = GetScreenshot()
            if screenshot.any():
                buffer = cv2.imencode('.png', screenshot)[1]
                response = make_response(buffer.tobytes())
                response.headers['Content-Type'] = 'image/png'
                return response
            abort(503)

        server.run(debug=False, threaded=True, host=config["server"]["ip"], port=config["server"]["port"])
    except Exception as e:
        log.debug(str(e))
