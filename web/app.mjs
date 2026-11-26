import {localToday, matches} from './model.mjs';
const program = document.querySelector('#program');
const region = document.querySelector('#region');
const period = document.querySelector('#period');
const rows = Array.from(document.querySelectorAll('tbody tr'));
function filter() {
  for (const option of program.options) {
    option.disabled = Boolean(option.value && region.value && option.dataset.region !== 'CA' && option.dataset.region !== region.value);
  }
  if (program.selectedOptions[0]?.disabled) program.value = '';
  const today = localToday();
  const upcoming = [];
  for (const row of rows) {
    const relevant = matches(row.dataset, program.value, region.value, '');
    row.hidden = !relevant || (period.value === 'upcoming' && row.dataset.date < today);
    if (relevant && row.dataset.date >= today) upcoming.push(row);
  }
  const soonest = upcoming[0];
  const next = document.querySelector('#next');
  if (soonest) {
    const due = upcoming.filter(row => row.dataset.date === soonest.dataset.date);
    next.textContent = soonest.cells[0].textContent + ' · ' + due.map(row => row.cells[1].textContent).join(' · ');
  } else {
    next.textContent = 'No upcoming dates have been published for this selection. Choose “All published dates” to see past payments.';
  }
  document.querySelector('#asof').textContent = 'Showing dates relative to your local calendar day, ' + today + '.';
  const feed = new URL('calendars/' + (program.value || (region.value && 'region-' + region.value) || 'all') + '.ics', import.meta.url);
  document.querySelector('#download').href = feed.href;
  document.querySelector('#subscribe').href = 'webcal://' + feed.host + feed.pathname;
}
document.querySelector('#filters').addEventListener('change', filter);
filter();
