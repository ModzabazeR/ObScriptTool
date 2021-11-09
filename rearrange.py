#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pandas as pd

def create_ordered_toc(toc_file: str, output_file: str) -> None:
    df = pd.read_csv(toc_file)
    ordered = df.sort_values(by=['# id'])
    ordered.to_csv(output_file, index=False)

if __name__ == "__main__":
    create_ordered_toc("encoding_toc.csv", "testtt.csv")