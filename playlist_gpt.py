import os
import shutil
from syrics.api import Spotify
import g4f

#################
### CONSTANTS ###
#################

PREPEND = "https://open.spotify.com/track/"
SP_DC_KEY = "SP_DC_KEY.txt"
LINKS_FILE = "links.txt"
NO_LYRICS_FILE = "Playlists/no_lyrics.txt"
LYRICS_DIR = "Lyrics/"
PLAY_DIR = "Playlists/"
EXPORT_DIR = "Export/"

PROVIDER = g4f.Provider.Aura #gpt4 best
        # g4f.Provider.Koala #gpt4
        # g4f.Provider.ChatgptDemo #gpt4
        # g4f.Provider.DeepInfra
        # g4f.Provider.AItianhuSpace

# Corrido playlist category instructions for g4f
DIRECTION = "Analizamos las canciones y las dividimos con precisión en 5 categorías.\
    1. Contentos.\
    2. Tristes.\
    3. Negocios mafiosos.\
    4. Tensión sensual.\
    5. Enamorados. \
    ANALIZA LO SIGUIENTE Y RESPONDE SOLO CON EL NÚMERO Y CATEGORÍA: "

##################
### GET LYRICS ###
##################

def format_lrc(lyrics_json):
    lyrics = lyrics_json['lyrics']['lines']
    lrc = []
    for lines in lyrics:
        lrc.append(lines['words'])

    lrc = '\n'.join(lrc)
    lrc = lrc.replace("\n", " ")
    return lrc

def get_lyrics():
    with open(SP_DC_KEY, "r") as file:
        sp_dc = file.read().strip()

    syrics = Spotify(sp_dc)

    with open(LINKS_FILE, 'r') as file:
        links = file.read().splitlines()

    for link in links:
        track_id = link.split("/")[-1].split("?")[0]
        lyrics_json = syrics.get_lyrics(track_id)
        
        if lyrics_json is None:
            with open(NO_LYRICS_FILE, 'a') as file:
                file.write(PREPEND + track_id + "\n")
        else:
            lyrics = format_lrc(lyrics_json)
            filename = os.path.join(LYRICS_DIR, f"{track_id}.lrc")
            with open(filename, "w+") as file:   
                file.write(lyrics)
    print("Lyric download complete.\n")

#########################
### CATEGORIZE LYRICS ###
#########################

# Functions for G4F integration
def send_message(content):
    response = g4f.ChatCompletion.create(
        model="g4f.models.gpt_4",
        provider=PROVIDER,
        messages=[{"role": "user", "content": DIRECTION + content}],
    )
    return response

def categorize(response, track_id):
    categories = ["arriba", "tristes", "belicos", "sensual", "enamorado"]

    if response[0].isnumeric() and 0 < int(response[0]) < 6:
        category_index = int(response[0]) - 1
        with open(os.path.join(PLAY_DIR, f"bien_{categories[category_index]}.txt"), 'a') as file:
            file.write(PREPEND + track_id + "\n")
            print(f"Added {track_id} to {categories[category_index].upper()}")
    else:
        with open(os.path.join(PLAY_DIR, "uncategorized.txt"), 'a') as file:
            file.write(PREPEND + track_id + "\n")
            print(f"Added {track_id} to UNCATEGORIZED")

def analyze_lyrics():
    for entry in os.scandir(LYRICS_DIR):
            with open(os.path.join(LYRICS_DIR, entry.name), "r") as file:
                lyrics = file.read()
                track_id = entry.name.split(".")[0]
                response = send_message(lyrics)
                categorize(response, track_id)
                os.remove(entry.path)

########################
### HELPER FUNCTIONS ###
########################
def make_dirs():
    for dir_path in [LYRICS_DIR, PLAY_DIR, EXPORT_DIR]:
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)

def check_lyrics_dir():
    num_lyrics = len(os.listdir(LYRICS_DIR))
    if num_lyrics == 0:
        print("Run Get Lyrics first")
        quit()
    else:
        print(f"Lyric entries remaining: {num_lyrics}")

def clean_play_dir():
    for entry in os.scandir(PLAY_DIR):
        with open(entry.path, "w+") as file:
            file.write("")

def clean_export_dir():
    for entry in os.scandir(EXPORT_DIR):
        if not os.path.isdir(entry.path):
            os.remove(entry.path)

def clean_lyric_dir():
    for entry in os.scandir(LYRICS_DIR):
        os.remove(entry.path)

    if os.path.exists(NO_LYRICS_FILE):
        os.remove(NO_LYRICS_FILE)

def clean_links_file():
    with open(LINKS_FILE, "w") as file:
        file.write("")

def check_links():
    if not os.path.exists(LINKS_FILE):
        clean_links_file()
        print("PASTE LINKS INTO LINKS.TXT")
        return False

    with open(LINKS_FILE, "r") as file:
        links = file.read().strip()
        if len(links) == 0:
            print("PASTE LINKS INTO LINKS.TXT")
            return False
        else:
            print("NICE LINKS, SETUP COMPLETE")
            return True
        
def export_playlists():
    if not os.path.isdir(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)
    for entry in os.scandir(PLAY_DIR):
        shutil.copy(entry.path, EXPORT_DIR + entry.name)

def full_reset():
    clean_play_dir()
    clean_lyric_dir()
    clean_export_dir()
    clean_links_file()

def run_decision(choice):
    if choice == 1: 
        print("Setting up...")
        print("PASTE LINKS INTO LINKS.TXT")
    elif choice == 2:
        if len(os.listdir(LYRICS_DIR)) != 0:
            print("Lyrics already downloaded...")
        else:
            print("Getting lyrics...")
            get_lyrics()
    elif choice == 3:
        print("Categorizing lyrics...")
        check_lyrics_dir()
        analyze_lyrics()
    elif choice == 4:
        print("Exporting playlists...")
        export_playlists()
    elif choice == 5:
        confirm = input("PRESS 1 TO CONFIRM RESET: ")
        confirm = int(confirm) if confirm.isnumeric() else 0
        if confirm == 1:
            print("Cleaning...")
            full_reset()
        else:
            print("Nothing happened...")
    # No Choice
    else: 
        print("Nothing happened...")

def display_menu():
    message = "Welcome to TumbadoAI. Options:\n\
        1. Get sp_dc token first.\n\
        2. Get lyrics.\n\
        3. Categorize lyrics.\n\
        4. Export Playlists.\n\
        5. Reset Session.\n"
    print(message)

############
### MAIN ###
############

def main():
    make_dirs()

    if not check_links(): quit()

    display_menu()
    choice = input("Choice: ")
    choice = int(choice) if choice.isnumeric() else 0

    run_decision(choice)
    
if __name__ == "__main__":
    main()


# MORE PROVIDERS
# provider=g4f.Provider.AiChatOnline,
# provider=g4f.Provider.ChatBase,
# provider=g4f.Provider.ChatForAi,
# provider=g4f.Provider.ChatgptAi,
# provider=g4f.Provider.ChatgptNext,
# provider=g4f.Provider.Gemini,
# provider=g4f.Provider.FreeChatgpt,
# provider=g4f.Provider.GeminiProChat,
# provider=g4f.Provider.Gpt6,
# provider=g4f.Provider.GptChatly,
# provider=g4f.Provider.GptForLove,
# provider=g4f.Provider.GptGo,
# provider=g4f.Provider.GptTalkRu,
# provider=g4f.Provider.HuggingChat,
# provider=g4f.Provider.Liaobots,
# provider=g4f.Provider.Llama2,
# provider=g4f.Provider.MyShell,
# provider=g4f.Provider.OnlineGpt,
# provider=g4f.Provider.OpenaiChat,
# provider=g4f.Provider.Pi,
# provider=g4f.Provider.Poe,
# provider=g4f.Provider.Raycast,
# provider=g4f.Provider.You,