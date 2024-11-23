import datetime
from unittest.mock import call, patch

import pytest
from lib.main import Utils


class TestUtils:
    base_dir = "./test/files"

    def test_get_clean_file_list(self):
        files = Utils(base_dir=self.base_dir, is_dry_run=True).get_clean_file_list()

        assert sorted(
            [
                "./test/files/heic_with_exif.heic",
                "./test/files/heic_without_exif.heic",
                "./test/files/jpeg_with_exif.jpeg",
                "./test/files/jpeg_without_exif.jpeg",
                "./test/files/nef_without_exif.nef",
                "./test/files/png_with_exif.png",
                "./test/files/png_without_exif.png",
                "./test/files/png.jpeg",
                "./test/files/dup1.png",
                "./test/files/dup2.png",
            ]
        ) == sorted(files)

    def test_get_extension(self):
        assert Utils(base_dir=self.base_dir).get_extension("./foo/abc/bar.job") == "job"

    def test_strip_extension(self):
        assert (
            Utils(base_dir=self.base_dir).strip_extension("./foo/abc/bar.job")
            == "./foo/abc/bar"
        )

    @pytest.mark.parametrize(
        "file_path, expected_ext",
        [
            ("./test/files/png.jpeg", "png"),
            ("./test/files/png_with_exif.png", "png"),
            ("./test/files/png_without_exif.png", "png"),
            ("./test/files/jpeg_with_exif.jpeg", "jpg"),
        ],
    )
    def test_get_file_type(self, file_path, expected_ext):
        assert Utils(base_dir=self.base_dir).get_file_type(file_path) == expected_ext

    @patch("lib.main.os.rename")
    def test_rename(self, mock_rename):
        Utils(base_dir=self.base_dir, is_dry_run=False)._rename(
            "./test/files/png.jpeg", "./test/files/png.jpg"
        )
        mock_rename.assert_called_with("./test/files/png.jpeg", "./test/files/png.jpg")

    @pytest.mark.parametrize(
        "file_path, expected_date",
        [
            (
                "./test/files/jpeg_with_exif.jpeg",
                datetime.datetime(2024, 7, 27, 18, 7, 51),
            ),
            (
                "./test/files/png_with_exif.png",
                datetime.datetime(2024, 7, 27, 18, 7, 51),
            ),
            (
                "./test/files/heic_with_exif.heic",
                datetime.datetime(2024, 7, 27, 18, 7, 51),
            ),
            (
                "./test/files/jpeg_without_exif.jpeg",
                None,
            ),
            (
                "./test/files/png_without_exif.png",
                None,
            ),
            (
                "./test/files/nef_without_exif.nef",
                None,
            ),
        ],
    )
    def test_get_file_created_date(self, file_path, expected_date):
        assert (
            Utils(base_dir=self.base_dir).get_file_created_date(file_path)
            == expected_date
        )

    @patch("lib.main.os.rename")
    def test_correct_file_types(self, mock_rename):
        Utils(base_dir=self.base_dir, is_dry_run=False).correct_file_types()
        assert mock_rename.call_count == 3

        assert mock_rename.call_args_list == [
            call("./test/files/png.jpeg", "./test/files/./test/files/png.png"),
            call(
                "./test/files/jpeg_without_exif.jpeg",
                "./test/files/./test/files/jpeg_without_exif.jpg",
            ),
            call(
                "./test/files/jpeg_with_exif.jpeg",
                "./test/files/./test/files/jpeg_with_exif.jpg",
            ),
        ]

    def test_find_duplicates(self):
        assert Utils(base_dir=self.base_dir, is_dry_run=True).find_duplicates() == {
            5310: sorted(
                [
                    "dup1.png",
                    "dup2.png",
                ]
            ),
            534283: sorted(
                [
                    "png.jpeg",
                    "png_without_exif.png",
                ]
            ),
        }
