host = window.location.protocol + "//" + window.location.host

function header_stats() {
    $.ajax({
        method: "GET",
        url: host + "/stats",
        crossDomain: true,
        dataType: "json",
        format: "json",
        timeout: 2500,
    }).done(function(stats) {
        $("#nav_stat_phase").text(
            stats["totals"]["phase_encounters"].toLocaleString()
        );
        $("#nav_stat_total").text(stats["totals"]["encounters"].toLocaleString());

        stats["totals"]["shiny_encounters"] = (stats["totals"]["shiny_encounters"] === undefined) ? 0 : stats["totals"]["shiny_encounters"];
        $("#nav_stat_shiny").text(
            stats["totals"]["shiny_encounters"].toLocaleString()
        );
    });
}

// get info from emulator for game / fps
function header_emu() {
    $.ajax({
        method: "GET",
        url: host + "/emu",
        crossDomain: true,
        dataType: "json",
        format: "json",
        timeout: 2500,
    }).done(function(emu) {
        $("#nav_emu").text(
            emu["detectedGame"] + " | " + emu["fps"] + "fps"
        );
    });
}

// encounter log for encounters/hr
function header_encounter_rate() {
    $.ajax({
        method: "GET",
        url: host + "/encounter_rate",
        crossDomain: true,
        dataType: "json",
        format: "json",
        timeout: 2500,
    }).done(function(encounter_rate) {
        $("#encounters_hour").text(encounter_rate["encounter_rate"].toLocaleString() + "/h");
    });
}

// needed for encounters/hr calculation,
// phase encounters/total encounters/shinys
window.setInterval(function() {
    header_encounter_rate();
    header_stats();
    header_emu();
}, 2500);
header_encounter_rate();
header_stats();
header_emu();