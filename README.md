# TIDAL Account Migration Tool

An interactive CLI tool to migrate **Artists, Albums, Tracks, and Playlists** between two **TIDAL** accounts while **preserving the original chronological order**.

## ✨ Key Features

* ✅ Migrate **followed artists** (preserves follow order)
* ✅ Migrate **liked albums** (preserves date added)
* ✅ Migrate **liked tracks** with chronological integrity
* ✅ Migrate **user-created playlists** (name, description, track order)
* 🗑️ Optional **wipe of destination liked tracks**
* 🔐 OAuth authentication for source and destination accounts
* 🖥️ Modern **Rich-powered CLI UI**
* 📋 Interactive menus via **Questionary**
* 📊 Progress bars, spinners, previews, and confirmations
* 🚦 Rate-limit safe with configurable delays

## 📦 Requirements

* Python **3.8+**
* Active TIDAL account(s)

All Python dependencies are defined in **`requirements.txt`**.

## 📥 Installation

1. Clone the repository:

```bash
git clone https://github.com/subenoeva/tidal-migration-tool.git
cd tidal-migration-tool
```

2. (Recommended) Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate      # Linux / macOS
venv\Scripts\activate         # Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## 🚀 Usage

Run the tool:

```bash
python3 tidal_migration.py
```

Or (Linux/macOS):

```bash
chmod +x tidal_migration.py
./tidal_migration.py
```

## 🔐 Authentication Flow

You will authenticate **two accounts**:

1. **SOURCE** → account to migrate from
2. **DESTINATION** → account to migrate to

⚠️ **Important:**
Open the **second login link in incognito/private mode** or a different browser to avoid session conflicts.

## 🧭 Interactive Menu

The tool provides a fully interactive menu:

```
🚀 Full Account Migration (Everything)
   Artists → Albums → Tracks → Playlists

🎤 Migrate Artists Only
💿 Migrate Albums Only
❤️  Migrate Tracks Only (Wipe & Copy)
📂 Migrate Playlists Only
🗑️  Wipe Destination Tracks
❌ Exit
```

Navigation is done using arrow keys and Enter.

## 🎯 Migration Behavior (Details)

### Artists

* Retrieved using raw API calls with:

  * `order=DATE`
  * `orderDirection=DESC`
* Inserted oldest → newest to preserve follow chronology

### Albums

* Preserves original “liked date”
* Migrated in correct chronological order

### Tracks

* Raw API used to bypass library default sorting
* Displays a **Rich table preview** of the most recent tracks
* Requires explicit user confirmation before copying
* Inserts tracks oldest → newest to maintain timeline order
* Optional full wipe of destination tracks

### Playlists

* Only playlists **created by the user** are migrated
* Skips:

  * Followed playlists
  * Collaborative playlists
* Preserves:

  * Playlist name
  * Description
  * Track order
* Empty playlists are skipped automatically

## 🖥️ User Experience Highlights

* Rich panels and headers
* Progress bars with ETA
* Spinners during API fetches
* Interactive confirmations
* Safe cancellation handling (`Ctrl+C`)
* Clear visual feedback for each operation

## ⚙️ Configuration

At the top of the script:

```python
API_SLEEP_TIME = 0.02        # Delay between API calls
PLAYLIST_SLEEP_TIME = 0.5   # Delay between playlist operations
LIMIT_PAGINATION = 50       # API pagination size
```

Increase delays if you encounter **HTTP 429 (Rate Limit)** errors.

## ⚠️ Warnings & Limitations

* ❌ Deleting liked tracks on the destination account is **irreversible**
* ⚠️ The following are NOT migrated:

  * Playback history
  * Downloads / offline content
  * Account settings
* ⚠️ TIDAL may silently ignore duplicates
* ⏱️ Large libraries may take several minutes to migrate

## 🧪 Project Status

* ✔️ Stable for personal use
* 🛠️ No automated tests
* 📌 Intended for one-time or occasional migrations
* 🎯 Focused on correctness and UX over raw speed

## 📄 License

Free for personal use.
No warranty provided. Use at your own risk.