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
  link — it does not parse exact showtimes.
- If a theater redesigns its site to load listings via JavaScript instead of
  plain HTML, that theater's checks will stop finding anything. Run
  `python -m nyc_movie_alert.cli check --debug` to see how many characters
  were fetched from each theater — a suspiciously small number means that
  theater's page didn't come back with real content and the URL in
  `theaters.yaml` needs updating.
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
```

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
   schedule.

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
