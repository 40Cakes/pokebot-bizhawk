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
        document.getElementById("trainer").innerHTML = JSONTree.create(trainer)
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
        document.getElementById("encounter").innerHTML = JSONTree.create(encounter)
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
        document.getElementById("encounter_log").innerHTML = JSONTree.create(encounter_log)
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
        document.getElementById("shiny_log").innerHTML = JSONTree.create(shiny_log)
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
        document.getElementById("stats").innerHTML = JSONTree.create(stats)
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
        document.getElementById("emu").innerHTML = JSONTree.create(emu)
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
        document.getElementById("party").innerHTML = JSONTree.create(party)
    });
}

trainer();
encounter();
encounter_log();
shiny_log();
stats();
emulator();
party();