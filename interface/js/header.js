function header_stats_info() {
  $.ajax({
    method: "GET",
    url: "http://127.0.0.1:6969/stats",
    crossDomain: true,
    dataType: "json",
    format: "json",
    timeout: 50,
  }).done(function (stats) {
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
function header_emu_info() {
  $.ajax({
    method: "GET",
    url: "http://127.0.0.1:6969/emu_info",
    crossDomain: true,
    dataType: "json",
    format: "json",
    timeout: 50,
  }).done(function (emu_info) {
    $("#nav_emu_info").text(
      emu_info["detectedGame"] + " | " + emu_info["emuFPS"] + "fps"
    );
  });
}

// encounter log for encounters/hr
function header_encounter_log() {
  $.ajax({
    method: "GET",
    url: "http://127.0.0.1:6969/encounter_log",
    crossDomain: true,
    dataType: "json",
    format: "json",
    timeout: 50,
  }).done(function (encounter_log) {
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
window.setInterval(function () {
  header_encounter_log();
  header_stats_info();
  header_emu_info();
}, 1000);
header_encounter_log();
header_stats_info();
header_emu_info();