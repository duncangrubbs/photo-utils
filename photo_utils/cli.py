from typing import Annotated
import typer
from photo_utils.lib import Utils

app = typer.Typer()

path_type = Annotated[
    str,
    typer.Option(
        help="Path to base media directory. Note that there should only be media files in this directory, no subfolders, etc."
    ),
]
dry_run_type = Annotated[
    bool, typer.Option(help="Run in dry-run mode? If True, no files will be modified.")
]


@app.command(
    help="Corrects file extensions based on the actual file type from the header data."
)
def correct_file_types(
    path: path_type,
    dry_run: dry_run_type = False,
):
    Utils(base_dir=path, is_dry_run=dry_run).correct_file_types()


@app.command(
    help="Renames files to a normalized format that contains the date along with an optional unique string to avoid duplicate file names."
)
def normalize_file_names(
    path: path_type,
    dry_run: dry_run_type = False,
    prevent_duplicates: Annotated[
        bool,
        typer.Option(help="Append random numbers to file names to prevent duplicates?"),
    ] = True,
):
    Utils(base_dir=path, is_dry_run=dry_run).convert_names_to_dates(
        prevent_duplicates=prevent_duplicates
    )


@app.command(help="Updates the file creation date based on the EXIF data.")
def correct_file_dates(
    path: path_type,
    dry_run: dry_run_type = False,
):
    Utils(base_dir=path, is_dry_run=dry_run).update_dates_from_metadata()


@app.command(
    help="Prints out files with duplicate names, exluding the random number. This is really only useful if it's ran after normalize_file_names."
)
def find_duplicates(
    path: path_type,
    dry_run: dry_run_type = False,
):
    Utils(base_dir=path, is_dry_run=dry_run).find_duplicates()


if __name__ == "__main__":
    app()
