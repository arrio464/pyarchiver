import os
import sys
import time
from typing import List, Optional

import pathspec
import py7zr

from utils import calculate_checksum, setup_logging

logger = setup_logging()


class PaZipCompressor:
    def __init__(self, folder: str, output_dir: Optional[str] = None) -> None:
        """
        Initialize the compressor with the directory to compress and an optional output directory.

        :param folder: The directory to compress.
        :param output_dir: The directory to write the compressed archive to (optional).
        :raises AssertionError: If the folder to be archived does not exist or the output directory does not exist.
        """
        assert os.path.isdir(
            folder
        ), f"The folder {folder} to be archived does not exist."
        assert output_dir is None or os.path.isdir(
            output_dir
        ), f"Output directory {output_dir} does not exist."

        self.folder = folder
        self.output_dir = output_dir or os.getcwd()
        self.spec = self.load_paignore(folder)

    def load_paignore(self, directory: str) -> List[str]:
        """
        Load the ignore rules from a .paignore file in the specified directory.

        :param directory: The directory to search for a .paignore file.
        :return: A PathSpec object containing the ignore patterns.
        """
        paignore_path = os.path.join(directory, ".paignore")
        if os.path.exists(paignore_path):
            with open(paignore_path, "r") as f:
                return pathspec.PathSpec.from_lines("gitwildmatch", f)
        return pathspec.PathSpec([])

    def matches_ignore_pattern(self, filepath: str) -> bool:
        """
        Check if a file path matches any of the ignore patterns in the .paignore file.

        :param filepath: The file path to check.
        :return: True if the file path matches an ignore pattern, False otherwise.
        """
        relative_path = os.path.relpath(filepath, self.folder)
        return self.spec.match_file(relative_path)

    def get_files_to_compress(self) -> List[str]:
        """
        Get the list of files to compress based on the .paignore rules.
        """
        compress_files = []
        for root, dirs, files in os.walk(self.folder):
            # Filter directories
            dirs[:] = [
                d
                for d in dirs
                if not self.matches_ignore_pattern(os.path.join(root, d))
            ]

            # Filter files
            for file in files:
                file_path = os.path.join(root, file)
                if not self.matches_ignore_pattern(file_path):
                    compress_files.append(file_path)

        if not compress_files:
            logger.warning("No files found to compress.")

        return compress_files

    def compress_folder(self) -> None | str:
        """
        Compress the directory recursively into a 7z archive, ignoring files/folders based on the .paignore rules.
        """
        folder_name = os.path.basename(os.path.normpath(self.folder))
        tmp_archive_path = os.path.join(self.output_dir, f"{folder_name}.7z.tmp")
        timestamp = time.strftime("%Y%m%d%H%M%S%z")
        files_to_compress = self.get_files_to_compress()

        # Compress the files
        try:
            with py7zr.SevenZipFile(tmp_archive_path, "w") as archive:
                for file_path in files_to_compress:
                    logger.info(f"Compressing '{file_path}'...")
                    if os.path.islink(file_path):
                        logger.warning(
                            f"Symbolic links are not fully tested, may cause problems: {file_path}"
                        )
                    arcname = os.path.relpath(file_path, self.folder)
                    archive.write(file_path, arcname=arcname)

            output_archive_path = os.path.join(
                self.output_dir,
                f"{folder_name}_{timestamp}_{calculate_checksum(tmp_archive_path)}.7z",
            )
            os.rename(tmp_archive_path, output_archive_path)

            logger.success(
                f"Folder '{self.folder}' compressed successfully to '{output_archive_path}'."
            )
            return output_archive_path
        except Exception as e:
            logger.error(f"Error compressing directory: {e}", exc_info=True)
            if os.path.isfile(tmp_archive_path):
                os.remove(tmp_archive_path)
            return


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compress folder into .7z archive")
    parser.add_argument("folder", help="Path to the folder to compress")
    parser.add_argument(
        "-o",
        "--output",
        help="Directory to store the compressed archive",
        default=os.getcwd(),
    )
    args = parser.parse_args()

    if os.path.isfile(args.folder):
        logger.error("Archiving of individual files has not been implemented yet.")
        sys.exit(1)

    try:
        compressor = PaZipCompressor(args.folder, output_dir=args.output)
        compressor.compress_folder()
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
