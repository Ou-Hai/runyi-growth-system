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

The app is designed to stay lightweight and local-first:

- all records are stored in local CSV files,
- current points are recalculated from logs instead of being manually edited,
- the UI supports Chinese, English, and German,
- displayed labels inside tables are localized without changing the underlying stored data.

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
- Localized table display for records and redemption history

### Reward Shop

- Sunday-only redemption flow
- Reward tiers
- Redemption history logging

### Edit Records

- Edit `daily_log.csv`
- Edit `redeem_log.csv`
- Recalculate points automatically after edits
- Table headers and visible values follow the selected language

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

The CSV files remain language-agnostic storage. The app localizes displayed values at render time, so historical data stays compatible even after adding new languages.

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

## Data Behavior

- `daily_log.csv` stores completed earning and deduction tasks as pipe-separated values.
- `redeem_log.csv` stores the redeemed reward name and the remaining points after redemption.
- `weekly_log.csv` stores the starting points for each logged week.
- The UI may show translated task names or reward names, but the original CSV structure is unchanged.
- When records are edited, points are recalculated from the logs instead of patched manually.

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

## How The UI Works

- The app uses `st.session_state["route"]` for single-page route switching.
- The language switcher stores the selected language in `st.session_state["lang"]`.
- Shared text rendering goes through `app/ui.py`.
- Shared rules, task labels, and reward definitions live in `app/rules.py`.
- Record loading, CSV normalization, and point calculation live in `app/data_manager.py`.
- Table localization is handled in the view layer so storage stays stable while display language changes.

## Development Notes

- The app now uses a single-page routing model driven by `st.session_state["route"]`.
- `app/legacy_pages/` is kept only as a backup of the older multipage version.
- The default Streamlit sidebar and top toolbar are hidden in the current UI.
- The `Deploy` button is a built-in Streamlit header control, not part of the app's business logic.
- The current implementation keeps CSV field names in a stable internal format and only translates what the user sees.

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
- real-time point calculation,
- cross-week history retention,
- weekly ledger support via `weekly_log.csv`,
- reward redemption,
- editable historical records,
- localized table headers and table cell values for tasks and rewards.

## Future Ideas

- Push the home screen further toward a playful illustrated map style
- Give each entry area its own visual theme, such as candy house, star gate, post office, or toy shop
- Export weekly reports as an image or PDF
- Add more customizable family rules
