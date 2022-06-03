# -*- coding: utf-8 -*-
"""
Created on Fri Jun  3 13:25:59 2022

@author: Noah Schapera
"""

import os
import csv

projectID = input("Input Project ID: ")
setName = input("Input Subject Set Name: ")

os.system('panoptes configure')


pub=''

header = ['RA', 'DEC', 'file']
f = open('manifest.csv', 'w', newline='')
writer= csv.writer(f)


writer.writerow(header)
print('Header Created')

with open('targets.csv', newline='') as targetList:
    reader = csv.DictReader(targetList)
    for row in reader:
        RA=row['RA']
        DEC=row['DEC']
        gifName=f"gifs\{RA}-{DEC}.gif"
        os.system(f"python one_wiseview_gif.py --outdir pngs --keep_pngs {RA} {DEC} {gifName}")
        
        print(f"Target {RA}, {DEC}")
        
        row=[RA,DEC,gifName]
        writer.writerow(row)
        print('Added Manifest Line')

f.close()
print('Generation Complete')

pub=input("Publish to zooniverse? y/n : ")

if pub == 'y':
    newset=input('Create new subject set? y/n : ')
    if newset == 'y':
        os.system(f"panoptes subject-set create {projectID} '{setName}'")
        setNum=input('Input subject set number : ')
        os.system(f"panoptes subject-set upload-subjects {setNum} manifest.csv")
        
    else:
        setNum=input('Input subject set number : ')
        os.system(f"panoptes subject-set upload-subjects {setNum} manifest.csv")
else:
    print('Program Complete')
    
