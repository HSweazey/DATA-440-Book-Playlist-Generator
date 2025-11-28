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

# 🚀🔑 Quickstart Guide 🔑🚀

### 1. Clone the Repository 
```python
git clone <repo_url>
cd FINAL
```

### 2. Install Dependencies 
- We use uv to manage the python environment


### 3. Insert Your API Keys 
**Spotify API Keys**

Open: 
```python
src/clients/keys/spotify_client_info.py
```
Replace Placeholders: 
```python
CLIENT_ID = "<your-spotify-client-id>"
CLIENT_SECRET = "<your-spotify-client-secret>"
```

**Gemini API Key**

Open: 
```python
src/clients/keys/gemini_key.json
```
Replace Placeholder: 
```python
{
  "api_key": "YOUR_REAL_KEY_HERE"
}

```

### 4. Run the Program 
```python
uv run src/main.py
```

**You will be prompted for:**
- Book title
- Author
- Optional page count

**The pipeline will automatically decide whether to use:**
- Real Spotify + real Gemini
- Real Spotify + dummy Gemini
- Backup CSVs + dummy Gemini

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
- It automatically falls back to genre-based CSV backups containing pre-collected Spotify songs.

#### 5. Playlist generation logic:
- Maps book → genre
- Estimates reading time
- Assembles tracks whose total duration is within ±10% of the target

#### 6. Output:
- A genre-aligned playlist printed to console and optionally saved to /playlist storage/.


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
├── playlist storage/
│   └── # all playlists generated during testing 
│
├── src/
│   ├── clients/
│   │   ├── keys/
│   │   │   ├── dummy_gemini.json
│   │   │   ├── gemini_key.json
│   │   │   └── spotify_client_info.py
│   │   │   
│   │   ├── gemini_client_base.py
│   │   ├── gemini_client_dummy.py
│   │   ├── gemini_client_real.py
│   │   └── gemini_loader.py
│   │
│   ├── data_ingestion/
│   │   ├── dummy_csv_generation.py
│   │   ├── dummy_csv_prompting.py
│   │   └── spotify_extract_v2.py
│   │
│   ├── processing/
│   │   ├── csv_backup_generation_app.py
│   │   ├── csv_backup_generation.py
│   │   ├── generate_playlist_csv_app.py
│   │   ├── generate_playlist_csv.py
│   │   ├── generate_playlist_input_app.py
│   │   ├── generate_playlist_input.py
│   │   └──holder.py
│   │
│   ├── recycling_bin/
│   │   └── # old functions kept for reference and documentation (disregard) 
│   │
│   ├── utils/
│   │   ├── io_utils.py
│   │   └── config.py
│   │
│   └── main.py
│
├── app.py
├── test_main.py
│
├── outline.md
├── README.md
│
├── pyproject.toml
└── uv.lock

```

## ⬇️ Error Handling Pipeline 

```python

USER RUNS: main.py
│
└──→ Check if Spotify CLIENT_ID and CLIENT_SECRET exist  
       │
       ├── NO → Use backup CSV playlists (generate_playlist_csv.py)
       │
       └── YES → Check Gemini API key  
                │
                ├── NO → Use dummy Gemini + real Spotify
                │
                └── YES → Full pipeline (Gemini + Spotify)
```