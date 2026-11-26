# Canada Benefit Payment Dates

[Open the calendar](https://coolcode.ca/benefitcalendar/).

<!-- coolcode:guide -->
Choose a benefit to see its next published payment and upcoming dates. The Canada-wide view includes CPP, OAS, CCB and the Canada Groceries and Essentials Benefit. Filter provincial schedules for Alberta, Newfoundland and Labrador, or Ontario. Download a calendar or subscribe to its stable ICS address to receive later published dates. Switch to **All published dates** to check a past payment.
<!-- /coolcode:guide -->

The [Government of Canada benefits calendar](https://www.canada.ca/en/services/benefits/calendar.html) identifies the administering agency and publishes dates by program and year. Coverage can differ across programs. The discontinued GST/HST credit has its own historical entries. A date is an official scheduled issue date. Individual eligibility, amount and bank posting depend on the recipient and are not collected. Filter choices stay in the browser. CoolCode's standard counter receives the tool ID.

## Expand or customize

Edit `config/programs.json`. Keys correspond to the identifier preceding the year in the official calendar's details panels. Give the program its name, region, official section anchor and expected payments per full year. Add explicit exceptions with tests if a program starts or ends partway through a year. Keep the display region names and common route definitions in `scripts/pages.py` aligned. Add new indexed routes to the central sitemap.

Run `python3 scripts/refresh.py` to download and validate the calendar. The collector rejects missing, duplicated, malformed or unexpectedly short schedules. Successful refreshes replace active year panels and preserve older published years. A failed refresh keeps the previous deployment. `web/data/calendar.json` records the actual check time, sources and number of program/date entries.

## Calendar subscriptions

`calendars/all.ics`, `calendars/<program>.ics` and `calendars/region-<code>.ics` are generated at build time. Events use all-day dates and stable program/month UIDs. Regional feeds include national programs. Calendar clients control their refresh interval. The static pages contain the published dates even before interactive filtering loads.

## Build and publish

Run `node --test tests/*.test.mjs`, `python3 -m unittest discover -s tests -v`, and `python3 scripts/build.py`. Serve `dist/` locally. Run `python3 tests/browser_smoke.py` with Playwright Chromium installed. GitHub Pages uses the Actions source. The weekly and manual workflow runs collect and validate the official calendar before publication. No API credentials are required.
