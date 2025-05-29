from core.chat import conversar, set_system_prompt

PERSONALITY_FILE = "config/personality.txt"

if __name__ == "__main__":
    with open(PERSONALITY_FILE, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    set_system_prompt(system_prompt)

    print("🧠 Aria está pronta para conversar.\n")

    while True:
        entrada = input("Você: ")
        if entrada.lower() in ["sair", "exit", "quit"]:
            break

        resposta = ""
        for token in conversar(entrada):
            print(token, end="", flush=True)
            resposta += token
        print("\n")


