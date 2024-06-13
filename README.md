# Gemini Image Tagger

A script to use Gemini to generate image tags for a directory full of
images, and then apply those into a pre-existing database.

## Installation

```
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
```

## Usage

```
   ./tag_gemini_api.py path/to/images/
```

This assumes a database. I'll probably make a version that outputs JSON instead,
as that may be more useful as an example.