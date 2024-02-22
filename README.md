# PlaylistGPT
PlaylistGPT is a Python script designed to enhance your Spotify playlist experience by categorizing songs based on their lyrics. Built using the Syrics API for fetching song lyrics and the GPT-4 framework for natural language processing.

## Requirements
To use PlaylistGPT, you need the following:
- Python 3.x installed on your system.
- Access to Spotify Developer Console to generate an API key.
- Necessary Python packages installed. `pip install -r requirements.txt`.

## Setup
1. Generate a Spotify API key and save it in a file named `SP_DC_KEY.txt` in the root directory of the project.
2. Paste the Spotify track URLs into a file named `links.txt`. Inside Spotify Desktop, you can Ctrl+A, Ctrl+C entire playlists.
3. Ensure that the `links.txt` file is in the root directory of the project.

## Usage
1. Run the script.
   ```
   python playlist_gpt.py
   ```
2. You will be presented with a menu with the following options:
   - **Get sp_dc token first:** Use this option to retrieve the sp_dc token required for accessing Spotify API.
   - **Get lyrics:** This option retrieves lyrics for the tracks listed in `links.txt`.
   - **Categorize lyrics:** Categorizes the downloaded lyrics into predefined categories.
   - **Export Playlists:** Export categorized playlists into separate text files.
   - **Restart Session:** Clears the session and resets the process.
   - **Clear cache:** Cleans the cache directory.
   - **Run all:** Automatically performs all the steps from fetch lyrics to export playlists.
3. Follow instructions to proceed.
4. Review your categorized playlists for accuracy as automated categorization may not always be perfect.

### Disclaimer
*This script uses external APIs and services, and its functionality may be subject to changes in these services. Use it responsibly and in compliance with the terms of service of the respective platforms. Use at your own risk. Do not use spotify data to train AI models. This is just NLP i think. :o*
