# Gemini Image Tagger

A script to use Gemini to generate image tags for a directory full of
images, and then apply those into a pre-existing database.

## Installation

```
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
```

You will also need a Google Gemini API key, which should be in the
environment variable API_KEY:

```
    export API_KEY=A....
```

## Usage

```
   ./tag_gemini_api.py path/to/images/*.jpg
```

This assumes a database. I should probably make a version that outputs JSON instead,
as that may be more useful as an example.

Note that, since Gemini can only handle some file types (notably, not
.gif), limiting the files passed through the command line is sensible.
