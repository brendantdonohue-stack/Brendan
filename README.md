# nyc-movie-alert

Keep a personal movie watchlist and get an email whenever one of those titles
is playing at an NYC theater.

It checks two kinds of theaters:
- **Indie / repertory houses** (Film Forum, IFC Center, Metrograph, Angelika,
  Nitehawk, Quad, BAM, Roxy, Museum of the Moving Image, Anthology Film
  Archives) — these run revival/classic screenings, so this is where an older
  movie on your list is most likely to show up.
- **Mainstream chains** (a few NYC AMC/Regal/Alamo Drafthouse locations) —
  mostly current first-run releases.

The full list of theaters lives in [`config/theaters.yaml`](config/theaters.yaml) —
add, remove, or edit entries there any time.

## How matching works (and its limits)

There is no free, reliable "all NYC showtimes" API, so this works by fetching
each theater's public "now playing" page and checking whether your movie's
title appears in it (matched case/punctuation-insensitively). This is
deliberately simple and resilient to page redesigns, but it means:

- It tells you a title is **listed on the page** and gives you the theater's
  link, plus a snippet of surrounding text so you can eyeball whether it's a
  real listing (a date/showtime nearby) or an incidental mention — it does
  not parse an actual showtimes table. When a date/time-shaped string (e.g.
  "Wed Sep 10 7:00pm") appears near the match, the email includes it as
  "First showing" and marks the alert `likely a real listing`; when nothing
  date-shaped is found nearby, it's marked `UNCONFIRMED` instead — click
  through and check before making plans either way.
- It can only see what a theater has **already published**, which in practice
  means today through the next few weeks (repertory houses usually post
  roughly a month out, chains often just 1-2 weeks). There's no way to check
  "is this playing in the next 6 months" up front — theaters simply haven't
  scheduled that far ahead yet. Instead, this runs on a schedule (every 6
  hours via GitHub Actions) and alerts you the moment a title newly appears,
  so over a 6-month period you'd naturally be notified as soon as each
  screening is announced.
- Matching runs against the page's **visible text** (scripts/nav/footer
  stripped), not raw HTML, to avoid false positives from site chrome or
  embedded JSON. Each alert is tagged `likely real` or `UNCONFIRMED` based on
  whether a date/time-like string appears near the match.
- Some theater sites need JavaScript to render their listings at all, or
  block plain HTTP requests outright (bot protection). For those, fetching
  automatically falls back to a headless Chromium browser (via Playwright)
  that actually renders the page before reading it. This is slower and
  doesn't guarantee success against every bot wall (a hard CAPTCHA-style
  challenge won't be solved), but it recovers real content from JS-only
  sites. Run `python -m nyc_movie_alert.cli diag` to see, per theater,
  whether it succeeded on a plain fetch or needed the browser fallback, and
  how much visible text came back — a suspiciously small number (or a
  persistent failure) means the URL in `theaters.yaml` needs updating.
- Once you're alerted about a movie at a theater, it won't alert you again
  for the same pair for 30 days (see `COOLDOWN_DAYS` in
  `nyc_movie_alert/state.py`), since engagements typically run for weeks.

## Setup

```bash
pip install -r requirements.txt
```

### Configure email

Copy the example config and fill it in, **or** set the equivalent environment
variables (env vars always win — this is what the GitHub Actions workflow
uses):

```bash
cp config/config.example.yaml config/config.yaml
# edit config/config.yaml
```

For Gmail: use an
[App Password](https://myaccount.google.com/apppasswords) (not your normal
password) as `smtp_password`.

Environment variable equivalents: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`,
`SMTP_PASSWORD`, `ALERT_FROM`, `ALERT_TO`.

## Usage

```bash
# manage your watchlist
python -m nyc_movie_alert.cli add "Blade Runner"
python -m nyc_movie_alert.cli remove "Blade Runner"
python -m nyc_movie_alert.cli list

# run a check now
python -m nyc_movie_alert.cli check            # sends email + saves state
python -m nyc_movie_alert.cli check --dry-run  # prints matches, sends nothing
python -m nyc_movie_alert.cli check --debug    # also prints per-theater fetch diagnostics

# confirm your email settings work, without waiting for a real match
python -m nyc_movie_alert.cli test-email

# check why a theater is or isn't fetching, with no side effects at all
python -m nyc_movie_alert.cli diag
```

`diag` needs a headless Chromium installed for the browser fallback to work locally:
`python -m playwright install --with-deps chromium` (the GitHub Actions workflow does this
automatically, cached between runs).

## Running it automatically

### Option A: GitHub Actions (recommended, no machine to keep running)

A workflow at `.github/workflows/movie-check.yml` already runs `check` every
6 hours and commits the updated `data/state.json` back to the repo so
dedupe state survives between runs.

To enable it:
1. Push this repo to GitHub (already done if you're reading this from there).
2. Add repo secrets (Settings → Secrets and variables → Actions):
   `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `ALERT_FROM`, `ALERT_TO`.
3. Manage your watchlist locally with `add`/`remove`, then commit and push
   `data/watchlist.json` — the workflow reads it from the repo, not from your
   machine.
4. You can trigger a run immediately from the Actions tab
   ("Check NYC movie watchlist" → "Run workflow") instead of waiting for the
   schedule. Tick the "Send a test email instead" checkbox on that dialog to
   just confirm email delivery works, without waiting for a real match, or
   tick "Just fetch each theater..." to run `diag` instead (no email, no
   state changes, no SMTP secrets needed).

### Option B: cron on your own machine

```cron
0 */6 * * * cd /path/to/this/repo && /usr/bin/python3 -m nyc_movie_alert.cli check >> check.log 2>&1
```

## Tests

```bash
python -m pytest tests/ -q
```

Tests cover the watchlist store, the dedupe/cooldown state, and title
matching — they don't hit the network, since theater sites aren't something
this repo can (or should) call in CI.
