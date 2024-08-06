import io
import os
import subprocess
import sys
import threading
import time

import yaml

from tkinter import ttk
import tkinter as tk
from unWISE_verse.Spout import Spout


class ClassificationManager:
    directory = None
    def __init__(self, UI):
        self.UI = UI

        # Initialize the following variables in the UI class using setattr
        setattr(self.UI, 'classificationsFile', tk.StringVar(value=""))
        setattr(self.UI, 'workflowsFile', tk.StringVar(value=""))
        setattr(self.UI, 'workflowID', tk.StringVar(value=""))
        setattr(self.UI, 'workflowMinVersion', tk.StringVar(value=""))
        setattr(self.UI, 'workflowMaxVersion', tk.StringVar(value=""))

        # Verify whether a Classifications folder located in the current working directory exists
        if not os.path.exists("ClassificationFiles"):
            os.mkdir("ClassificationFiles")

        self.directory = os.path.join(os.getcwd(), "ClassificationFiles")

    def initializeUIElements(self):
        self.classification_window_frame = ttk.Frame(master=self.UI.window, borderwidth=10, relief="groove")
        self.UI.configureFrame(self.classification_window_frame, 1, 2, self.UI.background_color_hex)

        self.classification_window_label = ttk.Label(master=self.classification_window_frame, text="Classification Manager", font=("Helvetica", 16), background=self.UI.background_color_hex)

        self.worfklowVersion_frame = ttk.Frame(self.UI.window)
        self.UI.configureFrame(self.worfklowVersion_frame, 2, 3, self.UI.background_color_hex)

        self.UI.style.configure("BW.TLabel", background=self.UI.background_color_hex)
        self.workflowVersionRangeLabel = ttk.Label(self.worfklowVersion_frame, text="Workflow Controls", style="BW.TLabel")

        # workflow minVersion entry
        self.workflowMinVersion_frame, self.workflowMinVersion_entry = self.UI.makeEntryField(self.worfklowVersion_frame, 'Workflow Min Version', self.UI.workflowMinVersion, self.UI.background_color_hex)

        # workflow maxVersion entry
        self.workflowMaxVersion_frame, self.workflowMaxVersion_entry = self.UI.makeEntryField(self.worfklowVersion_frame, 'Workflow Max Version', self.UI.workflowMaxVersion, self.UI.background_color_hex)

        # Create a frame for workflow control buttons
        self.workflow_control_frame = ttk.Frame(self.worfklowVersion_frame)
        self.UI.configureFrame(self.workflow_control_frame, 1, 2, self.UI.background_color_hex)

        def aggregate():
            self.UI.perform("Aggregate")

        # Aggregate button
        self.aggregate_button = ttk.Button(master=self.workflow_control_frame, text="Aggregate", command=aggregate, style="BW.TButton", takefocus=0)

        self.classify_button = ttk.Button(master=self.workflow_control_frame, text="Classify", command=self.classify, style="BW.TButton", takefocus=0)


    def place(self):
        self.initializeUIElements()

        self.classification_window_frame.pack(fill=tk.BOTH, expand=True)

        self.classification_window_label.grid(row=0, column=0, columnspan=2, pady=10)
        self.worfklowVersion_frame.pack(side=tk.TOP, fill=tk.BOTH)
        self.workflowVersionRangeLabel.grid(row=0, column=0, columnspan=3)
        self.workflowMinVersion_frame.grid(row=1, column=0, padx=10)
        self.workflow_control_frame.grid(row=1, column=1, padx=10)
        self.aggregate_button.grid(row=0, column=0)
        self.classify_button.grid(row=0, column=1)
        self.workflowMaxVersion_frame.grid(row=1, column=2, padx=10)

    def setFiles(self):
        project_id = int(self.UI.projectID.get())
        spout = Spout(login=self.UI.login,  display_printouts=False, progress_callback=None, termination_event=None)
        project = spout.findProject(project_id)
        project_display_name = project.display_name

        # Convert the project display name to the right format
        formatted_project_display_name = project_display_name.lower().replace(" ", "-")
        formatted_project_display_name = formatted_project_display_name.replace("(", "")
        formatted_project_display_name = formatted_project_display_name.replace(")", "")
        formatted_project_display_name = formatted_project_display_name.replace(":", "")
        formatted_project_display_name = formatted_project_display_name.replace(",", "")
        formatted_project_display_name = formatted_project_display_name.replace("?", "")
        formatted_project_display_name = formatted_project_display_name.replace("!", "")
        formatted_project_display_name = formatted_project_display_name.replace("'", "")
        formatted_project_display_name = formatted_project_display_name.replace(".", "")
        formatted_project_display_name = formatted_project_display_name.replace(";", "")

        # Format the associated filenames to set the text variables in the UI
        classifications_file_name = f"{formatted_project_display_name}-classifications.csv"
        classifications_file_path = os.path.join(self.directory, classifications_file_name)
        self.UI.classificationsFile.set(classifications_file_path)

        workflow_file_name = f"{formatted_project_display_name}-workflows.csv"
        workflow_file_path = os.path.join(self.directory, workflow_file_name)
        self.UI.workflowsFile.set(workflow_file_path)

    def filesExist(self):
        classifications_file_path = self.UI.classificationsFile.get()
        workflow_file_path = self.UI.workflowsFile.get()

        #url = f"https://www.zooniverse.org/lab/{self.UI.projectID.get()}/data-exports"

        classifications_file_exists = os.path.exists(classifications_file_path)
        workflow_file_exists = os.path.exists(workflow_file_path)

        return classifications_file_exists, workflow_file_exists

    def classify(self):
        print("Classifying...")

    def aggregate(self):

        aggregate_directory = os.path.join(self.directory, "Aggregate")

        if not os.path.exists(aggregate_directory):
            os.mkdir(aggregate_directory)

        project_directory = os.path.join(aggregate_directory, f"Project_{self.UI.projectID.get()}")

        if(not os.path.exists(project_directory)):
            os.mkdir(project_directory)

        workflow_directory = os.path.join(project_directory, f"Workflow_{self.UI.workflowID.get()}")

        if(not os.path.exists(workflow_directory)):
            os.mkdir(workflow_directory)

        version_range_directory = os.path.join(workflow_directory, f"V{self.UI.workflowMinVersion.get()}_V{self.UI.workflowMaxVersion.get()}")

        if(not os.path.exists(version_range_directory)):
            os.mkdir(version_range_directory)

        config_directory = os.path.join(version_range_directory, "Config")
        extractions_directory = os.path.join(version_range_directory, "Extractions")
        reductions_directory = os.path.join(version_range_directory, "Reductions")

        aggregator = Aggregator(self.UI.classificationsFile.get(), self.UI.workflowsFile.get(), progress_callback=self.UI.display, config_directory=config_directory, extractions_directory=extractions_directory, reductions_directory=reductions_directory)

        # Generate config files, extracted files, and reduction files
        self.UI.action_manager.setActionState("Configure")
        version_dict = {"min_version": float(self.UI.workflowMinVersion.get()), "max_version": float(self.UI.workflowMaxVersion.get())}
        aggregator.config(int(self.UI.workflowID.get()), **version_dict)

        self.UI.action_manager.setActionState("Extract")
        aggregator.extract()

        self.UI.action_manager.setActionState("Reduce")
        aggregator.reduce()

# Based on: https://aggregation-caesar.zooniverse.org/README.html
class Aggregator:
    def __init__(self, classifications_csv_filename, workflows_csv_filename, config_directory="Config", extractions_directory="Extractions", reductions_directory="Reductions", progress_callback=None):
        """
        Initializes a Classifier object. This object is used to generate config files,
        extracted files, and reduction files of a workflow using the Panoptes aggregation CLI.

        Parameters
        ----------
            classifications_csv_filename : str
                The name of the classifications csv file.
            workflows_csv_filename : str
                The name of the workflow csv file.
            config_directory : str, optional
                The name of the directory where the config files will be stored.
                The default is "Config".
            extractions_directory : str, optional
                The name of the directory where the extracted files will be stored.
                The default is "Extractions".
            reductions_directory : str, optional
                The name of the directory where the reduction files will be stored.
                The default is "Reductions".

        Notes
        -----
        The config files are used to generate the extracted files, which are used to generate the reduction files.
        """

        if(progress_callback is not None):
            progress_callback("Initializing Aggregator...")
        else:
            progress_callback = print
            progress_callback("Initializing Aggregator...")

        self.progress_callback = progress_callback

        # Initialize variables

        # If the classifications csv filename is a relative path, make it an absolute path based on the current working directory
        if(not os.path.isabs(classifications_csv_filename)):
            classifications_csv_filename = os.path.join(os.getcwd(), classifications_csv_filename)

        # If the workflow csv filename is a relative path, make it an absolute path based on the current working directory
        if(not os.path.isabs(workflows_csv_filename)):
            workflows_csv_filename = os.path.join(os.getcwd(), workflows_csv_filename)

        # Check if there are any spaces in the filenames
        if(" " in classifications_csv_filename):
            raise ValueError(f"The classifications csv filename cannot contain spaces: {classifications_csv_filename}")

        if(" " in workflows_csv_filename):
            raise ValueError(f"The workflows csv filename cannot contain spaces: {workflows_csv_filename}")

        self.classifications_csv_filename = classifications_csv_filename
        self.workflows_csv_filename = workflows_csv_filename

        # If the config directory is a relative path, make it an absolute path based on the current working directory
        if(not os.path.isabs(config_directory)):
            config_directory = os.path.join(os.getcwd(), config_directory)

        # If the extraction directory is a relative path, make it an absolute path based on the current working directory
        if(not os.path.isabs(extractions_directory)):
            extractions_directory = os.path.join(os.getcwd(), extractions_directory)

        # If the reductions directory is a relative path, make it an absolute path based on the current working directory
        if(not os.path.isabs(reductions_directory)):
            reductions_directory = os.path.join(os.getcwd(), reductions_directory)

        if (" " in config_directory):
            raise ValueError(f"The config directory cannot contain spaces: {config_directory}")

        if (" " in extractions_directory):
            raise ValueError(f"The extractions directory cannot contain spaces: {extractions_directory}")

        if (" " in reductions_directory):
            raise ValueError(f"The reductions directory cannot contain spaces: {reductions_directory}")

        self.config_directory = config_directory
        self.extractions_directory = extractions_directory
        self.reductions_directory = reductions_directory
        self.extractor_config_file = None
        self.reducer_config_file = None
        self.task_config_file = None
        self.workflow_id = None
        self.extracted_file = None
        self.reduced_file = None
        self.min_version = None
        self.max_version = None

    def aggregateWorkflow(self, workflow_id, **kwargs):
        """
        Classifies a workflow using the Panoptes aggregation client by generating config files,
        extracted files, and reduction files.

        Parameters
        ----------
            workflow_id : int
                The ID of the workflow to be aggregated.
            **kwargs : dict
                Optional arguments to be passed to the config command.
        """

        # Generate config files, extracted files, and reduction files
        self.config(workflow_id, **kwargs)
        self.extract()
        self.reduce()

        # Print the results
        self.progress_callback(f"Classifications complete.")
        self.progress_callback(f"Extracted file: {self.extracted_file}")
        self.progress_callback(f"Reduced file: {self.reduced_file}")

    def config(self, workflow_id, **kwargs):
        """
        Generates config files for a workflow using the Panoptes aggregation CLI.

        Parameters
        ----------
            workflow_id : int
                The ID of the workflow to be aggregated.
            **kwargs : dict
                Optional arguments to be passed to the config command.
        """

        self.progress_callback(f"Configuring workflow {workflow_id}...")

        # Store the workflow ID
        self.workflow_id = workflow_id

        if(self.workflow_id is None):
            raise ValueError("Workflow ID has not been set.")

        if(not os.path.exists(self.workflows_csv_filename)):
            raise FileNotFoundError(f"Workflow file {self.workflows_csv_filename} does not exist.")

        # Create the config directory if it does not exist
        if(not os.path.exists(self.config_directory)):
            os.mkdir(self.config_directory)

        # Define the command you want to run
        command = f"panoptes_aggregation config {self.workflows_csv_filename} {workflow_id} -d {self.config_directory}"

        # Construct the command string with optional arguments
        command_str = command

        # Define the allowed keys for the optional arguments of the config command
        single_dash_keys = ["v", "vv", "k", "h"]
        double_dash_keys = ["version", "help", "min_version", "max_version", "keywords", "verbose"]
        allowed_keys = single_dash_keys + double_dash_keys

        # Check that the kwargs are valid and add them to the command string
        for key, value in kwargs.items():
            if(key not in allowed_keys):
                raise ValueError(f"Invalid argument: {key}")
            if(key in single_dash_keys):
                if(value is not None):
                    command_str += f" -{key} {value}"
                else:
                    command_str += f" -{key}"
            elif(key in double_dash_keys):
                if(value is not None):
                    command_str += f" --{key} {value}"
                else:
                    command_str += f" --{key}"

        if (kwargs.get("min_version") is not None):
            self.min_version = kwargs.get("min_version")
        if (kwargs.get("max_version") is not None):
            self.max_version = kwargs.get("max_version")

        # Run the command and capture the output
        try:
            config_subprocess = subprocess.Popen(command_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = config_subprocess.communicate()[0]
        except AssertionError as e:
            self.progress_callback(f"Invalid request made: {command_str}")
            raise ValueError(f"Invalid request made: {command_str}")
        except subprocess.CalledProcessError as e:
            self.progress_callback(f"Error running command: {command_str}")
            raise ValueError(f"Error running command: {command_str}")

        # Decode the output assuming it's in UTF-8 encoding
        decoded_output = output.decode("utf-8")

        # Extract the files from the output
        split_output = decoded_output.split("\n")[1:-1]

        # Initialize the files list
        files = []
        for line in split_output:
            possible_file = line.removesuffix("\r")
            # If the possible file exists
            if(os.path.exists(possible_file)):
                files.append(possible_file)

        # Store the config files in the appropriate variables
        for file in files:
            if("Extractor" in file):
                self.extractor_config_file = file
            elif("Reducer" in file):
                self.reducer_config_file = file
            elif("Task" in file):
                self.task_config_file = file

    def extract(self, **kwargs):
        """
        Generates an extracted file using the Panoptes aggregation CLI.

        Parameters
        ----------
            **kwargs : optional
                Optional arguments to be passed to the extract command.
        """

        # Check that the extractor config file is defined
        if(self.extractor_config_file is None):
            raise ValueError("Extractor file is not defined. Please run config() first.")

        if(not os.path.exists(self.classifications_csv_filename)):
            raise ValueError(f"Classifications file {self.classifications_csv_filename} does not exist.")

        if(not os.path.exists(self.extractor_config_file)):
            raise ValueError(f"Extractor config file {self.extractor_config_file} does not exist.")

        # Create the extraction directory if it does not exist
        if(not os.path.exists(self.extractions_directory)):
            os.mkdir(self.extractions_directory)

        # Define the command you want to run
        command = f"panoptes_aggregation extract {self.classifications_csv_filename} {self.extractor_config_file} -d {self.extractions_directory}"
        command_args = command.split(" ")
        # Construct the command string with optional arguments
        command_str = command

        # Set the default output file name to be a modified version of the config file name
        if(kwargs.get("o") is None and kwargs.get("output") is None):
            kwargs["o"] = self.extractor_config_file.split("_config_")[1]
            kwargs["output"] = self.extractor_config_file.split("_config_")[1]

        # Define the allowed keys for the optional arguments of the extract command
        single_dash_keys = ["o", "O", "c", "vv", "h"]
        double_dash_keys = ["output", "help", "order", "cpu_count", "verbose"]
        allowed_keys = single_dash_keys + double_dash_keys

        # Check that the kwargs are valid and add them to the command string
        for key, value in kwargs.items():
            if (key not in allowed_keys):
                raise ValueError(f"Invalid argument: {key}")
            if (key in single_dash_keys):
                if (value is not None):
                    command_str += f" -{key} {value}"
                else:
                    command_str += f" -{key}"
            elif (key in double_dash_keys):
                if (value is not None):
                    command_str += f" --{key} {value}"
                else:
                    command_str += f" --{key}"

        # Run the command and capture the output
        try:
            process = subprocess.Popen(command_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

            self.progress_callback("Preparing Extractor...")
            started = False
            while not process.poll():
                line = process.stdout.readline()

                if(line == "" and started):
                    break

                if(not started):
                    self.progress_callback("Extracting...")
                    started = True

                if line:
                    percentage_value = line.split("%")[0].split(" ")[-1]
                    eta_string = line.split("ETA:   ")[-1]

                    if(percentage_value.isnumeric()):
                        try:
                            self.progress_callback(f"Extract: {percentage_value}/100", level=10)
                        except:
                            pass
        except AssertionError as e:
            self.progress_callback(f"Invalid request made: {command_str}")
            raise ValueError(f"Invalid request made: {command_str}")
        except subprocess.CalledProcessError as e:
            self.progress_callback(f"Error running command: {command_str}")
            raise ValueError(f"Error running command: {command_str}")

        extractor_type_prefix = None

        # Read the extractor yaml file
        with open(self.extractor_config_file, "r") as f:
            extractor_yaml = yaml.safe_load(f)
            extractor_type_prefix = list(extractor_yaml["extractor_config"].keys())[0] + "_"

        # Save the filename of the extracted file
        if(kwargs.get("o") is not None):
            self.extracted_file = os.path.join(self.extractions_directory, extractor_type_prefix + kwargs.get("o").removesuffix(".yaml") + ".csv")
        else:
            self.extracted_file = os.path.join(self.extractions_directory, extractor_type_prefix + kwargs.get("output").removesuffix(".yaml") + ".csv")

        # Rename the extracted file to have the appropriate name
        os.rename(os.path.join(self.extractions_directory, f"{extractor_type_prefix}extractions.csv"), self.extracted_file)

    def reduce(self, **kwargs):
        """
        Generates a reduced file using the Panoptes aggregation CLI.

        Parameters
        ----------
            **kwargs : optional
                Optional arguments to be passed to the reduce command.
        """

        # Check that the reducer config file is defined
        if(self.reducer_config_file is None):
            raise ValueError("Extractor file is not defined. Please run config() first.")

        # Check that the extracted file is defined
        if(self.extracted_file is None):
            raise ValueError("Extracted file is not defined. Please run extract() first.")

        if(not os.path.exists(self.extracted_file)):
            raise ValueError(f"Extracted file {self.extracted_file} does not exist.")

        if(not os.path.exists(self.reducer_config_file)):
            raise ValueError(f"Reducer config file {self.reducer_config_file} does not exist.")

        # Create the reductions directory if it does not exist
        if(not os.path.exists(self.reductions_directory)):
            os.mkdir(self.reductions_directory)

        # Define the command you want to run
        command = f"panoptes_aggregation reduce {self.extracted_file} {self.reducer_config_file} -d {self.reductions_directory} -s"
        command_args = command.split(" ")

        # Construct the command string with optional arguments
        command_str = command

        extractor_type_prefix = None

        # Set the default output file name to be a modified version of the extracted file name
        if(kwargs.get("o") is None and kwargs.get("output") is None):
            head, tail = os.path.split(self.extracted_file)

            # Read the extractor yaml file
            with open(self.extractor_config_file, "r") as f:
                extractor_yaml = yaml.safe_load(f)
                extractor_type_prefix = list(extractor_yaml["extractor_config"].keys())[0] + "_"

            extracted_filename = tail.removeprefix(extractor_type_prefix)
            kwargs["o"] = extracted_filename
            kwargs["output"] = extracted_filename

        # Define the allowed keys for the optional arguments of the reduce command
        single_dash_keys = ["o", "O", "F", "c", "h"]
        double_dash_keys = ["output", "help", "order", "cpu_count"]
        allowed_keys = single_dash_keys + double_dash_keys

        # Check that the kwargs are valid and add them to the command string
        for key, value in kwargs.items():
            if (key not in allowed_keys):
                raise ValueError(f"Invalid argument: {key}")
            if (key in single_dash_keys):
                if (value is not None):
                    command_str += f" -{key} {value}"
                else:
                    command_str += f" -{key}"
            elif (key in double_dash_keys):
                if (value is not None):
                    command_str += f" --{key} {value}"
                else:
                    command_str += f" --{key}"

        # Run the command and capture the output
        try:
            process = subprocess.Popen(command_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

            self.progress_callback("Preparing Reducer...")
            started = False
            while not process.poll():

                line = process.stdout.readline()

                if (line == "" and started):
                    break

                if (not started):
                    self.progress_callback("Reducing...")
                    started = True

                if line:
                    percentage_value = line.split("%")[0].split(" ")[-1]
                    eta_string = line.split("ETA:   ")[-1]

                    if (percentage_value.isnumeric()):
                        try:
                            self.progress_callback(f"Reduce: {percentage_value}/100", level=10)
                        except:
                            pass

        except AssertionError as e:
            self.progress_callback(f"Invalid request made: {command_str}")
            raise ValueError(f"Invalid request made: {command_str}")
        except subprocess.CalledProcessError as e:
            self.progress_callback(f"Error running command: {command_str}")
            raise ValueError(f"Error running command: {command_str}")

        # Save the filename of the reduced file
        if (kwargs.get("o") is not None):
            self.reduced_file = os.path.join(self.reductions_directory, extractor_type_prefix + kwargs.get("o").removesuffix(".csv") + ".csv")
        else:
            self.reduced_file = os.path.join(self.reductions_directory, extractor_type_prefix + kwargs.get("output").removesuffix(".csv") + ".csv")

        # Rename the reduced file to have the appropriate name
        os.rename(os.path.join(self.reductions_directory, f"{extractor_type_prefix}reductions.csv"), self.extracted_file)


