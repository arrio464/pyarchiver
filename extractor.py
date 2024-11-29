import os
import sys
from typing import Optional

import py7zr

from utils import setup_logging

logger = setup_logging()


class PaZipExtractor:
    def __init__(self, archive_path: str, extract_to: Optional[str] = None):
        """
        Initialize the extractor with the path to the .7z archive and an optional directory to extract to.

        :param archive_path: The path to the .7z archive.
        :param extract_to: The directory to extract the archive to (optional).
        """
        self.archive_path = archive_path
        self.extract_to = extract_to or os.getcwd()

    def extract_archive(self):
        """
        Extract the contents of the .7z archive to the specified directory.
        """
        if not os.path.exists(self.archive_path):
            logger.error(f"The archive '{self.archive_path}' does not exist.")
            return

        # if not self.archive_path.endswith(".7z"):
        #     logger.error(f"The file '{self.archive_path}' is not a .7z archive.")
        #     return

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
        except Exception as e:
            logger.error(f"Error extracting the archive: {e}")


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

    if not os.path.isfile(args.archive):
        logger.error(f"The specified path '{args.archive}' is not a valid file.")
        sys.exit(1)

    if os.path.exists(args.output):
        logger.error(f"The specified output directory '{args.output}' already exists.")
        sys.exit(1)

    try:
        extractor = PaZipExtractor(args.archive, extract_to=args.output)
        extractor.extract_archive()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
