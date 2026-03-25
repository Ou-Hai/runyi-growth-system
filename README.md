# Yoyo Growth Points System

A Streamlit-based family growth points app for tracking daily habits, point changes, reward redemption, weekly progress, and monthly review.

The current version uses a single-page routing pattern. The home screen works like a clickable adventure map and no longer relies on Streamlit's default multipage sidebar navigation.

## Overview

This project is designed for a family reward system where a child can:

- earn points from daily positive habits,
- lose points from reminder-based deductions,
- save points across weeks,
- redeem rewards on Sunday,
- review weekly progress in a simple and visual way.

The app is designed to keep the UI lightweight while using persistent storage for production:

- production data is stored in PostgreSQL-compatible storage such as Supabase,
- current points are recalculated from logs instead of being manually edited,
- the UI supports Chinese, English, and German,
- displayed labels inside tables are localized without changing the underlying stored data,
- the UI includes a mobile-first responsive layer while still keeping desktop layouts usable.

## Features

### Home Map

- Illustrated home screen
- Mobile-friendly clickable entry cards
- Single-page route switching
- Reordered navigation flow for smaller screens

### Task Center

- Daily habit check-in
- Completion feedback for the day
- Reward preview and reward radar
- Undo last action

### Weekly Views

- Weekly summary
- Weekly growth report
- Parent dashboard
- Localized table display for records and redemption history
- Card view plus table view for daily and redemption records

### Monthly Views

- Monthly report
- Monthly habit summary
- Monthly redemption history
- Month-level point trend review
- Card view plus table view for monthly records

### Reward Shop

- Sunday-only redemption flow
- Reward tiers
- Redemption history logging
- Mobile-first reward ordering and clearer redeem state display

### Edit Records

- Edit daily records
- Edit redeem records
- Recalculate points automatically after edits
- Table headers and visible values follow the selected language
- Card view plus table view for browsing history before editing

## Tech Stack

- Python
- Streamlit
- Pandas
- SQLAlchemy
- PostgreSQL / Supabase
- `uv` for local dependency management

## Project Structure

```text
app/
  main.py            # Single-page app entrypoint
  router_views.py    # Rendering logic for the six main views
  data_manager.py    # Data I/O, weekly ledger, and point calculation
  rules.py           # Unified rules, tasks, rewards, and shared constants
  ui.py              # Styling, language switcher, and shared UI helpers
  legacy_pages/      # Backup of the old multipage implementation

data/
  daily_log.csv      # Daily task records
  redeem_log.csv     # Reward redemption records
  weekly_log.csv     # Weekly starting-point ledger
  points.json        # Legacy file, no longer used as the source of truth
```

`data/*.csv` is now used only as optional seed data for first-time database bootstrapping.

## Mobile And Desktop Behavior

The current UI is designed to work on both desktop and phone screens:

- desktop keeps the wider adventure-map layout and full tables,
- smaller screens automatically tighten spacing and stack columns,
- record-heavy pages offer both a card view and a full table view,
- the reward shop and home navigation are ordered more clearly for top-to-bottom phone use.

This is still a Streamlit app, so it behaves like a responsive web app rather than a fully native mobile app.

## Language Support

The current UI supports:

- `中文`
- `English`
- `Deutsch`

Language switching currently covers:

- home screen navigation
- hero cards and action buttons
- task and reward labels
- reward shop text
- weekly report and parent dashboard labels
- edit-record forms
- table headers and visible task / reward values in tables

The database keeps stable internal field names. The app localizes displayed values at render time, so historical data stays compatible even after adding new languages.

## Database Setup

The app expects one of these settings:

- `DATABASE_URL`
- `SUPABASE_DB_URL`
- `SUPABASE_DATABASE_URL`

You can provide the value either as an environment variable or in Streamlit secrets.

Example:

```toml
DATABASE_URL = "postgresql://postgres:<password>@<host>:5432/postgres"
```

For Supabase on Streamlit Cloud, the production setup used in this project is typically:

```toml
DATABASE_URL = "postgresql://postgres.<project-ref>:<password>@<pooler-host>:5432/postgres?sslmode=require"
```

Notes:

- using the Supabase session pooler is generally more reliable than a direct connection on Streamlit Cloud,
- if your password contains reserved URL characters such as `@`, it must be URL-encoded,
- Streamlit Cloud in this project reads dependencies successfully through `uv.lock`.

On first startup:

- tables are created automatically if they do not exist,
- for PostgreSQL-compatible databases such as Supabase, the app also enables RLS on its `public` tables and revokes direct access from `anon` / `authenticated`,
- if the database is empty and `data/*.csv` exists, those CSV files are imported as seed data.
- `weekly_log` is auto-initialized for the current week if needed.

## Access Control

The app now supports a simple admin login model:

- visitors can browse pages in read-only mode,
- only the admin session can save daily records, undo actions, redeem rewards, or edit historical logs,
- the edit-records page is hidden unless the admin is logged in.

Configure an admin password with either:

- `RUNYI_ADMIN_PASSWORD`
- `ADMIN_PASSWORD`

You can set it in Streamlit secrets, for example:

```toml
RUNYI_ADMIN_PASSWORD = "replace-with-a-strong-password"
```

If no admin password is configured, the app stays in read-only mode.

If Supabase `Security Advisor` still reports `RLS Disabled in Public`, run the SQL in [sql/supabase_enable_rls.sql](/Users/haiou/data_engineer/projects/runyi-growth-system/sql/supabase_enable_rls.sql) inside the Supabase SQL Editor. The final query in that file should return `rowsecurity = true` for `daily_log`, `redeem_log`, and `weekly_log`.

## Data Model

### `daily_log`

Fields:

- `date`
- `timestamp`
- `week_start_date`
- `earned_tasks`
- `deduction_tasks`
- `earned_points`
- `deduction_points`
- `net_change`

### `redeem_log`

Fields:

- `date`
- `timestamp`
- `week_start_date`
- `reward_name`
- `points_cost`
- `points_after_redeem`

### `weekly_log`

Fields:

- `week_start_date`
- `timestamp`
- `weekly_start_points`

The app calculates current points in real time from:

`weekly_log + daily_log - redeem_log`

## Data Behavior

- `daily_log` stores completed earning and deduction tasks as pipe-separated values.
- `redeem_log` stores the redeemed reward name and the remaining points after redemption.
- `weekly_log` stores the starting points for each logged week.
- The UI may show translated task names or reward names, but the stored field structure remains stable.
- When records are edited, points are recalculated from the logs instead of patched manually.
- current points are derived from logs, not stored as a standalone mutable number.

## Rules

The default rules are defined in `app/rules.py`:

- Weekly starting points: `2`
- Maximum daily earned points: `3`
- Maximum daily deductions: `2`
- Reward tiers: `12 / 30 / 38`

Each logged week starts with `2` points through `weekly_log`. The system adds that weekly baseline automatically when a new week is first touched by the app.

## Run Locally

### Option 1

```bash
streamlit run app/main.py
```

### Option 2

If you use `uv`:

```bash
uv run streamlit run app/main.py
```

Default local URL:

```text
http://localhost:8501
```

## How The UI Works

- The app uses `st.session_state["route"]` for single-page route switching.
- The language switcher stores the selected language in `st.session_state["lang"]`.
- Shared text rendering goes through `app/ui.py`.
- Shared rules, task labels, and reward definitions live in `app/rules.py`.
- Record loading, database initialization, optional CSV seeding, and point calculation live in `app/data_manager.py`.
- Table localization is handled in the view layer so storage stays stable while display language changes.
- Monthly reporting is generated from the same stored logs without changing the write path.
- Mobile-friendly behavior is mostly implemented through shared CSS in `app/ui.py` plus card/table dual presentation in `app/router_views.py`.

## Development Notes

- The app now uses a single-page routing model driven by `st.session_state["route"]`.
- `app/legacy_pages/` is kept only as a backup of the older multipage version.
- The default Streamlit sidebar and top toolbar are hidden in the current UI.
- The `Deploy` button is a built-in Streamlit header control, not part of the app's business logic.
- The current implementation keeps database field names in a stable internal format and only translates what the user sees.
- Database-backed reads use a short cache window to reduce repeated rerun latency while still refreshing quickly after edits.
- Manual edits made directly in Supabase may take a few seconds to appear because of the short read cache.

## Verification

You can run a basic compile check with:

```bash
PYTHONPYCACHEPREFIX=/tmp/runyi-pyc python3 -m compileall app
```

## Current Status

The current version includes:

- single-page map-style home screen,
- Chinese / English / German language switching,
- natural German spelling with `ä / ö / ü / ß`,
- PostgreSQL / Supabase-ready persistence,
- Supabase session-pooler compatible deployment,
- real-time point calculation,
- cross-week history retention,
- weekly ledger support via `weekly_log`,
- monthly report page,
- reward redemption,
- editable historical records,
- localized table headers and table cell values for tasks and rewards,
- responsive mobile-friendly layout updates,
- card view plus table view on record-heavy pages,
- shortened home-screen week-start metric for narrow layouts,
- shorter rerun latency via lightweight read caching.

## Future Ideas

- Push the home screen further toward a playful illustrated map style
- Give each entry area its own visual theme, such as candy house, star gate, post office, or toy shop
- Export weekly reports as an image or PDF
- Add more customizable family rules
