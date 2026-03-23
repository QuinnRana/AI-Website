# app/menu.py

def show_main_menu() -> str:
    print("\n========================")
    print("      NOVA MAIN MENU    ")
    print("========================")
    print("1) Games")
    print("2) Just Chatting")
    print("3) Record")
    print("4) Recordings / Transcriptions")
    print("5) Music")
    print("0) Exit")
    return input("\nSelect an option: ").strip()
