#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import json
import os
from sys import exit
import add
import alphabet as alp
import rearrange as rr

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

# Add new strings and update TOC
add.add_str(entries, KAN_CHARSET)
add.update_toc(entries, toc_file)
print("Updated entries: {0}".format(len(entries)))
print()

# Encode the file
print("Mode: " + config["mode"])
script_file = input("File to process: ")
print()
alp.startup()
print()
if config["mode"] == "encode":
    print("Encoding...")
    alp.encode(entries, script_file)
else:
    print("Decoding...")
    alp.decode(entries, script_file)
print()

# Rearrange TOC file
print("Rearranging...")
rr.create_ordered_toc(toc_file, "ordered_encoding_toc.csv")
print()

print("All done.")
print("Please check the output file.")
print("If you want to add new strings and update the TOC file, please run the script again.")
print()
input("Press enter to exit...")