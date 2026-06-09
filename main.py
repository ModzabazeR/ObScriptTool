#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import json
import os
from sys import exit
import add
import alphabet as alp
import rearrange as rr
from tkinter import filedialog, Tk

root = Tk()
root.withdraw()
passed = 0
failed = 0

# https://stackoverflow.com/questions/287871/how-to-print-colored-text-to-the-terminal
os.system("")
print('\033[93m' + "IMPORTANT: If Thai alphabets are not display properly, please run this program in different console program" + '\033[0m')
print()

# Get config
with open("config.json", "r", encoding="utf8") as config_file:
    config = json.load(config_file) 

if config["mode"] != "encode" and config["mode"] != "decode":
    print("Invalid mode")
    exit()

# Get character set
with open(config["kan_charset"], "r", encoding="utf8") as f:
    KAN_CHARSET = f.read()

# TOC file
toc_file = config["toc_file"]
entries = pd.read_csv(toc_file, encoding="utf8")
print("Total entries found: {0}".format(len(entries)))

want_update = input("Do you want to update TOC (y/n): ")
if want_update.lower() == "y":
	# Add new strings and update TOC
	add.add_str(entries, KAN_CHARSET)
	add.update_toc(entries, toc_file)
	print("Updated entries: {0}".format(len(entries)))
	print()

# Pick a folder and gather script files recursively
print("Mode: " + config["mode"])
folder = filedialog.askdirectory(title="Folder to process (searched recursively)")
print()
if not folder:
	print("No folder selected.")
	input("Press enter to exit...")
	exit()

script_files = []
for dirpath, dirnames, fnames in os.walk(folder):
	# Don't descend into generated output or VCS folders
	dirnames[:] = [d for d in dirnames if d not in ("output", ".git")]
	for fname in fnames:
		if fname.lower().endswith(".txt"):
			script_files.append(os.path.join(dirpath, fname))
script_files.sort()

print(f"Found {len(script_files)} .txt file(s) under {folder}")
print()
alp.startup()
print()
for script_file in script_files:
	# Mirror the source folder structure under output/ to avoid name collisions
	rel_path = os.path.relpath(script_file, folder)
	output_file = os.path.join("output", rel_path)
	if config["mode"] == "encode":
		print(f"Encoding... {rel_path}")
		error_count = alp.encode(entries, script_file, output_file)
		if error_count > 0: failed += 1
		else: passed += 1
	else:
		print(f"Decoding... {rel_path}")
		alp.decode(entries, script_file, output_file)
	print()

# Rearrange TOC file
if want_update.lower() == "y":
	print("Rearranging...")
	rr.create_ordered_toc(toc_file, "ordered_encoding_toc.csv")
	print()

print("All done.")
print(f"\033[92mPassed: {passed}\033[0m, \033[91mFailed: {failed}\033[0m")
print("Please check the output file.")
print("If you want to add new strings and update the TOC file, please run the script again.")
print()
input("Press enter to exit...")