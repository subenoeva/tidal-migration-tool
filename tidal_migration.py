#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tidal Account Migration Tool (Pro UX Version).
Migrates Tracks, Albums, Artists, and Playlists using a modern CLI interface.
"""

import tidalapi
import time
import sys

# --- UX LIBRARIES ---
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich import print as rprint
import questionary

# --- CONFIGURATION ---
API_SLEEP_TIME = 0.02 
PLAYLIST_SLEEP_TIME = 0.5
LIMIT_PAGINATION = 50

# Initialize Rich Console
console = Console()

def print_header():
    """Prints a nice header for the tool."""
    console.clear()
    title = "[bold cyan]🌊 TIDAL MIGRATION TOOL[/bold cyan]"
    subtitle = "[dim]Migrate your library preserving chronological order[/dim]"
    console.print(Panel(f"{title}\n{subtitle}", expand=False, border_style="cyan"))

def authenticate_user(session_name):
    """Handles the OAuth2 authentication flow with visual feedback."""
    console.print(f"\n[bold yellow]🔑 LOGIN REQUIRED: {session_name} ACCOUNT[/bold yellow]")
    
    session = tidalapi.Session()
    try:
        # We assume login_oauth_simple handles the print internally.
        # We wrap it in a visual separator.
        print("-" * 40)
        session.login_oauth_simple()
        print("-" * 40)
        
        if session.check_login():
            user_name = f"{session.user.first_name} {session.user.last_name}"
            console.print(f"✅ [green]Connected as:[/green] [bold white]{user_name}[/bold white]")
            return session
        else:
            console.print(f"❌ [red]Error: Could not verify session for {session_name}[/red]")
            sys.exit(1)
    except Exception as e:
        console.print(f"❌ [red]Critical error logging into {session_name}: {e}[/red]")
        sys.exit(1)

def get_ordered_favorites(session, content_type):
    """Generic fetcher with a Spinner animation."""
    found_items = []
    offset = 0
    user_id = session.user.id
    is_artist = content_type == 'artists'

    # Rich Spinner context
    with console.status(f"[bold cyan]Fetching {content_type} from Tidal API...[/bold cyan]", spinner="dots"):
        while True:
            try:
                params = {
                    'limit': LIMIT_PAGINATION,
                    'offset': offset,
                    'order': 'DATE',           
                    'orderDirection': 'DESC'   
                }
                endpoint = f'users/{user_id}/favorites/{content_type}'
                json_obj = session.request.request('GET', endpoint, params=params).json()
                items = json_obj.get('items', [])
                
                if not items:
                    break 
                
                for entry in items:
                    data = entry.get('item', {})
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
                        'desc': desc,
                        'added_at': added_at
                    })
                
                offset += LIMIT_PAGINATION
                if len(items) < LIMIT_PAGINATION:
                    break
                    
            except Exception as e:
                console.print(f"\n❌ [red]Error fetching {content_type}: {e}[/red]")
                break
    
    console.print(f"   ✨ Found [bold green]{len(found_items)}[/bold green] {content_type}.")
    return found_items

# --- MIGRATION FUNCTIONS ---

def migrate_artists(src, dst):
    console.print("\n[bold magenta]🎤 MIGRATING ARTISTS[/bold magenta]")
    artists = get_ordered_favorites(src, 'artists')
    if not artists: return

    artists.reverse()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Following artists...", total=len(artists))
        
        for item in artists:
            try:
                dst.user.favorites.add_artist(item['id'])
                time.sleep(API_SLEEP_TIME)
            except Exception:
                pass
            progress.advance(task)
    
    console.print("✅ [green]Artists migration finished.[/green]")

def migrate_albums(src, dst):
    console.print("\n[bold blue]💿 MIGRATING ALBUMS[/bold blue]")
    albums = get_ordered_favorites(src, 'albums')
    if not albums: return

    albums.reverse()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[blue]Adding albums...", total=len(albums))
        
        for item in albums:
            try:
                dst.user.favorites.add_album(item['id'])
                time.sleep(API_SLEEP_TIME)
            except Exception:
                pass
            progress.advance(task)
            
    console.print("✅ [green]Albums migration finished.[/green]")

def migrate_tracks(src, dst, wipe_first=False):
    if wipe_first:
        wipe_destination_tracks(dst)

    console.print("\n[bold red]❤️  MIGRATING LIKED TRACKS[/bold red]")
    tracks = get_ordered_favorites(src, 'tracks')
    if not tracks: return

    # --- RICH TABLE PREVIEW ---
    table = Table(title="Preview: Most Recent Tracks", border_style="red")
    table.add_column("#", style="dim")
    table.add_column("Track", style="bold white")
    table.add_column("Artist", style="cyan")
    table.add_column("Added At", style="dim")

    for i, t in enumerate(tracks[:5]):
        table.add_row(str(i+1), t['name'], t['desc'], t.get('added_at', '')[:10])
    
    console.print(table)
    
    if not questionary.confirm("Do these tracks look correct? Start copying?").ask():
        console.print("[yellow]Skipping tracks.[/yellow]")
        return

    console.print("[dim]🔄 Reversing list for chronological insertion...[/dim]")
    tracks.reverse()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[red]Copying tracks...", total=len(tracks))
        
        for item in tracks:
            try:
                dst.user.favorites.add_track(item['id'])
                time.sleep(API_SLEEP_TIME)
            except Exception:
                pass 
            progress.advance(task)

    console.print("✅ [green]Tracks migration finished.[/green]")

def migrate_playlists(src, dst):
    console.print("\n[bold green]🎵 MIGRATING PLAYLISTS[/bold green]")
    try:
        playlists = src.user.playlists() 
    except Exception as e:
        console.print(f"❌ [red]Error reading playlists: {e}[/red]")
        return

    # Filter own playlists first
    own_playlists = []
    for pl in playlists:
        try:
            if str(pl.creator.id) == str(src.user.id):
                own_playlists.append(pl)
        except AttributeError:
            continue

    console.print(f"   Found [bold]{len(own_playlists)}[/bold] user-created playlists.")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console
    ) as progress:
        main_task = progress.add_task("[green]Processing playlists...", total=len(own_playlists))
        
        for pl in own_playlists:
            progress.update(main_task, description=f"[green]Migrating: {pl.name}[/green]")
            
            try:
                tracks = pl.tracks(limit=None)
                track_ids = [t.id for t in tracks]
                
                if track_ids:
                    new_pl = dst.user.create_playlist(pl.name, pl.description or "")
                    new_pl.add(track_ids)
                    time.sleep(PLAYLIST_SLEEP_TIME)
            except Exception as e:
                console.print(f"   ⚠️ Error in '{pl.name}': {e}")
            
            progress.advance(main_task)

    console.print("✅ [green]Playlists migration finished.[/green]")

def wipe_destination_tracks(dst):
    console.print("\n[bold red]🗑️  WIPING DESTINATION TRACKS[/bold red]")
    
    # Check quickly if empty
    with console.status("Checking destination...", spinner="dots"):
        tracks = dst.user.favorites.tracks(limit=None)
    
    total = len(tracks)
    if total == 0: 
        console.print("   [green]Destination is already clean.[/green]")
        return

    if not questionary.confirm(f"WARNING: DELETE {total} tracks from DESTINATION?").ask():
        console.print("[yellow]Wipe cancelled.[/yellow]")
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        task = progress.add_task("[red]Deleting...", total=total)
        
        for track in tracks:
            try:
                dst.user.favorites.remove_track(track.id)
                time.sleep(API_SLEEP_TIME)
            except Exception:
                pass
            progress.advance(task)

    console.print("✅ [green]Wipe completed.[/green]")

# --- MAIN FLOW ---

def main():
    print_header()
    
    # Login Section
    console.print(Panel("Please authenticate both accounts.", style="dim"))
    session_source = authenticate_user("SOURCE")
    
    console.print("\n[yellow]⚠️  IMPORTANT: Open the next link in INCOGNITO mode.[/yellow]")
    session_dest = authenticate_user("DESTINATION")

    # Interactive Menu Loop
    while True:
        print_header()
        console.print(f"[dim]Source: {session_source.user.first_name} | Dest: {session_dest.user.first_name}[/dim]\n")
        
        choice = questionary.select(
            "What would you like to do?",
            choices=[
                "🚀 Full Account Migration (Everything)",
                "🎤 Migrate Artists Only",
                "💿 Migrate Albums Only",
                "❤️  Migrate Tracks Only (Wipe & Copy)",
                "📂 Migrate Playlists Only",
                "🗑️  Wipe Destination Tracks",
                "❌ Exit"
            ],
            style=questionary.Style([
                ('qmark', 'fg:#00ffff bold'),       
                ('question', 'bold'),               
                ('answer', 'fg:#f44336 bold'),      
                ('pointer', 'fg:#673ab7 bold'),     
                ('highlighted', 'fg:#673ab7 bold'), 
                ('selected', 'fg:#cc5454'),         
                ('separator', 'fg:#cc5454'),        
                ('instruction', ''),                
                ('text', ''),                       
                ('disabled', 'fg:#858585 italic')   
            ])
        ).ask()

        if not choice or "Exit" in choice:
            console.print("[bold cyan]👋 Happy listening![/bold cyan]")
            break

        if "Full Account Migration" in choice:
            migrate_artists(session_source, session_dest)
            migrate_albums(session_source, session_dest)
            migrate_tracks(session_source, session_dest, wipe_first=True)
            migrate_playlists(session_source, session_dest)
        
        elif "Artists Only" in choice:
            migrate_artists(session_source, session_dest)
        
        elif "Albums Only" in choice:
            migrate_albums(session_source, session_dest)
        
        elif "Tracks Only" in choice:
            migrate_tracks(session_source, session_dest, wipe_first=True)
        
        elif "Playlists Only" in choice:
            migrate_playlists(session_source, session_dest)
        
        elif "Wipe" in choice:
            wipe_destination_tracks(session_dest)
        
        questionary.press_any_key_to_continue(message="Press any key to return to menu...").ask()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[red]Operation cancelled by user.[/red]")
        sys.exit(0)