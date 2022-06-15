# -*- coding: utf-8 -*-
"""
Created on Wed Jun  8 12:02:10 2022

@author: Noah Schapera
"""

import spout
import Login
import UI


def fullPipeline(ui):
    """
    Goes through the entire pipeline. Generates manifest, uploads to Zooniverse.

    Returns
    -------
    None.

    """

    user = ui.acc_username
    pwd = ui.acc_password

    projectID = int(ui.acc_projectID)
    subject_set_id = int(ui.acc_setID)

    target = ui.acc_targetFile
    manifest = ui.acc_manifestFile

    login = Login.Login(user,pwd)
    workingSpout = spout.Spout(projectID,login,bool(ui.printProgress.get()))

    subject_set = workingSpout.get_subject_set(subject_set_id)
    workingSpout.upload_data_to_subject_set(subject_set,manifest,target)


def generateManifest(ui):
    """
    Just downloads png's and generates manifest.
    Not sure exactly what the use case for this is, but it seemed like a good thing to add

    Returns
    -------
    None.

    """

    login = Login.Login('BYWDummyAccount','NOIRLabBYW')
    target = ui.acc_targetFile
    manifest = ui.acc_manifestFile
   
    workingSpout = spout.Spout(18929,login,bool(ui.printProgress.get()))
    workingSpout.generate_manifest(manifest,target)


def publishToZooniverse(ui):
    """
    Publishes an existing manifest and previously downloaded png's to Zooniverse'

    Returns
    -------
    None.

    """

    user = ui.acc_username
    pwd = ui.acc_password
    
    projectID = int(ui.acc_projectID)
    subject_set_id = int(ui.acc_setID)
    
    manifest = ui.acc_manifestFile
    
    login= Login.Login(user,pwd)
    workingSpout = spout.Spout(projectID,login,bool(ui.printProgress.get()))
    
    subject_set=workingSpout.get_subject_set(subject_set_id)
    workingSpout.publish_existing_manifest(subject_set,manifest)
    
    
if __name__ == "__main__":
    ui=UI.UI_obj()

