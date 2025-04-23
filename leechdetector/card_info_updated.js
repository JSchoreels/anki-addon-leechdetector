const healthy_color = "#22c55e";
const warning_color = "#fdba74";
const alert_color = "#f87171";

function add_lapse_stats() {
    const rows = document.querySelectorAll('tr');

    const table = document.getElementsByClassName('stats-table')[0];
    const tbody = table.querySelector('tbody') || table;

    tbody.insertAdjacentHTML('beforeend', `$table_html`)

    let oldHref = window.location.href;
    const observer = new MutationObserver(mutations => {
        if (oldHref !== document.location.href) {
            oldHref = document.location.href;
            new_card_id = get_cardid()// Handle trailing slash
            console.log("Card Change Detected")
            if (new_card_id) {
                request_lapseinfo(new_card_id)
            }
        }
    });

    body = document.querySelector('body');
    observer.observe(body, {characterData: true, childList: true, subtree: true});

    console.log(document.location.href)
    cardid = get_cardid()
    console.log(cardid)
    if (cardid){
        request_lapseinfo(cardid)
    }
}

function resetStyle(cells){
        Object.values(cells).forEach(cell => {
            cell.style.color = ""
            cell.style.fontWeight = ""
        });
}

function updateCellsContent(cells, lapseInfos){
        cells.leechStatusCell.textContent = lapseInfos.leech_status
        cells.pastMaxIntervalsCell.textContent = JSON.stringify(lapseInfos.past_max_intervals)
        cells.currentLapseMaxIntervalsCell.textContent = lapseInfos.current_lapse_max_intervals
        cells.performanceDropCountCell.textContent = lapseInfos.performance_drop_count
        cells.performanceDropRatioCell.textContent = (lapseInfos.performance_drop_ratio * 100).toFixed(2) + "%"
}

function colorCells(cells, lapseInfos){

        cells.leechStatusCell.style.fontWeight = "bold"
        cells.leechStatusCell.style.color = {
            Healthy: healthy_color,
            Recovered: healthy_color,
            Recovering: warning_color,
            Leech: alert_color
        }[lapseInfos.leech_status];

        const maxPastInterval = Math.max(...lapseInfos.past_max_intervals);

        if (lapseInfos.current_lapse_max_intervals > maxPastInterval * 2) {
            cells.currentLapseMaxIntervalsCell.style.color = healthy_color
        } else if (lapseInfos.leech_status !== "Healthy") {
            cells.currentLapseMaxIntervalsCell.style.color = warning_color;
        }

        if(lapseInfos.performance_drop_count > 1 && lapseInfos.performance_drop_ratio > 0.33){
            cells.performanceDropCountCell.style.color = alert_color
            cells.performanceDropCountCell.style.fontWeight = "bold"
            cells.performanceDropRatioCell.style.color = alert_color
            cells.performanceDropRatioCell.style.fontWeight = "bold"
        } else if (lapseInfos.performance_drop_count > 1) {
            cells.performanceDropCountCell.style.color = warning_color
        } else if (lapseInfos.performance_drop_ratio > 0.33) {
            cells.performanceDropRatioCell.style.color = warning_color
        }
}

function request_lapseinfo(card_id) {
    pycmd("leechdetector:getcard:" + card_id, (lapseInfos) => {
        const extraStatsFields = {
            leechStatusCell: document.querySelector('#leech_status'),
            pastMaxIntervalsCell: document.querySelector('#past_max_intervals'),
            currentLapseMaxIntervalsCell: document.querySelector('#current_lapse_max_intervals'),
            performanceDropCountCell: document.querySelector('#performance_drop_count'),
            performanceDropRatioCell: document.querySelector('#performance_drop_ratio'),
        }

        lapseInfos = JSON.parse(lapseInfos)

        resetStyle(extraStatsFields)
        updateCellsContent(extraStatsFields, lapseInfos)
        colorCells(extraStatsFields, lapseInfos)
    })
}

function get_cardid(){
    let url = document.location.href.split('#')[0]; // First load has a #night trailing
    locationLastPart =  url.split('/').pop() || parts.pop()
    if (Number.isInteger(Number(locationLastPart))) {
        return Number(locationLastPart)
    }
}

setTimeout(add_lapse_stats, 200);
