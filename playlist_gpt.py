import os
import shutil
import g4f
from g4f.client import Client
from g4f.Provider import Aura
from collections import Counter
from syrics.api import Spotify
import argparse

#################
### ARGUMENTS ###
#################

parser = argparse.ArgumentParser(description='PlaylistGPT')
parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
args = parser.parse_args()

def verbose_print(message, end='\n'):
    if VERBOSE: print(message, end)


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
# NUM_ITERATIONS = 1 # DEFAULT
NUM_ITERATIONS = 3 # MORE ACCURACY
VERBOSE = args.verbose

current_state = []
no_lyrics = []


##############
### SYRICS ###
##############

with open(SP_DC_KEY, "r") as file:
    sp_dc = file.read().strip()

syrics = Spotify(sp_dc)


##################
### GPT 4 FREE ###
##################

MODEL = "gpt-4"
# MODEL = "gpt-3.5-turbo"

PROVIDER = g4f.Provider.Aura #gpt4 best
        # g4f.Provider.Koala #gpt4
        # g4f.Provider.ChatgptDemo #gpt4
        # g4f.Provider.DeepInfra
        # g4f.Provider.AItianhuSpace

client = Client( 
    # provider=PROVIDER
)

# Playlist categorization instructions
DIRECTION = "Analizamos las canciones y las dividimos con precisión en 5 categorías.\
    1. Contentos y pasandola bien.\
    2. Tristes y corazon roto.\
    3. Negocios mafiosos y belicos.\
    4. Tensión sensual.\
    5. Enamorados. \
    ANALIZA LO SIGUIENTE Y RESPONDE SOLO CON EL NÚMERO Y CATEGORÍA: "

def send_message(content):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": DIRECTION + content}],
        # messages=[{"role": "user", "content": "hello"}],
    )
    return response.choices[0].message.content


#########################
### GET PLAYLIST INFO ###
#########################

def get_playlist():    
    while True:
        playlist_link = input("Enter the Spotify playlist link: ")
        if "spotify" in playlist_link.lower(): break
        else: print("Enter valid spotify link.")

    playlist_id = playlist_link.split("/")[-1].split("?")[0]
    
    playlist_data = syrics.playlist(playlist_id)
    playlist_total = playlist_data['tracks']['total']
    playlist = syrics.playlist_tracks(playlist_id, playlist_total)

    with open("links.txt", "a+") as file:
        for track_id in playlist:
            file.write(PREPEND + track_id + '\n')


################################
### PROCESS AND CACHE LYRICS ###
################################

def format_lrc(lyrics_json):
    lines = [line['words'] for line in lyrics_json['lyrics']['lines']]
    lrc = ' '.join(lines)
    remove_char = "♪'.!?¿(),"
    for char in remove_char:
        lrc = lrc.replace(char, "")
    lrc.replace("-", " ")
    return lrc.lower()

def retrieve_lyrics_from_cache(track_id):
    filename = os.path.join(CACHE_DIR, track_id)
    if os.path.exists(filename):
        verbose_print(f"{track_id}: Cache access")
        with open(filename, "r") as file:
            return file.read()
    else:
        verbose_print(f"{track_id}: Not cached. Downloading...", end=' ')
        return None
    
def process_no_lyrics(track_id):
    global no_lyrics
    no_lyrics.append(track_id)
    verbose_print(f"No lyrics.")

def cache_lyrics(lyrics, track_id):
    filename = os.path.join(CACHE_DIR, track_id)
    with open(filename, "w+") as file:
        file.write(lyrics)
    verbose_print("Downloaded.")

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
    global no_lyrics
    no_lyrics = []
    for track_id in current_state:
        process_track_lyrics(track_id)


#########################
### CATEGORIZE LYRICS ###
#########################
    
def prepare_no_lyrics_state():
    global current_state
    global no_lyrics

    for no_lyric in no_lyrics:
        current_state.remove(no_lyric)
        with open(NO_LYRICS_FILE, 'a') as file:
            file.write(PREPEND + no_lyric + "\n")
    save_state()

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
    
    prepare_no_lyrics_state()
    check_num_remaining()

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
                    print(f"Categorized as: {categories}")
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

    if not os.path.exists(SP_DC_KEY):
        with open(SP_DC_KEY, "w+") as file:
            file.write("")

    if not os.path.exists(STATE_FILE):
        with open(STATE_FILE, "w+") as file:
            file.write("")

    for dir_path in [PLAY_DIR, CACHE_DIR]:
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)


def check_links():
    if not os.path.exists(LINKS_FILE) or os.path.getsize(LINKS_FILE) == 0:
        clean_links_file()
        print("No links found in", LINKS_FILE)
        mode = input("Do you want to import links automatically? (yes/no): ").lower()
        if mode == "yes":
            get_playlist()
            return True
        else:
            print("Please paste the links into", LINKS_FILE)
            input("Press Enter to open links.txt with Notepad...")
            os.system("notepad.exe " + LINKS_FILE)
            return False
    else:
        verbose_print(f"Found links in {LINKS_FILE}. Session continuing.")
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

# Reset links.txt
def clean_state_file():
    with open(STATE_FILE, "w") as file:
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

# Keep cache, restart playlist analysis
def restart_session():
    global current_state 
    current_state = []
    clean_play_dir()
    clean_links_file()
    clean_state_file()

# Delete caches and exports
def complete_reset():
    restart_session()
    clean_export_dir()
    clean_cache_dir()
    clean_links_file()

# Keep accurate results
def auto_export_high_iter():
    if NUM_ITERATIONS > 3:
        export_playlists()


##################
### USER INPUT ###
##################
        
def one_set_up_token():
    verbose_print("Setting up...")
    print("PASTE YOUR sp_dc int SP_DC_KEY")

def two_get_lyrics():
    if os.path.getsize(STATE_FILE) == 0:
        verbose_print("New playlist initialized...")
        initialize_state()
    else:
        load_state()
    get_lyrics_from_links()
    verbose_print("Lyrics downloaded...")

def three_categorize_lyrics():
    load_state()
    analyze_lyrics_from_links()
    auto_export_high_iter()
    verbose_print("Lyrics categorized...")

def four_export_playlists():
    export_playlists()
    verbose_print("Playlists exported...")

def five_restart_session():
    confirm = input("PRESS 1 TO CONFIRM RESTART SESSION: ")
    confirm = int(confirm) if confirm.isnumeric() else 0
    if confirm == 1:
        verbose_print("Cleaning...\n")
        restart_session()
    else:
        verbose_print("Nothing happened...")

def seven_run_all():
    two_get_lyrics()
    three_categorize_lyrics()

def eight_complete_reset():
    five_restart_session()
    clean_cache_dir()
    
def run_decision(choice):
    if choice == 1: 
        one_set_up_token()
    elif choice == 2:
        two_get_lyrics()
    elif choice == 3:
        three_categorize_lyrics()
    elif choice == 4:
        four_export_playlists()
    elif choice == 5:
        five_restart_session()
    elif choice == 6:
        clean_cache_dir()
    elif choice == 7:
        seven_run_all()
    elif choice == 8:
        eight_complete_reset()
    elif choice == 9:
        exit()
    else: 
        print("Nothing happened...")

def display_menu():
    message = """\nWelcome to PlaylistGPT. Options:
    1. Get sp_dc token first.
    2. Get lyrics.
    3. Categorize lyrics.
    4. Export Playlists.
    5. Restart Session.
    6. Clear cache.
    7. Run all.
    8. Complete reset
    9. Exit
    """
    print(message)


############
### MAIN ###
############

def main():
    # setup()

    while True:
        setup()
        display_menu()
        choice = input("Choice: ")
        choice = int(choice) if choice.isnumeric() else 0
        run_decision(choice)
    
if __name__ == "__main__":
    main()