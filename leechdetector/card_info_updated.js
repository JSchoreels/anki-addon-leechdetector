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

function request_lapseinfo(card_id) {
    pycmd("leechdetector:getcard:" + card_id, (lapseInfos) => {
        // console.log("Received : " + lapseInfos)
        const pastMaxIntervalsCell = document.querySelector('#past_max_intervals');
        const currentLapseMaxIntervalsCell = document.querySelector('#current_lapse_max_intervals');
        const biggestIntervalDropCell = document.querySelector('#biggest_interval_drop');
        const failedOutperformanceRatio = document.querySelector('#failed_outperformance_ratio');

        lapseInfos = JSON.parse(lapseInfos)

        pastMaxIntervalsCell.textContent = JSON.stringify(lapseInfos.past_max_intervals)
        currentLapseMaxIntervalsCell.textContent = lapseInfos.current_lapse_max_intervals
        biggestIntervalDropCell.textContent = lapseInfos.biggest_interval_drop
        failedOutperformanceRatio.textContent = lapseInfos.failed_outperformance_ratio
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
