# -*- coding: utf-8 -*-
"""
Created on Friday, June 3rd
Refactored on Tuesday, June 7th

@authors: Noah Schapera, Austin Humphreys
"""

import csv
import wv
import os

from panoptes_client import Panoptes, Project, SubjectSet, Subject

#initialize image manipulation variables
enableOverlay = True
scaling = 2

class Login:
    def __init__(self, username='', password=''):
        """
        Construct a Login object, a simple way to store a Zooniverse user's username and password.

        Parameters
        ----------
            username : str
                A string representing the username of a user on Zooniverse
                Defaults to empty
            password : str
                A string representing the password of the same user on Zooniverse
                Defaults to empty
        Notes
        -----
            This object and the login process probably could be made more secure, but this doesn't seem very necessary
            if the login is done locally and for our own purposes
        """
        self.username = username
        self.password = password

# Errors
class ProjectIdentificationError(Exception):
    def __init__(self, project_identifier):
        super(SubjectSetIdentificationError, self).__init__("Project Identifier was not a string or an integer: " + str(project_identifier))

class SubjectSetIdentificationError(Exception):
    def __init__(self, subject_set_identifier):
        super(SubjectSetIdentificationError, self).__init__("Subject Set Identifier was not a string or an integer: " + str(subject_set_identifier))

class SubjectSetRetrievalError(Exception):
    def __init__(self, subject_set_id):
        super(InvalidDatasetError, self).__init__("Subject Set Identifier is not associated with any known subject set in this project: " + str(subject_set_id))


class InvalidDatasetError(Exception):
    def __init__(self, dataset_filename,manifest_header, metadata_keys):
        bool_list = (key in manifest_header for key in metadata_keys)
        invalid_metadata_key_indices = [i for i, x in enumerate(bool_list) if not x]
        invalid_metadata_keys = []
        for index in invalid_metadata_key_indices:
            invalid_metadata_keys.append(metadata_keys[index])
        error_message = "The accessed dataset file at: " + str(dataset_filename) + " is not compliant with the current master manifest header: " + str(manifest_header) + "\n" + "The following entries are mismatched in the dataset file: " + str(invalid_metadata_keys)
        super(InvalidDatasetError, self).__init__(error_message)


class Spout:

    def __init__(self, project_identifier,login):

        """
        Construct a Spout object, a data pipeline between local files and any accessible Zooniverse project.
        This logs into Zooniverse as a particular user, links this Spout to a specific Zooniverse project that user has
        access to, and defines the master manifest header.

        Parameters
        ----------
            project_identifier : str or int
                A generalized identifier for both string-based slugs, defined in the panoptes_client API, or an
                integer ID number associated with a project (can be found on Zooniverse)
            login : Login object
                A login object which holds the login details of the user trying to access Zooniverse. Consists of
                a username and a password.

        Notes
        -----
            The slug identifier only can work if the owner of the project is the one who is logging in
            since the owner's name is a part of the slug.


            A Zooniverse slug is of the form: "owner_username/project-name-with-dashes-for-spaces"

            Change the master manifest header to add new metadata or if you want to increase the total maximum of frames
            Frames are recognized as frames if they start with f and the rest is an integer. Slots them in the the order they appear
            in the master header from left to right
        """


        Panoptes.connect(username=login.username, password=login.password)

        if(isinstance(project_identifier,str)):
            project_slug = login.username + "/" + project_identifier.replace(" ", "-")
            self.linked_project = Project.find(slug=project_slug)
        elif(isinstance(project_identifier,int)):
            self.linked_project = Project.find(id=project_identifier)
        else:
            raise ProjectIdentificationError(project_identifier)

        print("Project ID: " + str(self.linked_project.id))
        print("Project Slug: " + str(self.linked_project.slug))

        self.manifest_header = ['RA', 'DEC', 'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10']


    def create_subject_set(self, display_name):
        """
        Create a subject set in the linked Zooniverse project.

        Parameters
        ----------
            display_name : str
                A string representing the display name associated with this subject set

        Returns
        -------
        subject_set : SubjectSet object
            A newly created SubjectSet object associated to the linked project on Zooniverse

        Notes
        -----
            At this point, I don't see a need to try to associate an ID with our subject sets ourselves since
            Zooniverse does this automatically with the creation of any new subject set.
        """

        subject_set = SubjectSet()
        subject_set.links.project = self.linked_project
        subject_set.display_name = display_name
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
                particular subject set)

        Returns
        -------
         True/False: boolean
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
                    return subject_set
            raise SubjectSetRetrievalError(subject_set_identifier)

        elif (isinstance(subject_set_identifier, int)):
            # subject_set_identifier is the subject set's id number in the linked project
            for subject_set in self.linked_project.links.subject_sets:
                subject_set.reload()
                if (int(subject_set.id) == subject_set_identifier):
                    return subject_set
            raise SubjectSetRetrievalError(subject_set_identifier)

        else:
            raise SubjectSetIdentificationError(subject_set_identifier)

    def is_valid_dataset(self, dataset_filename):
        with open(dataset_filename, newline='') as targetList:
            reader = csv.DictReader(targetList)
            metadata_keys = reader.fieldnames
            return all(key in self.manifest_header for key in metadata_keys)

    def generate_manifest(self, manifest_filename, dataset_filename, overwrite_automatically = None):
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

        Notes
        -----
            Just to prevent wasteful redundancy, I implemented a way to ask the user if they are supposed to overwrite
            an existing manifest if it finds a manifest at the provided full path filename of the manifest CSV.
        """

        overwrite_manifest = None
        if(overwrite_automatically is None):
            if (os.path.exists(manifest_filename)):
                print("Manifest File: " + str(manifest_filename))
                response = input("This manifest already exists. Would you like to overwrite this manifest? (y/n) ")
                end_prompt = False
                while (not end_prompt):
                    if (response.lower() == "y"):
                        end_prompt = True
                        overwrite_manifest = True
                        print("Warning: manifest file being overridden at: " + str(manifest_filename))
                    elif (response.lower() == "n"):
                        end_prompt = True
                        overwrite_manifest = False
                    else:
                        response = input("Invalid response, please type a valid response (y/n): ")
            else:
                overwrite_manifest = True
        elif(overwrite_automatically):
            overwrite_manifest = True

        else:
            overwrite_manifest = False

        if(overwrite_manifest):
            f = open(manifest_filename, 'w', newline='')
            writer = csv.writer(f)
            writer.writerow(self.manifest_header)
            print('Header Created')
            with open(dataset_filename, newline='') as targetList:
                reader = csv.DictReader(targetList)
                if (self.is_valid_dataset(dataset_filename)):
                    for row in reader:
                        RA = row['RA']
                        DEC = row['DEC']

                        metadata = []
                        for key in row:
                            metadata.append(row[key])

                        # set WV parameters to RA and DEC
                        wv.custom_params(RA, DEC)

                        # Save all images for parameter set
                        flist = wv.png_set(RA, DEC, "pngs", scale_factor=scaling, addGrid=enableOverlay)

                        # write everything to a row in the manifest
                        row = [*metadata, *flist]
                        writer.writerow(row)

                        print(f"Added Manifest Line for Target {RA}, {DEC}")

                    f.close()
                    print('Manifest Generation Complete')
                else:
                    metadata_keys = reader.fieldnames
                    raise InvalidDatasetError(dataset_filename, self.manifest_header, metadata_keys)
        else:
            print("Existing Manifest Preserved")


    def generate_subject_data_dicts(self,manifest_filename):
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
            A list of subject data dictionaries generated from the provided manifest CSV

        Notes
        -----
            These subject data dictionaries contain both data, the images of our flipbooks, and metadata such as the
            RA and DEC associated with the center of these images. We could potentially include more metadata if we
            think it would be useful.
        """

        manifest_file = open(manifest_filename)
        manifest = csv.reader(manifest_file)
        count = 0
        subject_data_dicts = []
        for row in manifest:
            count = count + 1
            if(count != 1):
                subject_data_dict = {}
                for i in range(len(self.manifest_header)):
                    key = self.manifest_header[i]
                    data = row[i]
                    subject_data_dict[key] = data
                subject_data_dicts.append(subject_data_dict)
        return subject_data_dicts

    def generate_subjects_from_subject_data_dicts(self,subject_data_dicts):
        """
        Generates a list of subjects from a list of subject data dictionaries.

        Parameters
        ----------
            subject_data_dicts : str
                A full path filename of the manifest CSV to be overwritten or created.

        Returns
        -------
        subjects : List of SubjectSet objects
            A list of newly created SubjectSet objects which are not associated with any SubjectSet object

        Notes
        -----

        """

        subjects = []
        metadata_dict = {}
        for subject_data_dict in subject_data_dicts:
            subject = Subject()
            subject.links.project = self.linked_project
            for key in subject_data_dict:
                split_index = 1
                left_side_of_key = key[:split_index]
                right_side_of_key = key[split_index:]
                if(left_side_of_key == "f"):
                    try:
                        int(right_side_of_key)
                        subject.add_location(subject_data_dict[key])
                    except:
                        pass
                else:
                    metadata_dict[key] = subject_data_dict[key]

            subject.metadata.update(metadata_dict)
            subject.save()
            subjects.append(subject)
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
        subject_set.add(subjects)
        subject_set.save()
        
    def publish_existing_manifest(self,subject_set,manifest_filename):
        
        
        subject_data_dicts = self.generate_subject_data_dicts(manifest_filename)
        subjects = self.generate_subjects_from_subject_data_dicts(subject_data_dicts)
        self.fill_subject_set(subject_set, subjects)

    def upload_data_to_subject_set(self,subject_set, manifest_filename,dataset_filename, overwrite_automatically = None):
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

        Notes
        -----

        """

        self.generate_manifest(manifest_filename, dataset_filename, overwrite_automatically)
        subject_data_dicts = self.generate_subject_data_dicts(manifest_filename)
        subjects = self.generate_subjects_from_subject_data_dicts(subject_data_dicts)
        self.fill_subject_set(subject_set, subjects)
        print("Subjects Uploaded")