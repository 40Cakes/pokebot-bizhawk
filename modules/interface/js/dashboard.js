host = window.location.protocol + "//" + window.location.host

function trainer() {
    $.ajax({
        method: "GET",
        url: host + "/trainer",
        crossDomain: true,
        dataType: "json",
        format: "json",
        timeout: 50,
    }).done(function(trainer) {
        $("#trainer_id").text(trainer["tid"]);
        $("#trainer_secret").text(trainer["sid"]);
        $("#trainer_map_bank_id").text(
            trainer["mapBank"] + ":" + trainer["mapId"]
        );
        $("#trainer_coords").text(
            "X " + trainer["posX"] + ", Y " + trainer["posY"]
        );
        $("#trainer_state").text(trainer["state"]);
    });
}

function get_type_image(type_str) {
    return `<img src=\"/interface/sprites/types/${type_str}.png\">`;
}

function encounter() {
    $.ajax({
        method: "GET",
        url: host + "/encounter",
        crossDomain: true,
        dataType: "json",
        format: "json",
        timeout: 50,
    }).done(function(encounter) {
        $(".opponent_name").text(encounter["name"]);
        $("#health-bar-fill").css(
            "width",
            (encounter["hp"] / encounter["maxHP"]) * 100 + "%"
        );

        if (encounter["shiny"]) {
            $("#opponent_name").css("color", "gold");
            $("#opponent_shiny").text("Yes!");
            $("#opponent_sprite").attr(
                "src",
                "/interface/sprites/pokemon/shiny/" + encounter["name"] + ".png"
            );
            $("#opponent_shiny").css("color", "gold");
            $("#opponent_shiny_value").css("color", "gold");
        } else {
            $("#opponent_shiny").text("No");
            $("#opponent_sprite").attr(
                "src",
                "/interface/sprites/pokemon/" + encounter["name"] + ".png"
            );
            $("#opponent_shiny").css("color", "red");
            $("#opponent_shiny_value").css("color", "red");
            $("#opponent_name").css("color", "");
        }
        $("#opponent_shiny_value").text(
            encounter["shinyValue"].toLocaleString()
        );
        $("#opponent_hidden_power_type").html(
            get_type_image(encounter["hiddenPowerType"])
        );
        $("#opponent_personality").text(encounter["personality"]);
        $("#opponent_hp").text(encounter["hp"].toLocaleString());
        $("#opponent_hp_iv").text(encounter["hpIV"]);
        $("#opponent_attack").text(encounter["attack"].toLocaleString());
        $("#opponent_attack_iv").text(encounter["attackIV"]);
        $("#opponent_defense").text(encounter["defense"].toLocaleString());
        $("#opponent_defense_iv").text(encounter["defenseIV"]);
        $("#opponent_spattack").text(encounter["spAttack"].toLocaleString());
        $("#opponent_spattack_iv").text(encounter["spAttackIV"]);
        $("#opponent_spdef").text(encounter["spDefense"].toLocaleString());
        $("#opponent_spdef_iv").text(encounter["spDefenseIV"]);
        $("#opponent_speed").text(encounter["speed"].toLocaleString());
        $("#opponent_speed_iv").text(encounter["speedIV"]);

        if (encounter["hpIV"] <= 15) {
            $("#opponent_hp_iv").css("color", "red");
        } else if (encounter["hpIV"] <= 30) {
            $("#opponent_hp_iv").css("color", "green");
        } else {
            $("#opponent_hp_iv").css("color", "gold");
        }
        if (encounter["attackIV"] <= 15) {
            $("#opponent_attack_iv").css("color", "red");
        } else if (encounter["attackIV"] <= 30) {
            $("#opponent_attack_iv").css("color", "green");
        } else {
            $("#opponent_attack_iv").css("color", "gold");
        }
        if (encounter["defenseIV"] <= 15) {
            $("#opponent_defense_iv").css("color", "red");
        } else if (encounter["defenseIV"] <= 30) {
            $("#opponent_defense_iv").css("color", "green");
        } else {
            $("#opponent_defense_iv").css("color", "gold");
        }
        if (encounter["spAttackIV"] <= 15) {
            $("#opponent_spattack_iv").css("color", "red");
        } else if (encounter["spAttackIV"] <= 30) {
            $("#opponent_spattack_iv").css("color", "green");
        } else {
            $("#opponent_spattack_iv").css("color", "gold");
        }
        if (encounter["spDefenseIV"] <= 15) {
            $("#opponent_spdef_iv").css("color", "red");
        } else if (encounter["spDefenseIV"] <= 30) {
            $("#opponent_spdef_iv").css("color", "green");
        } else {
            $("#opponent_spdef_iv").css("color", "gold");
        }
        if (encounter["speedIV"] <= 15) {
            $("#opponent_speed_iv").css("color", "red");
        } else if (encounter["speedIV"] <= 30) {
            $("#opponent_speed_iv").css("color", "green");
        } else {
            $("#opponent_speed_iv").css("color", "gold");
        }

        $("#opponent_level").text(encounter["level"]);
        $("#opponent_nature").text(encounter["nature"]);
        $("#opponent_location").text(encounter["metLocationName"]);
        $("#opponent_item").text(encounter["itemName"]);
        $("#opponent_item_image").attr(
            "src",
            "/interface/sprites/items/" + encounter["itemName"] + ".png"
        );

        encounter["type"] = encounter["type"].filter((e) => e !== "Fairy");
        var types = "";
        var arrayLength = encounter["type"].length;
        for (var o = 0; o < arrayLength; o++) {
            types +=
                get_type_image(encounter["type"][o]) +
                String(encounter["type"][o] != 0 && arrayLength != 1 ? "" : " ");
        }
        $("#opponent_type").html(types);

        if (encounter["stats"]) {
            $("#opponent_phase_encounters").text(
                encounter["stats"]["phase_encounters"].toLocaleString()
            );
            $("#opponent_encounters").text(
                encounter["stats"]["encounters"].toLocaleString()
            );
            $("#opponent_shiny_encounters").text(
                encounter["stats"]["shiny_encounters"].toLocaleString()
            );
            $("#opponent_shiny_average").text(
                encounter["stats"]["shiny_average"]
            );
            $("#opponent_phase_lowest_sv").text(
                encounter["stats"]["phase_lowest_sv"].toLocaleString()
            );
        } else {
            $("#opponent_encounters").text("-");
            $("#opponent_phase_encounters").text("-");
            $("#opponent_shiny_encounters").text("-");
            $("#opponent_shiny_average").text("-");
            $("#opponent_phase_lowest_sv").text("-");
        }

        if (encounter["stats"]["phase_lowest_sv"] < 8) {
            $("#opponent_phase_lowest_sv").css("color", "green");
        } else {
            $("#opponent_phase_lowest_sv").css("color", "red");
        }

        for (i of Array(4).keys()) {
            if (encounter["moves"][i]) {
                $("#opponent_move_" + i).text(
                    encounter["enrichedMoves"][i]["name"]
                );
                $("#opponent_move_pp_" + i).text(
                    encounter["pp"][i] + "/" + encounter["enrichedMoves"][i]["pp"]
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
        url: host + "/encounter_log",
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
        url: host + "/shiny_log",
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

function stats() {
    $.ajax({
        method: "GET",
        url: host + "/stats",
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
    encounter();
}, 250);

window.setInterval(function() {
    trainer();
}, 50);

window.setInterval(function() {
    stats();
}, 500);

trainer();
encounter();
encounter_log();