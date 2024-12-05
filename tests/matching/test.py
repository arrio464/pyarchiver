import filecmp
import os
import shutil
import sys

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from compressor import PaZipCompressor
from extractor import PaZipExtractor


def test_matching():
    base_dir = os.path.dirname(__file__)
    test_input = os.path.join(base_dir, "test_input")
    expected_output = os.path.join(base_dir, "expected_output")
    temporary_dir = os.path.join(base_dir, "temp")

    if not os.path.exists(temporary_dir):
        os.makedirs(temporary_dir)

    try:
        compressor = PaZipCompressor(test_input, temporary_dir)
        archive_path = compressor.compress_folder()
        assert archive_path is not None, "Failed to compress folder"

        extractor = PaZipExtractor(archive_path, temporary_dir)
        extract_path = extractor.extract_archive()
        assert extract_path is not None, "Failed to extract archive"

        dir_comparison = filecmp.dircmp(extract_path, expected_output)
        assert (
            dir_comparison.common_files
            and dir_comparison.diff_files == []
            and dir_comparison.left_only == []
            and dir_comparison.right_only == []
        ), "Mismatch between the expected and extracted folders."

        # Cleanup temporary files
        if os.path.isdir(temporary_dir):
            shutil.rmtree(temporary_dir)

        print("Parrent matching tests passed!")
        return True
    except Exception as e:
        print(f"Error on parent matching test: {e}")
        return False


if __name__ == "__main__":
    assert test_matching(), "Parent matching tests failed!"
