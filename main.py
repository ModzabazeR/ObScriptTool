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

# Encode the file
print("Mode: " + config["mode"])
filenames = filedialog.askopenfilenames(title="File(s) to process")
print()
alp.startup()
print()
for script_file in filenames:
	base_name = os.path.basename(script_file)
	if config["mode"] == "encode":
		print(f"Encoding... {base_name}")
		alp.encode(entries, base_name)
	else:
		print(f"Decoding... {base_name}")
		alp.decode(entries, base_name)
	print()

# Rearrange TOC file
if want_update.lower() == "y":
	print("Rearranging...")
	rr.create_ordered_toc(toc_file, "ordered_encoding_toc.csv")
	print()

print("All done.")
print("Please check the output file.")
print("If you want to add new strings and update the TOC file, please run the script again.")
print()
input("Press enter to exit...")