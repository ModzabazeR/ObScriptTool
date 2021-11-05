#!/usr/bin/env python
# -*- coding: utf-8 -*-
import csv

entries = []
def get_entries(toc_file: str) -> None:
    # Get entries from TOC file
    with open(toc_file, "r", encoding="utf8") as encoding_toc:
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

def add_str(entries: list, charset: str) -> None:
    new_str = input("Add new Thai string: ")
    while new_str != "-1":
        if any(d["th"] == new_str for d in entries):
            print("Value already exists")
            new_str = input("Add new Thai string: ")

        entry = {
                'id': len(entries) + 1,
                'th': new_str,
                'kan': charset[len(entries)]
            }
        if len(new_str) >= 3:
            entries.insert(0, entry.copy())
        else:
            entries.append(entry.copy())

        new_str = input("Add new Thai string: ")    

def update_toc(entries: list, toc_file: str) -> None:
    # Write header
    with open(toc_file, "w", encoding="utf8", newline="") as encoding_toc:
        writer = csv.writer(encoding_toc)
        writer.writerow(["# id", "thai", "kan"])

    # Write TOC
    with open(toc_file, "a", encoding="utf8", newline="") as encoding_toc:
        for i in range(len(entries)):
            items = csv.DictWriter(encoding_toc, ["id", "th", "kan"])
            items.writerow(entries[i])

    print("TOC file updated successfully")

if __name__ == "__main__":

    with open("kan_charset.utf8", "r", encoding="utf8") as f:
        KAN_CHARSET = f.read()
    toc_file = "encoding_toc.csv"
    
    get_entries(toc_file)
    add_str(entries, KAN_CHARSET)
    update_toc(entries, toc_file)