function stats_info() {
    $.ajax({
            method: "GET",
            url: "http://127.0.0.1:6969/stats",
            crossDomain: true,
            dataType: "json",
            format: "json",
            timeout: 50
        })
        .done(function(stats) {
            $("#stats_phase_encounters").text(stats["totals"]["phase_encounters"].toLocaleString());
            $("#stats_shiny_encounters").text(stats["totals"]["shiny_encounters"].toLocaleString());
            $("#stats_total_encounters").text(stats["totals"]["encounters"].toLocaleString());
            $("#stats_shiny_average").text(stats["totals"]["shiny_average"]);
            $("#stats_shortest_phase").text(stats["totals"]["shortest_phase_encounters"].toLocaleString());
            $("#stats_longest_phase").text(stats["totals"]["longest_phase_encounters"].toLocaleString());
            $("#nav_stat_phase").text(stats["totals"]["phase_encounters"].toLocaleString());
            $("#nav_stat_total").text(stats["totals"]["encounters"].toLocaleString());
            $("#nav_stat_shiny").text(stats["totals"]["shiny_encounters"].toLocaleString());
        })
}

function emu_info() {
    $.ajax({
            method: "GET",
            url: "http://127.0.0.1:6969/emu_info",
            crossDomain: true,
            dataType: "json",
            format: "json",
            timeout: 50
        })
        .done(function(emu_info) {
            $("#nav_emu_info").text(emu_info["detectedGame"] + " | " + emu_info["emuFPS"] + "fps");
        })

}

function trainer_info() {
    $.ajax({
            method: "GET",
            url: "http://127.0.0.1:6969/trainer_info",
            crossDomain: true,
            dataType: "json",
            format: "json",
            timeout: 50
        })
        .done(function(trainer_info) {
            $("#trainer_id").text(trainer_info["tid"]);
            $("#trainer_secret").text(trainer_info["sid"]);
            $("#trainer_map_bank_id").text(trainer_info["mapBank"] + ":" + trainer_info["mapId"]);
            $("#trainer_coords").text("X " + trainer_info["posX"] + ", Y " + trainer_info["posY"]);
            $("#trainer_state").text(trainer_info["state"]);
        })
}
function get_type_image(type_str){
    return `<img src=\"sprites/types/${type_str}.png\">`
        
}
function opponent_info() {
    $.ajax({
            method: "GET",
            url: "http://127.0.0.1:6969/opponent_info",
            crossDomain: true,
            dataType: "json",
            format: "json",
            timeout: 50
        })
        .done(function(opponent_info) {
            $(".opponent_name").text(opponent_info["name"]);
            $("#health-bar-fill").css("width", ((opponent_info["hp"] / opponent_info["maxHP"]) * 100) + "%");

            if (opponent_info["shiny"]) {
                $("#opponent_name").css("color", "gold");
                $("#opponent_shiny").text("Yes!");
                $("#opponent_sprite").attr("src", "./sprites/pokemon/static/shiny/" + opponent_info["name"] + ".png");
                $("#opponent_shiny").css("color", "gold");
                $("#opponent_shiny_value").css("color", "gold");
            } else {
                $("#opponent_shiny").text("No");
                $("#opponent_sprite").attr("src", "./sprites/pokemon/static/" + opponent_info["name"] + ".png");
                $("#opponent_shiny").css("color", "red");
                $("#opponent_shiny_value").css("color", "red");
                $("#opponent_name").css("color", "");
            }
            $("#opponent_shiny_value").text(opponent_info["shinyValue"].toLocaleString());
            $("#opponent_hidden_power_type").html(get_type_image(opponent_info["hiddenPowerType"]));
            $("#opponent_personality").text(opponent_info["personality"]);
            $("#opponent_hp").text(opponent_info["hp"].toLocaleString());
            $("#opponent_hp_iv").text(opponent_info["hpIV"]);
            $("#opponent_attack").text(opponent_info["attack"].toLocaleString());
            $("#opponent_attack_iv").text(opponent_info["attackIV"]);
            $("#opponent_defense").text(opponent_info["defense"].toLocaleString());
            $("#opponent_defense_iv").text(opponent_info["defenseIV"]);
            $("#opponent_spattack").text(opponent_info["spAttack"].toLocaleString());
            $("#opponent_spattack_iv").text(opponent_info["spAttackIV"]);
            $("#opponent_spdef").text(opponent_info["spDefense"].toLocaleString());
            $("#opponent_spdef_iv").text(opponent_info["spDefenseIV"]);
            $("#opponent_speed").text(opponent_info["speed"].toLocaleString());
            $("#opponent_speed_iv").text(opponent_info["speedIV"]);

            if (opponent_info["hpIV"] <= 15) {
                $("#opponent_hp_iv").css("color", "red");
            } else if (opponent_info["hpIV"] <= 30) {
                $("#opponent_hp_iv").css("color", "green");
            } else {
                $("#opponent_hp_iv").css("color", "gold");
            }
            if (opponent_info["attackIV"] <= 15) {
                $("#opponent_attack_iv").css("color", "red");
            } else if (opponent_info["attackIV"] <= 30) {
                $("#opponent_attack_iv").css("color", "green");
            } else {
                $("#opponent_attack_iv").css("color", "gold");
            }
            if (opponent_info["defenseIV"] <= 15) {
                $("#opponent_defense_iv").css("color", "red");
            } else if (opponent_info["defenseIV"] <= 30) {
                $("#opponent_defense_iv").css("color", "green");
            } else {
                $("#opponent_defense_iv").css("color", "gold");
            }
            if (opponent_info["spAttackIV"] <= 15) {
                $("#opponent_spattack_iv").css("color", "red");
            } else if (opponent_info["spAttackIV"] <= 30) {
                $("#opponent_spattack_iv").css("color", "green");
            } else {
                $("#opponent_spattack_iv").css("color", "gold");
            }
            if (opponent_info["spDefenseIV"] <= 15) {
                $("#opponent_spdef_iv").css("color", "red");
            } else if (opponent_info["spDefenseIV"] <= 30) {
                $("#opponent_spdef_iv").css("color", "green");
            } else {
                $("#opponent_spdef_iv").css("color", "gold");
            }
            if (opponent_info["speedIV"] <= 15) {
                $("#opponent_speed_iv").css("color", "red");
            } else if (opponent_info["speedIV"] <= 30) {
                $("#opponent_speed_iv").css("color", "green");
            } else {
                $("#opponent_speed_iv").css("color", "gold");
            }

            $("#opponent_level").text(opponent_info["level"]);
            $("#opponent_nature").text(opponent_info["nature"]);
            $("#opponent_location").text(opponent_info["metLocationName"]);
            $("#opponent_item").text(opponent_info["itemName"]);
            $("#opponent_item_image").attr("src", "./sprites/items/" + opponent_info["itemName"] + ".png");

            opponent_info["type"] = opponent_info["type"].filter(e => e !== "Fairy");
            var types = ""
            var arrayLength = opponent_info["type"].length;
            for (var o = 0; o < arrayLength; o++) {
                types += get_type_image(opponent_info["type"][o]) + String((opponent_info["type"][o] != 0 && arrayLength != 1)? '':' ');
            }
            $("#opponent_type").html(types);
            
            if (opponent_info["stats"]) {
                $("#opponent_phase_encounters").text(opponent_info["stats"]["phase_encounters"].toLocaleString());
                $("#opponent_encounters").text(opponent_info["stats"]["encounters"].toLocaleString());
                $("#opponent_shiny_encounters").text(opponent_info["stats"]["shiny_encounters"].toLocaleString());
                $("#opponent_shiny_average").text(opponent_info["stats"]["shiny_average"]);
                $("#opponent_phase_lowest_sv").text(opponent_info["stats"]["phase_lowest_sv"].toLocaleString());
            } else {
                $("#opponent_encounters").text("-");
                $("#opponent_phase_encounters").text("-");
                $("#opponent_shiny_encounters").text("-");
                $("#opponent_shiny_average").text("-");
                $("#opponent_phase_lowest_sv").text("-");
            }

            if (opponent_info["stats"]["phase_lowest_sv"] < 8) {
                $("#opponent_phase_lowest_sv").css("color", "green");
            } else {
                $("#opponent_phase_lowest_sv").css("color", "red");
            }

            for (i of Array(4).keys()) {
                if (opponent_info["moves"][i]) {
                    $("#opponent_move_" + i).text(opponent_info["enrichedMoves"][i]["name"]);
                    $("#opponent_move_pp_" + i).text(opponent_info["pp"][i] + "/" + opponent_info["enrichedMoves"][i]["pp"]);
                } else {
                    $("#opponent_move_" + i).text("-");
                    $("#opponent_move_pp_" + i).text("-");
                }
            }
        })
}

function encounter_log() {
    $.ajax({
            method: "GET",
            url: "http://127.0.0.1:6969/encounter_log",
            crossDomain: true,
            dataType: "json",
            format: "json",
            timeout: 50
        })
        .done(function(encounter_log) {
            var tr = ''
            var wrapper = document.getElementById("encounter_log");

            reverse_encounter_log = encounter_log["encounter_log"].reverse()

            for (var i = 0; i < 10; i++) {
                if (reverse_encounter_log[i]) {
                    if (reverse_encounter_log[i]["pokemon_obj"]["shiny"]) {
                        sprite_dir = "shiny/"
                        sv_colour = "gold"
                    } else {
                        sprite_dir = ""
                        sv_colour = "red"
                    }

                    tr += '<tr><td><img class="sprite32" src="./sprites/pokemon/static/' + sprite_dir + reverse_encounter_log[i]["pokemon_obj"]["name"] + '.png"></td><td class="text-center">' + reverse_encounter_log[i]["pokemon_obj"]["name"] + '</td><td class="text-center">' + reverse_encounter_log[i]["pokemon_obj"]["level"] + '</td><td class="text-center">' + reverse_encounter_log[i]["pokemon_obj"]["nature"] + '</td><td class="text-center"><img title="' + reverse_encounter_log[i]["pokemon_obj"]["itemName"] + '" class="sprite16" src="./sprites/items/' + reverse_encounter_log[i]["pokemon_obj"]["itemName"] + '.png"></td><td class="text-center"><code class="code">' + reverse_encounter_log[i]["pokemon_obj"]["personality"] + '</code></td><td class="text-center" style="color:' + sv_colour + ';">' + reverse_encounter_log[i]["pokemon_obj"]["shinyValue"].toLocaleString() + '</td></tr>'
                }
            }

            wrapper.innerHTML = tr

            if (encounter_log["encounter_log"][50]) {
                var range = (moment(reverse_encounter_log[0]["time_encountered"]).subtract(moment(reverse_encounter_log[10]["time_encountered"]))).format("x")
                $('#encounters_hour').text(Math.round((60 / (range / 1000 / 60)) * 10).toLocaleString() + "/h");
            } else {
                $('#encounters_hour').text("-");
            }
        })
}

window.setInterval(function() {
    encounter_log();
}, 1000);

window.setInterval(function() {
    stats_info();
    emu_info();
    opponent_info();
}, 250);

window.setInterval(function() {
    trainer_info();
}, 50);

stats_info();
emu_info();
trainer_info();
opponent_info();
encounter_log();