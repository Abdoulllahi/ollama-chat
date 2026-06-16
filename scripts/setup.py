import platform
import shutil
import subprocess
import sys
import webbrowser

MODELS = [
    {
        "tag": "llama3.2:1b",
        "name": "Llama 3.2 (1B)",
        "size": "~1.3 GB",
        "description": "Smallest and fastest. Good for quick testing on low-end "
        "hardware or laptops with 8GB RAM or less. Less capable at complex "
        "reasoning or long conversations.",
    },
    {
        "tag": "llama3.2",
        "name": "Llama 3.2 (3B)",
        "size": "~2 GB",
        "description": "The recommended default. Good balance of speed and "
        "quality for general chat, runs comfortably on 16GB RAM. This is "
        "what gets installed automatically if you don't choose.",
    },
    {
        "tag": "mistral",
        "name": "Mistral (7B)",
        "size": "~4.1 GB",
        "description": "Stronger reasoning than the 3B Llama model, still "
        "runs fine on 16GB RAM, but slower per response and a bigger download.",
    },
    {
        "tag": "qwen2.5:7b",
        "name": "Qwen 2.5 (7B)",
        "size": "~4.7 GB",
        "description": "Strong general-purpose model, particularly good at "
        "coding and multilingual tasks. Needs 16GB RAM minimum.",
    },
]

DEFAULT_MODEL = "llama3.2"


def is_ollama_installed() -> bool:
    return shutil.which("ollama") is not None


def is_ollama_running() -> bool:
    try:
        result = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def installed_models() -> list:
    try:
        result = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.strip().splitlines()[1:]  # skip header row
        return [line.split()[0] for line in lines if line.strip()]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def open_install_page():
    system = platform.system()
    urls = {
        "Windows": "https://ollama.com/download/windows",
        "Darwin": "https://ollama.com/download/mac",
        "Linux": "https://ollama.com/download/linux",
    }
    url = urls.get(system, "https://ollama.com/download")
    print(f"\nOllama isn't installed. Opening the download page for {system}:")
    print(url)
    webbrowser.open(url)
    print("\nAfter installing, run this script again.")


def print_model_choices():
    print("\nAvailable models:\n")
    for i, model in enumerate(MODELS, start=1):
        print(f"  {i}. {model['name']}  ({model['size']})")
        print(f"     {model['description']}\n")


def choose_model() -> str:
    print_model_choices()
    choice = input(
        f"Pick a number, or press Enter for the default ({DEFAULT_MODEL}): "
    ).strip()

    if not choice:
        return DEFAULT_MODEL

    try:
        index = int(choice) - 1
        return MODELS[index]["tag"]
    except (ValueError, IndexError):
        print("Invalid choice, using the default model.")
        return DEFAULT_MODEL


def pull_model(tag: str):
    print(f"\nPulling '{tag}' - this may take a few minutes depending on size...")
    subprocess.run(["ollama", "pull", tag])


def main():
    print("Ollama Chat - setup check\n")

    if not is_ollama_installed():
        open_install_page()
        sys.exit(0)

    print("Ollama is installed.")

    if not is_ollama_running():
        print(
            "Ollama doesn't seem to be running. Try starting it "
            "(it usually runs automatically after install, or run 'ollama serve')."
        )
        sys.exit(1)

    existing = installed_models()
    if existing:
        print(f"\nModels already installed: {', '.join(existing)}")
        use_existing = input("Use one of these instead of pulling a new one? (y/n): ").strip().lower()
        if use_existing == "y":
            print("You can set MODEL_NAME in backend/app.py to one of the models above.")
            sys.exit(0)

    tag = choose_model()
    pull_model(tag)

    print(f"\nDone. Set MODEL_NAME = \"{tag}\" in backend/app.py if it isn't already.")


if __name__ == "__main__":
    main()