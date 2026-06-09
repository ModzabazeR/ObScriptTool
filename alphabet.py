#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import pandas as pd
from pandas.core.frame import DataFrame
import vowels

def get_entries(toc_file: str) -> DataFrame:
    df = pd.read_csv(toc_file)
    print("Total entries found: {0}".format(len(df)))
    return df

def startup() -> None:
    print("                THAI ALPHABET EN/DECODER FOR S;G")
    print("\"Thailand will get to play Steins;Gate.\" --Phachara Chirapakachote")
    if not os.path.exists('output'):
        os.makedirs('output')

def encode(toc: DataFrame, script_file: str, output_file: str = None) -> int:
    if output_file is None:
        output_file = os.path.join("output", os.path.basename(script_file))
    os.system("")
    entries = toc.to_dict("records")
    lst = []
    counter = 0
    vowels.fix_sara_um(script_file)
    f = open(script_file, "r", encoding="utf8", errors="ignore")
    for line in f:
        for letter in entries:
            if letter["thai"] in line:
                line = line.replace(letter["thai"], letter["kan"])
                counter += 1
        lst.append(line)
    f.close()

    out_dir = os.path.dirname(output_file)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(output_file, "w", encoding="utf8") as f:
        for line in lst: f.write(line)

    error_count = vowels.detect_vowel(output_file)
    print("\033[93m" + f"{error_count} error(s) found" + "\033[0m")
    print("\033[92m" + f"{counter} point(s) replaced" + "\033[0m")
    return error_count


def decode(toc:DataFrame, script_file: str, output_file: str = None) -> None:
    if output_file is None:
        output_file = os.path.join("output", os.path.basename(script_file))
    entries = toc.to_dict("records")
    lst = []
    counter = 0
    f = open(script_file, "r", encoding="utf8", errors="ignore")
    for line in f:
        for letter in entries:
            if letter["kan"] in line:
                line = line.replace(letter["kan"], letter["thai"])
                counter += 1
        lst.append(line)
    f.close()

    out_dir = os.path.dirname(output_file)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(output_file, "w", encoding="utf8") as f:
        for line in lst: f.write(line)

    print("{0} points replaced".format(counter))

if __name__ == "__main__":
    startup()
    if len(sys.argv) != 3:
        print("Usage: alphabet.py <file name> <encode/decode>")
        print("Example: alphabet.py SG00_01.SCX.txt encode")
        sys.exit()

    filename = sys.argv[1]
    mode = sys.argv[2]
    entries = get_entries("encoding_toc.csv")

    if mode.lower() == "encode":
        encode(entries, filename)
    elif mode.lower() == "decode":
        decode(entries, filename)
    else:
        print("Invalid mode selection")
        print("Usage: alphabet.py <file name> <encode/decode>")
        print("Example: alphabet.py SG00_01.SCX.txt encode")
        sys.exit()
