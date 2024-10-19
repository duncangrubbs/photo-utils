import datetime

import pytest
from photo_utils.lib import Utils


class TestUtils:
    base_dir = "./photo_utils/test/files"

    def test_get_clean_file_list(self):
        files = Utils(base_dir=self.base_dir, is_dry_run=True).get_clean_file_list()

        assert sorted(
            [
                "./photo_utils/test/files/heic_with_exif.heic",
                "./photo_utils/test/files/heic_without_exif.heic",
                "./photo_utils/test/files/jpeg_with_exif.jpeg",
                "./photo_utils/test/files/jpeg_without_exif.jpeg",
                "./photo_utils/test/files/nef_without_exif.nef",
                "./photo_utils/test/files/png_with_exif.png",
                "./photo_utils/test/files/png_without_exif.png",
                "./photo_utils/test/files/png.jpeg",
                "./photo_utils/test/files/dup1.png",
                "./photo_utils/test/files/dup2.png",
            ]
        ) == sorted(files)

    @pytest.mark.parametrize(
        "file_path, expected_ext",
        [
            ("./photo_utils/test/files/png.jpeg", "png"),
            ("./photo_utils/test/files/png_with_exif.png", "png"),
            ("./photo_utils/test/files/png_without_exif.png", "png"),
            ("./photo_utils/test/files/jpeg_with_exif.jpeg", "jpg"),
        ],
    )
    def test_get_file_type(self, file_path, expected_ext):
        assert Utils(base_dir=self.base_dir).get_file_type(file_path) == expected_ext

    def test_strip_extension(self):
        assert (
            Utils(base_dir=self.base_dir).strip_extension("./foo/abc/bar.job")
            == "./foo/abc/bar"
        )

    def test_get_extension(self):
        assert Utils(base_dir=self.base_dir).get_extension("./foo/abc/bar.job") == "job"

    @pytest.mark.parametrize(
        "file_path, expected_date",
        [
            (
                "./photo_utils/test/files/jpeg_with_exif.jpeg",
                datetime.datetime(2024, 7, 27, 18, 7, 51),
            ),
            (
                "./photo_utils/test/files/png_with_exif.png",
                datetime.datetime(2024, 7, 27, 18, 7, 51),
            ),
            (
                "./photo_utils/test/files/heic_with_exif.heic",
                datetime.datetime(2024, 7, 27, 18, 7, 51),
            ),
            (
                "./photo_utils/test/files/jpeg_without_exif.jpeg",
                None,
            ),
            (
                "./photo_utils/test/files/png_without_exif.png",
                None,
            ),
            (
                "./photo_utils/test/files/nef_without_exif.nef",
                None,
            ),
        ],
    )
    def test_get_file_created_date(self, file_path, expected_date):
        assert (
            Utils(base_dir=self.base_dir).get_file_created_date(file_path)
            == expected_date
        )

    def test_find_duplicates(self):
        assert Utils(base_dir=self.base_dir, is_dry_run=True).find_duplicates() == {
            5310: [
                "dup1.png",
                "dup2.png",
            ],
            534283: [
                "png.jpeg",
                "png_without_exif.png",
            ],
        }
