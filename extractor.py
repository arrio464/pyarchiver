import os
import re
from typing import Optional

import py7zr

from utils import calculate_checksum, setup_logging

logger = setup_logging()


class PaZipExtractor:
    def __init__(self, archive_path: str, extract_to: Optional[str] = None) -> None:
        """
        Initialize the extractor with the path to the .7z archive and an optional directory to extract to.

        :param archive_path: The path to the .7z archive.
        :param extract_to: The directory to extract the archive to (optional).
        """
        assert os.path.isfile(
            archive_path
        ), f"Archive file '{archive_path}' does not exist."
        assert extract_to is None or os.path.isdir(
            extract_to
        ), f"Output directory '{extract_to}' does not exist."
        pattern = re.match(
            r"^([\w_-]+)_(\d{8}\d{6}[+-]\d{4})_([a-fA-F0-9]{8})\.7z$",
            os.path.basename(archive_path),
        )
        assert pattern is not None, f"Invalid archive name: '{archive_path}'"

        self.archive_path = archive_path
        self.extract_to = extract_to or os.getcwd()
        self.extract_to = os.path.join(self.extract_to, *(pattern.groups()))
        assert calculate_checksum(archive_path) == pattern.group(
            3
        ), f"Checksum mismatch for '{archive_path}'"

    def extract_archive(self) -> None | str:
        """
        Extract the contents of the .7z archive to the specified directory.
        """
        # Ensure the output directory exists
        if not os.path.exists(self.extract_to):
            os.makedirs(self.extract_to)

        try:
            logger.info(f"Extracting archive '{self.archive_path}'...")

            with py7zr.SevenZipFile(self.archive_path, mode="r") as archive:
                archive.extractall(path=self.extract_to)

            logger.success(
                f"Archive '{self.archive_path}' successfully extracted to '{self.extract_to}'."
            )
            return self.extract_to
        except Exception as e:
            logger.error(f"Error extracting the archive: {e}", exc_info=True)
            return


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Decompress a .7z archive")
    parser.add_argument("archive", help="Path to the .7z archive to extract")
    parser.add_argument(
        "-o",
        "--output",
        help="Directory to extract the archive to",
        default=os.getcwd(),
    )
    args = parser.parse_args()

    try:
        extractor = PaZipExtractor(args.archive, extract_to=args.output)
        extractor.extract_archive()
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
