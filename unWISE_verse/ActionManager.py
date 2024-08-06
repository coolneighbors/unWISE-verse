import csv
import io
import logging
import multiprocessing
import os.path
import platform
import threading
from pathlib import Path
from time import sleep
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from PIL import Image
from tqdm import tqdm

from unWISE_verse.Data import Data
from unWISE_verse.Dataset import get_available_astronomy_datasets, AstronomyDataset
from unWISE_verse.Spout import Spout
import tkinter as tk

global action_index
action_index = 0

class ActionManager:
    def __init__(self, UI):
        # Find all the subclasses of Action
        action_dict = {}
        action_subclasses = Action.__subclasses__()
        action_subclasses = [action_class for action_class in action_subclasses if action_class not in [CompositeAction, StagedAction]]
        # Add all the subclasses of CompositeAction
        composite_action_subclasses = CompositeAction.__subclasses__()
        action_subclasses.extend(composite_action_subclasses)

        # Add all the subclasses of StagedAction
        staged_action_subclasses = StagedAction.__subclasses__()
        action_subclasses.extend(staged_action_subclasses)

        for action_subclass in action_subclasses:
            action = action_subclass(UI)
            action_dict[action.name] = action

        self.UI = UI
        self.action_monitor = ActionMonitor(UI)
        self.action_dict = action_dict
        self.current_action = None
        self.active = False
        self.staged_action = False
        self.warning_flags = {}

        mutable_columns = getAllMutableColumns()
        self.attribute_column_association_dict = getAssociatedUIAttributeDict(UI, mutable_columns)

    def display(self, text, level=logging.INFO):
        self.action_monitor.display(text, level)

    def execute(self, action_name, *args, **kwargs):
        if(self.current_action is None):
            self.active = True
            action = self.action_dict[action_name]
            if(issubclass(type(action), StagedAction)):
                self.staged_action = True
            action.execute(*args, **kwargs)
            self.active = False
            self.staged_action = False

    def perform(self, *args, **kwargs):
        if(not self.active):
            self.warning_flags = {}

            if (self.getActionState() == ''):
                flag_dict = {1: 'Please select a program action.'}
                self.addWarningFlags(flag_dict)

            self.UI.termination_event = multiprocessing.Event()
            current_action_state = self.UI.action_state.get()
            try:
                action = self.action_dict[current_action_state]
            except KeyError:
                self.display(f"Error: Action '{current_action_state}' not found.")
                return
            action_warning_flags = action.verifyInputs()
            self.addWarningFlags(action_warning_flags)
            if(len(self.warning_flags) > 0):
                self.display("Warning: Please resolve the following issues before continuing.")
                for flag_message in self.warning_flags.values():
                    self.display(f"- {flag_message}")
            else:
                global action_index

                if(isinstance(action, StagedAction)):

                    # Create a thread which will update the progress bar as each stage is completed
                    stage_names = action.stage_names
                    def updateProgressBar(termination_event):
                        # Set the initial stage
                        global action_index
                        action_index += 1
                        self.UI.action_state.set(stage_names[0])
                        self.display(f"Action Index:{action_index}", level=self.UI.logger.level_values.get("DEBUG"))
                        self.action_monitor.progress_bar.initializeProgressBar(stage_names[0])

                        last_stage_name = stage_names[-1]

                        for stage_name in stage_names:
                            # Determine if a new action is being executed
                            while(self.UI.action_state.get() == stage_name):
                                if(termination_event.is_set()):
                                    return

                            next_stage_name = self.UI.action_state.get()
                            self.action_monitor.progress_bar.progress_bar = None
                            self.action_monitor.progress_bar.clear()
                            action_index += 1
                            self.display(f"Action Index:{action_index}", level=self.UI.logger.level_values.get("DEBUG"))
                            self.action_monitor.progress_bar.initializeProgressBar(next_stage_name)

                    progress_bar_termination_event = multiprocessing.Event()
                    stage_progress_thread = threading.Thread(target=updateProgressBar, args=(progress_bar_termination_event,))
                    stage_progress_thread.start()
                    self.execute(current_action_state, *args, **kwargs)

                    # Wait for the thread to finish
                    progress_bar_termination_event.set()
                    stage_progress_thread.join()
                    action_index += 1
                    self.action_monitor.progress_bar.progress_bar = None
                    self.action_monitor.progress_bar.clear()
                else:
                    self.action_monitor.display(f"Action Index:{action_index}", level=self.UI.logger.level_values.get("DEBUG"))
                    self.action_monitor.progress_bar.initializeProgressBar(action.name)
                    self.execute(action.name, *args, **kwargs)
                    action_index += 1
                    self.action_monitor.progress_bar.progress_bar = None
                    self.action_monitor.progress_bar.clear()
        else:
            self.display("Process is already active. Please wait until it is finished.")

    def setActionState(self, action_name):
        if(self.active and not self.staged_action):
            self.display("Process is already active. Please wait until it is finished.")
        else:
            self.UI.action_state.set(action_name)

    def getActionState(self):
        return str(self.UI.action_state.get())

    def addWarningFlags(self, warning_flags):
        self.warning_flags.update(warning_flags)

class BaseAction:
    def __init__(self, name, function, UI):
        self.name = name
        self.function = function
        self.UI = UI

    def execute(self, *args, **kwargs):
        self.function(*args, **kwargs)

class Action(BaseAction):
    flag_value_master_dictionary = {
        # Flags for missing inputs
        "No program action": (None, "Please select a program action."),
        "No target file": (None, "Please select a target file."),
        "No manifest file": (None, "Please select a manifest file."),
        "No dataset type": (None, "Please select a dataset type."),
        "No PNG directory": (None, "Please enter a PNG directory."),
        "No project ID": (None, "Please enter a project ID."),
        "No subject set ID": (None, "Please enter a subject set ID."),
        "No username": (None, "Please enter a username in the login screen."),
        "No password": (None, "Please enter a password in the login screen."),

        # Flags for missing files
        "Target file not found": (None, "Target file could not found."),
        "Manifest file not found": (None, "Manifest file could not found."),

        # Flags for invalid inputs
        "Invalid PNG directory": (None, "Please provide a valid PNG directory."),
        "Invalid project ID": (None, "Please provide a valid project ID."),
        "Invalid subject set ID": (None, "Please provide a valid subject set ID."),
        "Invalid Zooniverse credentials": (None, "Please provide valid Zooniverse credentials."),

        # Flags for non-empty directories
        "PNG directory is not empty": (None, "PNG directory is not empty."),

        # Flags for Panoptes warnings
        "Project does not exist": (None, "Project does not exist."),
        "Subject Set does not exist": (None, "Subject Set does not exist."),
        "Insufficient user subjects": (None, "The logged in user does not have enough allocated subjects to complete the upload."),
        "Out of subjects": (None, "The subject upload limit has been already reached. Please request for more subjects to be allocated to your account."),
        "User does not have access to project": (None, "The logged in user does not have access to the desired project."),

        # Flags for manipulation action warnings
        "Empty field": (None, "Please enter values for the remaining empty fields."),
        "Invalid field name": (None, "Please enter a valid field name."),
        "No selected subjects": (None, "Please select subjects to modify."),
        "Invalid download directory": (None, "Please provide a valid download directory."),
        "Invalid speed value": (None, "Please enter a speed value which is a number greater than 0."),

        # Flags for classification action warnings
        "No workflow ID": (None, "Please enter a workflow ID."),
        "Invalid workflow ID": (None, "Please enter a valid workflow ID."),
        "Classifications file not found": (None, f"Classifications file could not found. Please download the classifications file from the Zooniverse project and put it in the local 'ClassificationFiles' folder."),
        "Workflows file not found": (None, "Workflows file could not found. Please download the workflows file from the Zooniverse project and put it in the local 'ClassificationFiles' folder."),
    }

    # Assign flag values to each warning message
    current_flag_value = 1
    for key, value in flag_value_master_dictionary.items():
        flag_value = value[0]
        flag_message = value[1]
        flag_value_master_dictionary[key] = (current_flag_value, flag_message)
        current_flag_value += 1

    def __init__(self, UI, name, function, UI_elements=None, disabled=False):

        # Verify that the name is a string
        if not isinstance(name, str):
            raise ValueError("Action name must be a string")

        # Verify that the function is callable
        if not callable(function):
            raise ValueError("Action function must be callable")

        self.UI_elements = UI_elements
        self.disabled = disabled

        super().__init__(name, function, UI)

    def execute(self, *args, **kwargs):
        if(not self.disabled):
            if(self.UI_elements is not None):
                self.disableUIElements()
                super().execute(*args, **kwargs)
                self.enableUIElements()
            else:
                super().execute(*args, **kwargs)
        else:
            self.UI.display(f"Warning: '{self.name}' is disabled. Did not execute.")

    def disableUIElements(self):
        for element in self.UI_elements:
            # Verify that the element is a tkinter widget with a config method
            if not hasattr(element, 'config'):
                raise ValueError(f"UI element, {element}, must have a config method.")
            element.config(state=tk.DISABLED)

    def enableUIElements(self):
        for element in self.UI_elements:
            # Verify that the element is a tkinter widget with a config method
            if not hasattr(element, 'config'):
                raise ValueError(f"UI element, {element}, must have a config method.")
            element.config(state=tk.NORMAL)

    def verifyInputs(self):
        """
        This method must be implemented in each subclass to verify the inputs before executing the action.

        Returns
        -------
        warning_flags : dict
            A dictionary of warning flags for the UI to display to the user. An empty dictionary means that the inputs are valid.

        """

        raise NotImplementedError("verifyInputs method must be implemented in each subclass.")

    def getFlagTupleFromMasterDictionary(self, flag_key):
        """
        Get the flag tuple from the master dictionary.
        Used to keep track of the flag values for each action by providing a descriptive key.

        Parameters
        ----------
        flag_key : str
            The key for the flag value in the master dictionary.


        Returns
        -------
        flag_tuple : tuple
            The flag tuple containing the flag value and flag message.

        """

        return self.flag_value_master_dictionary.get(flag_key, (None, None))

    def assignWarningFlag(self, flag_key):
        """
        Assign a warning flag for the action.

        Parameters
        ----------
        flag_key : str
            The key for the flag value in the master dictionary.

        Returns
        -------
        warning_flag : dict
            A dictionary containing the warning flag for the action.
        """

        flag_value, flag_message = self.getFlagTupleFromMasterDictionary(flag_key)
        if (flag_value is not None):
            warning_flag = {flag_value: flag_message}
            return warning_flag
        else:
            raise ValueError(f"Warning: flag key '{flag_key}' not found in the master dictionary.")

class GenerateManifest(Action):
    name = "Generate Manifest"
    def __init__(self, UI):
        function = self.generateManifest
        UI_elements = [UI.submit_button, UI.metadata_button, UI.pngDirectory_button, UI.pngDirectory_entry, UI.targetFile_button, UI.targetFile_entry, UI.manifest_button, UI.upload_button, UI.full_button, UI.datasetTypeOptionMenu]
        disabled = False

        super().__init__(UI, self.name, function, UI_elements, disabled)

    def generateManifest(self):

        dataset_dict = get_available_astronomy_datasets()
        dataset_type = dataset_dict.get(self.UI.datasetType.get(), None)

        if (dataset_type is None):
            self.UI.display(f"Error: Dataset '{self.UI.datasetType.get()}' not found.")
            return

        metadata_dict = {}

        if (hasattr(dataset_type, 'mutable_columns_dict')):
            mutable_columns = list(dataset_type.mutable_columns_dict.keys())
            UI_metadata_variables_dict = self.UI.action_manager.attribute_column_association_dict
            UI_metadata_private_variables = dataset_type.required_private_columns
            UI_metadata_keys_dict = dataset_type.mutable_columns_keys_dict

            for column in mutable_columns:
                if(column == 'png_directory'):
                    continue
                if (column in UI_metadata_variables_dict):
                    column_key = UI_metadata_keys_dict[column]
                    if (column in UI_metadata_private_variables):
                        column_key = f"{Data.privatization_symbol}{column_key}"

                    UI_attribute = getattr(self.UI, UI_metadata_variables_dict[column])
                    if (isinstance(UI_attribute, tk.Variable)):
                        metadata_dict[column_key] = castVariableValue(UI_attribute.get())
                    else:
                        metadata_dict[column_key] = castVariableValue(UI_attribute)
                else:
                    self.UI.display(f"Error: Metadata variable '{column}' not found.")
                    return

            metadata_dict[f'{Data.privatization_symbol}PNG DIRECTORY'] = self.UI.pngDirectory.get()
        else:
            self.UI.display(f"Error: Dataset '{self.UI.datasetType.get()}' does not have a pre-defined mutable columns list.")
            return

        metadata_target_filename = mergeMetadataAndTargetFile(metadata_dictionary=metadata_dict, target_filename=self.UI.targetFile.get())

        dataset_dict = get_available_astronomy_datasets()

        dataset_type = dataset_dict.get(self.UI.datasetType.get(), None)

        if (dataset_type is None):
            self.UI.display(f"Error: {self.UI.datasetType.get()} is not a valid dataset type.")
            return
        else:
            dataset = dataset_type(metadata_target_filename, self.UI.manifestFile.get(), ignore_incomplete_data=self.UI.ignorePartialCutouts.get(), termination_event=self.UI.termination_event, log_queue=self.UI.logger.log_queue)

    def verifyInputs(self):
        """
        Verify that the metadata and target file are valid before generating the manifest.

        Returns
        -------
        warning_flags : dict
            A dictionary of warning flags for the UI to display to the user. An empty dictionary means that the inputs are valid.
        """

        warning_flags = {}

        # Verify target file
        if (self.UI.targetFile.get() == ''):
            warning_flags.update(self.assignWarningFlag("No target file"))
        if(not os.path.exists(self.UI.targetFile.get()) and self.UI.targetFile.get() != ''):
            warning_flags.update(self.assignWarningFlag("Target file not found"))

        # Verify manifest file
        if(self.UI.manifestFile.get() == ''):
            warning_flags.update(self.assignWarningFlag("No manifest file"))

        # Verify PNG directory
        if(self.UI.pngDirectory.get() == ''):
            warning_flags.update(self.assignWarningFlag("No PNG directory"))
        if(not os.path.exists(self.UI.pngDirectory.get()) and self.UI.pngDirectory.get() != ''):
            try:
                os.mkdir(self.UI.pngDirectory.get())
            except:
                warning_flags.update(self.assignWarningFlag("Invalid PNG directory"))
        if (os.path.isdir(self.UI.pngDirectory.get())):
            # Check if the PNG directory is empty
            save_state_file_exists = False
            files = os.listdir()
            for file in files:
                if (file.endswith('.save_state')):
                    save_state_file_exists = True
                    break

            png_directory_files = os.listdir(self.UI.pngDirectory.get())

            if (platform.system() == "Darwin" and ".DS_Store" in png_directory_files):
                png_directory_files.remove(".DS_Store")

            if (len(png_directory_files) != 0 and not save_state_file_exists):
                warning_flags.update(self.assignWarningFlag("PNG directory is not empty"))

        # Verify dataset type
        if(self.UI.datasetType.get() == ''):
            warning_flags.update(self.assignWarningFlag("No dataset type"))

        # Verify metadata variables
        #

        return warning_flags

class StagedAction(Action):
    def __init__(self, stage_names, function, UI_elements, UI, disabled=False):
        self.stage_names = stage_names

        if (self.name is None):
            raise ValueError("StagedAction must have a name.")

        super().__init__(UI, self.name, function, UI_elements=UI_elements, disabled=disabled)

    def setStage(self, action_name):
        self.UI.action_manager.setActionState(action_name)

    def verifyInputs(self):
        raise NotImplementedError("verifyInputs method must be implemented in each subclass.")

class UploadManifest(StagedAction):
    name = "Upload Manifest"
    def __init__(self, UI):
        function = self.uploadManifest
        UI_elements = [UI.submit_button, UI.manifest_button, UI.upload_button, UI.full_button, UI.projectID_entry, UI.subjectSetID_entry, UI.manifestFile_entry, UI.manifestFile_button]
        disabled = False

        stage_names = ["Create Subjects", "Update Subjects", "Upload Subjects"]

        super().__init__(stage_names, function, UI_elements, UI, disabled=disabled)

    def uploadManifest(self):
        login = self.UI.login

        if (Spout.verifyLogin(login)):
            spout = Spout(login=login, display_printouts=True, progress_callback=self.UI.display, termination_event=self.UI.termination_event)
            self.UI.display("Required Zooniverse information was verified.")

            self.setStage("Create Subjects")
            subjects = spout.generateSubjects(self.UI.manifestFile.get())

            project = spout.findProject(self.UI.projectID.get())

            self.setStage("Update Subjects")
            success = spout.updateSubjects(subjects, project)

            if (success):
                self.UI.display("Manifest subjects have been given unique Zooniverse IDs.")

            self.setStage("Upload Subjects")
            success = spout.uploadSubjects(self.UI.subjectSetID.get(), subjects)

            if (success):
                self.UI.display("Manifest subjects have been published to Zooniverse.")
        else:
            self.UI.display("Error: Could not verify login credentials.")
            return

    def verifyInputs(self):
        """
        Verify that the project ID, subject set ID, and manifest file are valid before uploading the manifest.

        Returns
        -------
        warning_flags : dict
            A dictionary of warning flags for the UI to display to the user. An empty dictionary means that the inputs are valid.
        """

        warning_flags = {}

        valid_login = False
        spout = None

        # Verify Zooniverse credentials
        if (self.UI.login.username == ''):
            warning_flags.update(self.assignWarningFlag("No username"))
        if (self.UI.login.password == ''):
            warning_flags.update(self.assignWarningFlag("No password"))
        if (not Spout.verifyLogin(self.UI.login)):
            warning_flags.update(self.assignWarningFlag("Invalid Zooniverse credentials"))
        else:
            valid_login = True
            spout = Spout(login=self.UI.login, display_printouts=True, progress_callback=self.UI.display, termination_event=self.UI.termination_event)

        # Verify project ID
        if(self.UI.projectID.get() == ''):
            warning_flags.update(self.assignWarningFlag("No project ID"))
        if(not self.UI.projectID.get().isnumeric() and self.UI.projectID.get() != ''):
            warning_flags.update(self.assignWarningFlag("Invalid project ID"))
        if(valid_login and not spout.projectExists(self.UI.projectID.get())):
            warning_flags.update(self.assignWarningFlag("Project does not exist"))

        # Verify subject set ID
        if(self.UI.subjectSetID.get() == ''):
            warning_flags.update(self.assignWarningFlag("No subject set ID"))
        if(not self.UI.subjectSetID.get().isnumeric() and self.UI.subjectSetID.get() != ''):
            warning_flags.update(self.assignWarningFlag("Invalid subject set ID"))
        if(valid_login and not spout.subjectSetExists(self.UI.subjectSetID.get())):
            warning_flags.update(self.assignWarningFlag("Subject Set does not exist"))

        # Verify manifest file
        if(self.UI.manifestFile.get() == ''):
                warning_flags.update(self.assignWarningFlag("No manifest file"))
        if(not os.path.exists(self.UI.manifestFile.get()) and self.UI.manifestFile.get() != ''):
                warning_flags.update(self.assignWarningFlag("Manifest file not found"))

        # Verify that the user has enough subjects to complete the upload
        if(valid_login):
            user = spout.getUser(self.UI.login.username)
            user_subject_limit = user.raw['subject_limit']
            user_uploaded_subjects_count = user.raw['uploaded_subjects_count']

            if(not self.getFlagTupleFromMasterDictionary("No manifest file")[0] in warning_flags):
                # Get the number of subjects in the manifest file
                manifest_subject_count = 0
                with open(self.UI.manifestFile.get(), newline='') as manifest_file:
                    reader = csv.DictReader(manifest_file)
                    for row in reader:
                        manifest_subject_count += 1

                if(manifest_subject_count > user_subject_limit - user_uploaded_subjects_count):
                    warning_flags.update(self.assignWarningFlag("Insufficient user subjects"))

            if(user_uploaded_subjects_count >= user_subject_limit):
                warning_flags.update(self.assignWarningFlag("Out of subjects"))

            if(not self.getFlagTupleFromMasterDictionary("No project ID")[0] in warning_flags and not self.getFlagTupleFromMasterDictionary("Project does not exist")[0] in warning_flags):
                if(not spout.userHasProjectAccess(user, self.UI.projectID.get())):
                    warning_flags.update(self.assignWarningFlag("User does not have access to project"))

        return warning_flags

class CompositeAction(Action):
    def __init__(self, name, actions, UI, disabled=False):
        self.actions = actions

        def combined_function():
            for action in actions:
                action.execute()

        function = combined_function
        super().__init__(UI, name, function, UI_elements=None, disabled=disabled)

    def verifyInputs(self):
        warning_flags = {}
        for action in self.actions:
            action_warning_flags = action.verifyInputs()
            warning_flags.update(action_warning_flags)
        return warning_flags

class FullPipeline(CompositeAction):
    name = "Full Pipeline"
    def __init__(self, UI):
        disabled = False
        super().__init__(self.name, [GenerateManifest(UI), UploadManifest(UI)], UI, disabled=disabled)

class CollectSubjects(Action):
    name = "Collect Subjects"
    def __init__(self, UI):
        function = UI.subject_manager.collectSubjects
        UI_elements = [UI.projectID_entry, UI.subjectSetID_entry]
        disabled = False

        super().__init__(UI, self.name, function, UI_elements, disabled)

    def verifyInputs(self):
        """
        Verify that the project ID and subject set ID are valid before collecting subjects.

        Returns
        -------
        warning_flags : dict
            A dictionary of warning flags for the UI to display to the user. An empty dictionary means that the inputs are valid.
        """

        warning_flags = {}

        valid_login = False
        spout = None

        # Verify Zooniverse credentials
        if (self.UI.login.username == ''):
            warning_flags.update(self.assignWarningFlag("No username"))
        if (self.UI.login.password == ''):
            warning_flags.update(self.assignWarningFlag("No password"))
        if (not Spout.verifyLogin(self.UI.login)):
            warning_flags.update(self.assignWarningFlag("Invalid Zooniverse credentials"))
        else:
            valid_login = True
            spout = Spout(login=self.UI.login, display_printouts=True, progress_callback=self.UI.display, termination_event=self.UI.termination_event)

        # Verify project ID
        if(self.UI.projectID.get() == ''):
            warning_flags.update(self.assignWarningFlag("No project ID"))
        if(not self.UI.projectID.get().isnumeric() and self.UI.projectID.get() != ''):
            warning_flags.update(self.assignWarningFlag("Invalid project ID"))
        if(valid_login and not spout.projectExists(self.UI.projectID.get())):
            warning_flags.update(self.assignWarningFlag("Project does not exist"))

        # Verify subject set ID
        if(self.UI.subjectSetID.get() == ''):
            warning_flags.update(self.assignWarningFlag("No subject set ID"))
        if(not self.UI.subjectSetID.get().isnumeric() and self.UI.subjectSetID.get() != ''):
            warning_flags.update(self.assignWarningFlag("Invalid subject set ID"))
        if(valid_login and not spout.subjectSetExists(self.UI.subjectSetID.get())):
            warning_flags.update(self.assignWarningFlag("Subject Set does not exist"))

        return warning_flags

class ModifyFieldName(Action):
    name = "Modify Field Name"
    def __init__(self, UI):
        function = self.modifyFieldName
        UI_elements = [UI.submit_button]
        disabled = False

        super().__init__(UI, self.name, function, UI_elements, disabled)

    def modifyFieldName(self):
        login = self.UI.login
        spout = Spout(login=login, display_printouts=True, progress_callback=self.UI.display, termination_event=self.UI.termination_event)

        current_field_names = self.UI.current_action_field_inputs_dict['Current Field Names'].get().split(',')
        new_field_names = self.UI.current_action_field_inputs_dict['New Field Names'].get().split(',')

        # strip whitespace from field names
        current_field_names = [field_name.strip() for field_name in current_field_names]
        new_field_names = [field_name.strip() for field_name in new_field_names]

        selected_subject_objects = self.UI.subject_manager.getSubjectObjects(self.UI.selected_subjects)

        spout.modifySubjectMetadataFieldName(selected_subject_objects, current_field_names, new_field_names)

        self.UI.subject_manager.saveSubjectsToJSON(filename=self.UI.subject_manager.subjects_json_filename)

        self.UI.subject_manager.subject_panel.subject_page.showSubjectMetadata(self.UI.selected_subjects[0])

    def verifyInputs(self):
        """
        Verify that the target file and field name are valid before modifying the field name.

        Returns
        -------
        warning_flags : dict
            A dictionary of warning flags for the UI to display to the user. An empty dictionary means that the inputs are valid.
        """

        warning_flags = {}

        # Verify field name
        for input_name in self.UI.current_action_field_inputs_dict.keys():
            current_action_field_input = self.UI.current_action_field_inputs_dict[input_name]
            if(current_action_field_input.get() == ''):
                warning_flags.update(self.assignWarningFlag("Empty field"))

        current_field_names = self.UI.current_action_field_inputs_dict['Current Field Names'].get()
        new_field_name = self.UI.current_action_field_inputs_dict['New Field Names'].get()

        # Try to split the current field names and new field names by commas
        current_field_names = current_field_names.split(',')
        new_field_names = new_field_name.split(',')

        if(len(current_field_names) != len(new_field_names)):
            warning_flags.update(self.assignWarningFlag("The number of current field names does not match the number of new field names."))

        # Verify that subjects are selected
        if(len(self.UI.selected_subjects) == 0):
            warning_flags.update(self.assignWarningFlag("No selected subjects"))

        return warning_flags

class ModifyFieldValue(Action):
    name = "Modify Field Value"
    def __init__(self, UI):
        function = self.modifyFieldValue
        UI_elements = [UI.submit_button]
        disabled = False

        super().__init__(UI, self.name, function, UI_elements, disabled)

    def modifyFieldValue(self):
        login = self.UI.login
        spout = Spout(login=login, display_printouts=True, progress_callback=self.UI.display, termination_event=self.UI.termination_event)

        field_names = self.UI.current_action_field_inputs_dict['Field Names'].get().split(',')
        field_values = self.UI.current_action_field_inputs_dict['New Values'].get().split(',')

        # strip whitespace from field names
        field_names = [field_name.strip() for field_name in field_names]
        field_values = [field_value.strip() for field_value in field_values]

        selected_subject_objects = self.UI.subject_manager.getSubjectObjects(self.UI.selected_subjects)

        spout.modifySubjectMetadataFieldValue(selected_subject_objects, field_names, field_values)

        self.UI.subject_manager.saveSubjectsToJSON(filename=self.UI.subject_manager.subjects_json_filename)

        self.UI.subject_manager.subject_panel.subject_page.showSubjectMetadata(self.UI.selected_subjects[0])

    def verifyInputs(self):
        """
        Verify that the target file, field name, and field value are valid before modifying the field value.

        Returns
        -------
        warning_flags : dict
            A dictionary of warning flags for the UI to display to the user. An empty dictionary means that the inputs are valid.
        """

        warning_flags = {}

        # Verify field name and field value
        for input_name in self.UI.current_action_field_inputs_dict.keys():
            current_action_field_input = self.UI.current_action_field_inputs_dict[input_name]
            if(current_action_field_input.get() == ''):
                warning_flags.update(self.assignWarningFlag("Empty field"))

        # Verify that subjects are selected
        if(len(self.UI.selected_subjects) == 0):
            warning_flags.update(self.assignWarningFlag("No selected subjects"))

        return warning_flags

class DownloadSubjectGif(Action):
    name = "Download Subject GIF"
    def __init__(self, UI):
        function = self.downloadSubjectGif
        UI_elements = [UI.submit_button]
        disabled = False

        super().__init__(UI, self.name, function, UI_elements, disabled)

    def downloadSubjectGif(self):
        def get_downloads_dir():
            if os.name == 'nt':  # Windows
                downloads_dir = Path(os.path.join(os.environ['USERPROFILE'], 'Downloads'))
            else:  # Unix-like OS
                downloads_dir = Path.home() / 'Downloads'
            return downloads_dir

        download_directory = self.UI.current_action_field_inputs_dict["Download Directory"].get()

        if(download_directory == ''):  # If the directory is empty, use the default download directory
            download_directory = get_downloads_dir()

        selected_subjects = self.UI.selected_subjects

        # Create a folder to store the GIFs
        folder_name = f"Project_{self.UI.projectID.get()}_SubjectSet_{self.UI.subjectSetID.get()}"

        # Create the folder if it does not exist
        if not os.path.exists(os.path.join(download_directory, folder_name)):
            os.mkdir(os.path.join(download_directory, folder_name))
        else:
            # If the folder already exists, append a number to the folder name
            folder_number = 1
            while os.path.exists(os.path.join(download_directory, f"{folder_name}_{folder_number}")):
                folder_number += 1
            folder_name = f"{folder_name}_{folder_number}"
            os.mkdir(os.path.join(download_directory, folder_name))

        gif_directory = os.path.join(download_directory, folder_name)

        self.UI.display(f"Downloading GIFs to {gif_directory}")

        speed = float(self.UI.current_action_field_inputs_dict["Speed (ms/frame)"].get())
        total_subjects = len(selected_subjects)
        count = 1
        for subject_id in selected_subjects:
            gif_filename = f"{subject_id}_speed_{speed}.gif"
            gif_filepath = os.path.join(gif_directory, gif_filename)

            self.UI.display(f"Downloading GIF for subject {subject_id} to {gif_filepath}")
            self.UI.display(f"{self.name}:{count}/{total_subjects}", level=self.UI.logger.level_values.get("DEBUG"))
            count += 1

            filepaths = self.UI.subject_manager.getSubjectImages(subject_id)

            # Open the images and store them in a list
            images = [Image.open(image_path) for image_path in filepaths]

            ms_per_frame = int(speed)

            # Save the images as a GIF
            images[0].save(
                gif_filepath,
                save_all=True,
                append_images=images[1:],
                duration=ms_per_frame,
                loop=0
            )

            # Delete the images
            for image_path in filepaths:
                os.remove(image_path)

    def verifyInputs(self):
        """
        Verify that the target file is valid before downloading the subject GIF.

        Returns
        -------
        warning_flags : dict
            A dictionary of warning flags for the UI to display to the user. An empty dictionary means that the inputs are valid.
        """

        warning_flags = {}

        # Verify that subjects are selected
        if(len(self.UI.selected_subjects) == 0):
            warning_flags.update(self.assignWarningFlag("No selected subjects"))

        # Verify that the download directory is either empty or it exists
        download_directory = self.UI.current_action_field_inputs_dict["Download Directory"].get()
        if(download_directory != '' and not os.path.exists(download_directory)):
                warning_flags.update(self.assignWarningFlag("Invalid download directory"))

        # Verify speed is a number and greater than 0
        speed = self.UI.current_action_field_inputs_dict['Speed (ms/frame)'].get()
        if not speed.isnumeric() or float(speed) <= 0:
            warning_flags.update(self.assignWarningFlag("Invalid speed value"))

        return warning_flags

class RemoveSubjects(Action):
    name = "Remove Subjects"
    def __init__(self, UI):
        function = self.removeSubjects
        UI_elements = [UI.submit_button]
        disabled = False

        super().__init__(UI, self.name, function, UI_elements, disabled)

    def removeSubjects(self):
        login = self.UI.login
        spout = Spout(login=login, display_printouts=True, progress_callback=self.UI.display, termination_event=self.UI.termination_event)

        selected_subjects = self.UI.selected_subjects.copy()
        subject_set = spout.findSubjectSet(self.UI.subjectSetID.get())

        # Open a confirmation window to confirm the removal of the subjects
        user_response = tk.BooleanVar()
        user_response.set(False)

        if(len(selected_subjects) == 1):
            self.UI.openConfirmationWindow(f"Are you sure you want to remove subject {selected_subjects[0]} from subject set {self.UI.subjectSetID.get()}?", user_response)
        else:
            self.UI.openConfirmationWindow(f"Are you sure you want to remove {len(selected_subjects)} subjects from subject set {self.UI.subjectSetID.get()}?", user_response)

        if(not user_response.get()):
            return

        spout.removeSubjects(subject_set, selected_subjects, override_verification=True)

        self.UI.subject_manager.removeSubjects(selected_subjects)

        if(len(selected_subjects) == 1):
            self.UI.display(f"Removed subject {selected_subjects[0]} from subject set {self.UI.subjectSetID.get()}")
        else:
            self.UI.display(f"Removed {len(selected_subjects)} subjects from subject set {self.UI.subjectSetID.get()}")

        self.UI.display("Saving subjects to JSON: " + self.UI.subject_manager.subjects_json_filename)

        self.UI.subject_manager.saveSubjectsToJSON(filename=self.UI.subject_manager.subjects_json_filename)

    def verifyInputs(self):
        """
        Verify that the target file is valid before removing the subjects.

        Returns
        -------
        warning_flags : dict
            A dictionary of warning flags for the UI to display to the user. An empty dictionary means that the inputs are valid.
        """

        warning_flags = {}

        # Verify that subjects are selected
        if(len(self.UI.selected_subjects) == 0):
            warning_flags.update(self.assignWarningFlag("No selected subjects"))

        return warning_flags


class DeleteSubjects(Action):
    name = "Delete Subjects"
    def __init__(self, UI):
        function = self.deleteSubjects
        UI_elements = [UI.submit_button]
        disabled = False

        super().__init__(UI, self.name, function, UI_elements, disabled)

    def deleteSubjects(self):
        login = self.UI.login
        spout = Spout(login=login, display_printouts=True, progress_callback=self.UI.display, termination_event=self.UI.termination_event)

        selected_subjects = self.UI.selected_subjects.copy()

        # Open a confirmation window to confirm the deletion of the subjects
        user_response = tk.BooleanVar()
        user_response.set(False)

        if(len(selected_subjects) == 1):
            self.UI.openConfirmationWindow(f"Are you sure you want to delete subject {selected_subjects[0]} from Zooniverse?", user_response)
        else:
            self.UI.openConfirmationWindow(f"Are you sure you want to delete {len(selected_subjects)} subjects from Zooniverse?", user_response)

        if(not user_response.get()):
            return

        spout.deleteSubjects(selected_subjects, override_verification=True)

        self.UI.subject_manager.removeSubjects(selected_subjects)

        if(len(selected_subjects) == 1):
            self.UI.display(f"Deleted subject {selected_subjects[0]} from subject set {self.UI.subjectSetID.get()}")
        else:
            self.UI.display(f"Deleted {len(selected_subjects)} subjects from subject set {self.UI.subjectSetID.get()}")

        self.UI.display("Saving subjects to JSON: " + self.UI.subject_manager.subjects_json_filename)

        self.UI.subject_manager.saveSubjectsToJSON(filename=self.UI.subject_manager.subjects_json_filename)

    def verifyInputs(self):
        """
        Verify that the target file is valid before deleting the subjects.

        Returns
        -------
        warning_flags : dict
            A dictionary of warning flags for the UI to display to the user. An empty dictionary means that the inputs are valid.
        """

        warning_flags = {}

        # Verify that subjects are selected
        if(len(self.UI.selected_subjects) == 0):
            warning_flags.update(self.assignWarningFlag("No selected subjects"))

        return warning_flags

class Aggregate(StagedAction):
    name = "Aggregate"
    def __init__(self, UI):
        function = self.aggregate
        UI_elements = []
        disabled = False

        stage_names = ["Configure", "Extract", "Reduce"]

        super().__init__(stage_names, function, UI_elements, UI, disabled=disabled)

    def aggregate(self):
        self.UI.classification_manager.aggregate()

    def verifyInputs(self):
        """
        Verify that the target file is valid before aggregating the subjects.

        Returns
        -------
        warning_flags : dict
            A dictionary of warning flags for the UI to display to the user. An empty dictionary means that the inputs are valid.
        """

        warning_flags = {}

        valid_login = False
        spout = None

        # Verify Zooniverse credentials
        if (self.UI.login.username == ''):
            warning_flags.update(self.assignWarningFlag("No username"))
        if (self.UI.login.password == ''):
            warning_flags.update(self.assignWarningFlag("No password"))
        if (not Spout.verifyLogin(self.UI.login)):
            warning_flags.update(self.assignWarningFlag("Invalid Zooniverse credentials"))
        else:
            valid_login = True
            spout = Spout(login=self.UI.login, display_printouts=True, progress_callback=self.UI.display,
                          termination_event=self.UI.termination_event)

        # Verify project ID
        if (self.UI.projectID.get() == ''):
            warning_flags.update(self.assignWarningFlag("No project ID"))
        if (not self.UI.projectID.get().isnumeric() and self.UI.projectID.get() != ''):
            warning_flags.update(self.assignWarningFlag("Invalid project ID"))
        if (valid_login and not spout.projectExists(self.UI.projectID.get())):
            warning_flags.update(self.assignWarningFlag("Project does not exist"))


        # Verify workflow ID
        if (self.UI.workflowID.get() == ''):
            warning_flags.update(self.assignWarningFlag("No workflow ID"))
        if (not self.UI.workflowID.get().isnumeric() and self.UI.workflowID.get() != ''):
            warning_flags.update(self.assignWarningFlag("Invalid workflow ID"))

        self.UI.classification_manager.setFiles()

        classifications_file_exists, workflows_file_exists = self.UI.classification_manager.filesExist()

        if(not classifications_file_exists):
            warning_flags.update(self.assignWarningFlag("Classifications file not found"))
        if(not workflows_file_exists):
            warning_flags.update(self.assignWarningFlag("Workflows file not found"))

        return warning_flags

# Action Helper functions
def mergeMetadataAndTargetFile(metadata_dictionary, target_filename):
        metadata_target_filename = target_filename.split('.')[0] + '-metadata-target.csv'

        target_dict_list = []
        with open(target_filename, newline='') as target_file:
            reader = csv.DictReader(target_file)
            for row in reader:
                target_dict_list.append(row)

        target_field_names = list(target_dict_list[0].keys())

        metadata_field_names = list(metadata_dictionary.keys())

        metadata_target_field_names = [*target_field_names, *metadata_field_names]

        metadata_target_dict_list = []

        # If there are duplicate keys, the target dictionary will overwrite the metadata dictionary
        for target_dict in target_dict_list:
            metadata_target_dict = {}
            for field_name in metadata_field_names:
                metadata_target_dict[field_name] = metadata_dictionary[field_name]
            for field_name in target_field_names:
                metadata_target_dict[field_name] = target_dict[field_name]
            metadata_target_dict_list.append(metadata_target_dict)

        with open(metadata_target_filename, "w", newline='') as metadata_targets_file:
            writer = csv.DictWriter(metadata_targets_file, metadata_target_field_names)
            writer.writeheader()
            writer.writerows(metadata_target_dict_list)

        return metadata_target_filename

def getMutableColumns(dataset_type):
    """
    Get the mutable columns from an AstronomyDataset subclass.

    Parameters
    ----------
    dataset_type : AstronomyDataset
        The AstronomyDataset object

    Returns
    -------
    mutable_columns : list
        A list of mutable columns from the AstronomyDataset
    """

    if(hasattr(dataset_type, 'mutable_columns_dict')):
        return list(dataset_type.mutable_columns_dict.keys())
    else:
        return []

def getAllMutableColumns():
    """
    Get all the mutable columns from all the AstronomyDatasets subclasses.

    Returns
    -------
    mutable_columns : list
        A list of all mutable columns from all the AstronomyDatasets subclasses
    """

    dataset_dict = get_available_astronomy_datasets()
    mutable_columns = []
    for dataset_type in dataset_dict.values():
        mutable_columns.extend(getMutableColumns(dataset_type))
    return mutable_columns

def getAssociatedUIAttributeDict(UI, mutable_columns):
    """
    Get the dictionary of UI attribute associated with a mutable column from an AstronomyDataset.

    Parameters
    ----------
    UI : UserInterface
        The UserInterface object.
    mutable_columns : list of str
        The mutable columns from an AstronomyDataset.

    Returns
    -------
    attribute_dict : dict
        A dictionary of UI attribute associated with the mutable column.
    """

    UI_attributes = UI.__dict__
    association_dict = {}
    for mutable_column in mutable_columns:
        found_match = False
        for attribute_name, attribute_value in UI_attributes.items():
            if(attributeMatchesToColumn(attribute_name, mutable_column)):
                association_dict.update({mutable_column: attribute_name})
                found_match = True
        if(not found_match):
            raise ValueError(f"Error: No attribute found in the user interface for mutable column '{mutable_column}'.")

    return association_dict

def attributeMatchesToColumn(attribute, mutable_column):
    """
    Match an attribute to a mutable column from an AstronomyDataset.

    Parameters
    ----------
    attribute : str
        The attribute to match to a mutable column.
    mutable_column : str
        The mutable column from an AstronomyDataset.

    Returns
    -------
    match : bool
        True if the attribute matches the mutable column, False otherwise.
    """

    # Check if the attribute name is the same as the mutable column when put into the form xxx_xxx

    def convert_to_snake_case(s):
        return ''.join(['_'+i if i.isupper() else i for i in s]).lstrip('_')

    # Convert CamelCase to snake_case
    attribute_lower_snake_case = convert_to_snake_case(attribute).lower()

    # Verify that the column satisfies snake_case and is all lowercase
    if(convert_to_snake_case(mutable_column) == mutable_column and mutable_column.islower()):
        if(attribute_lower_snake_case == mutable_column):
            return True
        else:
            removed_underscore_attribute = attribute_lower_snake_case.replace('_', '')
            removed_underscore_mutable_column = mutable_column.replace('_', '')
            if(removed_underscore_attribute == removed_underscore_mutable_column):
                return True
            else:
                return False
    else:
        raise ValueError(f"Error: Mutable column '{mutable_column}' is not in snake case and all lowercase.")

def castVariableValue(value):
    """
    Cast the value of a variable to the appropriate type.

    Parameters
    ----------
    value : str
        The value of the variable.

    Returns
    -------
    cast_value : str, int, float, or bool
        The cast value of the variable.
    """

    if(value == 'True'):
        return True
    elif(value == 'False'):
        return False
    else:
        try:
            if(int(value) == float(value)):
                return int(value)
        except:
            try:
                return float(value)
            except:
                if(isinstance(value, str)):
                    return value
                else:
                    return repr(value)

class ActionMonitor:
    def __init__(self, UI):
        self.UI = UI
        self.console = Console(self)
        self.progress_bar = ProgressBar(self)

    def display(self, text, level=logging.INFO):
        self.console.display(text, level)

    def formatLogText(self, level=None):
        logger = self.UI.logger
        log_text = ''
        with open(logger.log_file_path, 'r', newline=None) as log_file:
            log_text = log_file.read()

        # Go through each line and remove the text preceding the first space
        log_text_lines = log_text.split('\n')

        log_text_lines.pop(-1)

        formatted_log_text = ''

        for line in log_text_lines:
            level_name, message = line.split(' ', 1)
            level_value = self.UI.logger.level_values.get(level_name, None)
            if(level is None):
                formatted_log_text += message + '\n'
            else:
                if(level_value == level):
                    formatted_log_text += message + '\n'
                elif(level_value is None):
                    raise ValueError(f"Error: Level '{level_name}' not found in the level values dictionary.")

        return formatted_log_text

class Console:
    def __init__(self, action_monitor):
        self.action_monitor = action_monitor
        self.UI = action_monitor.UI
        self.console_scrolled_text_frame = ttk.Frame(master=self.UI.window)
        self.console_scrolled_text = ScrolledText(master=self.console_scrolled_text_frame, height=30, width=90, font=("consolas", "8", "normal"), state=tk.DISABLED)

        self.UI.window.after(self.UI.refresh_rate, self.update)

    def display(self, text, level=logging.INFO):
        try:
            self.append(text, level)
        except(RuntimeError):
            print(text)

    def place(self, placement_type="grid"):
        if (placement_type == "grid"):
            #self.UI.window.geometry("600x625")
            self.console_scrolled_text_frame.grid(row=4, column=0, columnspan=5)
            self.console_scrolled_text.grid(row=0, column=0)
        elif (placement_type == "pack"):
            #self.UI.window.geometry("550x920")
            self.console_scrolled_text_frame.pack(side=tk.BOTTOM)
            self.console_scrolled_text.pack()

    def append(self, message, level=logging.INFO):
        self.UI.logger.updateLevel(level)
        self.UI.logger.log(message)

    def update(self):

        try:
            self.console_scrolled_text.config(state=tk.NORMAL)

            formatted_log_text = self.action_monitor.formatLogText(level=self.UI.logger.level_values.get("INFO"))

            # Get the current block of text in the console
            current_console_text = self.console_scrolled_text.get(1.0, tk.END)

            current_console_text_lines = current_console_text.split('\n')
            current_console_text_lines.pop(-1)

            # Collect the lines of the formatted log text
            formatted_log_text_lines = formatted_log_text.split('\n')

            # Compare line by line to see if the console text is the same as the formatted log text
            line_index = 0
            for console_line, log_line in zip(current_console_text_lines, formatted_log_text_lines):

                if(console_line != log_line):
                    break
                line_index += 1

            # Get all the lines after the line that is the same
            new_formatted_log_text_lines = formatted_log_text_lines[line_index:-1]

            # See if the console text is the same as the formatted log text
            for new_line in new_formatted_log_text_lines:
                self.console_scrolled_text.insert(tk.END, new_line + '\n')
                self.console_scrolled_text.see(tk.END)

            self.console_scrolled_text.config(state=tk.DISABLED)
        except tk.TclError:
            pass

        self.UI.window.after(self.UI.refresh_rate, self.update)

    def clear(self):
        self.console_scrolled_text.delete(1.0, tk.END)

class ProgressBar:
    progress_bar_format_kwargs = {"file": io.StringIO(), "ncols": 60, "ascii": "░▒█",
                                  "bar_format": "{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]"}
    def __init__(self, action_monitor):
        self.action_monitor = action_monitor
        self.UI = action_monitor.UI
        self.progress_bar_frame = ttk.Frame(master=self.UI.window)
        self.progress_bar_text = tk.Text(master=self.progress_bar_frame, height=1, width=90, font=("consolas", "12", "normal"), state=tk.DISABLED)
        self.progress_bar = None
        self.refresh_rate = self.UI.refresh_rate

    def place(self, placement_type="grid"):
        if(placement_type == "grid"):
            #self.UI.window.geometry("600x625")
            self.progress_bar_frame.grid(row=5, column=0, columnspan=5)
            self.progress_bar_text.grid(row=0, column=0, columnspan=5)
        elif(placement_type == "pack"):
            #self.UI.window.geometry("550x920")
            self.progress_bar_frame.pack(side=tk.BOTTOM)
            self.progress_bar_text.pack()

    def initializeProgressBar(self, action_name):
        self.progress_bar = tqdm(total=None, desc=action_name, position=0, leave=True, **self.progress_bar_format_kwargs)
        self.update()

    def setProgressBarTotal(self, total):
        if(self.progress_bar is not None and self.progress_bar.total is None):
            self.progress_bar.total = total

    def update(self):
        if(self.progress_bar is not None):
            # Determine the current value of the progress bar
            current_value = self.progress_bar.n

            # Get the latest DEBUG log message in the log file
            debug_formatted_log_text = self.action_monitor.formatLogText(level=self.UI.logger.level_values.get("DEBUG"))
            # Get the latest message in the log file

            debug_log_lines = debug_formatted_log_text.split('\n')
            debug_log_lines.pop(-1)

            action_log_lines = []
            valid_line = False

            global action_index

            for line in debug_log_lines:
                if(line.startswith("Action Index:")):
                    if(int(line.split(":")[1]) == action_index):
                        valid_line = True
                        continue

                if(valid_line):
                    if(line.startswith("Action Index:")):
                        continue
                    action_log_lines.append(line)

            if(len(action_log_lines) > 0):
                last_action_message = action_log_lines[-1]
                action_name = self.progress_bar.desc

                log_action_name, progress_str = last_action_message.split(":", 1)

                if(log_action_name != action_name):
                    raise ValueError(f"Error: Progress bar action name '{action_name}' does not match the last debug message action name '{log_action_name}'.")

                value = int(progress_str.split('/')[0])
                total = int(progress_str.split('/')[1])

                self.setProgressBarTotal(total)

                # Determine the difference between the current value and the new value
                difference = value - current_value

                if(difference < 0):
                    raise ValueError(f"Error: Progress bar value cannot be less than the current value. Current value: {current_value}, New value: {value}")

                self.progress_bar.update(difference)

                if(value == total):
                    self.print()
                    self.progress_bar.close()
                    self.progress_bar = None

            if(self.progress_bar is not None):
                # Set the text of the progress bar to be str(self.progress_bar)
                self.print()
                self.UI.window.after(self.refresh_rate, self.update)

    def print(self):
        self.progress_bar_text.config(state=tk.NORMAL)
        self.progress_bar_text.delete(1.0, tk.END)
        self.progress_bar_text.insert(tk.END, str(self.progress_bar))
        self.progress_bar_text.config(state=tk.DISABLED)

    def clear(self):
        self.progress_bar_text.config(state=tk.NORMAL)
        self.progress_bar_text.delete(1.0, tk.END)
        self.progress_bar_text.config(state=tk.DISABLED)

