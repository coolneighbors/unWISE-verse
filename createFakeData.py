# -*- coding: utf-8 -*-
"""
Created on Mon Jun 20 14:31:51 2022

@author: Noah Schapera
"""

import numpy as np
import numpy.random as nprnd
import csv

def main():  
    
    numOfTargets=int(input("Number of targets: "))
    
    print('Begin')
    header = ['RA','DEC']
    randRAs=nprnd.uniform(0,360,[numOfTargets])
    randDECs=nprnd.uniform(-90,90,[numOfTargets])
    print('Initialized')
    # open the file in the write mode
    with open('fake-targets.csv', 'w', newline='') as f:
        print('File Created')
        # create the csv writer
        writer = csv.writer(f)
        print('Header Written')
        
        writer.writerow(header)
        print("Starting to write data")
        for i in range(numOfTargets):
        # write a row to the csv file
            writer.writerow([str(randRAs[i]),str(randDECs[i])])
    
    print('Done')
    
if __name__ == "__main__":
    main()
    

