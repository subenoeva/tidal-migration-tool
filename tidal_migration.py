#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tidal Account Migration Tool.
Allows migrating Liked Tracks (preserving chronological order)
and User Playlists from one account to another.
"""

import tidalapi
import time
import sys

# --- CONFIGURATION ---
# Sleep time to avoid Rate Limiting (Error 429)
API_SLEEP_TIME = 0.02 
PLAYLIST_SLEEP_TIME = 0.5
LIMIT_PAGINATION = 50

def authenticate_user(session_name):
    """Handles the OAuth2 authentication flow."""
    print(f"\n🔑 --- LOGIN: {session_name} ACCOUNT ---")
    session = tidalapi.Session()
    try:
        # login_oauth_simple() handles the link printing and polling
        session.login_oauth_simple()
        if session.check_login():
            print(f"✅ Connected as: {session.user.first_name} {session.user.last_name}")
            return session
        else:
            print(f"❌ Error: Could not verify session for {session_name}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Critical error logging into {session_name}: {e}")
        sys.exit(1)

def confirm_action(message):
    """Asks for user confirmation (y/n)."""
    response = input(f"⚠️  {message} (y/n): ").lower()
    return response == 'y'

def get_favorites_manual(session):
    """
    Fetches favorites by forcing DATE order and DESCENDING direction
    via a raw API request, bypassing the library's default sort order.
    """
    print("   ...Fetching favorites list (Order: Date)...")
    found_tracks = []
    offset = 0
    user_id = session.user.id
    
    while True:
        try:
            params = {
                'limit': LIMIT_PAGINATION,
                'offset': offset,
                'order': 'DATE',           
                'orderDirection': 'DESC'   
            }
            
            # Raw request to ensure sorting parameters are respected
            json_obj = session.request.request('GET', f'users/{user_id}/favorites/tracks', params=params).json()
            items = json_obj.get('items', [])
            
            if not items:
                break 
            
            for item in items:
                track_data = item.get('item', {})
                found_tracks.append({
                    'id': track_data.get('id'),
                    'name': track_data.get('title'),
                    'artist': track_data.get('artist', {}).get('name', 'Unknown'),
                    'added_at': item.get('created') 
                })
            
            sys.stdout.write(f"\r   -> Fetched {len(found_tracks)} tracks...")
            sys.stdout.flush()
            
            offset += LIMIT_PAGINATION
            if len(items) < LIMIT_PAGINATION:
                break
                
        except Exception as e:
            print(f"\n❌ Error fetching favorites page: {e}")
            break
            
    print("") # Final newline
    return found_tracks

def wipe_destination_favorites(dst):
    """Removes all favorites from the destination account."""
    print("\n🗑️  --- WIPING DESTINATION FAVORITES ---")
    try:
        tracks = dst.user.favorites.tracks(limit=None)
        total = len(tracks)
        
        if total == 0:
            print("✅ Account is already clean.")
            return

        if not confirm_action(f"WARNING: This will DELETE {total} tracks from the DESTINATION account. Are you sure?"):
            print("Operation cancelled.")
            return

        print("🚀 Deleting...")
        count = 0
        for track in tracks:
            try:
                dst.user.favorites.remove_track(track.id)
                count += 1
                if count % 50 == 0:
                    sys.stdout.write(f"\r   -> Deleted {count}/{total}...")
                    sys.stdout.flush()
                time.sleep(API_SLEEP_TIME)
            except Exception:
                pass
        print(f"\n✅ Wipe completed.")
    except Exception as e:
        print(f"❌ Error during wipe: {e}")

def migrate_favorites(src, dst, wipe_first=False):
    """Orchestrates favorite tracks migration preserving chronological order."""
    if wipe_first:
        wipe_destination_favorites(dst)

    print("\n❤️  --- PREPARING FAVORITES MIGRATION ---")
    
    # 1. Get correctly ordered list (Newest -> Oldest)
    tracks = get_favorites_manual(src)
    total = len(tracks)
    
    if total == 0:
        print("No favorites found.")
        return

    # 2. Preview for safety
    print("\n📝 --- PREVIEW ---")
    print("Verify these are your MOST RECENT tracks:")
    for i, t in enumerate(tracks[:5]):
        print(f"   {i+1}. {t['name']} - {t['artist']}")
    
    if not confirm_action("Start copying?"):
        print("Cancelled.")
        return

    # 3. Reverse list (Oldest -> Newest) for sequential insertion
    print("\n🔄 Reversing list for chronological insertion...")
    tracks.reverse()

    print(f"🚀 Copying {total} tracks...")
    
    count = 0
    errors = 0
    
    for track in tracks:
        try:
            dst.user.favorites.add_track(track['id'])
            count += 1
            
            if count % 25 == 0:
                sys.stdout.write(f"\r   -> Processed {count}/{total}...")
                sys.stdout.flush()
            
            time.sleep(API_SLEEP_TIME)
            
        except Exception:
            errors += 1
            pass 
            
    print(f"\n✅ Process finished. Total: {count}. Errors/Duplicates: {errors}")

def migrate_playlists(src, dst):
    """Migrates only user-created playlists."""
    print("\n🎵 --- MIGRATING PLAYLISTS ---")
    try:
        playlists = src.user.playlists() 
    except Exception as e:
        print(f"❌ Error reading playlists: {e}")
        return

    print(f"Analyzing {len(playlists)} playlists...")
    
    migrated_count = 0
    for pl in playlists:
        try:
            # Check playlist ownership
            try:
                creator_id = pl.creator.id
            except AttributeError:
                continue

            if str(creator_id) != str(src.user.id):
                continue

            print(f"📂 Processing: {pl.name}...")
            
            tracks = pl.tracks(limit=None)
            track_ids = [t.id for t in tracks]
            
            if not track_ids:
                print(f"   (Empty, skipping)")
                continue

            new_pl = dst.user.create_playlist(pl.name, pl.description or "")
            new_pl.add(track_ids)
            migrated_count += 1
            print(f"   ✅ OK ({len(track_ids)} tracks)")
            time.sleep(PLAYLIST_SLEEP_TIME)
            
        except Exception as e:
            print(f"   ❌ Error in '{pl.name}': {e}")
    
    print(f"✅ Playlists finished. Migrated: {migrated_count}.")

def show_menu():
    print("\n========================================")
    print("   TIDAL MIGRATION TOOL")
    print("========================================")
    print("1. 🚀 FULL MIGRATION (Recommended)")
    print("2. ❤️  Favorites Only (With Wipe)")
    print("3. ❤️  Favorites Only (Append - No Wipe)")
    print("4. 📂 Playlists Only")
    print("5. 🗑️  Wipe Destination Favorites Only")
    print("6. ❌ Exit")
    print("========================================")

def main():
    print("--- AUTHENTICATION ---")
    session_source = authenticate_user("SOURCE")
    print("\n⚠️  IMPORTANT: Open the next link in INCOGNITO mode.")
    session_dest = authenticate_user("DESTINATION")

    while True:
        show_menu()
        choice = input("Select option: ")

        if choice == '1':
            migrate_favorites(session_source, session_dest, wipe_first=True)
            migrate_playlists(session_source, session_dest)
        elif choice == '2':
            migrate_favorites(session_source, session_dest, wipe_first=True)
        elif choice == '3':
            migrate_favorites(session_source, session_dest, wipe_first=False)
        elif choice == '4':
            migrate_playlists(session_source, session_dest)
        elif choice == '5':
            wipe_destination_favorites(session_dest)
        elif choice == '6':
            print("👋 Bye!")
            break
        else:
            print("Invalid option.")
        
        input("\n[ENTER] to return to menu...")

if __name__ == "__main__":
    main()