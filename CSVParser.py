# -*- coding: utf-8 -*-
"""
Created on Fri Jun  3 13:25:59 2022

@author: Noah Schapera
"""

import os
import csv

with open('manifest.csv', newline='') as manifest:
    reader = csv.DictReader(manifest)
    for row in reader:
        RA=row['RA']
        DEC=row['DEC']
        
        os.system(f"python one_wiseview_gif.py --outdir pngs --keep_pngs {RA} {DEC} {RA}-{DEC}.gif")
        
        print(f"Target {RA}, {DEC}")