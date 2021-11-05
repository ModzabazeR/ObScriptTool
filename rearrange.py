#!/usr/bin/env python
# -*- coding: utf-8 -*-
import csv

# Get entries from TOC file
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

def create_ordered_toc(entries: list) -> None:
    ordered_entries = []

    for i in range(len(entries)):
        # print("{0} = {1}".format(entries[i]["id"],(kan_charset.index(entries[i]["kan"])+1)==entries[i]["id"]))
        if (i+1) == entries[i]["id"]:
            ordered_entries.append(entries[i])
        else:
            desired_id = len(ordered_entries)+1
            for j in range(len(entries)):
                if (entries[j]["id"]==desired_id):
                    ordered_entries.append(entries[j])

    # Write header
    with open("ordered_encoding_toc.csv", "w", encoding="utf8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["# id", "thai", "kan"])

    with open("ordered_encoding_toc.csv", "a", encoding="utf8", newline="") as f:
        for i in range(len(ordered_entries)):
            items = csv.DictWriter(f, ["id", "th", "kan"])
            items.writerow(ordered_entries[i])

if __name__ == "__main__":
    get_entries()
    create_ordered_toc(entries)