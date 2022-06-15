# -*- coding: utf-8 -*-
"""
Created on Friday, June 3rd
Refactored on Tuesday, June 7th

@authors: Noah Schapera, Austin Humphreys
"""

import csv
from copy import copy
from panoptes_client import Panoptes, Project, SubjectSet, Subject
from Manifest import Manifest, Defined_Manifest
from Dataset import Dataset, Zooniverse_Dataset, CN_Dataset

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

    def __init__(self, project_identifier, login, display_printouts = False):

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

        Notes
        -----
            The slug identifier only can work if the owner of the project is the one who is logging in
            since the owner's name is a part of the slug.

            A Zooniverse slug is of the form: "owner_username/project-name-with-dashes-for-spaces".

        """

        Panoptes.connect(username=login.username, password=login.password)

        if(isinstance(project_identifier,str)):
            project_slug = login.username + "/" + project_identifier.replace(" ", "-")
            self.linked_project = Project.find(slug=project_slug)
        elif(isinstance(project_identifier,int)):
            self.linked_project = Project.find(id=project_identifier)
        else:
            raise ProjectIdentificationError(project_identifier)

        self.manifest = None
        self.display_printouts = display_printouts

        if(self.display_printouts):
            print(f"Project ID: {self.linked_project.id}")
            print(f"Project Slug: {self.linked_project.slug}")

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
                    if(self.display_printouts):
                        print("Subject set retrieved from Zooniverse.")
                    return subject_set
            raise SubjectSetRetrievalError(subject_set_identifier)

        elif (isinstance(subject_set_identifier, int)):
            # subject_set_identifier is the subject set's id number in the linked project
            for subject_set in self.linked_project.links.subject_sets:
                subject_set.reload()
                if (int(subject_set.id) == subject_set_identifier):
                    if(self.display_printouts):
                        print("Subject set retrieved from Zooniverse.")
                    return subject_set
            raise SubjectSetRetrievalError(subject_set_identifier)
        else:
            raise SubjectSetIdentificationError(subject_set_identifier)

    def generate_manifest(self, manifest_filename, dataset_filename, overwrite_automatically = None, enable_strict_manifest = True):
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

        dataset = CN_Dataset(dataset_filename,self.display_printouts)
        if(enable_strict_manifest):
            self.manifest = Defined_Manifest(dataset, manifest_filename, overwrite_automatically,display_printouts=self.display_printouts)
        else:
            self.manifest = Manifest(dataset, manifest_filename, overwrite_automatically,display_printouts=self.display_printouts)

        if(self.display_printouts):
            print("Manifest created.")

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

        if(self.display_printouts):
            print("Subjects generated.")

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

        if(self.display_printouts):
            print("Subject set filled.")
        
    def publish_existing_manifest(self,subject_set,manifest_filename):
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

        if(self.display_printouts):
            print("The existing manifest subjects have been published to Zooniverse.")

    def upload_data_to_subject_set(self,subject_set, manifest_filename,dataset_filename, overwrite_automatically = None, enable_strict_manifest = True):
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
        subject_data_dicts = self.generate_subject_data_dicts(manifest_filename)
        subjects = self.generate_subjects_from_subject_data_dicts(subject_data_dicts)
        self.fill_subject_set(subject_set, subjects)
        self.manifest = None

        if(self.display_printouts):
            print("Subjects uploaded to Zooniverse.")