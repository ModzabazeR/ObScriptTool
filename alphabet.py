#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import csv
import vowels

entries = []
def get_entries() -> None:
    with open("encoding_toc.csv", "r", encoding="utf8") as encoding_toc:
        reader = csv.reader(encoding_toc)
        for row in reader:
            if row[0].startswith('#'): # ถ้าแถวไหนเริ่มด้วย # ให้ข้ามไปเลย
                continue
            entry = {
                'id': int(row[0]),
                'th': row[1],
                'kan': row[2]
            }
            entries.append(entry) # output จะออกมาเป็น list ของ dictionary
        print("Total entries found: {0}".format(len(entries)))

def startup() -> None:
    print("                THAI ALPHABET EN/DECODER FOR S;G")
    print("\"Thailand will get to play Steins;Gate.\" --Phachara Chirapakachote")
    if not os.path.exists('output'):
        os.makedirs('output')

def encode(entries:list, script_file: str) -> None:
    for i in entries:
        lst = []
        counter = 0
        f = open(script_file, "r", encoding="utf8", errors="ignore")
        for line in f:
            for letter in entries:
                if letter["th"] in line:
                    line = line.replace(letter["th"], letter["kan"])
                    counter += 1
            lst.append(line)
        f.close()

        f = open("output/"+script_file, "w", encoding="utf8")
        for line in lst:
            f.write(line)

    print("{0} error(s) found".format(vowels.detect_vowel("output/" + script_file)))
    print("{0} point(s) replaced".format(counter))


def decode(entries:list, script_file: str) -> None:
    for i in entries:
        lst = []
        counter = 0
        f = open(script_file, "r", encoding="utf8", errors="ignore")
        for line in f:
            for letter in entries:
                if letter["kan"] in line:
                    line = line.replace(letter["kan"], letter["th"])
                    counter += 1
            lst.append(line)
        f.close()

        f = open("output/"+script_file, "w", encoding="utf8")
        for line in lst:
            f.write(line)

    print("{0} points replaced".format(counter))

if __name__ == "__main__":
    startup()
    if len(sys.argv) != 3:
        print("Usage: alphabet.py <file name> <encode/decode>")
        print("Example: alphabet.py SG00_01.SCX.txt encode")
        sys.exit()

    filename = sys.argv[1]
    mode = sys.argv[2]
    get_entries()

    if mode.lower() == "encode":
        encode(entries, filename)
    elif mode.lower() == "decode":
        decode(entries, filename)
    else:
        print("Invalid mode selection")
        print("Usage: alphabet.py <file name> <encode/decode>")
        print("Example: alphabet.py SG00_01.SCX.txt encode")
        sys.exit()
