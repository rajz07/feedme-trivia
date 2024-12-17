const playersGrid = document.getElementById("playersGrid");

function updatePlayersList(players) {
    playersGrid.innerHTML = ""; // Clear existing players
    players.forEach(player => {
        const tile = document.createElement("div");
        tile.className = "player-tile";
        tile.textContent = player;
        playersGrid.appendChild(tile);
    });
}

// Simulate adding players dynamically
socket.on("player_list", (players) => {
    updatePlayersList(players);
});

