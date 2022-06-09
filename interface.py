# -*- coding: utf-8 -*-
"""
Created on Wed Jun  8 12:09:42 2022

@author: Noah Schapera
"""

import getpass

def getCreds():
    '''
    Usage
    -------
    For quereying user credentials.
    
    Returns
    -------
    user : string
        Zooniverse username
    pwd : string
        Zooniverse password.

    '''
    user = input("Zooniverse Username: ")
    print("Warning, password will not be shown while typed")
    pwd = getpass.getpass(prompt = "Zooniverse Password: ")
    return user, pwd
    
def FileLocs():
    '''
    Usage
    -------
    For quereying target and manifest files.

    Returns
    -------
    target : string
        filename of the target csv file. By default, lists in current directory
    manifest : string
        filename of the target csv file. By default, lists in current directory

    '''
    target = targetFile()
    manifest = manifestFile()
    return target, manifest

def targetFile():
    target = input("Please input target list filename: ")
    return target

def manifestFile():
    manifest = input("Please input desired manifest filename (will be created in directory unless specified): ")
    return manifest

def projID():
    '''
    For quereying project ID

    Returns
    -------
    pID : int (or string for slug)
        Zooniverse project ID

    '''
    pID = int(input("Please enter Zooniverse project ID: "))
    return pID

def setID():
    '''
    For quereying subject set ID

    Returns
    -------
    sID : int (or string for slug)
        Zooniverse subject set ID

    '''
    
    sID = int(input("Please enter subject set ID: "))
    return sID
    
def PubYN():
    '''
    Prompts user whether to zooniverse

    Returns
    -------
    bool
        TRUE: Should publish dataset to zooniverse
        FALSE: Should not publish dataset to zooniverse

    '''
    while True:
        pYN = input("Publish data set to zooniverse? y/n : ").lower()
        if pYN == 'y':
            return True
        elif pYN =='n':
            return False
        else:
            print("Unrecognized input.")
            
def whatToDo():
    '''
    Propmpts user to input desired program functionality

    Returns
    -------
    int
        returns int which determins program functionality.
        0, 1, or 2

    '''
    print("Enter desired behavior.")
    print("Download data, generate manifest, and publish to Zooniverse - input 'full' ")
    print("Download data, generate manifest - input 'manifest' ")
    print("Publish existing manifest and data to Zooniverse - input 'publish' ")
    
    while True:
        behavior = input().lower()
        if behavior == 'full':
            return 0
        elif behavior == 'manifest':
            return 1
        elif behavior == 'publish':
            return 2
        else:
            print("Unknown input. Please try again.")
            
if __name__ == "__main__":
    getCreds()