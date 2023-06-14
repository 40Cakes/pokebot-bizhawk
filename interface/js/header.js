function header_stats_data() {
    $.ajax({
        method: "GET",
        url: "http://127.0.0.1:8888/stats",
        crossDomain: true,
        dataType: "json",
        format: "json",
        timeout: 50,
    }).done(function(stats) {
        $("#nav_stat_phase").text(
            stats["totals"]["phase_encounters"].toLocaleString()
        );
        $("#nav_stat_total").text(stats["totals"]["encounters"].toLocaleString());
        $("#nav_stat_shiny").text(
            stats["totals"]["shiny_encounters"].toLocaleString()
        );
    });
}

// get info from emulator for game / fps
function header_emu_data() {
    $.ajax({
        method: "GET",
        url: "http://127.0.0.1:8888/emu_data",
        crossDomain: true,
        dataType: "json",
        format: "json",
        timeout: 50,
    }).done(function(emu_data) {
        $("#nav_emu_data").text(
            emu_data["detectedGame"] + " | " + emu_data["fps"] + "fps"
        );
    });
}

// encounter log for encounters/hr
function header_encounter_log() {
    $.ajax({
        method: "GET",
        url: "http://127.0.0.1:8888/encounter_log",
        crossDomain: true,
        dataType: "json",
        format: "json",
        timeout: 50,
    }).done(function(encounter_log) {
        reverse_encounter_log = encounter_log["encounter_log"].reverse();
        if (encounter_log["encounter_log"][50]) {
            var range = moment(reverse_encounter_log[0]["time_encountered"])
                .subtract(moment(reverse_encounter_log[10]["time_encountered"]))
                .format("x");
            $("#encounters_hour").text(
                Math.round((60 / (range / 1000 / 60)) * 10).toLocaleString() + "/h"
            );
        } else {
            $("#encounters_hour").text("-");
        }
    });
}

// needed for encounters/hr calculation,
// phase encounters/total encounters/shinys
window.setInterval(function() {
    header_encounter_log();
    header_stats_data();
    header_emu_data();
}, 1000);
header_encounter_log();
header_stats_data();
header_emu_data();