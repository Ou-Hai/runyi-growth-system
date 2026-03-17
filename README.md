# Yoyo Growth Points System

A Streamlit-based family growth points app for tracking daily habits, point changes, reward redemption, and weekly progress.

The current version uses a single-page routing pattern. The home screen works like a clickable adventure map and no longer relies on Streamlit's default multipage sidebar navigation.

## Overview

This project is designed for a family reward system where a child can:

- earn points from daily positive habits,
- lose points from reminder-based deductions,
- save points across weeks,
- redeem rewards on Sunday,
- review weekly progress in a simple and visual way.

## Features

### Home Map

- Illustrated home screen
- Six fully clickable entry cards
- Single-page route switching

### Task Center

- Daily habit check-in
- Completion feedback for the day
- Reward preview and reward radar
- Undo last action

### Weekly Views

- Weekly summary
- Weekly growth report
- Parent dashboard

### Reward Shop

- Sunday-only redemption flow
- Reward tiers
- Redemption history logging

### Edit Records

- Edit `daily_log.csv`
- Edit `redeem_log.csv`
- Recalculate points automatically after edits

## Tech Stack

- Python
- Streamlit
- Pandas
- CSV-based local storage

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

## Data Model

### `daily_log.csv`

Fields:

- `date`
- `timestamp`
- `week_start_date`
- `earned_tasks`
- `deduction_tasks`
- `earned_points`
- `deduction_points`
- `net_change`

### `redeem_log.csv`

Fields:

- `date`
- `timestamp`
- `week_start_date`
- `reward_name`
- `points_cost`
- `points_after_redeem`

### `weekly_log.csv`

Fields:

- `week_start_date`
- `timestamp`
- `weekly_start_points`

The app calculates current points in real time from:

`weekly_log + daily_log - redeem_log`

## Rules

The default rules are defined in `app/rules.py`:

- Weekly starting points: `2`
- Maximum daily earned points: `3`
- Maximum daily deductions: `2`
- Reward tiers: `12 / 30 / 38`

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

## Development Notes

- The app now uses a single-page routing model driven by `st.session_state["route"]`.
- `app/legacy_pages/` is kept only as a backup of the older multipage version.
- The default Streamlit sidebar and top toolbar are hidden in the current UI.
- The `Deploy` button is a built-in Streamlit header control, not part of the app's business logic.

## Verification

You can run a basic compile check with:

```bash
PYTHONPYCACHEPREFIX=/tmp/runyi-pyc python3 -m compileall app
```

## Current Status

The current version includes:

- single-page map-style home screen,
- Chinese / English language switching,
- real-time point calculation,
- cross-week history retention,
- weekly ledger support via `weekly_log.csv`,
- reward redemption,
- editable historical records.

## Future Ideas

- Push the home screen further toward a playful illustrated map style
- Give each entry area its own visual theme, such as candy house, star gate, post office, or toy shop
- Export weekly reports as an image or PDF
- Add more customizable family rules
