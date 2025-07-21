#!/usr/bin/env python3
import os
import sys
import urllib.request
import subprocess

EPUBCHECK_JAR = "epubcheck-4.2.2.jar"
GUAVA_JAR = "guava-18.0.jar"
EPUBCHECK_URL = f"https://repo1.maven.org/maven2/org/w3c/epubcheck/4.2.2/{EPUBCHECK_JAR}"
GUAVA_URL = f"https://repo1.maven.org/maven2/com/google/guava/guava/18.0/{GUAVA_JAR}"

def download_file(url, filename):
    if os.path.exists(filename):
        print(f"{filename} already exists, skipping download.")
        return
    print(f"Downloading {filename} ...")
    urllib.request.urlretrieve(url, filename)
    print(f"Downloaded {filename}.")

def run_epubcheck(epub_file):
    cp = f"{EPUBCHECK_JAR}:{GUAVA_JAR}"
    if os.name == "nt":
        cp = f"{EPUBCHECK_JAR};{GUAVA_JAR}"
    cmd = ["java", "-cp", cp, "org.w3c.epubcheck.tool.Checker", epub_file]
    print(f"Validating {epub_file} with EPUBCheck 4.2.2 ...")
    proc = subprocess.run(cmd)
    if proc.returncode == 0:
        print("EPUB is valid!")
    else:
        print("EPUB is INVALID or warnings found.")

def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_epub2.py <epubfile>")
        sys.exit(1)
    epub_file = sys.argv[1]
    if not os.path.isfile(epub_file):
        print(f"EPUB file '{epub_file}' not found.")
        sys.exit(1)
    download_file(EPUBCHECK_URL, EPUBCHECK_JAR)
    download_file(GUAVA_URL, GUAVA_JAR)
    run_epubcheck(epub_file)

if __name__ == "__main__":
    main()