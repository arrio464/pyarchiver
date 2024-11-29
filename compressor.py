import fnmatch
import os
import sys
import time
import zlib
from typing import List

import py7zr

from utils import setup_logging

logger = setup_logging()


class PaZipCompressor:
    def __init__(self, directory: str, archive_locale: str = None):
        """
        Initialize the compressor with a directory and an optional archive location.

        :param directory: The directory to compress.
        :param archive_locale: The location to save the compressed archive (optional).
        """
        self.directory = directory
        self.archive_locale = archive_locale or os.getcwd()
        self.ignore_rules = self.load_paignore(directory)

    def load_paignore(self, directory: str) -> List[str]:
        """
        Load the .paignore file from the directory if it exists and return the list of ignore patterns.

        :param directory: The target directory.
        :return: List of ignore patterns.
        """
        ignore_rules = []
        paignore_path = os.path.join(directory, ".paignore")
        if os.path.exists(paignore_path):
            try:
                with open(paignore_path, "r") as f:
                    ignore_rules = [
                        line.strip() for line in f.readlines() if line.strip()
                    ]
            except Exception as e:
                logger.error(f"Error reading .paignore: {e}")
        return ignore_rules

    def matches_ignore_pattern(self, filepath: str) -> bool:
        """
        Check if a file or directory matches any of the ignore patterns.

        :param filepath: The path to check.
        :return: True if the file/directory should be ignored, False otherwise.
        """
        return any(fnmatch.fnmatch(filepath, pattern) for pattern in self.ignore_rules)

    def calculate_crc32(self, filepath: str) -> str:
        """
        Calculate the CRC32 hash of the file for unique naming of the archive.

        :param filepath: The file path to compute CRC32 checksum.
        :return: CRC32 checksum as a hex string.
        """
        hash_crc32 = 0
        try:
            with open(filepath, "rb") as f:
                while chunk := f.read(1024):
                    hash_crc32 = zlib.crc32(chunk, hash_crc32)
        except FileNotFoundError:
            logger.error(f"File {filepath} not found for CRC32 calculation.")
            return "00000000"
        return f"{hash_crc32 & 0xFFFFFFFF:08x}"

    def compress_directory(self):
        """
        Compress the directory recursively into a 7z archive, ignoring files/folders based on the .paignore rules.
        """
        # Create the archive filename based on the directory name, timestamp, and CRC32.
        directory_name = os.path.basename(os.path.normpath(self.directory))
        archive_tmp_path = os.path.join(self.archive_locale, f"{directory_name}.7z.tmp")

        files_to_compress = []
        for root, dirs, files in os.walk(self.directory):
            # Check and apply the ignore rules to directories
            dirs[:] = [
                d
                for d in dirs
                if not self.matches_ignore_pattern(os.path.join(root, d))
            ]
            for file in files:
                file_path = os.path.join(root, file)
                if not self.matches_ignore_pattern(file_path):
                    files_to_compress.append(file_path)

        if not files_to_compress:
            logger.warning(f"No files found to compress in '{self.directory}'.")
            return

        # Compress the files
        try:
            logger.info(f"Compressing directory '{self.directory}'...")

            with py7zr.SevenZipFile(archive_tmp_path, "w") as archive:
                for file_path in files_to_compress:
                    arcname = os.path.relpath(file_path, self.directory)
                    archive.write(file_path, arcname=arcname)

            timestamp = time.strftime("%Y%m%d%H%M%S%z")
            crc32_checksum = self.calculate_crc32(archive_tmp_path)
            archive_path = f"{directory_name}_{timestamp}_{crc32_checksum}.7z"
            os.rename(archive_tmp_path, os.path.join(self.archive_locale, archive_path))

            logger.success(
                f"Directory '{self.directory}' compressed successfully to '{archive_path}'."
            )

        except Exception as e:
            logger.error(f"Error compressing directory: {e}")
            if os.path.exists(archive_tmp_path):
                os.remove(archive_tmp_path)
            return


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compress directory into .7z archive")
    parser.add_argument("directory", help="Path to the directory to compress")
    parser.add_argument(
        "-o",
        "--output",
        help="Directory to store the compressed archive",
        default=os.getcwd(),
    )
    args = parser.parse_args()

    if os.path.isfile(args.directory):
        logger.error("Archiving of individual files has not been implemented yet.")
        sys.exit(1)

    if not os.path.isdir(args.directory):
        logger.error(f"The specified path '{args.directory}' is not a valid directory.")
        sys.exit(1)

    if os.path.exists(args.output):
        logger.error(f"The specified output directory '{args.output}' already exists.")
        sys.exit(1)

    try:
        compressor = PaZipCompressor(args.directory, archive_locale=args.output)
        compressor.compress_directory()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
