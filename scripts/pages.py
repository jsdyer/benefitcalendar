"""Build searchable schedules and subscriptions from the same dates."""
from datetime import date, datetime, timezone
from html import escape
import json
from pathlib import Path
from search_metadata import add_search_metadata

REGIONS = {'CA': 'Canada-wide', 'AB': 'Alberta', 'NL': 'Newfoundland and Labrador', 'ON': 'Ontario'}
ROUTES = {'cpp': 'cpp-payment-dates', 'oas': 'oas-payment-dates', 'ccb': 'canada-child-benefit-dates',
          'cgeb': 'groceries-and-essentials-benefit-dates', 'otb': 'ontario-trillium-benefit-dates'}


def fold(line):
    """RFC 5545 physical lines cannot exceed 75 octets, including continuation space."""
    result = ['']
    for char in line:
        if len((result[-1] + char).encode()) > 75:
            result.append(' ')
        result[-1] += char
    return '\r\n'.join(result)


def calendar_text(events, stamp):
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//CoolCode//Benefit Calendar//EN',
             'CALSCALE:GREGORIAN', 'METHOD:PUBLISH']
    for day, key, program in events:
        compact = day.replace('-', '')
        title = program['name'].replace('\\', '\\\\').replace(',', '\\,').replace(';', '\\;').replace('\n', '\\n')
        lines.extend(['BEGIN:VEVENT', f'UID:{key}-{compact[:6]}@benefitcalendar.coolcode.ca',
                      f'DTSTAMP:{stamp}', f'DTSTART;VALUE=DATE:{compact}', f'SUMMARY:{title}',
                      'TRANSP:TRANSPARENT', 'URL:' + program['source'], 'END:VEVENT'])
    return '\r\n'.join(fold(line) for line in [*lines, 'END:VCALENDAR']) + '\r\n'


def date_label(value):
    return date.fromisoformat(value).strftime('%a, %b %d, %Y').replace(' 0', ' ')


def render(data, target, prefix):
    programs = data['programs']
    events = sorted((day, key, program) for key, program in programs.items() for day in program['dates'])
    choices = ['<option value="">All programs</option>']
    for key, program in programs.items():
        selected = ' selected' if key == target else ''
        choices.append(f'<option value="{escape(key)}" data-region="{program["region"]}"{selected}>{escape(program["name"])}</option>')
    regions = '<option value="">All published regions</option>' + ''.join(
        f'<option value="{key}">{escape(name)} only</option>' if key == 'CA' else f'<option value="{key}">{escape(name)} and Canada-wide</option>'
        for key, name in REGIONS.items())
    today = data['checked_at'][:10]
    current = [e for e in events if (not target or e[1] == target) and e[0] >= today]
    first = current[0][0] if current else None
    next_text = (' · '.join([date_label(first)] + [p['name'] for day, _, p in current if day == first]) if first
                 else 'No later date has been published in this schedule.')
    rows = []
    for day, key, program in events:
        selected = (not target or target == key) and day >= today
        hidden = '' if selected else ' hidden'
        rows.append(f'<tr data-date="{day}" data-program="{key}" data-region="{program["region"]}"{hidden}>'
                    f'<td><time datetime="{day}">{date_label(day)}</time></td><td><a href="{escape(program["source"],quote=True)}">{escape(program["name"])}</a></td></tr>')
    nav = ' · '.join(f'<a href="{prefix}{route}/">{escape(programs[key]["name"])}</a>' for key, route in ROUTES.items())
    feed = f'{prefix}calendars/{target or "all"}.ics'
    return f'''<section class="calendar"><h2>Next payment</h2><p id="next" aria-live="polite">{escape(next_text)}</p>
<p id="asof">Schedule as of <time>{escape(today)}</time>.</p>
<form id="filters"><label>Program<select id="program" name="program">{''.join(choices)}</select></label>
<label>Region<select id="region">{regions}</select></label><label>Show dates<select id="period">
<option value="upcoming">Today onward</option><option value="all">All published dates</option></select></label></form>
<p><a id="download" href="{feed}">Download selected calendar (.ics)</a> · <a id="subscribe" href="webcal://coolcode.ca/benefitcalendar/calendars/{target or 'all'}.ics">Subscribe in a calendar app</a></p>
<p id="region-note">Published provincial schedules here cover Alberta, Newfoundland and Labrador, and Ontario. Canada-wide schedules are also available.</p>
<table><caption>Published payment dates</caption><thead><tr><th scope="col">Date</th><th scope="col">Benefit</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
</section><nav aria-label="Common calendars">{nav}</nav>
<p>Source checked {escape(today)} · <a href="{escape(data['source'],quote=True)}">Government of Canada benefit calendar</a>.</p>'''


def publish_pages(stage, template, tool):
    data = json.loads((stage / 'data/calendar.json').read_text())
    feed_dir = stage / 'calendars'
    feed_dir.mkdir()
    events = sorted((day, key, program) for key, program in data['programs'].items() for day in program['dates'])
    stamp = datetime.fromisoformat(data['checked_at']).astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    feeds = {'all': events}
    for key in data['programs']:
        feeds[key] = [entry for entry in events if entry[1] == key]
    for region in REGIONS:
        feeds['region-' + region] = [e for e in events if e[2]['region'] in ('CA', region)]
    for key, entries in feeds.items():
        (feed_dir / (key + '.ics')).write_bytes(calendar_text(entries, stamp).encode())
    for target, slug in [('', ''), *ROUTES.items()]:
        prefix = '../' if slug else './'
        copy = tool.copy()
        page = template
        if slug:
            program = data['programs'][target]
            copy.update(title=f"{program['name']} Payment Dates", url=f"{tool['url']}{slug}/",
                        description=f"Browse published {program['name']} dates and subscribe to its payment calendar.")
            page = (page.replace(escape(tool['title']), escape(copy['title']))
                        .replace(escape(tool['description']), escape(copy['description']))
                        .replace('href="./style.css"', 'href="../style.css"')
                        .replace('src="./app.mjs"', 'src="../app.mjs"'))
        page = page.replace('<!-- CALENDAR -->', render(data, target, prefix))
        destination = stage / slug
        destination.mkdir(exist_ok=True)
        (destination / 'index.html').write_text(add_search_metadata(page, copy))
