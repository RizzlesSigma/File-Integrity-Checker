import hashlib
import json
import os
import argparse

baseline_file = "baseline.json"

def argparse_argument():
    parser = argparse.ArgumentParser(
        description="A simple file integrity checker that uses SHA-256 hashes to detect changes in files."
    )
    parser.add_argument(
        "path",
        help="The file or directory path to check. If a directory is provided, all files within it will be checked.",
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Update the baseline with the current file hashes after checking.",
    )
    return parser.parse_args()

def calculate_file_hash(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(4096):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def collect_file(path):
    if os.path.isfile(path):
        return [path]
    elif os.path.isdir(path):
        all_files = []
        for root, dirs, files in os.walk(path):
            for file in files:
                full_path = os.path.join(root, file)
                if os.path.isfile(full_path):
                    all_files.append(full_path)
        return all_files
    else:
        print("Invalid path given.")
        return []

def load_baseline():
    try:
        with open(baseline_file, "r") as f:
            return json.load(f)  # ← no data.get(), return the whole dict
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def save_baseline(hashes):
    with open(baseline_file, "w") as f:
        json.dump(hashes, f, indent=4)  # ← no {"baseline": ...} wrapper

def main():
    argps = argparse_argument()

    file_path = argps.path
    files = collect_file(file_path)
    if not files:
        print("Path does not exist.")
        return
    
    # Inside main() — the hashing loop
    current_hashes = {}
    for file in files:
        try:
            print(f"Hashing: {file}")              # ← not "Hash = {file}"
            current_hashes[file] = calculate_file_hash(file)
        except PermissionError:
            print(f"[SKIPPED] {file} — permission denied")

    baseline = load_baseline()

    if baseline is None:
        print("No baseline found. Creating new baseline.")
        save_baseline(current_hashes)
        print(f"Baseline created for {len(files)} files.")
        return

    print("Check Results: ")
    all_ok = True
    for file, current_hash in current_hashes.items():
        if file not in baseline:
            print(f"[NEW] {file} is new and not in baseline.")
            all_ok = False
        elif current_hash != baseline[file]:
            print(f"[MODIFIED] {file} has been modified.")
            all_ok = False
        else:
            print(f"[UNCHANGED] {file} is unchanged.")

    for file in baseline:
        if file not in current_hashes:  # ← current_hashes is the full dict
            print(f"[DELETED] {file} has been deleted.")
            all_ok = False

    if all_ok:
        print("All files are unchanged.")
    else:
        print("Some files have changed. Updating baseline.")

if __name__ == "__main__":
    main()