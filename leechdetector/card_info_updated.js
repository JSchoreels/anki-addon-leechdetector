function add_lapse_stats(){
    const rows = document.querySelectorAll('tr');
    
    const table = document.getElementsByClassName('stats-table')[0];
    const tbody = table.querySelector('tbody') || table;
    tbody.insertAdjacentHTML('beforeend', `$table_html`)
    
    const targetCell = document.querySelector('#past_max_intervals');
    
    let oldHref = window.location.href;
    const observer = new MutationObserver(mutations => {
     if (oldHref != document.location.href) {
          oldHref = document.location.href;
          new_card_id = document.location.href.split('/').pop() || parts.pop(); // Handle trailing slash
          console.log("Card Change Detected")
          pycmd("new_card_id:"+new_card_id, (new_past_max_intervals) => targetCell.textContent = new_past_max_intervals.toString())
      }
    });
    
    body = document.querySelector('body');
    observer.observe(body, { childList: true, subtree: true });
}


setTimeout(add_lapse_stats, 200);
