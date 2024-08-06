import getpass
import os
import pickle
from copy import copy
from typing import Iterable

import requests
from panoptes_client import Panoptes, Project, SubjectSet, Subject, User, ProjectRole
from panoptes_client.panoptes import PanoptesAPIException

from unWISE_verse.Login import Login

client = Panoptes()

# TODO: If you provide one of the formatted inputs as a keyword, it breaks it the accessing. Fix this.
# TODO: Need to create a UI-integrated version of Spout

def checkLogin(func):
    def wrapper(*args, **kwargs):
        if not client.logged_in:
            try:
                raise Exception(f"You must be logged in to Zooniverse via unWISE-verse.Spout to use '{func.__name__}'.")
            except AttributeError:
                print(f"You must be logged in to Zooniverse via unWISE-verse.Spout to use the function '{func.__func__.__name__}'.")
        return func(*args, **kwargs)
    return wrapper

def formatProjectInput(func):
    def wrapper(*args, **kwargs):
        args = list(args)
        args[1] = Spout.findProject(args[1])
        args = tuple(args)
        return func(*args, **kwargs)
    return wrapper

def formatSubjectSetInput(func):
    def wrapper(*args, **kwargs):
        args = list(args)
        args[1] = Spout.findSubjectSet(args[1])
        args = tuple(args)
        return func(*args, **kwargs)
    return wrapper

def formatSubjectInput(func):
    def wrapper(*args, **kwargs):
        args = list(args)
        args[1] = Spout.findSubject(args[1])
        args = tuple(args)
        return func(*args, **kwargs)
    return wrapper

def formatSubjectsInput(func):
    def wrapper(*args, **kwargs):
        args = list(args)
        args[1] = Spout.findSubjects(args[1])
        args = tuple(args)
        return func(*args, **kwargs)
    return wrapper

class Spout:

    def __init__(self, login: Login = None, display_printouts=False, progress_callback=None, termination_event=None):
        """
        Initializes a Spout object, a data pipeline between local files and any accessible Zooniverse project.
        This logs into Zooniverse as a particular user and links this Spout object to a specific Zooniverse project
        (that the user has valid access to) via the project_identifier.

        Parameters
        ----------
            login : Login object, optional
                A login object which holds the login details of the user trying to access Zooniverse. Consists of
                a username and a password.
            display_printouts : bool, optional
                Used to determine whether to display progress information in the console.
            progress_callback : function, optional
                A function that takes in a string and displays it to the user. Used to display progress information
                in the console or in a GUI.
            termination_event : threading.Event, optional
                A threading.Event object that can be used to terminate the pipeline. If this is set, the pipeline
                will terminate its current action when the event is set.
        """

        if(login is None):
            self.login = Spout.requestLogin()
        else:
            self.login = login

        if(progress_callback is None):
            if(display_printouts):
                self.progress_callback = lambda x: print(x)
            else:
                self.progress_callback = lambda x: None
        else:
            if(display_printouts):
                self.progress_callback = progress_callback
            else:
                self.progress_callback = lambda x: None

        self.termination_event = termination_event

        self.loginToZooniverse(self.login)

    @staticmethod
    def verifyLogin(login):
        username = login.username
        password = login.password
        if (username == "" or password == ""):
            return False
        try:
            Panoptes.connect(username=username, password=password)
            return True
        except:
            return False

    @staticmethod
    def loginToZooniverse(login):
        """
        Logs into Zooniverse using the login details of the user.

        Parameters
        ----------
            login : Login object, optional
                A login object which holds the login details of the user trying to access Zooniverse.
                Consists of a username and a password. Can be created using the Login.requestLogin() method.
        """

        global client

        try:
            client = Panoptes.connect(username=login.username, password=login.password)
        except PanoptesAPIException:
            login.deleteLoginSave()
            raise Exception("Login to Zooniverse failed. Please try again.")

    @staticmethod
    def requestLogin(filename="login.pickle", save=True):
        if (Login.loginExists(filename)):
            login = Login.load(filename)
            print("Login credentials loaded.")
            return login
        else:
            print("Please enter your Zooniverse credentials.")
            username = getpass.getpass(prompt='Username: ')
            password = getpass.getpass(prompt='Password: ')

            login = Login(username=username, password=password)

            if (save):
                login.save(filename)
                print("Login credentials saved.")

            return login

    @staticmethod
    def requestProjectID(filename="project_id.pickle", save=True):
        if (os.path.exists(filename)):
            with open(filename, 'rb') as projectID_file:
                project_id = pickle.load(projectID_file)
                print(f"Project ID loaded: {project_id}")
                return Spout.formatID(project_id)
        else:
            print("Please enter a Zooniverse project ID.")
            project_id = getpass.getpass(prompt='Project ID: ')

            if (save):
                with open(filename, 'wb') as projectID_file:
                    pickle.dump(project_id, projectID_file)
                print(f"Project ID saved: {project_id}")

            return Spout.formatID(project_id)

    @staticmethod
    def requestSubjectSetID(filename="subject_set_id.pickle", save=True):
        if (os.path.exists(filename)):
            with open(filename, 'rb') as subjectSetID_file:
                subject_set_id = pickle.load(subjectSetID_file)
                print(f"Subject Set ID loaded: {subject_set_id}")
                return Spout.formatID(subject_set_id)
        else:
            print("Please enter a Zooniverse subject set ID.")
            subject_set_id = getpass.getpass(prompt='Subject Set ID: ')

            if (save):
                with open(filename, 'wb') as subjectSetID_file:
                    pickle.dump(subject_set_id, subjectSetID_file)
                print(f"Subject Set ID saved: {subject_set_id}")

            return Spout.formatID(subject_set_id)

    @staticmethod
    def requestZooniverseIDs(filenames=None, save=True):
        if (filenames is not None):
            if (not isinstance(filenames, list)):
                raise TypeError("Filenames must be a list of strings.")

            if (len(filenames) == 0):
                raise ValueError("No filenames provided.")
            elif (len(filenames) != 2):
                raise ValueError("Filenames must be a list of two strings: [project_id_filename, subject_set_id_filename]")
        else:
            filenames = ["project_id.pickle", "subject_set_id.pickle"]

        project_id_filename = filenames[0]
        subject_set_id_filename = filenames[1]
        project_id = Spout.requestProjectID(filename=project_id_filename, save=save)
        subject_set_id = Spout.requestSubjectSetID(filename=subject_set_id_filename, save=save)

        return project_id, subject_set_id

    @classmethod
    def formatID(cls, id):
        try:
            id = int(id)
            return id
        except ValueError:
            raise ValueError(f"Invalid Zooniverse ID {id}. ID must be an integer or a string that can be converted to an integer.")

    @classmethod
    @checkLogin
    def findProject(cls, project_id):
        if (isinstance(project_id, Project)):
            return project_id

        project_id = Spout.formatID(project_id)

        try:
            return Project.find(project_id)
        except PanoptesAPIException:
            raise PanoptesAPIException(f"Project with ID {project_id} does not exist or you do not have access to it.")

    @classmethod
    @checkLogin
    def findProjectRole(cls, project_role_id):
        if (isinstance(project_role_id, ProjectRole)):
            return project_role_id

        project_role_id = Spout.formatID(project_role_id)

        try:
            return ProjectRole.find(project_role_id)
        except PanoptesAPIException:
            raise PanoptesAPIException(f"Project role with ID {project_role_id} does not exist or you do not have access to it.")

    @classmethod
    @checkLogin
    def findSubjectSet(cls, subject_set_id):
        if (isinstance(subject_set_id, SubjectSet)):
            return subject_set_id

        subject_set_id = Spout.formatID(subject_set_id)

        try:
            return SubjectSet.find(subject_set_id)
        except PanoptesAPIException:
            raise PanoptesAPIException(f"Subject set with ID {subject_set_id} does not exist or you do not have access to it.")

    @classmethod
    @checkLogin
    def findSubject(cls, subject_id):
        if (isinstance(subject_id, Subject)):
            return subject_id

        subject_id = Spout.formatID(subject_id)
        try:
            return Subject.find(subject_id)
        except PanoptesAPIException:
            raise PanoptesAPIException(f"Subject with ID {subject_id} does not exist or you do not have access to it.")

    @classmethod
    @checkLogin
    def findSubjects(cls, subject_ids):
        if (isinstance(subject_ids, Subject)):
            return [subject_ids]
        elif (isinstance(subject_ids, int) or isinstance(subject_ids, str)):
            return [cls.findSubject(subject_ids)]

        subjects = []

        if(not isinstance(subject_ids, Iterable)):
            raise TypeError(f"Subject IDs must be an iterable of integers, strings, or Subject objects not {type(subject_ids)}.")

        for subject_id in subject_ids:
            subjects.append(cls.findSubject(subject_id))
        return subjects

    @formatProjectInput
    def createSubjectSet(self, project, display_name):
        """
        Create a subject set in the project.

        Parameters
        ----------
            project : Project object, int, or str
                A Project object, or a string or integer representing the ID of a project on Zooniverse.
            display_name : str
                A string representing the display name associated with this subject set.

        Returns
        -------
        subject_set : SubjectSet object
            A newly created SubjectSet object associated to the linked project on Zooniverse.
        """

        subject_set = SubjectSet()
        subject_set.links.project = project
        subject_set.display_name = copy(display_name)
        subject_set.save()
        return subject_set

    @checkLogin
    def projectExists(self, project_identifier):
        """
        Determine if a project exists on Zooniverse.

        Parameters
        ----------
            project_identifier : int or str
                An integer or string representing the ID of a project on Zooniverse.

        Returns
        -------
         True/False: bool
            A boolean output of whether the project exists on Zooniverse.
        """
        try:
            project_identifier = Spout.formatID(project_identifier)
        except ValueError:
            return False

        try:
            project = Project.find(project_identifier)

            if(project is None):
                return False
            else:
                self.progress_callback(f"Project '{project.display_name}' was found with ID {project.id}.")

            return True
        except PanoptesAPIException:
            return False

    @checkLogin
    def subjectSetExists(self, subject_set_identifier):
        """
        Determine if a subject set exists on Zooniverse.

        Parameters
        ----------
            subject_set_identifier : int or str
                An integer or string representing the ID of a subject set on Zooniverse.

        Returns
        -------
         True/False: bool
            A boolean output of whether the subject set exists on Zooniverse.
        """

        try:
            subject_set_identifier = Spout.formatID(subject_set_identifier)
        except ValueError:
            return False

        try:
            subject_set = SubjectSet.find(subject_set_identifier)

            if(subject_set is None):
                return False
            else:
                self.progress_callback(f"Subject set '{subject_set.display_name}' was found with ID {subject_set.id}.")

            return True
        except PanoptesAPIException:
            return False

    @checkLogin
    def subjectExists(self, subject_identifier):
        """
        Determine if a subject exists on Zooniverse.

        Parameters
        ----------
            subject_identifier : int or str
                An integer or string representing the ID of a subject on Zooniverse.

        Returns
        -------
         True/False: bool
            A boolean output of whether the subject exists on Zooniverse.
        """

        try:
            subject = Subject.find(subject_identifier)
            return True
        except PanoptesAPIException:
            return False

    def generateSubjects(self, manifest_filename):
        """
        Generates a list of subjects from a list of subjects from a Zooniverse manifest file.

        Parameters
        ----------
            manifest_filename : str
                A string representing the filename of the Zooniverse manifest file.

        Returns
        -------
        subjects : list
            A list of Subject objects generated from the manifest file.
        project : Project object
            A Project object that the subjects will be associated with.

        Notes
        -----
            This function is used to generate a list of Subject objects from a Zooniverse manifest file. The manifest
            file is a CSV file that contains information about each subject in the subject set.
        """

        from Dataset import ZooniverseDataset

        zooniverse_dataset = ZooniverseDataset(manifest_filename)

        subject_dictionaries = zooniverse_dataset.getDictionaries()
        subjects = []
        subject_total = len(subject_dictionaries)
        for subject_dictionary in subject_dictionaries:
            data_dictionary = subject_dictionary["data"]
            metadata_dictionary = subject_dictionary["metadata"]
            subject = Subject()
            for data_key in data_dictionary:
                if(os.path.exists(data_dictionary[data_key])):
                    subject.add_location(data_dictionary[data_key])
                else:
                    if(data_dictionary[data_key] != ""):
                        self.progress_callback(f"Could not complete subject upload. The image file requested at {data_dictionary[data_key]} does not exist.")
                        self.termination_event.set()

            subject.metadata.update(metadata_dictionary)
            subjects.append(subject)

            try:
                self.progress_callback(f"Create Subjects: {len(subjects)}/{subject_total}", level=10)
            except:
                pass

            self.progress_callback(f"Created subject {len(subjects)} out of {subject_total}.")

        self.progress_callback("Subjects generated.")

        return subjects

    @checkLogin
    def updateSubjects(self, subjects, project):
        """
        Updates the subject's metadata to include an ID field with their Zooniverse ID and associates them with a project for uploading purposes.

        Parameters
        ----------
            subjects : list
                A list of Subject objects that will be given their IDs.
        """

        total_subjects = len(subjects)

        try:
            index = 0
            for subject in subjects:
                subject.links.project = project
                subject.reload()
                subject.save()
                subject.reload()
                subject.metadata.update({"ID": subject.id})
                subject.save()
                subject.reload()
                try:
                    self.progress_callback(f"Update Subjects: {index+1}/{total_subjects}", level=10)
                except:
                    pass

                self.progress_callback(f"Updated Subject {index + 1} out of {total_subjects}")

                index += 1
        except PanoptesAPIException as e:
            self.progress_callback(f"Error updating subjects: {e}")
            return False

        self.progress_callback("Subjects updated.")
        return True

    @checkLogin
    def uploadSubjects(self, subject_set, subjects):
        """
        Uploads a list of subjects to a subject set on Zooniverse.

        Parameters
        ----------
            subject_set : SubjectSet object, int, or str
                A SubjectSet object, or a string or integer representing the ID of a subject set on Zooniverse.
            subjects : list
                A list of Subject objects to be uploaded to the subject set or a list of subject IDs.

        Returns
        -------
        bool
            True if the subjects were successfully uploaded, False otherwise.
        """

        subject_set = self.findSubjectSet(subject_set)
        subjects = self.findSubjects(subjects)

        chunk_size = 1000
        total_subjects = len(subjects)

        for i in range(0, len(subjects), chunk_size):
            subject_set.reload()
            chunk_subjects = subjects[i:i+chunk_size]
            subject_set.add(chunk_subjects)
            self.progress_callback(f"Added subjects " + str(i+1) + " through " + str(i+len(chunk_subjects)) + " to the subject set.")
            try:
                self.progress_callback(f"Upload Subjects: {i+len(chunk_subjects)}/{total_subjects}", level=10)
            except:
                pass
            subject_set.save()

        self.progress_callback("Subject set filled.")

        return True

    @formatSubjectSetInput
    def publishManifest(self, subject_set, manifest_filename):
        """
        Publishes a manifest file to a subject set in Zooniverse.

        Parameters
        ----------
            subject_set : SubjectSet object, subject set ID, or display name of the subject set (if it is a subject set of the linked project)
                The subject set that the subjects will be uploaded to.
            manifest_filename : str
                A string representing the filename of the Zooniverse manifest file.
        """

        subjects = self.generateSubjects(manifest_filename)

        success = self.uploadSubjects(subject_set, subjects)

        if(success):
            self.progress_callback("Manifest subjects have been published to Zooniverse.")

    @checkLogin
    def removeSubjects(self, subject_set, subjects=None, override_verification=False):
        """
        Removes a list of subjects from a subject set on Zooniverse.

        Parameters
        ----------
            subject_set : SubjectSet object
                A SubjectSet object that the subjects will be removed from.
            subjects : Subject object or list of Subject objects, optional
               A subject object or list of subject objects that will be removed from the subject set.
            override_verification : bool, optional
                If False, the function will ask for user verification before removing the subjects.

        Notes
        -----
            If subjects is None, then all subjects will be removed from the subject set.
            Removing subjects from a subject set does not delete the subjects from Zooniverse. It only removes them
            from the subject set and will leave them as orphaned subjects.
        """

        subject_set = self.findSubjectSet(subject_set)

        full_wipe = False

        if(subjects is not None):
            if(not isinstance(subjects, list)):
                if(isinstance(subjects, Subject)):
                    subjects = [subjects]
                else:
                    raise TypeError("subjects must be a list of Subject objects or IDs")
        else:
            full_wipe = True
            subjects = subject_set.subjects

        subjects = self.findSubjects(subjects)

        chunk_size = 1000

        total_subjects = len(subjects)

        if(not override_verification):
            print("This will remove all provided subjects from Zooniverse and cannot be undone. Are you sure you want to continue? (Yes or No)")
            answer = input()

            if (answer.lower() == "yes"):

                for i in range(0, total_subjects, chunk_size):
                    subject_set.reload()
                    chunk_subjects = subjects[i:i + chunk_size]
                    subject_set.remove(chunk_subjects)
                    subject_set.save()

                if (full_wipe):
                    self.progress_callback("All subjects removed from subject set.")
                else:
                    self.progress_callback("Specified subjects removed from subject set.")

            elif (answer.lower() == "no"):
                print("Cancelling deletion.")
                return None
            else:
                print("Invalid response. Cancelling removal.")
                return None
        else:

            for i in range(0, total_subjects, chunk_size):
                subject_set.reload()
                chunk_subjects = subjects[i:i + chunk_size]
                subject_set.remove(chunk_subjects)
                subject_set.save()

                try:
                    self.progress_callback(f"Remove Subjects: {i+1}/{total_subjects}", level=10)
                except:
                    pass

            if (full_wipe):
                self.progress_callback("All subjects removed from subject set.")
            else:
                self.progress_callback("Specified subjects removed from subject set.")

    @formatSubjectsInput
    def deleteSubjects(self, subjects, override_verification=False):
        """
        Deletes a list of subjects from Zooniverse.

        Parameters
        ----------
            subjects : Subject object or list of Subject objects
               A subject object or list of subject objects that will be deleted from Zooniverse.
            override_verification : bool, optional
                If False, the function will ask for user verification before deleting the subjects.

        Notes
        -----
            Deleting subjects from Zooniverse will remove them from all subject sets and will delete them from the
            Zooniverse database.
        """

        subjects = self.findSubjects(subjects)

        total_subjects = len(subjects)

        if(not override_verification):

            print("This will delete all provided subjects from Zooniverse and cannot be undone. Are you sure you want to continue? (Yes or No)")
            answer = input()

            if (answer.lower() == "yes"):

                for i in range(total_subjects):
                    subjects[i].delete()

                self.progress_callback("Subjects deleted from Zooniverse.")
            elif (answer.lower() == "no"):
                print("Cancelling deletion.")
                return None
            else:
                print("Invalid response. Cancelling removal.")
                return None

        else:

            for i in range(total_subjects):
                subjects[i].delete()

                try:
                    self.progress_callback(f"Delete Subjects: {i+1}/{total_subjects}", level=10)
                except:
                    pass

            self.progress_callback("Subjects deleted from Zooniverse.")

    @formatSubjectsInput
    def modifySubjectMetadataFieldName(self, subjects, current_field_names, new_field_names):
        """
        Modifies the metadata field of the subjects in the subject set.

        Parameters
        ----------
        subjects : List of Subject objects
            A list of Subject objects to be modified or a list of subject IDs to be modified.
        current_field_names : list of str
            The name of the metadata field to be modified.
        new_field_names : list of str
            The new name of the metadata field to be modified.
        """

        if (not isinstance(current_field_names, list)):
            if(isinstance(current_field_names, str)):
                current_field_names = [current_field_names]
            else:
                raise TypeError("current_field_names must be a list of strings.")

        if (not isinstance(new_field_names, list)):
            if(isinstance(new_field_names, str)):
                new_field_names = [new_field_names]
            else:
                raise TypeError("new_field_names must be a list of strings.")

        if(len(current_field_names) != len(new_field_names)):
            raise ValueError("current_field_names and new_field_names must be the same length.")

        total_subjects = len(subjects)
        count = 1
        for subject in subjects:
            subject.reload()
            modified = False
            for i, current_field_name in enumerate(current_field_names):
                try:
                    subject.metadata[new_field_names[i]] = subject.metadata[current_field_name]
                    del subject.metadata[current_field_name]
                    modified = True
                except KeyError:
                    self.progress_callback(f" The field name, {current_field_name}, does not exist in the metadata of subject {subject.id}.")
            if(modified):
                subject.save()
            try:
                self.progress_callback(f"Modify Field Name: {count}/{total_subjects}", level=10)
            except:
                pass
            count += 1
        self.progress_callback("Specified subjects were modified.")

    @formatSubjectsInput
    def modifySubjectMetadataFieldValue(self, subjects, field_names, new_field_values):
        """
        Modifies the metadata field value of the subjects in the subject set.

        Parameters
        ----------
        subjects : List of Subject objects or List of int or str
            A list of Subject objects to be modified or a list of subject IDs to be modified.
        field_names : list of str
            The name of the metadata fields to be modified.
        new_field_values : list of objects
            The new values of the metadata fields to be modified.
        """
        valid_new_fieldnames = []
        valid_new_field_values = []

        if(len(field_names) != len(new_field_values)):
            raise ValueError("field_names and new_field_values must be the same length.")

        for i, new_field_value in enumerate(new_field_values):
            if (not isinstance(new_field_value, str)):
                try:
                    str(new_field_value)
                    valid_new_fieldnames.append(field_names[i])
                    valid_new_field_values.append(new_field_values[i])
                except:
                    self.progress_callback(f"The new field value for field, {field_names[i]},could not be converted to a string.")
            else:
                valid_new_fieldnames.append(field_names[i])
                valid_new_field_values.append(new_field_values[i])

        for subject in subjects:
            subject.reload()
            modified = False
            for i, field_name in enumerate(valid_new_fieldnames):
                try:
                    subject.metadata[field_name] = valid_new_field_values[i]
                    modified = True
                except KeyError:
                    self.progress_callback(f"Specified subject {subject.id} was not modified. The current field name, {field_name}, does not exist.")
            if(modified):
                subject.save()
        self.progress_callback("Specified subjects were modified.")

    @formatSubjectInput
    def subjectHasImages(self, subject):
        """
        Checks if the subject has images.

        Parameters
        ----------
        subject : Subject object or subject ID
            A Subject object to be checked or a subject ID to be checked.

        Returns
        -------
        bool
            True if the subject has images, False otherwise.
        """

        return len(subject.raw['locations']) != 0

    @formatSubjectInput
    def getSubjectImages(self, subject, directory=None):
        """
        Gets the images of the subject from the Zooniverse server.

        Parameters
        ----------
        subject : Subject object or subject ID
            A Subject object to get the images from or a subject ID to get the images from.
        directory : str
            A string representing the directory where the images will be saved.

        Returns
        -------
        List of str
            A list of strings representing the image filepaths of the subject.
        """

        if(directory is None):
            directory = os.getcwd()

        subject = self.findSubject(subject)
        subject.reload()

        image_filepaths = []
        for i, location in enumerate(subject.raw['locations']):
            image_filename = f"{subject.id}_image_{i}.jpg"
            image_filepaths.append(self.downloadFromLocation(location, directory, image_filename))

        return image_filepaths

    @staticmethod
    def downloadFromLocation(location, directory=None, filename=None):
        """
        Downloads a file from a location on the Zooniverse server.

        Parameters
        ----------
        location : str
            A string representing the location of the file on the Zooniverse server.
        directory : str
            A string representing the directory where the file will be saved.

        Returns
        -------
        str
            A string representing the filepath of the downloaded file.
        """

        if(directory is None):
            directory = os.getcwd()

        if(filename is None):
            filename = os.path.basename(location["image/png"])

        filepath = os.path.join(directory, filename)

        # Make a request to download the file from the location on the Zooniverse server using requests
        response = requests.get(location["image/png"])

        with open(filepath, 'wb') as file:
            file.write(response.content)

        return filepath


    @formatSubjectInput
    def subjectHasMetadata(self, subject):
        """
        Checks if the subject has metadata.

        Parameters
        ----------
        subject : Subject object or subject ID
            A Subject object to be checked or a subject ID to be checked.

        Returns
        -------
        bool
            True if the subject has metadata, False otherwise.
        """

        return subject.metadata != {}

    @checkLogin
    def getSubjectsFromProject(self, project, subject_set=None, only_orphans=False):
        """
        Gets all subjects from the specified project.

        Parameters
        ----------
        project : Project object, int, or str
            A Project object from Zooniverse. Can also be the ID of the project as an int or str.
        subject_set : SubjectSet object, int, or str
            A SubjectSet object associated to the project on Zooniverse. Can also be the ID of the subject set as an int or str.
        only_orphans : bool
            If True, only subjects that are not in any subject set will be returned. If False, all subjects from the project will be returned.

        Returns
        -------
        List of Subject objects
            A list of Subject objects from the specified project.
        """

        subject_list = []

        if (subject_set is not None and only_orphans):
            raise Exception("You cannot specify a subject set ID and have only_orphans as True at the same time.")

        project = self.findProject(project)
        project.reload()
        project_id = project.id

        # Get the total number of subjects in the project, either from the specified subject set or from the project itself.
        if(subject_set is not None):
            subject_set = self.findSubjectSet(subject_set)

            if(subject_set.links.project.id != project_id):
                raise Exception("The specified subject set is not associated with the specified project.")

            subject_set_id = subject_set.id
            total_subjects = Subject.where(project_id=project_id, subject_set_id=subject_set_id).meta["count"]
        else:
            total_subjects = Subject.where(project_id=project_id).meta["count"]
            subject_set_id = None

        if(not only_orphans):
            self.progress_callback(f"Getting {total_subjects} subjects from project {project_id}...")
        else:
            self.progress_callback(f"Getting orphan subjects from project {project_id}...")

        self.progress_callback("Collecting subjects from Zooniverse...")

        count = 1
        for sms in Subject.where(project_id=project_id, subject_set_id=subject_set_id):
            if (only_orphans):
                if (len(sms.raw["links"]["subject_sets"]) == 0):
                    subject_list.append(sms)
            else:
                subject_list.append(sms)
            try:
                self.progress_callback(f"Collect Subjects: {count}/{total_subjects}", level=10)
            except:
                pass
            count += 1

        self.progress_callback("Subjects collected from Zooniverse.")

        return subject_list

    @formatSubjectSetInput
    def getSubjectsFromSubjectSet(self, subject_set):
        """
        Gets all subjects from the specified subject set.

        Parameters
        ----------
        subject_set : SubjectSet object, int, or str
            A SubjectSet object associated to a project on Zooniverse. Can also be the ID of the subject set as an int or str.

        Returns
        -------
        List of Subject objects
            A list of Subject objects from the specified project.
        """

        subject_list = []

        subject_set = self.findSubjectSet(subject_set)
        subject_set_id = subject_set.id

        for sms in Subject.where(subject_set_id=subject_set_id):
            subject_list.append(sms)

        return subject_list

    @formatProjectInput
    def getSubjectSetsFromProject(self, project):
        """
        Gets all subject sets from the specified project.

        Parameters
        ----------
        project : Project object, int, or str
            A Project object from Zooniverse. Can also be the ID of the project as an int or str.

        Returns
        -------
        List of SubjectSet objects
            A list of SubjectSet objects from the specified project.
        """

        subject_set_list = []

        project = self.findProject(project)
        project_id = project.id

        for sms in SubjectSet.where(project_id=project_id):
            subject_set_list.append(sms)

        return subject_set_list

    @formatSubjectSetInput
    def getProjectFromSubjectSet(self, subject_set):
        """
        Gets the project associated with the specified subject set.

        Parameters
        ----------
        subject_set : SubjectSet object, int, or str
            A SubjectSet object associated to a project on Zooniverse. Can also be the ID of the subject set as an int or str.

        Returns
        -------
        Project object
            A Project object associated with the specified subject set.
        """

        subject_set = self.findSubjectSet(subject_set)
        subject_set.reload()

        return subject_set.links.project

    @formatSubjectInput
    def getProjectFromSubject(self, subject):
        """
        Gets the project associated with the specified subject.

        Parameters
        ----------
        subject : Subject object or int
            A Subject object from Zooniverse. Can also be the ID of the subject as an int.

        Returns
        -------
        Project object
            A Project object associated with the specified subject.
        """

        subject = self.findSubject(subject)
        subject.reload()

        return subject.links.project

    @checkLogin
    def getUser(self, user_identifier):
        """
        Gets a user from Zooniverse.

        Parameters
        ----------
        user_identifier : str
            The username or id of the user to be retrieved.

        Returns
        -------
        User object
            A User object from Zooniverse.
        """

        if(isinstance(user_identifier, User)):
            return user_identifier

        try:
            user_identifier = int(user_identifier)
        except ValueError:
            pass

        if (isinstance(user_identifier, str)):
            for user in User.where(login=user_identifier):
                return user
        elif (isinstance(user_identifier, int)):
            for user in User.where(id=user_identifier):
                return user
        else:
            raise Exception("Invalid user identifier. Must be a string or an int.")

        self.progress_callback(f"Warning: User {user_identifier} does not exist or is inaccessible to the current user. Returning None.")

    @checkLogin
    def userHasProjectAccess(self, user, project):
        """
        Checks if a user has access to a project.

        Parameters
        ----------
        user : User object, str, or int
            A User object from Zooniverse or the username of the user.
        project : Project object, int, or str
            A Project object from Zooniverse or the ID of the project.

        Returns
        -------
        bool
            True if the user has access to the project, False otherwise.
        """

        user = self.getUser(user)
        project = self.findProject(project)

        if(user.raw['display_name'] == project.raw['links']['owner']['display_name']):
            return True

        for project_role_id in project.raw['links']['project_roles']:
            project_role = self.findProjectRole(project_role_id)
            if(project_role.raw['links']['owner']['id'] == user.id):
                return True

        return False






