# 📸 Photo Utils

> A collection of Python utilities to organize photos and other media

![Tests](https://github.com/duncangrubbs/photo-utils/actions/workflows/test.yaml/badge.svg)


## Why?

These days many of us have large, messy media libraries split between multiple drives and cloud storage. Organizing these can be very difficult, but Python can help!

### Key Features

- De-duplication of media files
- Correct the dates on files downloaded in bulk from Google Photos
- Consistently name files for better organization and sorting

## Usage

### Project Installation
- [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
- Run `uv sync`
- Run `source .venv/bin/activate`

The main entrypoint for usage is the CLI which you can access by running

```zsh
python cli.py --help
```

### Suggested Command Order
1. **Backup all your media first**
1. Collect your messy media into one folder (_Note that you should avoid putting too many files in one folder, so consider chunking the content you plan on processing_)
1. Run commands with `--dry-run` set first just to ensure nothing unwanted will happen
1. Run `python cli.py find-duplicates --path PATH_TO_FOLDER`. Check out the flagged files and delete any you want to!
1. Then run `python cli.py correct-file-types --path PATH_TO_FOLDER`
1. Then run `python cli.py correct-file-dates --path PATH_TO_FOLDER`
1. Then run `python cli.py normalize-file-names --path PATH_TO_FOLDER`


## Testing

```zsh
pytest
```

or

```zsh
coverage run -m pytest
```

## File Support
- jpg
- nef
- jpeg
- png
- heic
- mov
- mp4
- tif
