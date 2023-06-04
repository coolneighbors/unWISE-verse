# -*- coding: utf-8 -*-
"""
Created on Wed Jun  8 12:02:10 2022

@author: Noah Schapera
"""
import csv
from datetime import datetime

from panoptes_client import Panoptes

import Spout
import Login
from Data import Metadata


class NonUniqueFieldsError(Exception):
    def __init__(self, field_names):
        seen_field_names = set()
        duplicate_list = []
        for field_name in field_names:
            if field_name in seen_field_names:
                duplicate_list.append(field_name)
            else:
                seen_field_names.add(field_name)
        if(len(duplicate_list) == 1):
            super(NonUniqueFieldsError, self).__init__(f"The following field name is not unique: {duplicate_list[0]}")
        else:
            super(NonUniqueFieldsError, self).__init__(f"The following field names are not unique: {duplicate_list}")

def verifyLogin(UI):
    username = UI.username.get()
    pwd = UI.password.get()
    if(username == "" or pwd == ""):
        return False
    try:
        Panoptes.connect(username=username, password=pwd)
        return True
    except:
        return False


def fullPipeline(UI):
    """
    Goes through the entire pipeline. Generates manifest, uploads to Zooniverse.

    Returns
    -------
    None.

    """

    username = UI.username.get()
    pwd = UI.password.get()

    projectID = int(UI.projectID.get())
    subjectSetID = int(UI.subjectSetID.get())

    metadata_targets = UI.metadataTargetFile.get()
    manifest = UI.manifestFile.get()

    if (UI.printProgress.get()):
        UI.updateConsole("Full Pipeline Upload: ")

    login = Login.Login(username,pwd)
    workingSpout = Spout.Spout(projectID, login, UI.printProgress.get(), UI)

    subject_set = workingSpout.get_subject_set(subjectSetID)
    workingSpout.upload_data_to_subject_set(subject_set,manifest,metadata_targets)
    if(workingSpout.display_printouts):
        now = datetime.now()
        UI.updateConsole(f"Pipeline ended at: {now}")
        UI.updateConsole("---------------------------------")

def generateManifest(UI):
    """
    Just downloads png's and generates manifest.
    Not sure exactly what the use case for this is, but it seemed like a good thing to add

    Returns
    -------
    None.

    """

    metadata_targets = UI.metadataTargetFile.get()
    manifest = UI.manifestFile.get()
    if (UI.printProgress.get()):
        UI.updateConsole("Generate Manifest: ")
    Spout.Spout.generate_manifest_file(manifest,metadata_targets, display_printouts=UI.printProgress.get(), UI=UI)
    if(not UI.exitRequested):
        if (UI.printProgress.get()):
            now = datetime.now()
            UI.updateConsole(f"Pipeline ended at: {now}")
            UI.updateConsole("---------------------------------")

def publishToZooniverse(UI):
    """
    Publishes an existing manifest and previously downloaded png's to Zooniverse'

    Returns
    -------
    None.

    """

    username = UI.username.get()
    pwd = UI.password.get()
    
    projectID = int(UI.projectID.get())
    subjectSetID = int(UI.subjectSetID.get())
    
    manifest = UI.manifestFile.get()

    if (UI.printProgress.get()):
        UI.updateConsole("Publish Existing Manifest: ")

    login= Login.Login(username,pwd)
    workingSpout = Spout.Spout(projectID, login, UI.printProgress.get(), UI)
    
    subject_set=workingSpout.get_subject_set(subjectSetID)
    workingSpout.publish_existing_manifest(subject_set,manifest)
    if (workingSpout.display_printouts):
        now = datetime.now()
        UI.updateConsole(f"Pipeline ended at: {now}")
        UI.updateConsole("---------------------------------")

def mergeTargetsAndMetadata(targets_filename, metadata_dict, metadata_targets_filename):
    targets_dict_list = []
    with open(targets_filename, newline='') as targets_file:
        reader = csv.DictReader(targets_file)
        for row in reader:
            targets_dict_list.append(row)

    targets_field_names = list(targets_dict_list[0].keys())

    metadata_field_names = list(metadata_dict.keys())

    metadata_targets_field_names = [*targets_field_names,*metadata_field_names]
    # If these field names are in the targets file, it will override any assigned values by the UI
    allowed_duplicate_field_names = [f'{Metadata.privatization_symbol}MINBRIGHT',f'{Metadata.privatization_symbol}MAXBRIGHT']

    if(len(set(metadata_targets_field_names)) != len(metadata_targets_field_names)):
        for allowed_duplicate_field_name in allowed_duplicate_field_names:
            if(metadata_targets_field_names.count(allowed_duplicate_field_name) > 2):
                raise NonUniqueFieldsError(metadata_targets_field_names)

    allowed_duplicates_removed_field_names = [field_name for field_name in metadata_targets_field_names if field_name not in allowed_duplicate_field_names]
    if(len(set(allowed_duplicates_removed_field_names)) != len(allowed_duplicates_removed_field_names)):
        raise NonUniqueFieldsError(allowed_duplicates_removed_field_names)

    metadata_targets_dict_list = []
    for targets_dict in targets_dict_list:
        metadata_targets_dict_list.append(targets_dict | metadata_dict)
        if(metadata_dict[f'{Metadata.privatization_symbol}MINBRIGHT'] == ""):
            try:
                if(targets_dict[f'{Metadata.privatization_symbol}MINBRIGHT'] != ""):
                    metadata_targets_dict_list[-1][f'{Metadata.privatization_symbol}MINBRIGHT'] = targets_dict[f'{Metadata.privatization_symbol}MINBRIGHT']
            except KeyError:
                pass

        if(metadata_dict[f'{Metadata.privatization_symbol}MAXBRIGHT'] == ""):
            try:
                if(targets_dict[f'{Metadata.privatization_symbol}MAXBRIGHT'] != ""):
                    metadata_targets_dict_list[-1][f'{Metadata.privatization_symbol}MAXBRIGHT'] = targets_dict[f'{Metadata.privatization_symbol}MAXBRIGHT']
            except KeyError:
                pass

    with open(metadata_targets_filename,"w", newline='') as metadata_targets_file:
        writer = csv.DictWriter(metadata_targets_file, metadata_targets_field_names)
        writer.writeheader()
        writer.writerows(metadata_targets_dict_list)



