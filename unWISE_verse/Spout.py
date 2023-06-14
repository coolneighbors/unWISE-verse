# -*- coding: utf-8 -*-
"""
Created on Friday, June 3rd, 2022
Refactored on Tuesday, June 7th, 2022
Added further subject set manipulation on Tuesday, June 6th, 2023

@authors: Noah Schapera, Austin Humphreys
"""

import csv
import getpass
import os
import sys
import time
from copy import copy
from panoptes_client import Panoptes, Project, SubjectSet, Subject
from panoptes_client.set_member_subject import SetMemberSubject

import unWISE_verse

from unWISE_verse import Manifest

from unWISE_verse import Dataset

from unWISE_verse import Login

from unWISE_verse.UserInterface import display

Panoptes_client = Panoptes()

# Errors
class ProjectIdentificationError(Exception):
    def __init__(self, project_identifier):
        super(ProjectIdentificationError, self).__init__(f"Project Identifier was not a string or an integer: {project_identifier}")

class SubjectSetIdentificationError(Exception):
    def __init__(self, subject_set_identifier):
        super(SubjectSetIdentificationError, self).__init__(f"Subject Set Identifier was not a string or an integer: {subject_set_identifier}")

class SubjectSetRetrievalError(Exception):
    def __init__(self, subject_set_id):
        super(SubjectSetRetrievalError, self).__init__(f"Subject Set Identifier is not associated with any known subject set in this project: {subject_set_id}")

class Spout:

    def __init__(self, project_identifier, login, display_printouts=False, UI=None):

        """
        Initializes a Spout object, a data pipeline between local files and any accessible Zooniverse project.
        This logs into Zooniverse as a particular user and links this Spout object to a specific Zooniverse project
        (that the user has access to) via the project_identifier.

        Parameters
        ----------
            project_identifier : str or int
                A generalized identifier for both string-based slugs, defined in the panoptes_client API (see Notes),
                or an integer ID number associated with a project (can be found on Zooniverse).
            login : Login object
                A login object which holds the login details of the user trying to access Zooniverse. Consists of
                a username and a password.
            display_printouts : bool, optional
                Used to determine whether to display progress information in the console.
            UI : UI object, optional
                User interface object to request information from the user if the user interface is being used

        Notes
        -----
            The slug identifier only can work if the owner of the project is the one who is logging in
            since the owner's name is a part of the slug.

            A Zooniverse slug is of the form: "owner_username/project-name-with-dashes-for-spaces".

        """
        self.UI = UI
        global Panoptes_client
        Panoptes_client = Panoptes.connect(username=login.username, password=login.password)

        if(isinstance(project_identifier,str)):
            project_slug = login.username + "/" + project_identifier.replace(" ", "-")
            self.linked_project = Project.find(slug=project_slug)
        elif(isinstance(project_identifier,int)):
            self.linked_project = Project.find(id=project_identifier)
        else:
            raise ProjectIdentificationError(project_identifier)

        self.manifest = None
        self.display_printouts = display_printouts

        display(f"Project ID: {self.linked_project.id}", self.display_printouts, self.UI)
        display(f"Project Slug: {self.linked_project.slug}", self.display_printouts, self.UI)

    @staticmethod
    def requestLogin(filename="login.pickle", save=True):
        if (Login.Login.loginExists(filename)):
            login = Login.Login.load(filename)
            print("Login credentials loaded.")
            return login
        else:
            print("Please enter your Zooniverse credentials.")
            username = getpass.getpass(prompt='Username: ', stream=sys.stdin)
            password = getpass.getpass(prompt='Password: ', stream=sys.stdin)

            login = Login.Login(username=username, password=password)

            if(save):
                login.save(filename)
                print("Login credentials saved.")

            return login

    @staticmethod
    def requestZooniverseIDs():
        print("Please enter the following Zooniverse IDs.")
        project_id = int(getpass.getpass(prompt='Project ID: ', stream=sys.stdin))
        subject_set_id = int(getpass.getpass(prompt='Subject Set ID: ', stream=sys.stdin))
        return project_id, subject_set_id

    def display(self, text, display_printouts=False, UI=None):
        if (display_printouts):
            if (UI is None):
                print(text)
            elif (isinstance(UI, unWISE_verse.UserInterface.UserInterface)):
                try:
                    UI.updateConsole(text)
                except(RuntimeError):
                    print(text)

    def create_subject_set(self, display_name):
        """
        Create a subject set in the linked Zooniverse project.

        Parameters
        ----------
            display_name : str
                A string representing the display name associated with this subject set.

        Returns
        -------
        subject_set : SubjectSet object
            A newly created SubjectSet object associated to the linked project on Zooniverse.

        Notes
        -----
            At this point, I don't see a need to try to associate an ID with our subject sets ourselves since
            Zooniverse does this automatically with the creation of any new subject set.
        """

        subject_set = SubjectSet()
        subject_set.links.project = self.linked_project
        subject_set.display_name = copy(display_name)
        subject_set.save()
        return subject_set

    def subject_set_exists(self, subject_set_identifier):
        """
        Determine if a subject set, with a particular ID or display name, exists in the linked project.

        Parameters
        ----------
            subject_set_identifier : str or int
                A generalized identifier for both string-based display names, as seen in the linked project, or an
                integer ID number associated with the subject set (can be found on in the project under the
                particular subject set).

        Returns
        -------
         True/False: bool
            A boolean output of whether the subject set exists in the linked project on Zooniverse.

        Notes
        -----
            I figured it could be useful to have a function such as this, but I don't know if its critical to have.
        """

        if (isinstance(subject_set_identifier, str)):

            # subject_set_identifier is the subject set's name in the linked project
            for subject_set in self.linked_project.links.subject_sets:
                subject_set.reload()
                if(subject_set.raw["display_name"] == subject_set_identifier):
                    return True
            return False

        elif (isinstance(subject_set_identifier, int)):
            # subject_set_identifier is the subject set's id number in the linked project
            for subject_set in self.linked_project.links.subject_sets:
                subject_set.reload()
                if (int(subject_set.id) == subject_set_identifier):
                    return True
            return False

        else:
            raise SubjectSetIdentificationError(subject_set_identifier)

    def get_subject_set(self, subject_set_identifier):
        """
        Get a Subject Set object from the linked project using its ID or display name.

        Parameters
        ----------
            subject_set_identifier : str or int
                A generalized identifier for both string-based display names, as seen in the linked project, or an
                integer ID number associated with the subject set (can be found on in the project under the
                particular subject set)

        Returns
        -------
        subject_set : SubjectSet object
            A SubjectSet object associated with the subject_set_identifier and the linked project on Zooniverse

        Notes
        -----
            Uses the same logic as subject_set_exists but returns the actual subject set rather than booleans. Instead
            of using subject_set_exists to check if the subject set exists (and therefore looping over all subject sets
            in the project twice) I figured it would be better to loop over them once and return the subject set if it
            exists and then raise an error if it couldn't find the subject set requested. You should always be
            requesting an actual subject set anyways, so theres no need to loop over twice!
        """

        self.linked_project.reload()

        if (isinstance(subject_set_identifier, str)):
            # subject_set_identifier is the subject set's name in the linked project
            for subject_set in self.linked_project.links.subject_sets:
                subject_set.reload()
                if(subject_set.raw["display_name"] == subject_set_identifier):
                    display("Subject set retrieved from Zooniverse.", self.display_printouts, self.UI)
                    return subject_set
            raise SubjectSetRetrievalError(subject_set_identifier)

        elif (isinstance(subject_set_identifier, int)):
            # subject_set_identifier is the subject set's id number in the linked project
            for subject_set in self.linked_project.links.subject_sets:
                subject_set.reload()
                if (int(subject_set.id) == subject_set_identifier):
                    display("Subject set retrieved from Zooniverse.", self.display_printouts, self.UI)
                    return subject_set
            raise SubjectSetRetrievalError(subject_set_identifier)
        else:
            raise SubjectSetIdentificationError(subject_set_identifier)

    def generate_manifest(self, manifest_filename, dataset_filename, overwrite_automatically=None, enable_strict_manifest=False):
        """
        Generates a manifest CSV file used to compile the information necessary to send over subjects to a subject set
        associated with the linked project.

        Parameters
        ----------
            manifest_filename : str
                A full path filename of the manifest CSV to be overwritten or created.
            dataset_filename : str
                A full path filename of the dataset CSV to be accessed. Should at least contain RA and DEC values
                in the form: RA, DEC.
            overwrite_automatically : None or bool, optional
                Allows for a default option for overwriting the manifest file. If None, it will ask the user for a
                response and use that to decide whether or not to overwrite the existing manifest file. If set to true
                or to false, it will use that to decide.
            enable_strict_manifest: bool, optional
                Allows for manifests to be required to follow the standard a master_manifest.txt file, otherwise it
                will raise an error. This is to avoid any discrepancies in our uploading scheme, once it its finalized.
                Defaulted to true.

        Notes
        -----
            Just to prevent wasteful redundancy, I implemented a way to ask the user if they are supposed to overwrite
            an existing manifest if it finds a manifest at the provided full path filename of the manifest CSV.
        """

        dataset = Dataset.CN_Dataset(dataset_filename, ignore_partial_cutouts=True, require_uniform_fields=False, display_printouts=self.display_printouts, UI=self.UI)
        if (self.UI.exitRequested):
            return
        if(enable_strict_manifest):
            self.manifest = Manifest.Defined_Manifest(dataset, manifest_filename, overwrite_automatically,display_printouts=self.display_printouts,UI=self.UI)
        else:
            self.manifest = Manifest.Manifest(dataset, manifest_filename, overwrite_automatically,display_printouts=self.display_printouts,UI=self.UI)

    @classmethod
    def generate_manifest_file(cls, manifest_filename, dataset_filename, overwrite_automatically=None, enable_strict_manifest=False, display_printouts=False, UI=None):
        """
        Generates a manifest CSV file used to compile the information necessary to send over subjects to a subject set
        associated with the linked project.

        Parameters
        ----------
            manifest_filename : str
                A full path filename of the manifest CSV to be overwritten or created.
            dataset_filename : str
                A full path filename of the dataset CSV to be accessed. Should at least contain RA and DEC values
                in the form: RA, DEC.
            overwrite_automatically : None or bool, optional
                Allows for a default option for overwriting the manifest file. If None, it will ask the user for a
                response and use that to decide whether or not to overwrite the existing manifest file. If set to true
                or to false, it will use that to decide.
            enable_strict_manifest: bool, optional
                Allows for manifests to be required to follow the standard a master_manifest.txt file, otherwise it
                will raise an error. This is to avoid any discrepancies in our uploading scheme, once it its finalized.
                Defaulted to true.
            display_printouts : bool, optional
                Used to determine whether to display progress information in the console.
            UI : UI object, optional
                User interface object to request information from the user if the user interface is being used

        Notes
        -----
            Just to prevent wasteful redundancy, I implemented a way to ask the user if they are supposed to overwrite
            an existing manifest if it finds a manifest at the provided full path filename of the manifest CSV.
        """
        dataset = Dataset.CN_Dataset(dataset_filename, ignore_partial_cutouts=True, require_uniform_fields=False, display_printouts=display_printouts, UI=UI)
        if (UI.exitRequested):
            return
        if (enable_strict_manifest):
            Manifest.Defined_Manifest(dataset, manifest_filename, overwrite_automatically, display_printouts=display_printouts, UI=UI)
        else:
            Manifest.Manifest(dataset, manifest_filename, overwrite_automatically, display_printouts=display_printouts, UI=UI)

    def generate_subject_data_dicts(self, manifest_filename):
        """
        Generates a list of dictionaries containing the master manifest header elements as keys and the elements of
        the lines of the manifest (all except the first line which itself is the manifest header) as the associated data
        to those keys. A manifest CSV with n lines (n-1 subjects) will result in an array of n-1 subject data dictionaries.

        Parameters
        ----------
            manifest_filename : str
                A full path filename of the manifest CSV to be overwritten or created.

        Returns
        -------
        subject_data_dicts : List of dictionaries
            A list of subject data dictionaries generated from the provided manifest CSV.

        Notes
        -----
            These subject data dictionaries contain both data, the images path filenames of our flipbooks, and metadata
            such as the RA and DEC associated with the center of these images. The functionality to include an arbitrary
            amount of metadata has been implemented as well, but RA and DEC are required.
        """

        manifest_file = open(manifest_filename)
        manifest_file_reader = csv.reader(manifest_file)
        count = 0
        subject_data_dicts = []
        for row in manifest_file_reader:
            count += 1
            if(count == 1):
                header = row
            if(count != 1):
                subject_data_dict = {}
                for i in range(len(header)):
                    key = header[i]
                    subject_data_dict[key] = row[i]
                subject_data_dicts.append(subject_data_dict)
        return subject_data_dicts

    def generate_subjects_from_subject_data_dicts(self, subject_data_dicts):
        """
        Generates a list of subjects from a list of subject data dictionaries.

        Parameters
        ----------
            subject_data_dicts : list
                A list of subject data dictionaries

        Returns
        -------
        subjects : List of SubjectSet objects
            A list of newly created SubjectSet objects which are not associated with any SubjectSet object

        Notes
        -----

        """

        subjects = []
        metadata_dict = {}
        subject_count = 0
        subject_total = len(subject_data_dicts)
        for subject_data_dict in subject_data_dicts:
            subject = Subject()
            subject.links.project = self.linked_project
            for key in subject_data_dict:
                split_index = 1
                left_side_of_key = key[:split_index]
                right_side_of_key = key[split_index:]
                if (left_side_of_key == "f"):
                    try:
                        # Test if the value can be converted to an integer
                        int(right_side_of_key)
                        # Check if the filepath exists, if not, raise an error to avoid uploading a subject with missing images.
                        if(os.path.exists(subject_data_dict[key])):
                            subject.add_location(subject_data_dict[key])
                        else:
                            if(subject_data_dict[key] != ""):
                                display(f"Could not complete subject upload. The image file requested at {subject_data_dict[key]} does not exist.", self.display_printouts, self.UI)
                                self.UI.performingState = False
                                raise FileNotFoundError(f"Could not complete subject upload. The image file requested at {subject_data_dict[key]} does not exist.")
                    except ValueError:
                        pass
                else:
                    metadata_dict[key] = subject_data_dict[key]

            subject.metadata.update(metadata_dict)
            subject.save()
            subject.reload()
            subject.metadata.update({"ID": subject.id})
            subject.save()
            subjects.append(subject)
            subject_count += 1
            display(f"Created subject {subject_count} out of {subject_total}: " + str(subject.id), self.display_printouts, self.UI)

        display("Subjects generated.", self.display_printouts, self.UI)

        return subjects

    def fill_subject_set(self, subject_set, subjects):
        """
        Fills a SubjectSet object with Subjects and saves it to the linked project on Zooniverse.

        Parameters
        ----------
            subject_set : SubjectSet object
                A SubjectSet object associated to the linked project on Zooniverse.

            subjects : List of Subject objects
                A full path filename of the manifest CSV to be overwritten or created.

        Notes
        -----

        """

        if (not isinstance(subjects, list)):
            subjects = [subjects]

        chunk_size = 1000
        # for the number of subjects in the subject set, add the subjects to the subject set in chunks of chunk_size
        for i in range(0, len(subjects), chunk_size):
            chunk_subjects = subjects[i:i + chunk_size]
            subject_set.add(chunk_subjects)
            display("Added subjects " + str(i+1) + " through " + str(len(chunk_subjects)) + " to the subject set.", self.display_printouts, self.UI)
            subject_set.save()

        display("Subject set filled.", self.display_printouts, self.UI)
        
    def publish_existing_manifest(self, subject_set, manifest_filename):
        """
        Publishes data to Zooniverse subject set based on an existing manifest file, and existing data in the local png folder.

        Parameters
        ----------
            subject_set : SubjectSet object
                A SubjectSet object associated to the linked project on Zooniverse.

            manifest_filename : str
                A full path filename of the manifest CSV to be accessed.

        Notes
        -----
            One point of failure of this function is if a manifest exists but the pngs associated to the manifest's data
            does not exist. This will result in the code trying to access the image files to send to Zooniverse but it
            won't be able to do so since they are not there.
        """

        subject_data_dicts = self.generate_subject_data_dicts(manifest_filename)
        subjects = self.generate_subjects_from_subject_data_dicts(subject_data_dicts)
        self.fill_subject_set(subject_set, subjects)

        display("The existing manifest subjects have been published to Zooniverse.", self.display_printouts, self.UI)

    def upload_data_to_subject_set(self, subject_set, manifest_filename, dataset_filename, overwrite_automatically=None, enable_strict_manifest=False):
        """
        Uploads data from a dataset CSV, generates a manifest CSV, generates subjects from the manifest CSV, and then
        fills the subject set associated with the linked project on Zooniverse.

        Parameters
        ----------
            subject_set : SubjectSet object
                A SubjectSet object associated to the linked project on Zooniverse.
            manifest_filename : str
                A full path filename of the manifest CSV to be overwritten or created.
            dataset_filename : str
                A full path filename of the dataset CSV to be accessed. Should at least contain RA and DEC values
                in the form: RA, DEC.
            overwrite_automatically : None or bool, optional
                Allows for a default option for overwriting the manifest file. If None, it will ask the user for a
                response and use that to decide whether or not to overwrite the existing manifest file. If set to true
                or to false, it will use that to decide.
            enable_strict_manifest: bool, optional
                Allows for manifests to be required to follow the standard a master_manifest.txt file, otherwise it
                will raise an error. This is to avoid any discrepancies in our uploading scheme, once it its finalized.
                Defaulted to true.

        Notes
        -----
            Dataset CSV has the form:

            RA DEC metadata3 ...
            x y z ...

            Potential to use .fits files as well in the future, but this functionality is not yet developed.
        """

        self.generate_manifest(manifest_filename, dataset_filename, overwrite_automatically, enable_strict_manifest)

        # This allows the PNG modifications to catch up before it uploads to Zooniverse
        time.sleep(3)

        subject_data_dicts = self.generate_subject_data_dicts(manifest_filename)
        subjects = self.generate_subjects_from_subject_data_dicts(subject_data_dicts)
        self.fill_subject_set(subject_set, subjects)
        self.manifest = None
        display("Subjects uploaded to Zooniverse.", self.display_printouts, self.UI)

    def delete_subjects(self, subject_set, subjects):
        """
        Deletes the specified subjects from the given subject set.

        Parameters
        ----------
            subject_set : SubjectSet object
                A SubjectSet object associated to the linked project on Zooniverse.

            subjects : List of Subject objects
                A list of Subject objects to be deleted from the subject set.
        """

        if (not isinstance(subjects, list)):
            subjects = [subjects]

        subject_set.remove(subjects)
        display("Specified subjects were deleted.", self.display_printouts, self.UI)


    def modify_subject_metadata_field_name(self, subjects, current_field_name, new_field_name):
        """
        Modifies the metadata field of the subjects in the subject set.

        Parameters
        ----------
        subject_set : SubjectSet object
            A SubjectSet object associated to the linked project on Zooniverse.
        subjects : List of Subject objects
            A list of Subject objects to be modified.
        current_field_name : str
            The name of the metadata field to be modified.
        new_field_name : str
            The new name of the metadata field to be modified.
        """

        if(not isinstance(subjects, list)):
            subjects = [subjects]

        for subject in subjects:
            try:
                subject.metadata[new_field_name] = subject.metadata[current_field_name]
                del subject.metadata[current_field_name]
                subject.save()

            except KeyError:
                display(f"Specified subject {subject} was not modified. The current field name, {current_field_name}, does not exist.", self.display_printouts, self.UI)

        display("Specified subjects were modified.",self.display_printouts, self.UI)

    def modify_subject_metadata_field_value(self, subjects, field_name, new_field_value):
        """
        Modifies the metadata field value of the subjects in the subject set.

        Parameters
        ----------
        subjects : List of Subject objects
            A list of Subject objects to be modified.
        field_name : str
            The name of the metadata field to be modified.
        new_field_value : str
            The new value of the metadata field to be modified.
        """

        if(not isinstance(new_field_value, str)):
            try:
                new_field_value = str(new_field_value)
            except:
                display("Specified subjects were not modified. The new field value could not be converted to a string.", self.display_printouts, self.UI)

        if (not isinstance(subjects, list)):
            subjects = [subjects]

        for subject in subjects:
            try:
                subject.metadata[field_name] = new_field_value
                subject.save()

            except KeyError:
                display(f"Specified subject {subject} was not modified. The current field name, {field_name}, does not exist.", self.display_printouts, self.UI)
        display("Specified subjects were modified.", self.display_printouts, self.UI)


    def subject_has_images(self, subject):
        """
        Checks if the subject has images.

        Parameters
        ----------
        subject : Subject object
            A Subject object to be checked.

        Returns
        -------
        bool
            True if the subject has images, False otherwise.
        """

        return len(subject.raw['locations']) != 0

    def subject_has_metadata(self, subject):
        """
        Checks if the subject has metadata.

        Parameters
        ----------
        subject : Subject object
            A Subject object to be checked.

        Returns
        -------
        bool
            True if the subject has metadata, False otherwise.
        """

        return subject.metadata != {}

    @staticmethod
    def get_subject(subject_id, subject_set_id=None):
        """
        Gets a subject from the subject set.
        Parameters
        ----------
        subject_id : int
            The id of the subject to be retrieved.
        subject_set_id : int, optional
            The id of the subject set to be retrieved from. If None, it will do a blanketed search for the subject.

        Returns
        -------
        Subject object
            A Subject object from the subject set.
        """

        global Panoptes_client
        if(Panoptes_client.logged_in):
            if (subject_set_id is None):
                for sms in SetMemberSubject.where(subject_id=subject_id):
                    return sms.links.subject
                print(f"Warning: Subject {subject_id} does not exist or is inaccessible to the current user. Returning None.")
            else:
                for sms in SetMemberSubject.where(subject_set_id=subject_set_id, subject_id=subject_id):
                    return sms.links.subject
                print(f"Warning: Subject {subject_id} does not exist or is inaccessible to the current user. Returning None.")
        else:
            raise Exception("You must be logged to Zooniverse in to access subjects.")
