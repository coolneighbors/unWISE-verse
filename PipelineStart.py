# -*- coding: utf-8 -*-
"""
Created on Wed Jun  8 12:02:10 2022

@author: Noah Schapera
"""
import spout
import interface
import Login



def fullPipeline():
    '''
    Goes through the entire pipeline. Generates manifest, uploads to zooniverse

    Returns
    -------
    None.

    '''
    user,pwd = interface.getCreds()
    projectID = interface.projID()
    subject_set_id = interface.setID()
    target,manifest = interface.FileLocs()
    login = Login.Login(user,pwd)
    workingSpout = spout.Spout(projectID,login)
    
    subject_set = workingSpout.get_subject_set(subject_set_id)
    workingSpout.upload_data_to_subject_set(subject_set,manifest,target)
    
def generateManifest():
    '''
    Just downloads png's and generates manifest.
    Not sure exactly what the use case for this is, but it seemed like a good thing to add

    Returns
    -------
    None.

    '''
    login = spout.Login('BYWDummyAccount','NOIRLabBYW')
    target,manifest = interface.FileLocs()
   
    workingSpout = spout.Spout(18929,login)
    workingSpout.generate_manifest(manifest,target)
    
def publishToZooniverse():
    '''
    Publishes an existing manifest and previously downloaded png's to Zooniverse'

    Returns
    -------
    None.

    '''
    user,pwd = interface.getCreds()
    projectID = interface.projID()
    subject_set_id = interface.setID()
    manifest = interface.manifestFile()
    
    login=spout.Login(user,pwd)
    workingSpout = spout.Spout(projectID,login)
    
    subject_set=workingSpout.get_subject_set(subject_set_id)
    workingSpout.publish_existing_manifest(subject_set,manifest)
    
    
if __name__ == "__main__":
    #Calls interface to determine how the program should run.
    behavior = interface.whatToDo()
    if behavior == 0:
        fullPipeline()
    elif behavior == 1:
        generateManifest()
    elif behavior == 2:
        publishToZooniverse()
    else:
        print("You broke the pipeline :(")
