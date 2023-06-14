function trainer_data() {
    $.ajax({
        method: "GET",
        url: "http://127.0.0.1:8888/trainer_data",
        crossDomain: true,
        dataType: "json",
        format: "json",
        timeout: 50,
    }).done(function(trainer_data) {
        $("#trainer_id").text(trainer_data["tid"]);
        $("#trainer_secret").text(trainer_data["sid"]);
        $("#trainer_map_bank_id").text(
            trainer_data["mapBank"] + ":" + trainer_data["mapId"]
        );
        $("#trainer_coords").text(
            "X " + trainer_data["posX"] + ", Y " + trainer_data["posY"]
        );
        $("#trainer_state").text(trainer_data["state"]);
    });
}

function get_type_image(type_str) {
    return `<img src=\"/interface/sprites/types/${type_str}.png\">`;
}

function encounter_info() {
    $.ajax({
        method: "GET",
        url: "http://127.0.0.1:8888/encounter_info",
        crossDomain: true,
        dataType: "json",
        format: "json",
        timeout: 50,
    }).done(function(encounter_info) {
        $(".opponent_name").text(encounter_info["name"]);
        $("#health-bar-fill").css(
            "width",
            (encounter_info["hp"] / encounter_info["maxHP"]) * 100 + "%"
        );

        if (encounter_info["shiny"]) {
            $("#opponent_name").css("color", "gold");
            $("#opponent_shiny").text("Yes!");
            $("#opponent_sprite").attr(
                "src",
                "/interface/sprites/pokemon/shiny/" + encounter_info["name"] + ".png"
            );
            $("#opponent_shiny").css("color", "gold");
            $("#opponent_shiny_value").css("color", "gold");
        } else {
            $("#opponent_shiny").text("No");
            $("#opponent_sprite").attr(
                "src",
                "/interface/sprites/pokemon/" + encounter_info["name"] + ".png"
            );
            $("#opponent_shiny").css("color", "red");
            $("#opponent_shiny_value").css("color", "red");
            $("#opponent_name").css("color", "");
        }
        $("#opponent_shiny_value").text(
            encounter_info["shinyValue"].toLocaleString()
        );
        $("#opponent_hidden_power_type").html(
            get_type_image(encounter_info["hiddenPowerType"])
        );
        $("#opponent_personality").text(encounter_info["personality"]);
        $("#opponent_hp").text(encounter_info["hp"].toLocaleString());
        $("#opponent_hp_iv").text(encounter_info["hpIV"]);
        $("#opponent_attack").text(encounter_info["attack"].toLocaleString());
        $("#opponent_attack_iv").text(encounter_info["attackIV"]);
        $("#opponent_defense").text(encounter_info["defense"].toLocaleString());
        $("#opponent_defense_iv").text(encounter_info["defenseIV"]);
        $("#opponent_spattack").text(encounter_info["spAttack"].toLocaleString());
        $("#opponent_spattack_iv").text(encounter_info["spAttackIV"]);
        $("#opponent_spdef").text(encounter_info["spDefense"].toLocaleString());
        $("#opponent_spdef_iv").text(encounter_info["spDefenseIV"]);
        $("#opponent_speed").text(encounter_info["speed"].toLocaleString());
        $("#opponent_speed_iv").text(encounter_info["speedIV"]);

        if (encounter_info["hpIV"] <= 15) {
            $("#opponent_hp_iv").css("color", "red");
        } else if (encounter_info["hpIV"] <= 30) {
            $("#opponent_hp_iv").css("color", "green");
        } else {
            $("#opponent_hp_iv").css("color", "gold");
        }
        if (encounter_info["attackIV"] <= 15) {
            $("#opponent_attack_iv").css("color", "red");
        } else if (encounter_info["attackIV"] <= 30) {
            $("#opponent_attack_iv").css("color", "green");
        } else {
            $("#opponent_attack_iv").css("color", "gold");
        }
        if (encounter_info["defenseIV"] <= 15) {
            $("#opponent_defense_iv").css("color", "red");
        } else if (encounter_info["defenseIV"] <= 30) {
            $("#opponent_defense_iv").css("color", "green");
        } else {
            $("#opponent_defense_iv").css("color", "gold");
        }
        if (encounter_info["spAttackIV"] <= 15) {
            $("#opponent_spattack_iv").css("color", "red");
        } else if (encounter_info["spAttackIV"] <= 30) {
            $("#opponent_spattack_iv").css("color", "green");
        } else {
            $("#opponent_spattack_iv").css("color", "gold");
        }
        if (encounter_info["spDefenseIV"] <= 15) {
            $("#opponent_spdef_iv").css("color", "red");
        } else if (encounter_info["spDefenseIV"] <= 30) {
            $("#opponent_spdef_iv").css("color", "green");
        } else {
            $("#opponent_spdef_iv").css("color", "gold");
        }
        if (encounter_info["speedIV"] <= 15) {
            $("#opponent_speed_iv").css("color", "red");
        } else if (encounter_info["speedIV"] <= 30) {
            $("#opponent_speed_iv").css("color", "green");
        } else {
            $("#opponent_speed_iv").css("color", "gold");
        }

        $("#opponent_level").text(encounter_info["level"]);
        $("#opponent_nature").text(encounter_info["nature"]);
        $("#opponent_location").text(encounter_info["metLocationName"]);
        $("#opponent_item").text(encounter_info["itemName"]);
        $("#opponent_item_image").attr(
            "src",
            "/interface/sprites/items/" + encounter_info["itemName"] + ".png"
        );

        encounter_info["type"] = encounter_info["type"].filter((e) => e !== "Fairy");
        var types = "";
        var arrayLength = encounter_info["type"].length;
        for (var o = 0; o < arrayLength; o++) {
            types +=
                get_type_image(encounter_info["type"][o]) +
                String(encounter_info["type"][o] != 0 && arrayLength != 1 ? "" : " ");
        }
        $("#opponent_type").html(types);

        if (encounter_info["stats"]) {
            $("#opponent_phase_encounters").text(
                encounter_info["stats"]["phase_encounters"].toLocaleString()
            );
            $("#opponent_encounters").text(
                encounter_info["stats"]["encounters"].toLocaleString()
            );
            $("#opponent_shiny_encounters").text(
                encounter_info["stats"]["shiny_encounters"].toLocaleString()
            );
            $("#opponent_shiny_average").text(
                encounter_info["stats"]["shiny_average"]
            );
            $("#opponent_phase_lowest_sv").text(
                encounter_info["stats"]["phase_lowest_sv"].toLocaleString()
            );
        } else {
            $("#opponent_encounters").text("-");
            $("#opponent_phase_encounters").text("-");
            $("#opponent_shiny_encounters").text("-");
            $("#opponent_shiny_average").text("-");
            $("#opponent_phase_lowest_sv").text("-");
        }

        if (encounter_info["stats"]["phase_lowest_sv"] < 8) {
            $("#opponent_phase_lowest_sv").css("color", "green");
        } else {
            $("#opponent_phase_lowest_sv").css("color", "red");
        }

        for (i of Array(4).keys()) {
            if (encounter_info["moves"][i]) {
                $("#opponent_move_" + i).text(
                    encounter_info["enrichedMoves"][i]["name"]
                );
                $("#opponent_move_pp_" + i).text(
                    encounter_info["pp"][i] + "/" + encounter_info["enrichedMoves"][i]["pp"]
                );
            } else {
                $("#opponent_move_" + i).text("-");
                $("#opponent_move_pp_" + i).text("-");
            }
        }
    });
}

function encounter_log() {
    $.ajax({
        method: "GET",
        url: "http://127.0.0.1:8888/encounter_log",
        crossDomain: true,
        dataType: "json",
        format: "json",
        timeout: 50,
    }).done(function(encounter_log) {
        var tr = "";

        var wrapper = document.getElementById("encounter_log");

        reverse_encounter_log = encounter_log["encounter_log"].reverse();

        for (var i = 0; i < 25; i++) {
            if (reverse_encounter_log[i]) {
                if (reverse_encounter_log[i]["pokemon_obj"]["shiny"]) {
                    sprite_dir = "shiny/";
                    sv_colour = "gold";
                } else {
                    sprite_dir = "";
                    sv_colour = "red";
                }

                tr +=
                    '<tr><td><img class="sprite32" src="/interface/sprites/pokemon/' +
                    sprite_dir +
                    reverse_encounter_log[i]["pokemon_obj"]["name"] +
                    '.png"></td><td class="text-center">' +
                    reverse_encounter_log[i]["pokemon_obj"]["name"] +
                    '</td><td class="text-center">' +
                    reverse_encounter_log[i]["pokemon_obj"]["level"] +
                    '</td><td class="text-center">' +
                    reverse_encounter_log[i]["pokemon_obj"]["nature"] +
                    '</td><td class="text-center"><img title="' +
                    reverse_encounter_log[i]["pokemon_obj"]["itemName"] +
                    '" class="sprite16" src="/interface/sprites/items/' +
                    reverse_encounter_log[i]["pokemon_obj"]["itemName"] +
                    '.png"></td><td class="text-center"><code class="code">' +
                    reverse_encounter_log[i]["pokemon_obj"]["personality"] +
                    '</code></td><td class="text-center" style="color:' +
                    sv_colour +
                    ';">' +
                    reverse_encounter_log[i]["pokemon_obj"][
                        "shinyValue"
                    ].toLocaleString() +
                    "</td></tr>";
            }
        }

        wrapper.innerHTML = tr;
    });
}

function shiny_log() {
    $.ajax({
        method: "GET",
        url: "http://127.0.0.1:8888/shiny_log",
        crossDomain: true,
        dataType: "json",
        format: "json",
        timeout: 50,
    }).done(function(shiny_log) {
        var tr = "";
        var wrapper = document.getElementById("shiny_log");

        reverse_shiny_log = shiny_log["shiny_log"].reverse();

        for (var i = 0; i < 25; i++) {
            if (reverse_shiny_log[i]) {
                if (reverse_shiny_log[i]["pokemon_obj"]["shiny"]) {
                    sprite_dir = "shiny/";
                    sv_colour = "gold";
                } else {
                    sprite_dir = "";
                    sv_colour = "red";
                }
                tr +=
                    '<tr><td><img class="sprite32" src="/interface/sprites/pokemon/' +
                    sprite_dir +
                    reverse_shiny_log[i]["pokemon_obj"]["name"] +
                    '.png"></td><td class="text-center">' +
                    reverse_shiny_log[i]["pokemon_obj"]["name"] +
                    '</td><td class="text-center">' +
                    reverse_shiny_log[i]["pokemon_obj"]["level"] +
                    '</td><td class="text-center">' +
                    reverse_shiny_log[i]["pokemon_obj"]["nature"] +
                    '</td><td class="text-center"><img title="' +
                    reverse_shiny_log[i]["pokemon_obj"]["itemName"] +
                    '" class="sprite16" src="/interface/sprites/items/' +
                    reverse_shiny_log[i]["pokemon_obj"]["itemName"] +
                    '.png"></td><td class="text-center"><code class="code">' +
                    reverse_shiny_log[i]["pokemon_obj"]["personality"] +
                    '</code></td><td class="text-center" style="color:' +
                    sv_colour +
                    ';">' +
                    reverse_shiny_log[i]["pokemon_obj"]["shinyValue"].toLocaleString() +
                    "</td></tr>";
            }
        }

        wrapper.innerHTML = tr;
    });
}

function stats_data() {
    $.ajax({
        method: "GET",
        url: "http://127.0.0.1:8888/stats",
        crossDomain: true,
        dataType: "json",
        format: "json",
        timeout: 50,
    }).done(function(stats) {
        $("#stats_phase_encounters").text(
            stats["totals"]["phase_encounters"].toLocaleString()
        );
        $("#stats_shiny_encounters").text(
            stats["totals"]["shiny_encounters"].toLocaleString()
        );
        $("#stats_total_encounters").text(
            stats["totals"]["encounters"].toLocaleString()
        );
        $("#stats_shiny_average").text(stats["totals"]["shiny_average"]);
        $("#stats_shortest_phase").text(
            stats["totals"]["shortest_phase_encounters"].toLocaleString()
        );
        $("#stats_longest_phase").text(
            stats["totals"]["longest_phase_encounters"].toLocaleString()
        );
    });
}

window.setInterval(function() {
    shiny_log();
}, 1000);

shiny_log();
window.setInterval(function() {
    encounter_log();
}, 1000);

window.setInterval(function() {
    encounter_info();
}, 250);

window.setInterval(function() {
    trainer_data();
}, 50);

window.setInterval(function() {
    stats_data();
}, 500);

trainer_data();
encounter_info();
encounter_log();