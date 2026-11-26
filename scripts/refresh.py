"""Validate the published year panels, replacing active years and retaining older ones."""
import json
import re
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'https://www.canada.ca/en/services/benefits/calendar.html'


class YearPanels(HTMLParser):
    def __init__(self, programs):
        super().__init__()
        self.programs = programs
        self.panels = {}
        self.active = None
        self.item = None

    def handle_starttag(self, tag, attrs):
        if tag == 'details':
            match = re.fullmatch(r'([a-z0-9]+)-(20\d\d)', dict(attrs).get('id', ''))
            if match and match[1] in self.programs:
                self.active = (match[1], int(match[2]))
                if self.active in self.panels:
                    raise ValueError('Duplicate source year panel')
                self.panels[self.active] = []
        elif tag == 'li' and self.active:
            self.item = []

    def handle_data(self, data):
        if self.item is not None:
            self.item.append(data)

    def handle_endtag(self, tag):
        if tag == 'details':
            self.active = self.item = None
        elif tag == 'li' and self.item is not None:
            label = ' '.join(''.join(self.item).split())
            parsed = datetime.strptime(label, '%B %d, %Y').date()
            if parsed.year != self.active[1]:
                raise ValueError('Payment year differs from its heading')
            self.panels[self.active].append(parsed.isoformat())
            self.item = None


def collect(html, programs, old, checked):
    parser = YearPanels(programs)
    parser.feed(html)
    output = {}
    for key, program in programs.items():
        dates = old.get('programs', {}).get(key, {}).get('dates', [])
        years = {int(day[:4]) for day in dates}
        fresh = {year: values for (name, year), values in parser.panels.items() if name == key}
        if not fresh and not (key == 'gst' and dates and checked >= '2027-01-01'):
            raise ValueError(f'Missing program section for {key}')
        if fresh and any(y > max(fresh) for y in years):
            raise ValueError(f'Latest published {key} year disappeared')
        history = [day for day in dates if int(day[:4]) not in fresh]
        for year, values in fresh.items():
            expected = program['per_year']
            if year == 2026 and key in ('gst', 'cgeb'):
                expected = 2
            if len(values) != expected or values != sorted(set(values)):
                raise ValueError(f'Unexpected count or ordering in {key} {year}')
            history.extend(values)
        if not history:
            raise ValueError(f'Empty schedule for {key}')
        output[key] = {'name': program['name'], 'region': program['region'],
                       'source': SOURCE + '#' + program['anchor'], 'dates': sorted(history)}
    return {'checked_at': checked, 'source': SOURCE,
            'record_count': sum(len(p['dates']) for p in output.values()), 'programs': output}


def main():
    with urlopen(Request(SOURCE, headers={'User-Agent': 'CoolCode benefit calendar (+https://coolcode.ca/benefitcalendar/)'}), timeout=45) as response:
        html = response.read(2_000_001)
    if len(html) > 2_000_000:
        raise ValueError('Unexpected calendar size')
    path = ROOT / 'web/data/calendar.json'
    old = json.loads(path.read_text()) if path.exists() else {}
    config = json.loads((ROOT / 'config/programs.json').read_text())
    data = collect(html.decode(), config, old, datetime.now(timezone.utc).isoformat(timespec='seconds'))
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    tmp.replace(path)
    print(f"Validated {data['record_count']} published payment dates.")


if __name__ == '__main__':
    main()
