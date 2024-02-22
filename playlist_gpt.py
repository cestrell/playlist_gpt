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
PLAY_DIR = "Playlists/"
EXPORT_DIR = "Export/"
CACHE_DIR = ".cache/"

with open(SP_DC_KEY, "r") as file:
    sp_dc = file.read().strip()

syrics = Spotify(sp_dc)

current_playlist = []

PROVIDER = g4f.Provider.Aura #gpt4 best
        # g4f.Provider.Koala #gpt4
        # g4f.Provider.ChatgptDemo #gpt4
        # g4f.Provider.DeepInfra
        # g4f.Provider.AItianhuSpace

# Playlist categorization instructions
DIRECTION = "Analizamos las canciones y las dividimos con precisión en 5 categorías.\
    1. Contentos y pasandola bien.\
    2. Tristes y corazon roto.\
    3. Negocios mafiosos y belicos.\
    4. Tensión sensual.\
    5. Enamorados. \
    ANALIZA LO SIGUIENTE Y RESPONDE SOLO CON EL NÚMERO Y CATEGORÍA: "

################################
### PROCESS AND CACHE LYRICS ###
################################

def format_lrc(lyrics_json):
    lyrics = lyrics_json['lyrics']['lines']
    lrc = []
    for lines in lyrics:
        lrc.append(lines['words'])

    lrc = '\n'.join(lrc)
    lrc = lrc.replace("\n", " ")
    return lrc

def cache_lyrics(lyrics, track_id):
    filename = os.path.join(CACHE_DIR, track_id)
    with open(filename, "w+") as file:
        file.write(lyrics)

def retrieve_lyrics_from_cache(track_id):
    filename = os.path.join(CACHE_DIR, track_id)
    if os.path.exists(filename):
        print("Cache accessed")
        with open(filename, "r") as file:
            return file.read()
    else:
        print("Not in cache")
        return None
    
def process_no_lyrics(track_id):
    with open(NO_LYRICS_FILE, 'a') as file:
        file.write(PREPEND + track_id + "\n")

def process_track_lyrics(track_id):
    cached_lyrics = retrieve_lyrics_from_cache(track_id)
    if cached_lyrics:
        lyrics = cached_lyrics
    else:
        lyrics_json = syrics.get_lyrics(track_id)
        if lyrics_json is None:
            process_no_lyrics(track_id)
        else: 
            lyrics = format_lrc(lyrics_json)
            cache_lyrics(lyrics, track_id)

def num_processed():
    num_processed = 0
    for index in range(len(current_playlist)):
        if current_playlist[index][1] == True:
            num_processed += 1
    return num_processed

def get_lyrics_from_links():
    global current_playlist

    with open(LINKS_FILE, 'r') as file:
        links = file.read().splitlines()

    for link in links:
        track_id = link.split("/")[-1].split("?")[0]
        process_track_lyrics(track_id)
        current_playlist.append((track_id, False))

#########################
### CATEGORIZE LYRICS ###
#########################

def send_message(content):
    response = g4f.ChatCompletion.create(
        model="g4f.models.gpt_4",
        provider=PROVIDER,
        messages=[{"role": "user", "content": DIRECTION + content}],
    )
    return response

def categorize_lyrics(response, track_id):
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
    global current_playlist

    for index in range(len(current_playlist)):
        track_id = current_playlist[index][0]

        with open(os.path.join(CACHE_DIR, track_id), "r") as file:
            lyrics = file.read()
            response = send_message(lyrics)
            categorize_lyrics(response, track_id)
            current_playlist[index] = (track_id, True)


    for entry in os.scandir(CACHE_DIR):
            with open(os.path.join(CACHE_DIR, entry.name), "r") as file:
                lyrics = file.read()
                track_id = entry.name.split(".")[0]
                response = send_message(lyrics)
                categorize_lyrics(response, track_id)
                os.remove(entry.path)

###########################
### DIRECTORY FUNCTIONS ###
###########################
def make_dirs():
    for dir_path in [PLAY_DIR, CACHE_DIR]:
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)

def check_lyrics_dir():
    if len(current_playlist) == 0:
        print("Run Get Lyrics first")
        quit()
    else:
        num_remaining = len(current_playlist) - num_processed()
        print(f"Lyric entries remaining: {num_remaining}")

def clean_play_dir():
    if os.path.exists(NO_LYRICS_FILE):
        os.remove(NO_LYRICS_FILE)
    for entry in os.scandir(PLAY_DIR):
        with open(entry.path, "w+") as file:
            file.write("")

def clean_export_dir():
    if os.path.isdir(EXPORT_DIR):
        shutil.rmtree(EXPORT_DIR)

def clean_cache_dir():
    for entry in os.scandir(CACHE_DIR):
        if not os.path.isdir(entry.path):
            os.remove(entry.path)

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

def restart_session():
    clean_play_dir()
    clean_export_dir()
    clean_links_file()

##################
### USER INPUT ###
##################

def run_decision(choice):
    if choice == 1: 
        print("Setting up...")
        print("PASTE LINKS INTO LINKS.TXT")
    elif choice == 2:
        get_lyrics_from_links()
        print("Lyrics downloaded...")
    elif choice == 3:
        check_lyrics_dir()
        analyze_lyrics()
        print("Lyrics categorized...")
    elif choice == 4:
        export_playlists()
        print("Playlists exported...")
    elif choice == 5:
        confirm = input("PRESS 1 TO CONFIRM RESTART SESSION: ")
        confirm = int(confirm) if confirm.isnumeric() else 0
        if confirm == 1:
            print("Cleaning...")
            restart_session()
        else:
            print("Nothing happened...")
    elif choice == 6:
        clean_cache_dir()
    elif choice == 7:
        # TESTING
        get_lyrics_from_links()
        print("Lyrics downloaded...")
        check_lyrics_dir()
        analyze_lyrics()
        print("Lyrics categorized...")

    # No Choice
    else: 
        print("Nothing happened...")

def display_menu():
    message = "Welcome to PlaylistGPT. Options:\n\
        1. Get sp_dc token first.\n\
        2. Get lyrics.\n\
        3. Categorize lyrics.\n\
        4. Export Playlists.\n\
        5. Restart Session.\n\
        6. Clear cache.\n\
        7. Run all."
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