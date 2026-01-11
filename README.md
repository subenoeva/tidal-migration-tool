# TIDAL Full Account Migration Tool

A Python-based CLI tool to migrate **Artists, Albums, Tracks, and Playlists** between two **TIDAL** accounts while preserving the original chronological order (date followed / added).

This tool is designed for **full account migration**, safely handling large libraries and avoiding API rate limits.

## ✨ Features

* ✅ Migrate **followed artists** in original follow order
* ✅ Migrate **liked albums** preserving “date added”
* ✅ Migrate **liked tracks** preserving “date added”
* ✅ Migrate **user-created playlists** (name, description, track order)
* 🗑️ Optional **wipe of destination liked tracks** before migration
* 🔐 OAuth authentication for source and destination accounts
* 🚦 Rate-limit safe with configurable delays
* 📋 Interactive command-line menu
* 🔁 Correct chronological reconstruction via reversed insertion

## 📦 Requirements

* Python **3.8+**
* Active TIDAL account(s)
* `tidalapi` Python library

Install dependencies:

```bash
pip install tidalapi
```

## 🚀 Usage

1. Save the script, for example:

```bash
tidal_full_migration.py
```

2. (Optional) Make it executable on Linux/macOS:

```bash
chmod +x tidal_full_migration.py
```

3. Run it:

```bash
./tidal_full_migration.py
# or
python3 tidal_full_migration.py
```

## 🔐 Authentication Flow

You will authenticate **twice**:

1. **SOURCE** → account to migrate from
2. **DESTINATION** → account to migrate to

⚠️ **Important:**
Open the **second login link in incognito/private mode** (or a different browser) to avoid session conflicts.

## 📋 Menu Options

```
1. FULL ACCOUNT MIGRATION (Everything)
   Order:
   Artists → Albums → Tracks → Playlists

2. Artists Only
   Migrates followed artists

3. Albums Only
   Migrates liked albums

4. Tracks Only (Wipe & Copy)
   Deletes destination liked tracks, then migrates tracks

5. Playlists Only
   Migrates user-created playlists only

6. Exit
```

## 🎯 Migration Logic (Key Details)

### Artists

* Fetched via raw API with:

  * `order=DATE`
  * `orderDirection=DESC`
* Reversed before insertion to preserve follow chronology

### Albums

* Same raw API strategy
* Preserves original “liked date” order

### Tracks

* Uses raw API to bypass library default sorting
* Shows a **preview of most recent tracks** before copying
* Destination tracks can be **fully wiped** before migration
* Inserted from oldest → newest to maintain timeline integrity

### Playlists

* Only playlists **created by the user** are migrated
* Skips:

  * Followed playlists
  * Collaborative playlists
* Preserves:

  * Name
  * Description
  * Track order
* Empty playlists are skipped automatically

## ⚙️ Configuration

At the top of the script:

```python
API_SLEEP_TIME = 0.02        # Delay between API calls
PLAYLIST_SLEEP_TIME = 0.5   # Delay between playlist creations
LIMIT_PAGINATION = 50       # API page size
```

Increase delays if you encounter **HTTP 429 (Rate Limit)** errors.

## ⚠️ Warnings & Limitations

* ❌ Deleting liked tracks on the destination account is **irreversible**
* ⚠️ This tool does NOT migrate:

  * Playback history
  * Downloads
  * Account settings
* ⏱️ Large libraries may take several minutes to migrate
* ⚠️ Duplicate items may be silently skipped by TIDAL

## 🧪 Project Status

* ✔️ Stable for personal use
* 🛠️ No automated tests
* 📌 Intended for one-time or infrequent migrations

## 📄 License

Free for personal use.
No warranty provided. Use at your own risk.