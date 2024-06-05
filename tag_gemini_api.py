#!/usr/bin/env python3

import fileinput
import os
import re
import sys
import typing

import google.generativeai as genai
import sqlite3
from PIL import Image
import pydantic

def init_model() -> genai.GenerativeModel:
  genai.configure(api_key=os.environ["API_KEY"])
  return genai.GenerativeModel('gemini-1.5-flash')

def init_db() -> sqlite3.Connection:
  db_path = '/Users/blech/Documents/webservices/ffffound-mirror/db/ffffound-blech.db'
  conn = sqlite3.connect(db_path)
  return conn

def get_display_name_from_filename(path: str) -> str:
  return path.split('/')[-1]

def get_id_from_filepath(path: str) -> str:
  display_name = get_display_name_from_filename(path)
  return display_name.split('.')[0]

def fetch_tags_for_image(path: str, model: genai.GenerativeModel) -> list:
  try:
    image = Image.open(path)
  except IOError:
    return False

  display_name = get_display_name_from_filename(path)
  sample_file = genai.upload_file(path=path, display_name=display_name)
  prompt = 'Generate ten single or two word tags for this image. Output them as comma separated, without any additional text.'
  
  response = model.generate_content([sample_file, prompt])
  response_text = response.text.strip().strip('.')
  try:
    tags = response_text.split(', ')
  except ValueError as e:
    print (f"Got exception {e} fetching response text")
    print (response.result)
    return False
  return tags

def check_tags_in_db(path: str, conn: sqlite3.Connection) -> bool:
  ffffound_id = get_id_from_filepath(path)
  sql = '''
    SELECT COUNT(1) FROM tags WHERE id = ?
  '''

  cur = conn.cursor()
  res = cur.execute(sql, (ffffound_id,)) # Python gotcha: force tuple
  tag_count = res.fetchone()[0]
  return tag_count >= 10

def write_tags_to_db(path: str, tags: list, conn: sqlite3.Connection):
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
      print (f"Tag {tag} already exists for post {ffffound_id}; skipping")
  conn.commit()

if __name__ == "__main__":
  model = init_model()
  conn = init_db()
  
  for filename in sys.argv[1:]:
    # avoid analysing existing images
    if check_tags_in_db(filename, conn):
      print (f"Tags exist for {filename}")
      continue

    tags = fetch_tags_for_image(filename, model)
    if not tags:
      print (F"No tags found (not an image?) for '{filename}'")
    if tags:
      write_tags_to_db(filename, tags, conn)
      print (f"Written {len(tags)} tags for {filename}")

