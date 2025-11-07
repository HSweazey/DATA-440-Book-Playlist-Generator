# FINAL PROJECT

## 1. Project Overview 

Project Title: ?

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
| `current_page`  | `int`, optional | Current page number; default is 0                                                         |
| `book_data.csv` | `CSV`           | Cached or pre-downloaded dataset of books (title, author, genre, page count, description) |
| `spotify.csv`   | `CSV`           | Cached or pre-downloaded dataset of Spotify track metadata (title, artist, genre, duration, popularity)     |


## 4. Success Criteria (Validation) (?)

| Metric                                                               | Target |
| -------------------------------------------------------------------- | ------ |
| Playlist duration within ±10% of reading time estimate               | ✅      |
| Correct genre match ≥ 80% (verified by keyword/embedding similarity) | ✅      |
| Script runtime under 60 seconds (for local data)                     | ✅      |
| Fully reproducible pipeline with `uv run main.py`                    | ✅      |

## 5. System Architecture 

```python

readbeats/
│
├── data/                         # Data and cache directory
│   ├── spotify.csv
│   ├── books.csv
│   └── playlists/
│
├── src/
│   ├── data_ingestion/
│   │   ├── spotify_api.py        # Pulls Spotify data via API
│   │   └── books_csv.py          # Pulls book data (backup)
│   │
│   ├── processing/
│   │   ├── genre_mapping.py      # NLP-based genre/keyword matching
│   │   ├── reading_time.py       # Estimates reading time from page count
│   │   └── playlist_generator.py # Builds playlist matching duration & genre
│   │
│   ├── visualization/
│   │   └── playlist_plot.py      # Optional visualization tools
│   │
│   ├── utils/
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

## 6. Function Specifications 

### spotify_api.py

**Optional Backup:** [Existing Spotify Dataset](https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset)
- 114k rows, 

```python
def fetch_spotify_data(query: str, limit: int = 50) -> pd.DataFrame
```

**Input:** 
- query: keyword or genre to search
- limit: number of tracks to fetch

**Output:**
DataFrame with columns: ['track_name', 'artist', 'genre', 'duration_ms', 'popularity']

### books_api.py

**Optional Backups:** 
- [Existing Hugging Face Dataset](https://huggingface.co/datasets/booksouls/goodreads-book-descriptions?utm_source=chatgpt.com)
- 1.02m rows 
- [Existing Kaggle Dataset](https://www.kaggle.com/datasets/jealousleopard/goodreadsbooks?utm_source=chatgpt.com)
- 10k rows, updated regularly 

```python
def fetch_book_metadata(title: str) -> dict
```

**Input:** 
- title: book title 

**Output:**
Dictionary with keys: {'title', 'author', 'genre', 'page_count', 'description'}

### genre_mapping.py

```python
def map_book_to_music_genre(book_genre: str, description: str) -> List[str]
```

**Input:** 
- book_genre: literary genre label
- description: textual summary of the book

**Output:**
List of relevant music genres (['fantasy soundtrack', 'orchestral', 'ambient'])

### reading_time.py

```python
def estimate_reading_time(page_count: int, current_page: int, wpm: int = 250) -> float
```

**Input:** 
- page_count: total number of pages
- current_page: user’s current page
- wpm: words per minute (default 250)

**Output:**
Estimated reading time in minutes

### playlist_generator.py

```python
def generate_playlist(spotify_df: pd.DataFrame, target_genres: List[str], target_duration_min: float) -> pd.DataFrame
```

**Input:** 
- spotify_df: DataFrame of available tracks
- target_genres: list of matched genres
- target_duration_min: desired total playlist length

**Output:**
DataFrame of selected tracks (playlist.csv)

### playlist_plot.py

```python
def plot_playlist_duration(playlist_df: pd.DataFrame, target_duration: float) -> None
```

**Input:** 
- playlist_df: DataFrame of playlist
- target_duration: target duration in minutes- limit: number of tracks to fetch

**Output:**
Saved PNG visualization in /data/playlists/plots

### main.py

```python
def main():
    """
    Entry point: orchestrates input, data fetching, genre mapping, 
    reading time estimation, playlist generation, and output.
    """
```


## 7. Implementation Plan 

| Week                                 | Focus                   | Tasks                                                                                                                                                                                                  | Owner                                                        |
| ------------------------------------ | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------ |
| **Week 1: Data Acquisition** | Setup & ingestion       |<br>- Implement `spotify_api.py` (mock data if needed)<br>- Implement `books_api.py` (Goodreads or LoC) | Dev A: Spotify<br>Dev B: Books  
| **Week 2: Setup** | Setup & ingestion       | - Configure repo and UV environment<br>- Create `config.py` for keys<br>- Validate data schemas | Dev A: UV <br>Dev B: Config                                |
| **Week 3: Core Logic & Mapping**     | Processing pipeline     | - Implement `genre_mapping.py` (keyword or embedding-based)<br>- Implement `reading_time.py` (using avg reading speed)<br>- Draft `playlist_generator.py` to select songs                              | Dev A: Genre mapping<br>Dev B: Reading time & playlist logic |
| **Week 4: Integration & Validation** | Orchestration & testing | - Build `main.py` CLI<br>- Add visualization<br>- Write tests in `/tests`<br>- Document in README + Quickstart<br>- Validate success criteria (duration accuracy, genre match)                         | Both (pair review)                                           |



## 8. Optional Extensions 
- option to export to youtube playlist if no spotify account 