# app/router.py

from chat import ChatAI

def run_chat_mode(ai: ChatAI):
    print(f"\n{ai.name}: Chat mode active. Type 'back' to return to menu.\n")
    while True:
        user = input("You: ").strip()
        if user.lower() == "back":
            print(f"{ai.name}: Returning to the main menu...")
            return
        if user.lower() == "exit":
            raise SystemExit
        print(f"{ai.name}:", ai.respond(user))

def run_games_mode():
    # You can expand this into a games submenu later
    print("\n=== GAMES ===")
    print("1) Text RPG")
    print("0) Back")
    choice = input("Choose a game: ").strip()

    if choice == "1":
        # Import here so your project still runs even if RPG files aren’t finished yet
        from rpg.game import run_rpg
        run_rpg()
    else:
        return

def run_record_mode():
    print("\n=== RECORD ===")
    print("Coming soon: microphone recording, save clips, auto-transcribe.")
    input("Press Enter to go back...")

def run_recordings_mode():
    print("\n=== RECORDINGS / TRANSCRIPTIONS ===")
    print("Coming soon: list recordings, open transcript files, search transcripts.")
    input("Press Enter to go back...")

def run_music_mode():
    print("\n=== MUSIC ===")
    print("Coming soon: play local music, playlists, or Spotify control (later).")
    input("Press Enter to go back...")
