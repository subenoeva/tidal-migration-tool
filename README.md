# Tidal Account Migration Tool

A Python-based tool to migrate content between two **TIDAL** accounts, preserving the original chronological order of *Liked Tracks* (favorites) and copying user-created playlists.

## ✨ Features

* ✅ Migrate **liked tracks** while preserving the original “date added” order.
* ✅ Migrate **user-created playlists** (excluding followed or collaborative playlists).
* 🗑️ Optional **full wipe** of destination favorites before migration.
* 🔁 Append mode to add favorites without deleting existing ones.
* 🔐 OAuth authentication for both source and destination accounts.
* 🚦 Rate-limit safe with configurable delays.
* 📋 Interactive CLI menu.

## 📦 Requirements

* Python **3.8+**
* Active TIDAL account(s)
* `tidalapi` Python library

Install dependencies:

```bash
pip install tidalapi
```

## 🚀 Usage

1. Save the script, for example as:

```bash
tidal_migration.py
```

2. (Optional) Make it executable on Linux/macOS:

```bash
chmod +x tidal_migration.py
```

3. Run the script:

```bash
./tidal_migration.py
# or
python3 tidal_migration.py
```

## 🔐 Authentication

The script will prompt you to log in **twice**:

1. **SOURCE** → source account
2. **DESTINATION** → destination account

⚠️ **Important:**
Open the second login link in **incognito/private mode** or a different browser to avoid session reuse.

## 📋 Menu Options

```
1. FULL MIGRATION (Recommended)
   - Wipes destination favorites
   - Migrates favorites in chronological order
   - Migrates user-created playlists

2. Favorites Only (With Wipe)
   - Wipes destination favorites
   - Migrates favorites only

3. Favorites Only (Append - No Wipe)
   - Appends favorites without deleting existing ones

4. Playlists Only
   - Migrates user-created playlists only

5. Wipe Destination Favorites Only
   - Deletes all destination favorites

6. Exit
```

## ❤️ Favorites Migration (Technical Details)

* Uses a **raw API request** to force:

  * `order=DATE`
  * `orderDirection=DESC`
* Favorites are fetched from **newest to oldest**
* A preview of the most recent tracks is shown before copying
* The list is reversed prior to insertion to ensure correct chronological order in the destination account

## 🎵 Playlists Migration

* Only playlists:

  * Created by the user
  * Non-collaborative
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
LIMIT_PAGINATION = 50       # Pagination size
```

Adjust these values if you encounter **429 (Rate Limit)** errors.

## ⚠️ Warnings

* ❌ Favorite deletion is **irreversible**
* ⚠️ The following are NOT migrated:

  * Favorite albums
  * Favorite artists
  * Followed playlists
* ⏱️ Large libraries may take several minutes to migrate

## 🧪 Project Status

* ✔️ Stable for personal use
* 🛠️ No automated tests
* 📌 Designed as a one-time migration tool

## 📄 License

Free for personal use.
No warranty provided. Use at your own risk.