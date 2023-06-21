import json
import logging

import flask
from flask import Flask, abort, jsonify
from flask_cors import CORS

from modules.Config import GetConfig
from modules.Files import ReadFile
from modules.Stats import GetEncounterLog, GetShinyLog, GetStats
from modules.mmf.Emu import GetEmu
from modules.mmf.Pokemon import GetParty
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
            encounter = GetEncounterLog()["encounter_log"].pop()["pokemon_obj"]
            if encounter:
                stats = GetStats()
                if stats:
                    try:
                        encounter["stats"] = stats["pokemon"][encounter["name"]]
                        return jsonify(encounter)
                    except:
                        abort(503)
                else:
                    return jsonify(encounter)
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
            encounter_log = GetEncounterLog()
            if encounter_log:
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

        server.run(debug=False, threaded=True, host=config["server"]["ip"], port=config["server"]["port"])
    except Exception as e:
        log.debug(str(e))
