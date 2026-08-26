"""Command-line interface: manage the watchlist and run checks.

Usage:
    python -m nyc_movie_alert.cli add "Movie Title"
    python -m nyc_movie_alert.cli remove "Movie Title"
    python -m nyc_movie_alert.cli list
    python -m nyc_movie_alert.cli check [--dry-run] [--debug]
"""
import argparse
import sys

from . import state as state_module
from . import watchlist
from .checker import run_check
from .notifier import SmtpConfig, send_alert_email, send_test_email
from .theaters import load_theaters


def cmd_add(args: argparse.Namespace) -> None:
    added = watchlist.add_movie(args.title)
    print(f'Added "{args.title}".' if added else f'"{args.title}" is already on your list.')


def cmd_remove(args: argparse.Namespace) -> None:
    removed = watchlist.remove_movie(args.title)
    print(f'Removed "{args.title}".' if removed else f'"{args.title}" was not on your list.')


def cmd_list(_args: argparse.Namespace) -> None:
    movies = watchlist.list_movies()
    if not movies:
        print("Your watchlist is empty. Add one with: add \"Movie Title\"")
        return
    for m in movies:
        print(f'- {m["title"]} (added {m["added"]})')


def cmd_check(args: argparse.Namespace) -> None:
    movies = watchlist.list_movies()
    if not movies:
        print("Watchlist is empty, nothing to check.")
        return

    theaters = load_theaters()
    state = state_module.load()

    alerts, statuses = run_check(movies, theaters, state, debug=args.debug)

    failed = [s for s in statuses if not s.ok]
    if failed:
        print(f"Warning: failed to fetch {len(failed)} theater page(s):", file=sys.stderr)
        for s in failed:
            print(f"  - {s.theater.name} ({s.theater.url})", file=sys.stderr)

    if not alerts:
        print("No new matches.")
        return

    print(f"Found {len(alerts)} new match(es):")
    for a in alerts:
        print(f'  - "{a.movie_title}" at {a.theater_name} -> {a.link or a.theater_url}')

    if args.dry_run:
        print("(--dry-run: not sending email, not saving state)")
        return

    state_module.save(state)

    config = SmtpConfig.from_env()
    if config is None:
        print(
            "SMTP is not configured (set SMTP_HOST/SMTP_USER/SMTP_PASSWORD/ALERT_TO "
            "as env vars or in config/config.yaml) -- skipping email send.",
            file=sys.stderr,
        )
        return
    send_alert_email(alerts, config)
    print("Alert email sent.")


def cmd_test_email(_args: argparse.Namespace) -> None:
    config = SmtpConfig.from_env()
    if config is None:
        print(
            "SMTP is not configured (set SMTP_HOST/SMTP_USER/SMTP_PASSWORD/ALERT_TO "
            "as env vars or in config/config.yaml).",
            file=sys.stderr,
        )
        sys.exit(1)
    send_test_email(config)
    print(f"Test email sent to {config.to_addr}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="NYC movie watchlist alert tool")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Add a movie to your watchlist")
    p_add.add_argument("title")
    p_add.set_defaults(func=cmd_add)

    p_remove = sub.add_parser("remove", help="Remove a movie from your watchlist")
    p_remove.add_argument("title")
    p_remove.set_defaults(func=cmd_remove)

    p_list = sub.add_parser("list", help="Show your watchlist")
    p_list.set_defaults(func=cmd_list)

    p_check = sub.add_parser("check", help="Check theaters and send alerts for new matches")
    p_check.add_argument("--dry-run", action="store_true", help="Don't send email or save state")
    p_check.add_argument("--debug", action="store_true", help="Print per-theater fetch diagnostics")
    p_check.set_defaults(func=cmd_check)

    p_test_email = sub.add_parser("test-email", help="Send a test email to confirm SMTP settings work")
    p_test_email.set_defaults(func=cmd_test_email)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
