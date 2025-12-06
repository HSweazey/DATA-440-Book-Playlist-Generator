# 📚🎧 Project Overview 🎧📚

The **Book Playlist Generator** automatically creates a music playlist that matches the genre and remaining reading time of a book.
The system combines:
- Large Language Model (LLM) keyword generation via Google’s Gemini API
- Spotify API track retrieval (with a CSV-based fallback system)
- Custom logic for estimating reading time and selecting songs whose total duration approximates that time

This tool is designed so that users can input a book, and the system will output a curated, thematically coherent playlist.

## 🎯 Project Goal 

**Given:**
A book title, author, and (optionally) the total number of pages

**Produce:**
A playlist whose total runtime closely matches the estimated time remaining to finish the book.
Songs are selected based on genre, mood, or keywords derived from Gemini.

---

# 🚀🔑 Quick Start Guide 🔑🚀

### 1. Clone the Repository 
```python
git clone <repo_url>
cd FINAL
```

### 2. Install Dependencies 

#### Installing UV

This project is managed using UV, the link to which you can find [here](https://docs.astral.sh/uv/guides/install-python/).

Once you've properly installed UV, download the project and set it to your machine's directory. Then, run these commands to download dependencies and start the program.

```bash
uv sync
uv run main.py
```

If you need any troubleshooting assitance, refer to [UV's documentation](https://docs.astral.sh/uv/guides/install-python/).



### 3. Insert Your API Keys 
#### Spotify API Keys

**Open:** 
```python
src/processing/keys/spotify_client_info.py
```
**Replace Placeholders:**
```python
CLIENT_ID = "<your-spotify-client-id>"
CLIENT_SECRET = "<your-spotify-client-secret>"
```

For step-by-step instructions on creating your Spotify Client ID and Client Secret, see [Spotify's documentation](https://developer.spotify.com/documentation/web-api/concepts/apps). Before linking a Client ID and Client Secret to your account, you must have a Spotify account. You can create an account for free through [Spotify's website](https://www.spotify.com/us/free/?gclsrc=aw.ds&gad_source=1&gad_campaignid=1072719584&gbraid=0AAAAADfzDs2V6KHTEtEfksLNZSK4Oil0i&gclid=CjwKCAiA3L_JBhAlEiwAlcWO5xdTF-smDbsv4_mAEQttD4mvQrfaetxOw6RrPsf1vovU1ZOzIZikwxoCwUwQAvD_BwE).


#### Gemini API Key

**Open:**
```python
src/processing/keys/gemini_key.json
```
**Replace Placeholder:**
```python
{
  "api_key": "<your-gemini-key>"
}

```


To create your own Gemini Key, use [Gemini API's website](https://ai.google.dev/gemini-api/docs/api-key?gclsrc=aw.ds&gad_source=1&gad_campaignid=20866959509&gbraid=0AAAAACn9t67_UcOr7ckWtvOXljNtzsfl0&gclid=Cj0KCQiA_8TJBhDNARIsAPX5qxSOPEuIt8FXckHDbAJx6PNWLijF3TKjcge1eVXGRcPrEbd_jYNS45AaAjALEALw_wcB). It provides all necessary links and instructions to create and manage your Gemini API Keys from the Google AI Studio API Keys page.

*For the Spotfiy and Gemini keys, you must take care to make ONLY the edits specified. Any changes to the format of these files will create errors preventing playlist generation.* 


### 4. Run the Program 
```python
uv run main.py
```

**Using a virtual environment, the program will redirect you to an app interface where...**

**You will be prompted for:**
- Book title
- Author
- Page Count (Optional)

**The pipeline will automatically decide whether to use:**
- Real Spotify + Real Gemini
- Real Spotify + Dummy Gemini
- Backup track lists based on genre

---

# 📀 How does it work? 

#### 1. User Inputs
- Book title
- Author
- Page Count (Optional)

#### 2. If Gemini API key is available:
- The system queries Gemini for 5 mood words and (if applicable) a score and composer from a film/TV adaptation

#### 3. If not:
- Calls on dummy API for hard-coded mood words

#### 4. If Spotify API keys are available:
- The system fetches real track data matching those themes.

#### 5. If not:
- It automatically falls back to genre-based CSV backups containing pre-collected Spotify songs. Prompts user for genre of book.

#### 6. Playlist generation logic:
- Estimates reading time
  - Calculated using **average page reading time * page count**
  - Default page count of 100 is used if no page count is entered

- Queries Gemini for keyword dictionary
  - **If key/format issue:** returns dummy mood words if there is a key issue
- Queries Spotify with score and mood words
  - **If key issue:** prompts user to select genre and pulls from corresponding backup file
- Assembles tracks whose total duration is within 5 minutes of the target runtime

#### 7. Output:
- A genre-aligned playlist listed on UI (first six tracks embedding)


---

## ⬇️ System Architecture 

```python
FINAL/
│
├── data/
│   ├── biography_backup.csv
│   ├── classics_backup.csv
│   ├── contemporary_fiction_backup.csv
│   ├── dystopian_backup.csv
│   ├── fantasy_backup.csv
│   ├── graphic_novels_backup.csv
│   ├── historical_fiction_backup.csv
│   ├── horror_backup.csv
│   ├── instrumental_backup.csv
│   ├── literary_fiction_backup.csv
│   ├── mystery_backup.csv
│   ├── romance_backup.csv
│   ├── science_fiction_backup.csv
│   ├── textbook_backup.csv
│   ├── thriller_backup.csv
│   └── young_adult_backup.csv
│
├── src/
│   ├── clients/
│   │   ├── gemini_client_base.py
│   │   ├── gemini_client_dummy.py
│   │   ├── gemini_client_real.py
│   │   └── gemini_loader.py
│   │
│   ├── processing/
│   │   ├── keys/
│   │   │   ├── dummy_gemini.json
│   │   │   ├── gemini_key.json
│   │   │   └── spotify_client_info.py
│   │   │   
│   │   ├── csv_backup_generation_app.py
│   │   ├── generate_playlist_csv_app.py
│   │   └── generate_playlist_input_app.py
│   │
│   └── utils/
│       ├── io_utils.py
│       └── config.py
│
├── app.py
└── main.py

```

## ⬇️ Error Handling Pipeline 

### Key Failure and Formatting Accounts
```python

USER RUNS: main.py
│
└──→ Check if Spotify CLIENT_ID and CLIENT_SECRET exist  
       │
       ├── if NO → Use backup CSV playlists (generate_playlist_csv_app.py)
       │
       └── if YES → Check Gemini API key  
                │
                ├── if NO → Use dummy Gemini + real Spotify
                │       │
                │       └── optional: change dummy keywords in dummy_gemini.json 
                │           (see 'OPTIONAL Dummy Customization' below)
                │
                └── if YES → Full pipeline (Gemini + Spotify)
```

### Gemini and Query Handling

*The following handling considerations are taken provided both keys are inputted and working*

- **Prompt Gemini**

  - Specifies mood words will be for Spotify query, no musical soundtracks allowed
  - Checks if a score from TV adaptation of film exists, includes both title of album and composer in response if applicable
  - Expects python dict as response, built to handle formatting from advanced and normal Gemini models
    - Defaults to genre approach if format does not fall into either format structure
  - "Safety Override" feature when Gemini returns mood words that can generate inapproproate content when used with Spotify

- **Query Spotify**
  - (If applicable) searches for returned score album and returns 6 tracks
  - Uses each individual mood keyword alongside "instrumental" and "ambient instrumental"
    - Divides projected track count evenly between all combinations to return the best (top) tracks from each query
  - Checks for duplicate tracks, removes and replaces any if found
  - Calculates actual playlist length from combined durations of tracks, adds or removes tracks to get within 5 minutes of projected reading time

 ---

## ⬇️ OPTIONAL Dummy Customization

When the Gemini key is missing or disabled, but all other keys exist, this program uses a dummy response to protect playlist creation and prevent crashes. 

If you want this dummy response to match a specific theme or mood, you can change the keywords listed in the dummy response file. HOWEVER, you must take care to ONLY change the keywords and make no other changes to the formatting of this file. The number of keywords must always equal five and be written in all lowercase with no additional characters. Any changes to the format of this file will create errors preventing playlist generation in the absence of a valid Gemini key. 


**Open:**
```python
src/processing/keys/dummy_gemini.json
```
**Current dummy response:** 
```python
{
  "response": "{'mood_keywords': ['orchestral', 'ethereal', 'cinematic', 'lofi', 'symphony']}"
}
```

**Example format for edited dummy response:**
```python
{
  "response": "{'mood_keywords': ['word1', 'word2', 'word3', 'word4', 'word5']}"
}
```

---