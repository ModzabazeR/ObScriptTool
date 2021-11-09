#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pandas as pd
from pandas.core.frame import DataFrame

def get_entries(toc_file: str) -> DataFrame:
    df = pd.read_csv(toc_file, encoding="utf8")
    return df

def add_str(entries: DataFrame, charset: str) -> None:
    thais = [i for i in entries["thai"]]
    new_str = input("Add new Thai string: ")
    while new_str != "-1":
        if any(i == new_str for i in thais):
            print("Value already exists")
            new_str = input("Add new Thai string: ")

        if len(new_str) >= 3:
            # Insert at the start
            entries.loc[-1] = [len(entries) + 1, new_str, charset[len(entries)]]
            entries.index = entries.index + 1
            entries.sort_index(inplace=True)
        else:
            # Append at the end
            entries.loc[len(entries)] = [len(entries) + 1, new_str, charset[len(entries)]]

        new_str = input("Add new Thai string: ")    

def update_toc(entries: DataFrame, toc_file: str) -> None:
    entries.to_csv(toc_file, encoding="utf8", index=False)
    print("TOC file updated successfully")

if __name__ == "__main__":

    with open("kan_charset.utf8", "r", encoding="utf8") as f:
        KAN_CHARSET = f.read()
    toc_file = "encoding_toc.csv"
    
    entries = get_entries(toc_file)
    add_str(entries, KAN_CHARSET)
    update_toc(entries, toc_file)