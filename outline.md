# FINAL PROJECT

## 1. Project Overview 

Project Title: Book Playlist Generator 

Team: Hannah Sweazey and Ella Roach

Duration: 4 weeks

**Goal:** Automatically generate a music playlist matched to a book’s genre and remaining reading time using data from the Spotify API and a book data source such as Goodreads or the Library of Congress API.

## 2. Functional Summary 

**Given:** A book title (and optionally a page number the user is currently on)

**Produce:** A playlist of songs whose total duration approximates the estimated time remaining to finish the book. Songs matched by genre, mood, or theme to the book.

## 3. User Inputs 

| Input           | Type            | Description                                                                               |
| --------------- | --------------- | ----------------------------------------------------------------------------------------- |
| `book_title`    | `str`           | Title of the book the user is reading                                                     |
| `book_author`    | `str`          | Author of the book the user is reading                                                     |
| `total_page_number`  | `int`, optional | Total number of pages in book; default is 300                                                       |


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

## 6. Error Handling Pipeline 

```python

USER STARTS HERE: generate_playlist.py 
│
└──> DO CLIENT_ID AND CLIENT_SECRET EXIST AND CAN THEY BE IMPORTED #?
     │
     ├──> IF NO: # playlist generated using generate_playlist_csv.py and backup CSVs 
     │
     └──> IF YES: DOES gemini_key.json/api_key EXIST AND DOES IT WORK #?
          │
          ├──> IF NO: # playlist input generated using dummy_gemini.json and Spotify API 
          │
          └──> IF YES: # playlist generated using generate_playlist.py as normal 

```


## 7. Implementation Plan 

| Week                                 | Focus                   | Tasks                                                                                                                                                                                                  | Owner                                                        |
| ------------------------------------ | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------ |
| **Week 1: Data Acquisition** | Setup & ingestion       |<br>- Implement `spotify_api.py`<br>- Implement `books_api.py` (Goodreads or LoC) | Dev A: Spotify<br>Dev B: Books  
| **Week 2: Setup** | Setup & ingestion       | - Configure repo and UV environment<br>- Create `config.py` and `KEYS.py`<br>- Validate data schemas<br>- Draft `playlist_generator.py` and helper functions to select songs  | Dev A: UV and main function <br>Dev B: Config and helpers                                |
| **Week 3: Core Logic & Mapping**     | Processing pipeline     | - Finetune `playlist_generator.py` (keyword/genre based)<br>- Validate success criteria<br>- Implement dummy APIs for Spotify and Gemini access by users                           | Dev A: Finetuning main function <br>Dev B: Dummy APIs and export logic |
| **Week 4: Integration & Validation** | Orchestration & testing | - Build `main.py` CLI<br>- Add user interface<br>- Document in README + Quickstart                         | Both (pair review)                                           |



## 8. Optional Extensions 
- aesthetically pleasing user interface with extra time
- option to export to youtube playlist if no spotify account 