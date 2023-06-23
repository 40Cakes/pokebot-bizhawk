host = window.location.protocol + "//" + window.location.host

function trainer() {
    $.ajax({
        method: "GET",
        url: host + "/trainer",
        crossDomain: true,
        dataType: "json",
        format: "json",
        timeout: 500,
    }).done(function(trainer) {
        $("#trainer").text(JSON.stringify(trainer, null, 4));
    });
}

function encounter() {
    $.ajax({
        method: "GET",
        url: host + "/encounter",
        crossDomain: true,
        dataType: "json",
        format: "json",
        timeout: 1000,
    }).done(function(encounter) {
        $("#encounter").text(JSON.stringify(encounter, null, 4));
    });
}

function encounter_log() {
    $.ajax({
        method: "GET",
        url: host + "/encounter_log",
        crossDomain: true,
        dataType: "json",
        format: "json",
        timeout: 1000,
    }).done(function(encounter_log) {
        $("#encounter_log").text(JSON.stringify(encounter_log, null, 4));
    });
}

function shiny_log() {
    $.ajax({
        method: "GET",
        url: host + "/shiny_log",
        crossDomain: true,
        dataType: "json",
        format: "json",
        timeout: 1000,
    }).done(function(shiny_log) {
        $("#shiny_log").text(JSON.stringify(shiny_log, null, 4));
    });
}

function stats() {
    $.ajax({
        method: "GET",
        url: host + "/stats",
        crossDomain: true,
        dataType: "json",
        format: "json",
        timeout: 1000,
    }).done(function(stats) {
        $("#stats").text(JSON.stringify(stats, null, 4));
    });
}

function emulator() {
    $.ajax({
        method: "GET",
        url: host + "/emu",
        crossDomain: true,
        dataType: "json",
        format: "json",
        timeout: 1000,
    }).done(function(emu) {
        $("#emu").text(JSON.stringify(emu, null, 4));
    });
}

function party() {
    $.ajax({
        method: "GET",
        url: host + "/party",
        crossDomain: true,
        dataType: "json",
        format: "json",
        timeout: 1000,
    }).done(function(party) {
        $("#party").text(JSON.stringify(party, null, 4));
    });
}

trainer();
encounter();
encounter_log();
shiny_log();
stats();
emulator();
party();