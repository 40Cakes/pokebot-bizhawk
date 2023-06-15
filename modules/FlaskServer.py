import flask
import logging
from flask import Flask, abort, jsonify, request
from flask_cors import CORS

from modules.Config import GetConfig
from modules.mmf.Emu import GetEmu
from modules.mmf.Pokemon import GetOpponent, GetParty
from modules.mmf.Trainer import GetTrainer

config = GetConfig()

# TODO there's an issue with relative pathing, the static folder can't be found

pokedex_list = json.loads(read_file("data/pokedex.json")) # TODO

def httpServer(): # Run Flask server to make bot data available via HTTP GET
    try:
        log = logging.getLogger("werkzeug")
        log.setLevel(logging.ERROR)

        server = Flask(__name__,static_folder="interface")
        CORS(server)
        @server.route("/dashboard",methods=["GET"])
        def req_dashboard():
            return flask.render_template("dashboard.html")
        @server.route("/dashboard/pokedex",methods=["GET"])
        def req_dashboard_pokedex():
            return flask.render_template("pokedex.html")
        @server.route("/trainer_data", methods=["GET"])
        def req_trainer_data():
            trainer = GetTrainer()
            if trainer:
                response = jsonify(trainer)
                return response
            else: abort(503)
        @server.route("/party_data", methods=["GET"])
        def req_party_data():
            party = GetParty()
            if party:
                response = jsonify(party)
            else: abort(503)
        @server.route("/encounter_info", methods=["GET"])
        def req_encounter_info():
            match config["bot_mode"]: # change
                case "starters":
                    encounter = GetParty()[0]
                case other:
                    encounter = GetOpponent()
            if encounter:
                if stats: # TODO get stats from modules.Stats once created
                    try: 
                        encounter["stats"] = stats["pokemon"][encounter["name"]]
                        response = jsonify(encounter)
                        return response
                    except: abort(503)
                else: response = jsonify(encounter)
                return response
            else: abort(503)
        @server.route("/emu_data", methods=["GET"])
        def req_emu_data():
            emu = GetEmu()
            if emu:
                response = jsonify(emu)
                return response
            else: abort(503)
        @server.route("/stats", methods=["GET"])
        def req_stats():
            if stats:
                response = jsonify(stats)
                return response
            else: abort(503)
        @server.route("/encounter_log", methods=["GET"])
        def req_encounter_log():
            if encounter_log:
                response = jsonify(encounter_log)
                return response
            else: abort(503)
        @server.route("/shiny_log", methods=["GET"])		
        def req_shiny_log():		
            if shiny_log:		
                response = jsonify(shiny_log)		
                return response		
            else: abort(503)
        @server.route("/routes", methods=["GET"])
        def req_routes():
            if route_list:
                routes = route_list
                return routes
            else: abort(503)

        @server.route("/pokedex", methods=["GET"])
        def req_pokedex():
            if pokedex_list:
                pokedex = pokedex_list
                return pokedex
            else: abort(503)
        #@server.route("/config", methods=["POST"])
        #def submit_config():
        #    response = jsonify({})
        #    return response

        server.run(debug=False, threaded=True, host=config["ui"]["ip"], port=config["ui"]["port"])
    except Exception as e: log.exception(str(e))
