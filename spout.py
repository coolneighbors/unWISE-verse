# -*- coding: utf-8 -*-
"""
Created on Fri Jun  3 13:25:59 2022

@author: Noah Schapera
"""

import os
import csv
import wv

projectID = input("Input Project ID: ")
setName = input("Input Subject Set Name: ")

os.system('panoptes configure')


pub=''

header = ['RA', 'DEC', 'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10']
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
        
        #set WV parameters to RA and DEC
        wv.custom_params(RA, DEC)
        
        
        #Save all images for parameter set
        flist = wv.png_set(RA, DEC, "pngs")
        
        #os.system(f"python one_wiseview_gif.py --outdir pngs --keep_pngs {RA} {DEC} {gifName}")
        
        #write everything to a row in the manifest
        row=[RA,DEC,*flist]
        writer.writerow(row)
        
        print(f"Added Manifest Line for Target {RA}, {DEC}")

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
    
