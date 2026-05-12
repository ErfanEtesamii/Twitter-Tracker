# Twitter Monitor Bot

> I built this project to monitor selected Twitter/X accounts from Google Sheets and forward matching tweets to Telegram.  
> It was designed as a flexible, project-based monitoring system with regex management, username imports, and admin controls through Telegram.

---

## Overview

I built this bot to solve a very specific workflow: I wanted to monitor selected Twitter/X accounts, match tweets against configurable regex patterns, and forward only the relevant results to Telegram.  
Instead of hardcoding everything into a single script, I split the system into multiple projects so I could manage different rules, different username lists, and different Telegram destinations separately.

The bot is designed to be extensible. I can add or remove projects, update regexes, import usernames from files, and check status from Telegram without editing the code every time.

---

## What This Bot Does

I use this bot to:

- Read usernames from Google Sheets.
- Monitor tweets for each username.
- Match tweet text against one or more regex patterns.
- Send matching tweets to one or more Telegram chats.
- Store sent tweets in a cache so the same tweet is not sent twice.
- Track project state separately for each monitoring job.
- Manage projects and regexes through Telegram commands.

---

## Core Features

- Multiple monitoring projects.
- Project-specific regex lists.
- Google Sheets integration.
- Telegram admin commands.
- Inline keyboard support.
- Username import from `.txt` and `.csv`.
- Add/remove users from Telegram.
- Add/remove projects from Telegram.
- Enable/disable projects dynamically.
- Cache-based deduplication.
- Batch append to Google Sheets.
- Retry and recovery logic.
- Health/status monitoring.
- Export support for project data.
- Admin-only controls.

---

## Project Structure

```text
twitter-monitor-bot/
├─ main.py
├─ config.py
├─ models.py
├─ storage.py
├─ sheets.py
├─ twitter_client.py
├─ telegram_bot.py
├─ project_manager.py
├─ notifier.py
├─ utils.py
├─ requirements.txt
├─ .env.example
├─ data/
│  ├─ service_account.json
│  ├─ projects.json
│  ├─ cache.json
│  └─ cookies.pkl
├─ logs/
└─ README.md
```

---

## How It Works

I first load the bot configuration, then I read the project definitions from `projects.json`.  
Each project contains its own source sheet, source tab, regex list, and Telegram chat IDs.

For each active project, I read the usernames from the source sheet, scrape the relevant profiles, and compare tweet text against the compiled regex patterns.  
If a tweet matches, I send it to Telegram and store the result in the sent log so it does not get sent again later.

I also keep a persistent browser session by using a saved Chrome profile and cookies, which helps reduce repeated login friction.

---

## Project Format

Each project is stored as a JSON object. A project usually looks like this:

```json
{
  "name": "recall",
  "enabled": true,
  "source_sheet_id": "YOUR_SOURCE_SHEET_ID",
  "source_ws_title": "list_1",
  "sent_sheet_id": "YOUR_SENT_SHEET_ID",
  "sent_ws_title": "sent_all",
  "regexes": [
    "#recall",
    "#recallnet",
    "@recallnet",
    "\\$recall",
    "#ریکال"
  ],
  "chat_ids": [
    "775753176",
    "6868791468"
  ],
  "max_age_seconds": 10800
}
```

### Field meaning

- `name`: Project name.
- `enabled`: Turns monitoring on or off.
- `source_sheet_id`: Google Sheet ID that contains usernames.
- `source_ws_title`: Tab name that stores usernames.
- `sent_sheet_id`: Sheet used to store sent tweet history.
- `sent_ws_title`: History tab name.
- `regexes`: Patterns used to match tweets.
- `chat_ids`: Telegram chats that receive alerts.
- `max_age_seconds`: Maximum tweet age allowed for alerts.

---

## Google Sheets Setup

I keep usernames in the first column of the source sheet.  
Each sheet tab can represent a separate project or source list.

### Username column format

```text
username
account_one
account_two
account_three
```

### Sent log format

I store sent tweets in a dedicated tab with these columns:

- `timestamp_local`
- `username`
- `tweet_link`
- `project`
- `regex`

I use batch append where possible so the Sheets API stays efficient and the bot does not waste calls on single-row writes.

---

## Telegram Commands

I manage the bot from Telegram using admin-only commands.

### Basic commands

- `/start` — Show quick actions.
- `/help` — Show available commands.
- `/projects` — List all projects.
- `/status` — Show runtime status.
- `/health` — Show health info.
- `/reload` — Reload project data.

### Project management

- `/addproject` — Add a new project.
- `/removeproject <name>` — Remove a project.
- `/enable <name>` — Enable a project.
- `/disable <name>` — Disable a project.

### Regex management

- `/addregex <project> <regex>` — Add a regex.
- `/removeregex <project> <regex>` — Remove a regex.

### Chat management

- `/setchats <project> <chat1,chat2>` — Replace project chat IDs.

### User management

- `/addusers <project>` — Add usernames manually.
- `/removeusers <project>` — Remove usernames manually.
- `/importusers <project>` — Import usernames from a file.

### Export and broadcast

- `/export` — Export project data.
- `/broadcast <message>` — Send a message to admin chats.

I use inline keyboards for faster navigation, and callback queries are handled separately so button presses respond correctly.

---

## File Imports

I support importing usernames from two file types:

- `.txt`
- `.csv`

When I send a file to the bot, it reads the usernames and adds them to the selected project. This makes bulk updates much easier than typing usernames manually one by one.

I also make sure usernames are normalized so `@username`, `username`, and line-separated lists are handled consistently.

---

## Cache and Deduplication

I keep a cache of already sent tweet links so the same tweet is not forwarded twice.  
This is important because the bot may scan the same accounts repeatedly, and duplicate alerts would be noisy and confusing.

The cache also helps if the bot restarts, because it can continue from the last known sent state instead of starting blind.

---

## Configuration

I use environment variables for sensitive values and file paths.

### `.env.example`

```env
BOT_TOKEN=put-your-telegram-bot-token-here
ADMIN_IDS=123456789,987654321
GOOGLE_CREDS_PATH=data/service_account.json
PROJECTS_PATH=data/projects.json
CACHE_PATH=data/cache.json
LOG_LEVEL=INFO
```

### Notes

- I keep the Telegram bot token out of source control.
- I keep the Google service account JSON local.
- I store project definitions in `projects.json`.
- I store cache data in `cache.json`.

---

## Security Notes

I avoid hardcoding secrets directly in the code.  
I also recommend keeping the service account file private and rotating any exposed credentials immediately.

For a public repository, I would also add:

- `.gitignore`
- `SECURITY.md`
- `LICENSE`

GitHub also recommends using secret scanning, Dependabot alerts, and other repository security features when a repo is public.

---

## Troubleshooting

### The bot does not send alerts
I check:
- Telegram bot token.
- Admin/chat IDs.
- Project `enabled` state.
- Regex patterns.
- Google Sheet access.

### No usernames are loaded
I check:
- Sheet ID.
- Tab name.
- Column A data.
- Permissions on the sheet.

### Tweets are not detected
I check:
- Cookie/session validity.
- Browser profile persistence.
- Twitter/X page structure changes.
- Regex patterns.
- Network access.

### Duplicate alerts appear
I check:
- Cache file integrity.
- Whether the sent log tab is writable.
- Whether the tweet link format changed.

---

## Roadmap

Possible upgrades I would add next:

- Better browser recovery after session failures.
- More detailed per-project metrics.
- Per-project alert throttling.
- Auto backup of JSON state.
- Command for exporting cache and logs.
- Richer inline menus for project management.
- File upload progress and validation feedback.
- Better support for multiple source sheets.

