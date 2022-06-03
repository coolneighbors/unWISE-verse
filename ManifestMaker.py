# -*- coding: utf-8 -*-
"""
Created on Thu Jun  2 15:02:58 2022

@author: Noah Schapera
"""

##Generates a manifest for frames in a file


import csv
import sys

print('Making Manifest')
frames = int(sys.argv[1])

header = ['ID', 'frame0', 'frame1']


f = open('manifest.csv', 'w', newline='')
writer = csv.writer(f)

writer.writerow(header)

for frame in range(frames):
    fileName0 = 'TestData\Field-'+str(frame)+'-0.png'
    fileName1 = 'TestData\Field-'+str(frame)+'-1.png'

    row=[frame,fileName0,fileName1]
    writer.writerow(row)
    
f.close()
    
print('Manifest Complete')
    

