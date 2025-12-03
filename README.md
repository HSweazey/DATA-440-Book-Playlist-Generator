# 📚🎧 Project Overview 🎧📚

The Book Playlist Generator automatically creates a music playlist that matches the genre and remaining reading time of a book.
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

**Installing UV**

This project is managed using UV, the link to which you can find [here](https://docs.astral.sh/uv/guides/install-python/).

Once you've properly installed UV, download the project and set it to your machine's directory. Then, run these commands to download dependencies and start the program.

```bash
uv sync
uv run main.py
```

If you need any troubleshooting assitance, refer to [UV's documentation](https://docs.astral.sh/uv/guides/install-python/).



### 3. Insert Your API Keys 
**Spotify API Keys**

Open: 
```python
src/processing/keys/spotify_client_info.py
```
Replace Placeholders: 
```python
CLIENT_ID = "<your-spotify-client-id>"
CLIENT_SECRET = "<your-spotify-client-secret>"
```

**Gemini API Key**

Open: 
```python
src/processing/keys/gemini_key.json
```
Replace Placeholder: 
```python
{
  "api_key": "YOUR_REAL_KEY_HERE"
}

```

**Note:** For the Spotfiy and Gemini keys, you must take care to make ONLY the edits specified. Any changes to the format of these files will create errors preventing playlist generation. 


### 4. Run the Program 
```python
uv run main.py
```

**Using a virtual environment, the program will redirect you to an app interface where...**

**You will be prompted for:**
- Book title
- Author
- (Optional) page count

**The pipeline will automatically decide whether to use:**
- Real Spotify + real Gemini
- Real Spotify + dummy Gemini
- Backup CSVs based on genre

---

# 📀 How does it work? 

#### 1. User Inputs
- Book title
- Author
- Optional total page count 

#### 2. Gemini generates thematic keywords based on the book.

#### 3. If Spotify API keys are available:
- The system fetches real track data matching those themes.

#### 4. If not:
- It automatically falls back to genre-based CSV backups containing pre-collected Spotify songs. Prompts user for genre of book.

#### 5. Playlist generation logic:
- Maps book → genre
- Estimates reading time
- Assembles tracks whose total duration is within 10% of the target runtime

#### 6. Output:
- A genre-aligned playlist listed on UI.


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

### OPTIONAL Dummy Customization

When the Gemini key is missing or disabled, but all other keys exist, this program uses a dummy response to protect playlist creation and prevent crashes. 

If you want this dummy response to match a specific theme or mood, you can change the keywords listed in the dummy response file. HOWEVER, you must take care to ONLY change the keywords and make no other changes to the formatting of this file. The number of keywords must always equal five and be written in all lowercase with no additional characters. Any changes to the format of this file will create errors preventing playlist generation in the absence of a valid Gemini key. 


Open: 
```python
src/processing/keys/dummy_gemini.json
```
Current dummy response: 
```python
{
  "response": "{'mood_keywords': ['orchestral', 'ethereal', 'cinematic', 'lofi', 'symphony']}"
}
```

Example format for edited dummy response: 
```python
{
  "response": "{'mood_keywords': ['word1', 'word2', 'word3', 'word4', 'word5']}"
}
```

---