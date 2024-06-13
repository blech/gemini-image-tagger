#!/usr/bin/env python3

import os
import re
import sqlite3
import sys

import google.generativeai as genai
from PIL import Image

DB_PATH = '/Users/blech/Documents/webservices/ffffound-mirror/db/ffffound-blech.db'


def init_model() -> genai.GenerativeModel:
    genai.configure(api_key=os.environ["API_KEY"])
    return genai.GenerativeModel('gemini-1.5-flash')


def init_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    return conn


def get_display_name_from_filename(path: str) -> str:
    return path.split('/')[-1]


def get_id_from_filepath(path: str) -> str:
    display_name = get_display_name_from_filename(path)
    return display_name.split('.')[0]


def check_image(path: str) -> bool:
    try:
        Image.open(path)
    except IOError as e:
        print(f"IOError {e} for {path}")
        return False
    return True


def fetch_tags_for_image(path: str, model: genai.GenerativeModel) -> list[str]:
    display_name = get_display_name_from_filename(path)
    sample_file = genai.upload_file(path=path, display_name=display_name)
    prompt = """
        Generate ten unique, one to three word long, tags for this
        image. Output them as comma separated, without any additional
        text.
    """

    response = model.generate_content([sample_file, prompt])
    try:
        response_text = response.text.strip().strip('.')
    except ValueError as e:
        if response.candidates:
            parse_safety_reason(response.candidates)
        else:
            print(f"Got exception {e} fetching response text")
            print(response)
        return False
    tags = response_text.split(', ')
    return tags


def parse_safety_reason(candidates) -> None:
    for candidate in candidates:
        if candidate.finish_reason.name == 'SAFETY':
            for rating in candidate.safety_ratings:
                if rating.probability > 1:
                    print(f"{rating.category.name} has level {rating.probability.name}")
        else:
            print(f"Unhandled finish_reason {candidate.finish_reason.name}")


def check_tags_in_db(path: str, conn: sqlite3.Connection) -> bool:
    ffffound_id = get_id_from_filepath(path)
    sql = '''
        SELECT COUNT(1) FROM tags WHERE id = ?
    '''

    cur = conn.cursor()
    res = cur.execute(sql, (ffffound_id,))  # Python gotcha: force tuple
    tag_count = res.fetchone()[0]
    return tag_count >= 8  # allows for missing tags because of duplicate suggestions


def write_tags_to_db(path: str, tags: list, conn: sqlite3.Connection) -> None:
    ffffound_id = get_id_from_filepath(path)
    for tag in tags:
        tag_lower = tag.lower()
        tag_normalised = re.sub(r'[^a-z0-9]', r'_', tag_lower).strip('_')
        sql = '''
            INSERT INTO tags (id, tag, tag_lower, tag_normalised) VALUES (?, ?, ?, ?);
        '''
        cur = conn.cursor()
        try:
            cur.execute(sql, (ffffound_id, tag, tag_lower, tag_normalised))
        except sqlite3.IntegrityError:
            print(f"Tag {tag} already exists for post {ffffound_id}; skipping")
    conn.commit()


if __name__ == "__main__":
    model = init_model()
    conn = init_db()

    for filename in sys.argv[1:]:
        # avoid analysing existing images
        if check_tags_in_db(filename, conn):
            print(f"Tags exist for {filename}")
            continue

        IS_IMAGE = check_image(filename)
        if not IS_IMAGE:
            print(f"Pillow could not open {filename}")
            continue

        tags = fetch_tags_for_image(filename, model)
        if not tags:
            print(F"No tags found for '{filename}'")
            continue

        # ensure tags are unique
        tags = list(set(tags))
        write_tags_to_db(filename, tags, conn)
        print(f"Written {len(tags)} tags for {filename}")
