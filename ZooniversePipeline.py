# -*- coding: utf-8 -*-
"""
Created on Wed Jun  8 12:02:10 2022

@author: Noah Schapera
"""

import Spout
import Login
import UserInterface


def fullPipeline(ui):
    """
    Goes through the entire pipeline. Generates manifest, uploads to Zooniverse.

    Returns
    -------
    None.

    """

    username = ui.username.get()
    pwd = ui.password.get()

    projectID = int(ui.projectID.get())
    subjectSetID = int(ui.subjectSetID.get())

    target = ui.targetFile.get()
    manifest = ui.manifestFile.get()

    login = Login.Login(username,pwd)
    workingSpout = Spout.Spout(projectID, login, ui.printProgress.get(), ui)

    subject_set = workingSpout.get_subject_set(subjectSetID)
    workingSpout.upload_data_to_subject_set(subject_set,manifest,target)
    if(workingSpout.display_printouts):
        ui.updateConsole("---------------------------------")


def generateManifest(ui):
    """
    Just downloads png's and generates manifest.
    Not sure exactly what the use case for this is, but it seemed like a good thing to add

    Returns
    -------
    None.

    """

    login = Login.Login('BYWDummyAccount','NOIRLabBYW')
    target = ui.targetFile.get()
    manifest = ui.manifestFile.get()
   
    workingSpout = Spout.Spout(18929, login, ui.printProgress.get(), ui)
    workingSpout.generate_manifest(manifest,target)
    if (workingSpout.display_printouts):
        ui.updateConsole("---------------------------------")

def publishToZooniverse(ui):
    """
    Publishes an existing manifest and previously downloaded png's to Zooniverse'

    Returns
    -------
    None.

    """

    username = ui.username.get()
    pwd = ui.password.get()
    
    projectID = int(ui.projectID.get())
    subjectSetID = int(ui.subjectSetID.get())
    
    manifest = ui.manifestFile.get()
    
    login= Login.Login(username,pwd)
    workingSpout = Spout.Spout(projectID, login, ui.printProgress.get(), ui)
    
    subject_set=workingSpout.get_subject_set(subjectSetID)
    workingSpout.publish_existing_manifest(subject_set,manifest)
    if (workingSpout.display_printouts):
        ui.updateConsole("---------------------------------")
    
if __name__ == "__main__":
    ui=UserInterface.UserInterface()

