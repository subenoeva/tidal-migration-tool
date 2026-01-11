#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tidal Account Migration Tool (Full Suite).
Migrates Tracks, Albums, Artists, and Playlists preserving chronological order.
"""

import tidalapi
import time
import sys

# --- CONFIGURATION ---
API_SLEEP_TIME = 0.02 
PLAYLIST_SLEEP_TIME = 0.5
LIMIT_PAGINATION = 50

def authenticate_user(session_name):
    """Handles the OAuth2 authentication flow."""
    print(f"\n🔑 --- LOGIN: {session_name} ACCOUNT ---")
    session = tidalapi.Session()
    try:
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

def get_ordered_favorites(session, content_type):
    """
    Generic fetcher for Tracks, Albums, and Artists.
    Forces DATE order and DESCENDING direction via raw API.
    
    content_type options: 'tracks', 'albums', 'artists'
    """
    print(f"   ...Fetching {content_type} list (Order: Date)...")
    found_items = []
    offset = 0
    user_id = session.user.id
    
    # Adjust JSON parsing based on type
    is_artist = content_type == 'artists'
    
    while True:
        try:
            params = {
                'limit': LIMIT_PAGINATION,
                'offset': offset,
                'order': 'DATE',           
                'orderDirection': 'DESC'   
            }
            
            # Request to users/{id}/favorites/{content_type}
            endpoint = f'users/{user_id}/favorites/{content_type}'
            json_obj = session.request.request('GET', endpoint, params=params).json()
            items = json_obj.get('items', [])
            
            if not items:
                break 
            
            for entry in items:
                # The actual data is inside the 'item' key
                data = entry.get('item', {})
                
                # Extract info based on type
                item_id = data.get('id')
                added_at = entry.get('created')
                
                if is_artist:
                    name = data.get('name', 'Unknown')
                    desc = "Artist"
                else:
                    name = data.get('title', 'Unknown')
                    artist_name = data.get('artist', {}).get('name', 'Unknown')
                    desc = artist_name

                found_items.append({
                    'id': item_id,
                    'name': name,
                    'desc': desc, # Artist name or "Artist" label
                    'added_at': added_at
                })
            
            sys.stdout.write(f"\r   -> Fetched {len(found_items)} {content_type}...")
            sys.stdout.flush()
            
            offset += LIMIT_PAGINATION
            if len(items) < LIMIT_PAGINATION:
                break
                
        except Exception as e:
            print(f"\n❌ Error fetching {content_type}: {e}")
            break
            
    print("") 
    return found_items

# --- MIGRATION FUNCTIONS ---

def migrate_artists(src, dst):
    """Migrates followed artists."""
    print("\n🎤 --- MIGRATING ARTISTS ---")
    artists = get_ordered_favorites(src, 'artists')
    total = len(artists)
    
    if total == 0:
        print("No followed artists found.")
        return

    # Reverse to keep "Followed Date" order (Oldest -> Newest)
    artists.reverse()
    print(f"🚀 Copying {total} artists...")

    count = 0
    for item in artists:
        try:
            dst.user.favorites.add_artist(item['id'])
            count += 1
            if count % 10 == 0:
                sys.stdout.write(f"\r   -> Followed {count}/{total}...")
                sys.stdout.flush()
            time.sleep(API_SLEEP_TIME)
        except Exception:
            pass
    print(f"\n✅ Artists migration finished.")

def migrate_albums(src, dst):
    """Migrates liked albums."""
    print("\n💿 --- MIGRATING ALBUMS ---")
    albums = get_ordered_favorites(src, 'albums')
    total = len(albums)
    
    if total == 0:
        print("No liked albums found.")
        return

    # Reverse to keep "Added Date" order
    albums.reverse()
    print(f"🚀 Copying {total} albums...")

    count = 0
    for item in albums:
        try:
            dst.user.favorites.add_album(item['id'])
            count += 1
            if count % 10 == 0:
                sys.stdout.write(f"\r   -> Added {count}/{total}...")
                sys.stdout.flush()
            time.sleep(API_SLEEP_TIME)
        except Exception:
            pass
    print(f"\n✅ Albums migration finished.")

def migrate_tracks(src, dst, wipe_first=False):
    """Migrates liked tracks."""
    if wipe_first:
        wipe_destination_tracks(dst)

    print("\n❤️  --- MIGRATING LIKED TRACKS ---")
    tracks = get_ordered_favorites(src, 'tracks')
    total = len(tracks)
    
    if total == 0:
        print("No favorites found.")
        return

    # Preview
    print("\n📝 --- PREVIEW (Most Recent) ---")
    for i, t in enumerate(tracks[:5]):
        print(f"   {i+1}. {t['name']} - {t['desc']}")
    
    if not confirm_action("Start copying tracks?"):
        print("Skipping tracks.")
        return

    print("\n🔄 Reversing list for chronological insertion...")
    tracks.reverse()

    print(f"🚀 Copying {total} tracks...")
    count = 0
    for item in tracks:
        try:
            dst.user.favorites.add_track(item['id'])
            count += 1
            if count % 50 == 0:
                sys.stdout.write(f"\r   -> Processed {count}/{total}...")
                sys.stdout.flush()
            time.sleep(API_SLEEP_TIME)
        except Exception:
            pass 
    print(f"\n✅ Tracks migration finished.")

def migrate_playlists(src, dst):
    """Migrates user-created playlists."""
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

def wipe_destination_tracks(dst):
    """Removes all favorites from the destination account."""
    print("\n🗑️  --- WIPING DESTINATION TRACKS ---")
    try:
        tracks = dst.user.favorites.tracks(limit=None)
        total = len(tracks)
        if total == 0: return

        if not confirm_action(f"WARNING: This will DELETE {total} tracks from DESTINATION. Sure?"):
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

# --- MENU ---

def show_menu():
    print("\n========================================")
    print("   TIDAL FULL MIGRATION TOOL")
    print("========================================")
    print("1. 🚀 FULL ACCOUNT MIGRATION (Everything)")
    print("   (Artists -> Albums -> Tracks -> Playlists)")
    print("----------------------------------------")
    print("2. 🎤 Artists Only")
    print("3. 💿 Albums Only")
    print("4. ❤️  Tracks Only (Wipe & Copy)")
    print("5. 📂 Playlists Only")
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
            # Orden lógico: Primero lo básico (Artistas), luego colecciones (Albums), luego Tracks y Playlists
            migrate_artists(session_source, session_dest)
            migrate_albums(session_source, session_dest)
            migrate_tracks(session_source, session_dest, wipe_first=True)
            migrate_playlists(session_source, session_dest)
        elif choice == '2':
            migrate_artists(session_source, session_dest)
        elif choice == '3':
            migrate_albums(session_source, session_dest)
        elif choice == '4':
            migrate_tracks(session_source, session_dest, wipe_first=True)
        elif choice == '5':
            migrate_playlists(session_source, session_dest)
        elif choice == '6':
            print("👋 Bye!")
            break
        else:
            print("Invalid option.")
        
        input("\n[ENTER] to return to menu...")

if __name__ == "__main__":
    main()