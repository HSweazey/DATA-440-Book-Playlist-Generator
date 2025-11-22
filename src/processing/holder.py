prompt = f"""
    Analyze the book "{book}"{f" by {author}" if author else ""}.

    Your response must be a single Python dictionary with two keys:
    1. 'mood_keywords': A list of exactly three unique, lowercase, descriptive mood and style keywords that capture the story's tone and atmosphere. These keywords will be used to search for instrumental ambient music.
    2. 'score_query': (OPTIONAL) If the book has a well-known movie or TV adaptation, include this key with the official name of the instrumental score or soundtrack album (e.g., 'Dune Soundtrack 2021' or 'The Lord of the Rings: The Two Towers Score'). If NO adaptation exists, omit this key entirely.

    Respond **ONLY as a single-line Python dictionary** without any extra characters or words.
    
    Example (With Score): {{'mood_keywords': ['heroic', 'epic', 'grand'], 'score_query': 'Dune Soundtrack 2021'}}
    """