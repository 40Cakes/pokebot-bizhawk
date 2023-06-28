host = window.location.protocol + "//" + window.location.host;

var blocked = { block_list: [] };
function getBlocked() {
  $.ajax({
    method: "GET",
    url: host + "/blocked",
  }).done(function (blocklist) {
    blocked = blocklist;
  });
}
function dexEntries() {
  $.ajax({
    method: "GET",
    url: host + "/pokedex",
  }).done(function (dex) {
    var tableBody = document.querySelector("#pokedex");

    //sort by dex number
    var dexArray = dex.sort((a, b) => {
      var numberA = a.pokedex_id;
      var numberB = b.pokedex_id;
      return numberA - numberB;
    });
    //loop through dex and output data
    dexArray.forEach(function (pokemon) {
      var row = document.createElement("tr");

      var dexIDCell = document.createElement("td");
      dexIDCell.textContent = pokemon.pokedex_id; //dex number

      var imgCell = document.createElement("td");
      var pkmImg = document.createElement("img");
      imgCell.appendChild(pkmImg);
      var cleanedPokemonName = pokemon.name
        .replaceAll("'", "")
        .replaceAll("♀", "_F")
        .replaceAll("♂", "_M");
      pkmImg.src = "/interface/sprites/pokemon/" + cleanedPokemonName + ".png";
      row.setAttribute("data-pokemon", cleanedPokemonName);
      let locationStrings = pokemon.encounters.map((i) => i.location);
      row.setAttribute("data-locations", JSON.stringify(locationStrings));
      pkmImg.width = "50";

      var nameCell = document.createElement("td");
      nameCell.textContent = pokemon.name; //pokemon name

      var locationCell = document.createElement("td");
      if (pokemon.encounters.length > 0) {
        var groupedEncounters = {};

        pokemon.encounters.forEach((encounter) => {
          if (groupedEncounters[encounter.location]) {
            // If encounter location exists in groupedEncounters, append encounter details
            groupedEncounters[encounter.location].push(encounter);
          } else {
            // Otherwise, create a new entry in groupedEncounters
            groupedEncounters[encounter.location] = [encounter];
          }
        });

        // Iterate over grouped encounters and create elements
        Object.keys(groupedEncounters).forEach((location) => {
          var encounters = groupedEncounters[location];
          // Create pillbadge for each location it can be found on
          var div = document.createElement("div");
          var pill = document.createElement("span");
          pill.classList.add("badge");
          pill.classList.add("badge-pill");
          pill.style.margin = "0.5em";
          pill.textContent = location;
          pill.setAttribute("data-toggle", "dropdown");

          // dropdown solution
          div.classList.add("dropdown");
          div.classList.add("with-arrow");
          div.classList.add("toggle-on-hover");
          var dropdown = document.createElement("div");
          dropdown.classList.add("dropdown-menu");
          dropdown.style.padding = "0";

          // Create a table for the dropdown
          const table = document.createElement("table");
          const headerRow = document.createElement("tr");
          const methodHeader = document.createElement("th");
          methodHeader.textContent = "Method";
          headerRow.appendChild(methodHeader);
          const levelsHeader = document.createElement("th");
          levelsHeader.textContent = "Levels";
          headerRow.appendChild(levelsHeader);
          const rateHeader = document.createElement("th");
          rateHeader.textContent = "Rate";
          headerRow.appendChild(rateHeader);
          table.appendChild(headerRow);
          table.style.marginLeft = "1em";
          table.style.marginRight = "1em";
          table.style.tableLayout = "auto";

          // Set values for each encounter
          encounters.forEach((encounter) => {
            const valuesRow = document.createElement("tr");
            const methodCell = document.createElement("td");
            methodCell.style.whiteSpace = "nowrap";
            methodCell.textContent = getMethod(encounter.encounter_type);
            const levelsCell = document.createElement("td");
            levelsCell.style.whiteSpace = "nowrap";
            levelsCell.textContent = encounter.levels;
            const rateCell = document.createElement("td");
            rateCell.style.whiteSpace = "nowrap";
            rateCell.textContent = encounter.rate;
            valuesRow.appendChild(methodCell);
            valuesRow.appendChild(levelsCell);
            valuesRow.appendChild(rateCell);
            table.appendChild(valuesRow);
          });

          dropdown.appendChild(table);
          div.appendChild(pill);
          div.appendChild(dropdown);
          locationCell.appendChild(div);
        });
      } else {
        locationCell.textContent = "";
      }

      var catchPkm = document.createElement("td");
      var catchPkmBtn = document.createElement("button");
      var catchImg = "/interface/sprites/items/Poké Ball.png";
      var noCatchImg = "/interface/sprites/items/Poké Ball-disabled.png";
      var catchPkmImg = document.createElement("img");
      catchPkmImg.classList.add("pokeball-sprite");
      catchPkmImg.setAttribute("pokemon-name", pokemon.name);

      //check if pokemon is on the no-catch list, if so, disable the pokeball
      if (blocked["block_list"].includes(pokemon.name)) {
        catchPkmImg.src = noCatchImg;
      } else if (!blocked["block_list"].includes(pokemon.name)) {
        catchPkmImg.src = catchImg;
      }

      catchPkmBtn.appendChild(catchPkmImg);
      catchPkmBtn.style.all = "unset";

      catchPkmBtn.onclick = function () {
        //switch sprite depending on currently selected
        catchPkmImg.src.includes("-disabled")
          ? (catchPkmImg.src = catchImg)
          : (catchPkmImg.src = noCatchImg);
        //pass pkmname and current sprite to bot
        var data = {
          pokemonName: pokemon.name,
          spriteLoaded: catchPkmImg.src,
        };
        //send post req to flask with the data
        $.ajax({
          method: "POST",
          url: host + "/updateblocklist",
          crossDomain: true,
          contentType: "application/json",
          format: "json",
          data: JSON.stringify(data),
          timeout: 500,
        });
      };
      //if pokemon has encounters, show the button, otherwise don't
      if (pokemon.encounters.length > 0) {
        catchPkm.appendChild(catchPkmBtn);
      }

      // append the cells to the row
      row.appendChild(dexIDCell);
      row.appendChild(imgCell);
      row.appendChild(nameCell);
      row.appendChild(locationCell);
      row.appendChild(catchPkm);

      //add the row to the table #pokedex
      tableBody.appendChild(row);
    });
  });
}

getBlocked();
dexEntries();

//mess tbh, but it formats the encounter type nicer
function getMethod(method) {
  switch (method) {
    case "walking":
      return "Walking";
    case "walk":
      return "Walking";
    case "fishing_old":
      return "Old Rod";
    case "fishing_good":
      return "Good Rod";
    case "fishing_super":
      return "Super Rod";
    case "special":
      return "Special Encounter";
    case "deepsand":
      return "Deep Sand";
    case "rocksmash":
      return "Rock Smash";
    case "surfing":
      return "Surfing";
    case "surf":
      return "Surfing";
    case "grass":
      return "Grass";
    case "swarm":
      return "Swarm";
    case "trade":
      return "Trade";
    case "gift":
      return "Gift";
    case "roam":
      return "Roaming";
    case "underwater":
      return "Dive Underwater";
    case "wailmerpail":
      return "Wailmer Pail";
    case "hidden":
      return "Hidden";
    case "starter":
      return "Starter";
  }
}

// get info from stats
function stats() {
  $.ajax({
    method: "GET",
    url: host + "/stats",
    crossDomain: true,
    dataType: "json",
    format: "json",
    timeout: 2500,
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
function emu() {
  $.ajax({
    method: "GET",
    url: host + "/emu",
    crossDomain: true,
    dataType: "json",
    format: "json",
    timeout: 2500,
  }).done(function (emu) {
    $("#nav_emu").text(emu["detectedGame"] + " | " + emu["fps"] + "fps");
  });
}

// encounter log for encounters/hr
function encounter_log() {
  $.ajax({
    method: "GET",
    url: host + "/encounter_log",
    crossDomain: true,
    dataType: "json",
    format: "json",
    timeout: 2500,
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
  encounter_log();
  stats();
  emu();
}, 2500);

window.setInterval(function () {
  $.ajax({
    method: "GET",
    url: host + "/blocked",
  }).done(function (blocklist) {
    blocked = blocklist;
    checkBlocklist();
  });
}, 1000);

function checkBlocklist() {
  var pokeballs = document.getElementsByClassName("pokeball-sprite");
  for (var i = 0; i < pokeballs.length; i++) {
    var pokemonName = pokeballs[i].getAttribute("pokemon-name");
    if (blocked["block_list"].includes(pokemonName)) {
      pokeballs[i].src = "/interface/sprites/items/Poké Ball-disabled.png";
    } else {
      pokeballs[i].src = "/interface/sprites/items/Poké Ball.png";
    }
  }
}

// logic for search bar filtering on route/pokemon name
function filter() {
  let searchStr = document
    .getElementById("searchBar")
    .value.toLocaleLowerCase();
  const table = document.getElementById("pokedex");

  // filter table rows on data-pokemon or data-locations if either contain searchStr
  for (let row of table.children) {
    let pkmName = row.getAttribute("data-pokemon");
    let locations = row.getAttribute("data-locations");
    if (
      !pkmName.toLocaleLowerCase().includes(searchStr) &&
      !locations.toLocaleLowerCase().includes(searchStr)
    ) {
      row.style.display = "none";
    } else {
      row.style.display = "";
    }
  }
}
