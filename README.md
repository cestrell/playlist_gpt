# PlaylistGPT
PlaylistGPT is a Python script designed to enhance your Spotify playlist experience by categorizing songs based on their lyrics. Built using the Syrics API for fetching playlist info and song lyrics and the GPT-4 framework provided by GPT4FREE for natural language processing.

## Requirements
To use PlaylistGPT, you need:
- Python 3.x
- Access to Spotify Developer Console for the `sp_dc` key
- Required Python packages (`g4f`, `syrics`)

## Usage
1. **Setup:**
   - Obtain your Spotify Developer Client (SP_DC) key and save it in `SP_DC_KEY.txt`.
   - Install required packages: `pip install -r requirements.txt`.
   - Configure the GPT-4 Free provider in the script if needed.

2. **Running the Script:** 
```
python3 playlist_gpt.py --verbose
```

3. **Menu Options:**
- **1. Get sp_dc token first:** Retrieve SP_DC token from Spotify Developer Console.
- **2. Get lyrics:** Fetch lyrics for tracks listed in `links.txt`.
- **3. Categorize lyrics:** Analyze and categorize the downloaded lyrics.
- **4. Export Playlists:** Export categorized playlists to separate text files.
- **5. Restart Session:** Clear session and reset process.
- **6. Clear cache:** Clean the cache directory.
- **7. Run all:** Execute steps 2 and 3 consecutively.
- **8. Complete reset:** Reset system including cache and session data.

## Example

#### Input
Consider the following example input with 10 Spotify track links in `links.txt`:
```
- https://open.spotify.com/track/4uY9DiDYULeTvV1FsYFrAW
- https://open.spotify.com/track/1BxYaRKQzdaikFV2xJNpxd
- https://open.spotify.com/track/0KSwFEkVh0KCBR0TwqBVen
- https://open.spotify.com/track/0TeJBV1JebreflQy2yb315
- https://open.spotify.com/track/3wS0JIapaGqM2zqsRi3p86
- https://open.spotify.com/track/5rAnfPGKZGyRBzI5kcAaqB
- https://open.spotify.com/track/5qzepeW1CAsX5JhgNudQuP
- https://open.spotify.com/track/6rdqVFwrsavgoEzV4G3nqU
- https://open.spotify.com/track/7rxzL7rKUVa7epgDFjecGW
- https://open.spotify.com/track/75bTohS26lM1nbgDutXCoc
```

#### Output
After categorization, the playlists are organized as follows:
These can then be pasted into a new spotify playlist

**Playlist "arriba":**
```
- https://open.spotify.com/track/3wS0JIapaGqM2zqsRi3p86
- https://open.spotify.com/track/5rAnfPGKZGyRBzI5kcAaqB
- https://open.spotify.com/track/5qzepeW1CAsX5JhgNudQuP
- https://open.spotify.com/track/6rdqVFwrsavgoEzV4G3nqU
```
**Playlist "tristes":**
```
- https://open.spotify.com/track/0KSwFEkVh0KCBR0TwqBVen
- https://open.spotify.com/track/0TeJBV1JebreflQy2yb315
- https://open.spotify.com/track/7rxzL7rKUVa7epgDFjecGW
- https://open.spotify.com/track/75bTohS26lM1nbgDutXCoc
```
**Playlist "belicos":**
```
- https://open.spotify.com/track/4uY9DiDYULeTvV1FsYFrAW
- https://open.spotify.com/track/1BxYaRKQzdaikFV2xJNpxd
```

### Disclaimer
*This script uses external APIs and services, and its functionality may be subject to changes in these services. Use it responsibly and in compliance with the terms of service of the respective platforms. Use at your own risk. Do not use spotify data to train AI models. This is just NLP i think. :o*