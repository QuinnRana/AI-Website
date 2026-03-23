# main.py
from chat import ChatAI
from app.menu import show_main_menu

def main():
    ai = ChatAI(name="Nova")

    # Use intro() if your class has it
    if hasattr(ai, "intro"):
        print(f"{ai.name}: {ai.intro()}")
    else:
        print(f"{ai.name}: Hello!")

    print("Type 'exit' to quit\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "exit":
            print(f"{ai.name}: Goodbye!")
            break

        print(f"{ai.name}: {ai.respond(user_input)}")

if __name__ == "__main__":
    main()
