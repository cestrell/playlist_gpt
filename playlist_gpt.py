import os
import shutil
import g4f
from collections import Counter
from syrics.api import Spotify
import argparse

#################
### ARGUMENTS ###
#################
parser = argparse.ArgumentParser(description='PlaylistGPT')
parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
args = parser.parse_args()

def verbose_print(message):
    if VERBOSE: print(message)

#################
### CONSTANTS ###
#################

PREPEND = "https://open.spotify.com/track/"
SP_DC_KEY = "SP_DC_KEY.txt"
LINKS_FILE = "links.txt"
PLAY_DIR = "Playlists/"
NO_LYRICS_FILE = PLAY_DIR + "no_lyrics.txt"
EXPORT_DIR = "Export/"
CACHE_DIR = ".cache/"
STATE_FILE = ".state"
NUM_ITERATIONS = 1 # DEFAULT
# NUM_ITERATIONS = 5 # MORE ACCURACY
VERBOSE = args.verbose

with open(SP_DC_KEY, "r") as file:
    sp_dc = file.read().strip()

syrics = Spotify(sp_dc)

current_state = []

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

def retrieve_lyrics_from_cache(track_id):
    filename = os.path.join(CACHE_DIR, track_id)
    if os.path.exists(filename):
        verbose_print(f"{track_id}: Cache accessed")
        with open(filename, "r") as file:
            return file.read()
    else:
        verbose_print(f"{track_id}: Not in cache. Downloading...")
        return None
    
def process_no_lyrics(track_id):
    with open(NO_LYRICS_FILE, 'a') as file:
        file.write(PREPEND + track_id + "\n")

def cache_lyrics(lyrics, track_id):
    filename = os.path.join(CACHE_DIR, track_id)
    with open(filename, "w+") as file:
        file.write(lyrics)

def process_track_lyrics(track_id):
    cached_lyrics = retrieve_lyrics_from_cache(track_id)
    if not cached_lyrics:
        lyrics_json = syrics.get_lyrics(track_id)
        if lyrics_json is None:
            process_no_lyrics(track_id)
        else: 
            lyrics = format_lrc(lyrics_json)
            cache_lyrics(lyrics, track_id)

def get_lyrics_from_links():
    global current_state
    for track_id in current_state:
        process_track_lyrics(track_id)

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

def categorize_lyrics_pl(category, track_id):
    if category != "uncategorized":
        with open(os.path.join(PLAY_DIR, f"bien_{category}.txt"), 'a') as file:
            file.write(PREPEND + track_id + "\n")
            verbose_print(f"Added {track_id} to {category.upper()}")
    else:
        with open(os.path.join(PLAY_DIR, "uncategorized.txt"), 'a') as file:
            file.write(PREPEND + track_id + "\n")
            verbose_print(f"Added {track_id} to UNCATEGORIZED")

def get_category_from_response(response):
    categories = ["arriba", "tristes", "belicos", "sensual", "enamorado"]
    if response[0].isnumeric() and 0 < int(response[0]) < 6:
        category = categories[int(response[0]) - 1]
        return category
    else: 
        return "uncategorized"
    
def finalize_category(categories):
    category_counts = Counter(categories)
    final_category = max(category_counts, key=category_counts.get)
    return final_category

def analyze_lyrics_from_links():
    global current_state
    to_process = len(current_state)
    while to_process > 0:
        track_id = current_state[0]
        
        with open(os.path.join(CACHE_DIR, track_id), "r") as file:
            lyrics = file.read()
            category = "uncategorized"

            # Request response from g4f server, handle errors
            try:
                if NUM_ITERATIONS > 2:
                    categories = {}
                    for _ in range(NUM_ITERATIONS):
                        response = send_message(lyrics)
                        category = get_category_from_response(response)
                        if category in categories:
                            categories[category] += 1
                        else:
                            categories[category] = 1

                    category = finalize_category(categories)
                else:
                    response = send_message(lyrics)
                    category = get_category_from_response(response)
            except Exception as e:
                verbose_print(f"Server shutout: {e}")
                continue

            # Add to category playlist
            categorize_lyrics_pl(category, track_id)

            # Update state
            current_state.pop(0)
            save_state()
            to_process -= 1
        # with
    # for

##################
### SAVE STATE ###
##################
def check_num_remaining():
    global current_state
    num_remaining = len(current_state)
    verbose_print(f"Lyric entries remaining: {num_remaining}\n")

def load_state():
    global current_state
    with open(STATE_FILE, "r") as file:
        current_state = [track_id.strip() for track_id in file.readlines()]
    verbose_print("Previous state loaded.")

def save_state():
    global current_state
    with open(STATE_FILE, "w") as file:
        for track_id in current_state:
            file.write(track_id + "\n")
    verbose_print("State saved.")

# Create link list to process
def initialize_state():
    global current_state

    with open(LINKS_FILE, 'r') as file:
        links = file.read().splitlines()

    for link in links:
        track_id = link.split("/")[-1].split("?")[0]
        current_state.append(track_id)

    save_state()

###########################
### DIRECTORY FUNCTIONS ###
###########################

# Create necessary directories
def setup():
    if not check_links(): quit()

    if not os.path.exists(STATE_FILE):
        with open(STATE_FILE, "w+") as file:
            file.write("")

    for dir_path in [PLAY_DIR, CACHE_DIR]:
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)

# Verify list in links.txt
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

# Reset Playlist/
def clean_play_dir():
    if os.path.exists(NO_LYRICS_FILE):
        os.remove(NO_LYRICS_FILE)
    for entry in os.scandir(PLAY_DIR):
        with open(entry.path, "w+") as file:
            file.write("")

# Reset Exports/
def clean_export_dir():
    if os.path.isdir(EXPORT_DIR):
        shutil.rmtree(EXPORT_DIR)

# Reset .cache/
def clean_cache_dir():
    for entry in os.scandir(CACHE_DIR):
        if not os.path.isdir(entry.path):
            os.remove(entry.path)

# Reset links.txt
def clean_links_file():
    with open(LINKS_FILE, "w") as file:
        file.write("")

        
# Save PlaylistGPT output to Export/
def export_playlists():
    if not os.path.isdir(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)
    
    # Copy over files
    export_num = 0
    for entry in os.scandir(EXPORT_DIR):
        if entry.is_dir():
            export_num += 1
    
    folder_dir = EXPORT_DIR + f"trial_{export_num}_iter_{NUM_ITERATIONS}/"

    if not os.path.isdir(folder_dir):
        os.makedirs(folder_dir)

    for entry in os.scandir(PLAY_DIR):
        shutil.copyfile(entry.path, folder_dir + entry.name)

def restart_session():
    global current_state 
    current_state = []
    
    clean_play_dir()
    #clean_links_file()

def complete_reset():
    restart_session()
    clean_export_dir()
    clean_cache_dir()

def auto_export_high_iter():
    if NUM_ITERATIONS > 3:
        export_playlists()

##################
### USER INPUT ###
##################

def run_decision(choice):
    # Set up
    if choice == 1: 
        verbose_print("Setting up...")
        print("PASTE LINKS INTO LINKS.TXT")
    # Get lyrics
    elif choice == 2:
        initialize_state()
        get_lyrics_from_links()
        verbose_print("Lyrics downloaded...")
    # Categorize lyrics
    elif choice == 3:
        load_state()
        check_num_remaining()
        analyze_lyrics_from_links()
        auto_export_high_iter()
        verbose_print("Lyrics categorized...")
    # Export playlists
    elif choice == 4:
        export_playlists()
        verbose_print("Playlists exported...")
    # Restart session
    elif choice == 5:
        confirm = input("PRESS 1 TO CONFIRM RESTART SESSION: ")
        confirm = int(confirm) if confirm.isnumeric() else 0
        if confirm == 1:
            verbose_print("Cleaning...")
            restart_session()
        else:
            verbose_print("Nothing happened...")
    # Clean cache
    elif choice == 6:
        clean_cache_dir()
    elif choice == 7:
        # TESTING
        get_lyrics_from_links()
        verbose_print("Lyrics downloaded...")
        check_num_remaining()
        analyze_lyrics_from_links()
        auto_export_high_iter()
        verbose_print("Lyrics categorized...")
    elif choice == 8:
        #complete_reset()
        print("careful")

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
        7. Run all.\n\
        8. Complete reset\n"
    print(message)

############
### MAIN ###
############

def main():
    
    # Setup
    setup()

    # User input
    display_menu()
    choice = input("Choice: ")
    choice = int(choice) if choice.isnumeric() else 0

    # Run PlaylistGPT
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