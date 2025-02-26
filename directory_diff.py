# directory_diff.py
"""
This module provides functions for comparing the contents of two directories,
ignoring the '.kst-git' folder in comparisons.

It includes functions for:
    - Listing directory contents (basic).
    - Comparing directories using filecmp.dircmp (structured comparison).
    - Recursive comparison with content checking using difflib.
    - Using external 'diff' command (optional, if available).
"""

import os
import filecmp
import difflib
import subprocess


def list_directory_contents(dir_path, ignore_dirs=None):
    """
    Lists files and directories in a given path, optionally ignoring specified directories.

    Args:
        dir_path (str): The path to the directory.
        ignore_dirs (list, optional): A list of directory names to ignore. Defaults to None.

    Returns:
        list: A list of filenames and directory names in the directory,
              or None if the path is not a directory or an error occurs.
    """
    if not os.path.isdir(dir_path):
        print(f"Error: '{dir_path}' is not a valid directory.")
        return None
    try:
        contents = os.listdir(dir_path)
        if ignore_dirs:
            contents = [item for item in contents if item not in ignore_dirs]
        return contents
    except OSError as e:
        print(f"Error listing directory '{dir_path}': {e}")
        return None


def compare_directories_basic(dir1_path, dir2_path, ignore_dirs=None):
    """
    Compares two directories by listing their contents and finding differences in file/folder names,
    optionally ignoring specified directories.

    Args:
        dir1_path (str): Path to the first directory.
        dir2_path (str): Path to the second directory.
        ignore_dirs (list, optional): A list of directory names to ignore. Defaults to None.

    Returns:
        tuple: A tuple containing sets of:
            - files/folders only in directory 1
            - files/folders only in directory 2
            - common files/folders
            Returns None if there's an error listing directories.
    """
    contents1 = list_directory_contents(dir1_path, ignore_dirs=ignore_dirs)
    contents2 = list_directory_contents(dir2_path, ignore_dirs=ignore_dirs)

    if contents1 is None or contents2 is None:
        return None

    set1 = set(contents1)
    set2 = set(contents2)

    return set1 - set2, set2 - set1, set1 & set2


def compare_directories_structured(dir1_path, dir2_path, ignore_dirs=None):
    """
    Compares two directories using filecmp.dircmp to provide a structured comparison,
    optionally ignoring specified directories.

    Args:
        dir1_path (str): Path to the first directory.
        dir2_path (str): Path to the second directory.
        ignore_dirs (list, optional): A list of directory names to ignore. Defaults to None.

    Returns:
        filecmp.dircmp: A filecmp.dircmp object containing comparison results.
                         Prints comparison details to the console.
                         Returns None if directory paths are invalid.
    """
    if not os.path.isdir(dir1_path) or not os.path.isdir(dir2_path):
        print("Error: Both paths must be valid directories.")
        return None

    def _filter_item(names):
        if ignore_dirs:
            return [name for name in names if name not in ignore_dirs]
        return names

    dcmp = filecmp.dircmp(dir1_path, dir2_path, ignore=_filter_item(ignore_dirs) if ignore_dirs else None)

    print(f"Comparison between '{dir1_path}' and '{dir2_path}' (ignoring: {ignore_dirs if ignore_dirs else 'None'}):")

    if dcmp.left_only:
        print(f"\nFiles/folders only in '{dir1_path}': {dcmp.left_only}")
    if dcmp.right_only:
        print(f"Files/folders only in '{dir2_path}': {dcmp.right_only}")
    if dcmp.common_files:
        print(f"Common files: {dcmp.common_files}")
    if dcmp.common_dirs:
        print(f"Common directories: {dcmp.common_dirs}")
    if dcmp.diff_files:
        print(f"Different files (same name, different content): {dcmp.diff_files}") # Note: content not checked by default
    if dcmp.funny_files:  # Files that could not be compared (e.g., permissions issues)
        print(f"Funny files (uncomparable): {dcmp.funny_files}")
    if dcmp.subdirs:
        print("\nSubdirectory comparisons:")
        for subdir in dcmp.subdirs:
            if subdir not in (ignore_dirs or []): # Ensure subdir is not in ignore list
                print(f"\n-- Subdirectory: {subdir} --")
                compare_directories_structured(os.path.join(dir1_path, subdir), os.path.join(dir2_path, subdir), ignore_dirs=ignore_dirs)
    return dcmp


def show_file_diff(file1_path, file2_path):
    """
    Shows the differences between two files' content using difflib.unified_diff.

    Args:
        file1_path (str): Path to the first file.
        file2_path (str): Path to the second file.

    Returns:
        None: Prints the diff output to the console.
    """
    try:
        with open(file1_path, 'r') as file1, open(file2_path, 'r') as file2:
            text1_lines = file1.readlines()
            text2_lines = file2.readlines()

            diff = difflib.unified_diff(text1_lines, text2_lines,
                                        fromfile=file1_path, tofile=file2_path)

            for line in diff:
                print(line, end='')  # Print the diff output
    except Exception as e:
        print(f"Error comparing file content: {e}")


def compare_directories_content(dir1_path, dir2_path, ignore_dirs=None):
    """
    Compares directories recursively and checks file content differences for common files,
    optionally ignoring specified directories.

    Args:
        dir1_path (str): Path to the first directory.
        dir2_path (str): Path to the second directory.
        ignore_dirs (list, optional): A list of directory names to ignore. Defaults to None.

    Returns:
        filecmp.dircmp: A filecmp.dircmp object containing comparison results.
                         Prints comparison details, including content differences, to the console.
                         Returns None if directory paths are invalid.
    """
    if not os.path.isdir(dir1_path) or not os.path.isdir(dir2_path):
        print("Error: Both paths must be valid directories.")
        return None

    def _filter_item(names):
        if ignore_dirs:
            return [name for name in names if name not in ignore_dirs]
        return names

    dcmp = filecmp.dircmp(dir1_path, dir2_path, ignore=_filter_item(ignore_dirs) if ignore_dirs else None)

    print(f"Comparison between '{dir1_path}' and '{dir2_path}' (ignoring: {ignore_dirs if ignore_dirs else 'None'}):")

    if dcmp.left_only:
        print(f"\nFiles/folders only in '{dir1_path}': {dcmp.left_only}")
    if dcmp.right_only:
        print(f"Files/folders only in '{dir2_path}': {dcmp.right_only}")
    if dcmp.common_files:
        print(f"Common files: {dcmp.common_files}")
    if dcmp.common_dirs:
        print(f"Common directories: {dcmp.common_dirs}")
    if dcmp.funny_files:
        print(f"Funny files (uncomparable): {dcmp.funny_files}")

    if dcmp.diff_files:
        print(f"\nDifferent files (same name, different content): {dcmp.diff_files}")
        for filename in dcmp.diff_files:
            file1_path = os.path.join(dir1_path, filename)
            file2_path = os.path.join(dir2_path, filename)
            print(f"\n-- Differences in file: {filename} --")
            show_file_diff(file1_path, file2_path)  # Function to show content diff

    if dcmp.subdirs:
        print("\nSubdirectory comparisons:")
        for subdir in dcmp.subdirs:
            if subdir not in (ignore_dirs or []): # Ensure subdir is not in ignore list
                print(f"\n-- Subdirectory: {subdir} --")
                compare_directories_content(os.path.join(dir1_path, subdir), os.path.join(dir2_path, subdir), ignore_dirs=ignore_dirs)
    return dcmp


def compare_directories_external_diff(dir1_path, dir2_path, ignore_dirs=None):
    """
    Uses the external 'diff' command to compare directories, optionally ignoring specified directories.

    Args:
        dir1_path (str): Path to the first directory.
        dir2_path (str): Path to the second directory.
        ignore_dirs (list, optional): A list of directory names to ignore. Defaults to None.

    Returns:
        bool: True if directories are identical (according to diff -qr), False otherwise.
              Prints diff output to the console if differences are found.
              Returns None if there's an error running diff or if diff is not found.
    """
    diff_command = ['diff', '-qr']
    if ignore_dirs:
        for ignore_dir in ignore_dirs:
            diff_command.extend(['-x', ignore_dir])
    diff_command.extend([dir1_path, dir2_path])

    try:
        result = subprocess.run(diff_command, capture_output=True, text=True, check=True)
        if result.stdout:
            print("Differences found:")
            print(result.stdout)
            return False
        else:
            print("Directories are identical (according to diff -qr).")
            return True
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:  # 'diff' returns 1 if differences are found
            print("Differences found:")
            print(e.stdout)  # Differences are in stdout in this case
            return False
        else:
            print(f"Error running diff: {e}")
            return None
    except FileNotFoundError:
        print("Error: 'diff' command not found. Make sure it's in your PATH.")
        return None


if __name__ == "__main__":
    # Example usage when the module is run directly
    dir1 = "dir1_example"  # Replace with your directory paths or create example dirs
    dir2 = "dir2_example"

    ignore_folders = ['.kst-git'] # Specify folders to ignore

    # Create example directories if they don't exist and some sample files
    if not os.path.exists(dir1):
        os.makedirs(dir1)
        os.makedirs(os.path.join(dir1, ".kst-git")) # Create .kst-git in dir1
        with open(os.path.join(dir1, ".kst-git", "ignore_file.txt"), "w") as f:
            f.write("This file should be ignored.\n")
        with open(os.path.join(dir1, "file1.txt"), "w") as f:
            f.write("This is file1 in dir1.\n")
        with open(os.path.join(dir1, "common_file.txt"), "w") as f:
            f.write("This is a common file with content 1.\n")
        os.makedirs(os.path.join(dir1, "subdir1"))
        with open(os.path.join(dir1, "subdir1", "subfile1.txt"), "w") as f:
            f.write("Subfile in subdir1.\n")

    if not os.path.exists(dir2):
        os.makedirs(dir2)
        os.makedirs(os.path.join(dir2, ".kst-git")) # Create .kst-git in dir2
        with open(os.path.join(dir2, ".kst-git", "another_ignore_file.txt"), "w") as f:
            f.write("This file should also be ignored.\n")
        with open(os.path.join(dir2, "file2.txt"), "w") as f:
            f.write("This is file2 in dir2.\n")
        with open(os.path.join(dir2, "common_file.txt"), "w") as f:
            f.write("This is a common file with content 2 (different).\n")
        os.makedirs(os.path.join(dir2, "subdir1"))
        with open(os.path.join(dir2, "subdir1", "subfile1.txt"), "w") as f:
            f.write("Subfile in subdir1 (same content).\n")
        os.makedirs(os.path.join(dir2, "subdir2")) # dir2 has an extra subdir

    print("--- Basic Comparison (ignoring .kst-git) ---")
    basic_diff = compare_directories_basic(dir1, dir2, ignore_dirs=ignore_folders)
    if basic_diff:
        only_in_dir1, only_in_dir2, common = basic_diff
        print(f"Only in '{dir1}': {only_in_dir1}")
        print(f"Only in '{dir2}': {only_in_dir2}")
        print(f"Common: {common}")

    print("\n--- Structured Comparison (filecmp.dircmp, ignoring .kst-git) ---")
    compare_directories_structured(dir1, dir2, ignore_dirs=ignore_folders)

    print("\n--- Content Comparison (ignoring .kst-git) ---")
    compare_directories_content(dir1, dir2, ignore_dirs=ignore_folders)

    print("\n--- External diff Command (ignoring .kst-git) ---")
    compare_directories_external_diff(dir1, dir2, ignore_dirs=ignore_folders)