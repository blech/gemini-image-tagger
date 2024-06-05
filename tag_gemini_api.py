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

def fetch_tags_for_image(path: str, model: genai.GenerativeModel) -> list:
  try:
    image = Image.open(path)
  except IOError:
    return False

  sample_file = genai.upload_file(path=path, display_name = path.split('/')[-1])
  prompt = 'Generate ten single or two word tags for this image. Output them as comma separated, without any additional text.'
  
  response = model.generate_content([sample_file, prompt])
  response_text = response.text.strip().strip('.')
  tags = response_text.split(', ')
  return tags

def write_tags_to_db(path: str, tags: list, conn: sqlite3.Connection):
  cursor = conn.cursor()
  ffffound_id = path.split('/')[-1].split('.')[0]
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
    tags = fetch_tags_for_image(filename, model)
    if not tags:
      print (F"No tags found (not an image?) for '{filename}'")
    if tags:
      write_tags_to_db(filename, tags, conn)

