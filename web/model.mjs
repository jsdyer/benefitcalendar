export function localToday(now = new Date()) {
  return [now.getFullYear(), String(now.getMonth()+1).padStart(2,'0'), String(now.getDate()).padStart(2,'0')].join('-');
}
export function matches(row, program, region, earliest) {
  return (!program || row.program === program) && (!region || row.region === 'CA' || row.region === region) && row.date >= earliest;
}
