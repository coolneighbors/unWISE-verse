# -*- coding: utf-8 -*-
"""
Created on Wed Jun  8 10:39:25 2022

@author: Noah Schapera
"""

import os

def yesNo(question, a1, a2):
    while True:
        ans = input(question+' : '+a1+'/'+a2+' : ').lower()
        if ans == a1.lower():
            return True
        elif ans == a2.lower():
            return False
        else:
            print("Unrecognized input")

def pubHandler():
    yes='y'
    no='n'
    
    if yesNo("Publish to Zooniverse?",yes,no):
        os.system('panoptes configure')
        projectID = input('Please enter Zooniverse project ID : ')
        
        if yesNo("Create new subject set?",yes,no):
            setName = input("Input Subject Set Name: ")
            os.system(f"panoptes subject-set create {projectID} '{setName}'")
        
        setNum=input('Input subject set number : ')
        os.system(f"panoptes subject-set upload-subjects {setNum} manifest.csv")
        
if __name__ == "__main__":
    pubHandler()