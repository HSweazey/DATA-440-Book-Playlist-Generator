# FINAL PROJECT

## 1. Project Overview 

Project Title: Book Playlist Generator 

Team: Hannah Sweazey and Ella Roach

Duration: 4 weeks

**Goal:** Automatically generate a music playlist matched to a book’s genre and remaining reading time using data from the Spotify API and a book data source such as Goodreads or the Library of Congress API.

## 2. Functional Summary 

**Given:** A book title (and optionally a page number the user is currently on)

**Produce:** A playlist of songs whose total duration approximates the estimated time remaining to finish the book. Songs matched by genre, mood, or theme to the book.

## 3. Inputs and Outputs 

| Input           | Type            | Description                                                                               |
| --------------- | --------------- | ----------------------------------------------------------------------------------------- |
| `book_title`    | `str`           | Title of the book the user is reading                                                     |
| `book_author`    | `str`, optional          | Author of the book the user is reading                                                     |
| `page_number`  | `int`, optional | Current page number; default is 0                                                         |
| `book_data.csv` | `CSV`           | Cached or pre-downloaded dataset of books (title, author, genre, page count, description)(fallback in case user does not have Gemini API key working) |
| `spotify.csv`   | `CSV`           | Cached dataset of Spotify track metadata (title, artist, genre, duration, popularity)(fallback in case user does not have Spotify or Spotify API dummy key not working)     |


## 4. Success Criteria (Validation) (?)

| Metric                                                               | Target |
| -------------------------------------------------------------------- | ------ |
| Playlist duration within ±10% of reading time estimate               | ✅      |
| Correct genre match ≥ 80% (verified by keyword similarity) | ✅      |
| Script runtime under 60 seconds (for local data)                     | ✅      |
| Fully reproducible pipeline with `uv run main.py`                    | ✅      |

## 5. System Architecture 

```python

FINAL/
│
├── data/                         # Data and cache directory
│   ├── split_books/              # Fallback option 
│   │   ├── goodreads0.csv 
│   │   ├── ...
│   │   └── goodreads9.csv
│   │ 
│   └── playlists/                # Fallback option 
│       ├── x
│       ├── ...
│       └── x  
├── src/
│   ├── data_ingestion/
│   │   └── spotify_extract.py          # Pulls Spotify data via API
│   │
│   ├── processing/
│   │   ├── generate_playlist_mood.py      
│   │   ├── generate_playlist_input.py  # Generates keywords from Gemini as input for the playlist generator     
│   │   └── playlist_generator.py       # Builds playlist matching duration & genre
│   │
│   ├── visualization/
│   │   └── playlist_plot.py      # Optional visualization tools (WIP)
│   │
│   ├── utils/
│   │   ├── KEYS.py               # Key storage 
│   │   ├── io_utils.py           # CSV/JSON read-write helpers
│   │   └── config.py             # API keys, constants, directories
│   │
│   └── main.py                   # CLI entry point
│
├── tests/
│   ├── test_genre_mapping.py
│   ├── test_reading_time.py
│   └── test_playlist_generator.py
│
├── .gitignore
├── README.md
├── pyproject.toml
└── uv.lock
```



## 6. Implementation Plan 

| Week                                 | Focus                   | Tasks                                                                                                                                                                                                  | Owner                                                        |
| ------------------------------------ | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------ |
| **Week 1: Data Acquisition** | Setup & ingestion       |<br>- Implement `spotify_api.py` (mock data if needed)<br>- Implement `books_api.py` (Goodreads or LoC) | Dev A: Spotify<br>Dev B: Books  
| **Week 2: Setup** | Setup & ingestion       | - Configure repo and UV environment<br>- Create `config.py` and `KEYS.py`<br>- Validate data schemas<br>- Draft `playlist_generator.py` and helper functions to select songs  | Dev A: UV and main function <br>Dev B: Config and helpers                                |
| **Week 3: Core Logic & Mapping**     | Processing pipeline     | - Finetune `playlist_generator.py` (keyword/genre based)<br>- Validate success criteria<br>- Implement dummy APIs for Spotify and Gemini access by users                           | Dev A: Finetuning main function <br>Dev B: Dummy APIs and export logic |
| **Week 4: Integration & Validation** | Orchestration & testing | - Build `main.py` CLI<br>- Add optional user interface<br>- Document in README + Quickstart                         | Both (pair review)                                           |



## 7. Optional Extensions 
- aesthetically pleasing user interface with extra time
- explore export direct to spotify playlist if possible 
- option to export to youtube playlist if no spotify account 