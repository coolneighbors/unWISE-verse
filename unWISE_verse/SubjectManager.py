import ast
import importlib.util
import json
import os
import threading
import time
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

import numpy as np
from PIL import Image, ImageSequence, ImageTk
from PIL.ImageTk import PhotoImage

from unWISE_verse.Spout import Spout
import tkinter as tk
from tkinter import filedialog as fd
from Logger import Logger

global online
online = False

global user_interface
user_interface = None

def requiresOnline(func):
    def wrapper(*args, **kwargs):
        global online
        global user_interface
        if(not online):
            if(user_interface is not None):
                user_interface.display("This function requires an online connection to Zooniverse.")
            else:
                raise Exception("This function requires an online connection to Zooniverse.")
        return func(*args, **kwargs)
    return wrapper

# TODO: Figure out how to appropriately handle deleting widgets for switching between metadata and flipbook

class SubjectManager:
    directory = None
    def __init__(self, UI):
        self.UI = UI
        global user_interface
        user_interface = UI
        self.spout = None
        self.subjects = []
        self.subject_object_dict = {}
        self.subject_dictionaries = []
        self.subjects_dict = {}
        self.subject_display_list = []
        self.subjects_json_filename = None
        self.click_count = 0

        global online
        online = False

        # Initialize the following variables in the UI class using setattr
        setattr(self.UI, 'subjectSearchQuery', tk.StringVar(value=""))
        setattr(self.UI, 'subjectInfoType', tk.StringVar(value="Metadata"))
        setattr(self.UI, 'requestOnline', tk.BooleanVar(value=False))
        setattr(self.UI, 'selected_subjects', [])
        setattr(self.UI, 'current_gif_frames', [])
        setattr(self.UI, 'current_gif_fps', 0)
        setattr(self.UI, 'gifSliderValue', tk.DoubleVar(value=1.0))
        setattr(self.UI, 'select_subjects_thread', threading.Thread())

        # Verify whether a Subject Files directory exists
        if not os.path.exists("SubjectFiles"):
            os.mkdir("SubjectFiles")

        self.directory = os.path.join(os.getcwd(), "SubjectFiles")

        self.subject_gif_directory = os.path.join(self.directory, "GIFs")

    def createSpout(self):
        self.spout = Spout(login=self.UI.login, display_printouts=True, progress_callback=self.UI.display, termination_event=self.UI.termination_event)

    def place(self):
        self.initializeUIElements()
        self.subject_window_frame.pack(fill=tk.BOTH, expand=True)
        self.subject_selection_container.place()
        self.subject_panel.place()

    def initializeUIElements(self):
        self.subject_window_frame = ttk.Frame(master=self.UI.window, borderwidth=10, relief="groove")
        self.UI.configureFrame(self.subject_window_frame, 1, 2, self.UI.background_color_hex)

        # Subject selection container
        self.subject_selection_container = SubjectSelectionContainer(self)

        # Subject panel
        self.subject_panel = SubjectPanel(self)


    def collectSubjects(self):
        request_online = self.UI.requestOnline.get()

        project = self.UI.projectID.get()
        subject_set = self.UI.subjectSetID.get()

        # Verify whether a JSONs directory exists
        jsons_directory = os.path.join(self.directory, "JSONs")
        if not os.path.exists(jsons_directory):
            os.mkdir(jsons_directory)

        # Check if the subjects have already been collected
        if (subject_set is not None):
            self.subjects_json_filename = os.path.join(jsons_directory, f"{project}_{subject_set}_subjects.json")
        else:
            self.subjects_json_filename = os.path.join(jsons_directory, f"{project}_subjects.json")

        if (self.subjectFileExists(self.subjects_json_filename)):
            if(request_online):
                self.loadSubjectsFromJSON(self.subjects_json_filename)
            else:
                self.loadSubjectDictionariesFromJSON(self.subjects_json_filename)
        else:
            if(request_online):
                try:
                    self.UI.display("Collecting subjects from Zooniverse...")
                    self.subjects = self.spout.getSubjectsFromProject(project=project, subject_set=subject_set, only_orphans=False)
                    for subject in self.subjects:
                        self.subject_object_dict[str(subject.id)] = subject
                except Exception as e:
                    self.UI.display(f"Error: {e}")
                    return
                global online
                online = True
                self.UI.display(f"Saving subjects to JSON file: {self.subjects_json_filename}")
                self.saveSubjectsToJSON(filename=self.subjects_json_filename)
                self.UI.display(f"Subjects saved.")
            else:
                self.UI.display("Subjects have not been collected. Please collect subjects online.")
                return

        self.UI.display(f"Compiling subjects for viewing...")
        self.subject_selection_container.setDefaultListBox()
        self.UI.display(f"Subjects compiled.")

    def removeSubjects(self, subject_ids):
        for subject_id in subject_ids:
            self.subjects_dict.pop(subject_id)
            self.subject_object_dict.pop(subject_id)
            for subject_dict in self.subject_dictionaries:
                if(subject_dict['subject_id'] == subject_id):
                    self.subject_dictionaries.remove(subject_dict)
                    break

            self.subjects = self.getSubjectObjects(list(self.subjects_dict.keys()))

        # If any of these subjects are selected, unselect them
        for selected_subject in self.UI.selected_subjects:
            if selected_subject in subject_ids:
                self.UI.selected_subjects.remove(selected_subject)

        self.subject_selection_container.setDefaultListBox()

    @requiresOnline
    def saveSubjectsToJSON(self, filename):
        self.subject_dictionaries = []
        for subject in self.subjects:
            subject.reload()
            subject_dict = subject._savable_dict()
            subject_dict['subject_id'] = subject.id
            self.subject_dictionaries.append(subject_dict)

        # Sort the subject dictionaries by subject ID
        self.subject_dictionaries = sorted(self.subject_dictionaries, key=lambda x: x['subject_id'])

        for subject_dict in self.subject_dictionaries:
            self.subjects_dict[subject_dict['subject_id']] = subject_dict

        self.subject_selection_container.resetSubjectDisplayList()

        with open(filename, 'w') as json_file:
            json.dump(self.subject_dictionaries, json_file, indent=4)

    def loadSubjectDictionariesFromJSON(self, filename):
        with open(filename, 'r') as json_file:
            self.subject_dictionaries = json.load(json_file)

        for subject_dict in self.subject_dictionaries:
            self.subjects_dict[subject_dict['subject_id']] = subject_dict

        self.subject_selection_container.resetSubjectDisplayList()

    def loadSubjectsFromJSON(self, filename):
        with open(filename, 'r') as json_file:
            self.subject_dictionaries = json.load(json_file)

        for subject_dict in self.subject_dictionaries:
            self.subjects_dict[subject_dict['subject_id']] = subject_dict

        self.UI.display(f"Loading {len(self.subject_dictionaries)} subjects from JSON file: " + filename)
        subject_ids = [subject_dict['subject_id'] for subject_dict in self.subject_dictionaries]
        self.UI.display(f"Collecting Subjects from Zooniverse...")

        self.subjects = []
        total_subjects = len(subject_ids)
        for index, subject_id in enumerate(subject_ids):
            subject = self.spout.findSubject(subject_id)
            self.subjects.append(subject)
            self.UI.display(f"Collect Subjects: {index+1}/{total_subjects}", level=10)

        self.UI.display(f"Subjects collected from Zooniverse.")

        for subject in self.subjects:
            self.subject_object_dict[str(subject.id)] = subject

        global online
        online = True

        self.subject_selection_container.resetSubjectDisplayList()

    @staticmethod
    def subjectFileExists(filename):
        return os.path.isfile(filename)

    def getSubjectImages(self, subject_id):
        # Use the locations in the subject dictionary to download the images from the Zooniverse server

        subject_dict = self.subjects_dict[subject_id]
        filepaths = []
        for index, location in enumerate(subject_dict['locations']):
            image_filename = f"{subject_id}_image_{index}.png"
            filepath = self.spout.downloadFromLocation(location, self.subject_gif_directory, image_filename)
            filepaths.append(filepath)

        return filepaths

    def generateSubjectGIF(self, subject_id, duration = 5):

        if(not os.path.exists(self.subject_gif_directory)):
            os.makedirs(self.subject_gif_directory)

        gif_filename = f"{subject_id}.gif"
        gif_filepath = os.path.join(self.subject_gif_directory, gif_filename)

        if(os.path.exists(gif_filepath)):
            return gif_filepath

        filepaths = self.getSubjectImages(subject_id)

        # Open the images and store them in a list
        images = [Image.open(image_path) for image_path in filepaths]

        ms_per_frame = int((duration*1000) / len(images))

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

        return gif_filepath

    def deleteCache(self):
        if(os.path.exists(self.directory)):
            # Delete the SubjectFiles directory
            for root, dirs, files in os.walk(self.directory, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))

        self.subjects = []
        self.subject_dictionaries = []
        self.subjects_dict = {}
        self.subject_display_list = []

        global online
        online = False

        self.subjects_json_filename = None

        self.subject_selection_container.setDefaultListBox()
        self.subject_panel.subject_page.clear()

        self.subject_panel.subject_display.displaying = False
        self.UI.current_gif_frames = []
        self.UI.current_gif_fps = None
        self.subject_panel.subject_display.clearCanvas()

        self.UI.display("Cache deleted.")

    def getSubjectObjects(self, subject_ids):
        subject_objects = []
        for subject_id in subject_ids:
            subject_objects.append(self.subject_object_dict[str(subject_id)])
        return subject_objects

class SubjectSelectionContainer:
    def __init__(self, subject_manager):
        self.subject_manager = subject_manager
        self.UI = subject_manager.UI
        self.subject_display_list = []
        self.initializeUIElements()

    def initializeUIElements(self):
        # Subject list box to display the subject ids
        subject_list_width = 20
        self.subject_selection_container_frame = ttk.Frame(master=self.subject_manager.subject_window_frame, width=140, height=360)
        self.UI.configureFrame(self.subject_selection_container_frame, 2, 1, self.UI.background_color_hex)

        # Subject search bar and search button
        self.search_frame = ttk.Frame(master=self.subject_selection_container_frame)
        self.UI.configureFrame(self.search_frame, 1, 1, self.UI.background_color_hex)

        self.subject_search_bar_frame, self.subject_search_bar_entry = self.UI.makeEntryField(self.search_frame, '', self.UI.subjectSearchQuery, self.UI.background_color_hex, placeholder_text="Search for subjects...", takefocus=0, width=subject_list_width+1)

        def empty_search_query(event):
            self.UI.subjectSearchQuery.set("")

        self.subject_search_bar_entry.bind("<Double-Button-3>", empty_search_query)

        self.search_button_frame = ttk.Frame(master=self.search_frame)
        self.UI.configureFrame(self.search_button_frame, 1, 2, self.UI.background_color_hex)

        self.search_button = ttk.Button(master=self.search_button_frame, text="Search", takefocus=0, command=self.searchSubjects, width=int(subject_list_width/2)+1)

        def find_py_files():
            # Open a file dialog to select a file, specifically looking for .py files
            filetypes = [
                ('Python files', '*.py')
            ]

            filepath = fd.askopenfilename(
                title='Open a file',
                initialdir=os.getcwd(),
                filetypes=filetypes
            )

            self.UI.subjectSearchQuery.set(filepath)

        self.find_button = ttk.Button(master=self.search_button_frame, text="Find", command=lambda: threading.Thread(target=find_py_files).start(), takefocus=0, width=int(subject_list_width/2)-3)

        # Subject list box
        self.subject_list_box_frame = ttk.Frame(master=self.subject_selection_container_frame)
        self.UI.configureFrame(self.subject_list_box_frame, 1, 1, self.UI.background_color_hex)

        self.subject_list_box = tk.Listbox(master=self.subject_list_box_frame, font=("consolas", "8", "normal"), width=subject_list_width, height=20, selectmode=tk.EXTENDED)

        def selectSubjects(event):
            self.subject_manager.click_count += 1
            self.selectSubjects()

        self.subject_list_box.bind("<ButtonRelease-1>", selectSubjects)

        #When double right-clicking on the subject list box, unselect all subjects
        def unselectSubjects(event):
            self.unselectSubjects()

        self.subject_list_box.bind("<Double-Button-3>", unselectSubjects)

        def getAllSubjects(event):
            self.subject_manager.click_count += 1
            self.getAllSubjects()

        self.subject_list_box.bind("<Double-Button-1>", getAllSubjects)

        self.list_box_scrollbar = ttk.Scrollbar(self.subject_list_box_frame, orient="vertical", command=self.subject_list_box.yview)

        self.subject_list_box.config(yscrollcommand=self.list_box_scrollbar.set)

        # Collect and delete cache subjects frame
        self.search_utilities_frame = ttk.Frame(master=self.subject_selection_container_frame)
        self.UI.configureFrame(self.search_utilities_frame, 1, 1, self.UI.background_color_hex)

        def collect():
            self.UI.perform("Collect Subjects")

        self.collect_button = ttk.Button(master=self.search_utilities_frame, text="Collect", command=lambda: threading.Thread(target=collect).start(), takefocus=0, width=int(subject_list_width/2)-3)

        self.delete_cache_button = ttk.Button(master=self.search_utilities_frame, text="Delete", command=self.subject_manager.deleteCache, takefocus=0, width=int(subject_list_width/2)-3)

        # Request online checkbox
        self.UI.style.configure("BW.TCheckbutton", background=self.UI.background_color_hex)

        def toggle_request_online():
            self.UI.requestOnline.set(not self.UI.requestOnline.get())
            if(self.UI.requestOnline.get()):
                self.UI.display("Enabling online requests.")
            else:
                self.UI.display("Disabling online requests.")

        self.request_online_checkbox = ttk.Checkbutton(master=self.search_utilities_frame, text="", command=toggle_request_online, takefocus=0, style="BW.TCheckbutton")
        # Set the initial state of the checkbox so that it matches the request online variable
        if(self.UI.requestOnline.get()):
            self.request_online_checkbox.state(['selected'])

        def check_for_empty_search_query(event):
            if(self.UI.subjectSearchQuery.get() == "" or self.UI.subjectSearchQuery.get() == "Search for subjects..."):
                self.setDefaultListBox()

        self.subject_search_bar_entry.bind("<KeyRelease>", check_for_empty_search_query)

        self.place()

        self.update()

    def update(self):
        if(self.UI.sessionType.get() != "manipulate"):
            self.UI.selected_subjects = []
            return

        self.UI.window.after(self.UI.refresh_rate, self.update)

    def place(self):
        self.subject_selection_container_frame.grid(row=0, column=0, sticky="w")
        self.search_frame.grid(row=0, column=0, sticky="w")
        self.subject_search_bar_frame.grid(row=0, column=0, sticky="w")
        self.search_button_frame.grid(row=1, column=0, sticky="w")
        self.search_button.grid(row=1, column=0, sticky="w")
        self.find_button.grid(row=1, column=1, sticky="w")
        self.subject_list_box.grid(row=0, column=0, sticky="w")
        self.list_box_scrollbar.grid(row=0, column=1, sticky="ns")
        self.subject_list_box_frame.grid(row=1, column=0, sticky="w")
        self.search_utilities_frame.grid(row=2, column=0, sticky="w")
        self.collect_button.grid(row=0, column=0, sticky="w")
        self.delete_cache_button.grid(row=0, column=1, sticky="w")
        self.request_online_checkbox.grid(row=0, column=2, sticky="w")

    @staticmethod
    def getFormattedSubjectID(subject_id):
        global online
        if (online):
            return f"✔ Subject {subject_id}"
        else:
            return f"✖ Subject {subject_id}"

    @staticmethod
    def getSubjectIDFromFormattedSubjectID(formatted_subject_id):
        return formatted_subject_id.split(' ')[2]

    def applyStringSearch(self, search_string):

        valid_subjects = []

        for subject_dict in self.subject_manager.subject_dictionaries:
            subject_id = subject_dict['subject_id']
            subject_metadata = self.subject_manager.subjects_dict.get(subject_id, None)

            if(search_string in subject_id):
                valid_subjects.append(subject_id)
            else:
                if(subject_metadata is None):
                    continue
                metadata_keys = list(subject_metadata['metadata'].keys())
                metadata_values = list(subject_metadata['metadata'].values())

                for key, value in zip(metadata_keys, metadata_values):
                    if(search_string in key.lower() or search_string in value.lower()):
                        valid_subjects.append(subject_id)
                        break

        # Sort subjects
        valid_subjects.sort()

        return valid_subjects
    
    def applyFunctionalSearch(self, search_function_filepath):
        # A search function file is a .py file which contains one function declaration.
        # The function must take a dictionary as an argument and return a boolean value which determines if the subject
        # satisfies the search criteria.

        filename = os.path.basename(search_function_filepath)

        # Verify that the file is a .py file
        if(not search_function_filepath.endswith('.py')):
            self.UI.display(f"Search failed.")
            self.UI.display(f"Filetype Error: The search function file, {filename}, must be a .py file.")
            return None

        # Step 1: Read the file content
        with open(search_function_filepath, 'r') as file:
            file_content = file.read()

        # Step 2: Parse the file content to identify functions
        parsed_ast = ast.parse(file_content)
        function_defs = [node for node in parsed_ast.body if isinstance(node, ast.FunctionDef)]

        # Step 3: Ensure there is exactly one function
        if len(function_defs) != 1:
            self.UI.display(f"Search failed.")
            self.UI.display(f"Syntax Error: The search function file, {filename}, must contain exactly one function.")
            return None

        function_name = function_defs[0].name

        # Step 4: Import the function dynamically
        module_name = os.path.splitext(os.path.basename(search_function_filepath))[0]
        spec = importlib.util.spec_from_file_location(module_name, search_function_filepath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        search_function = getattr(module, function_name)

        # Step 5: Apply the function to the subjects
        self.UI.display(f"Applying search function from {filename} to {len(self.subject_manager.subject_dictionaries)} subjects.")
        valid_subjects = []
        failure_count = 0

        for subject_dict in self.subject_manager.subject_dictionaries:
            subject_id = subject_dict['subject_id']
            try:
                result = search_function(subject_dict)
                if(type(result) != bool):
                    self.UI.display(f"Error: The function must return a boolean value.")
                    return None

                if (result):
                    valid_subjects.append(subject_id)
            except Exception as e:
                self.UI.display(f"Search function failed on subject {subject_id}.")
                self.UI.display(f"Error: {e}")
                failure_count += 1
                continue

            if(failure_count > 3):
                self.UI.display(f"Search function failed on too many subjects. Aborting search. Verify the function's logic.")
                return None

        if(len(valid_subjects) == 1):
            self.UI.display(f"Search function found 1 subject which satisfied the functional criteria.")
        else:
            self.UI.display(f"Search function found {len(valid_subjects)} subjects which satisfied the functional criteria.")

        return valid_subjects

    def searchSubjects(self):
        search_string = self.UI.subjectSearchQuery.get()

        valid_subjects = []

        if(search_string == "" or search_string == "Search for subjects..."):
            self.setDefaultListBox()
            return

        if (search_string.endswith('.py')):
            valid_subjects = self.applyFunctionalSearch(search_string)
        else:
            valid_subjects = self.applyStringSearch(search_string)

        self.setSubjectDisplayList(valid_subjects)
        self.fillSubjectListBox()

    def setDefaultListBox(self):
        self.resetSubjectDisplayList()
        self.fillSubjectListBox()

    def setSubjectDisplayList(self, subject_ids):
        self.subject_manager.subject_display_list = []
        for subject_id in subject_ids:
            self.subject_manager.subject_display_list.append(self.getFormattedSubjectID(subject_id))

    def resetSubjectDisplayList(self):
        self.subject_manager.subject_display_list = []
        for subject_dict in self.subject_manager.subject_dictionaries:
            self.subject_manager.subject_display_list.append(self.getFormattedSubjectID(subject_dict['subject_id']))

    def fillSubjectListBox(self):
        self.subject_list_box.delete(0, tk.END)
        for subject_id in self.subject_manager.subject_display_list:
            self.subject_list_box.insert(tk.END, subject_id)

    def selectSubjects(self):
        self.UI.selected_subjects = []

        for index in self.subject_list_box.curselection():
            subject_item = self.subject_list_box.get(index)
            # Get the subject id from the subject item
            self.UI.selected_subjects.append(self.getSubjectIDFromFormattedSubjectID(subject_item))

        if(len(self.UI.selected_subjects) > 0):
            self.UI.current_gif_frames = self.subject_manager.subject_panel.subject_display.getGIFFrames("Ajax_loader_metal_512_modified.gif")

        try:
            if(self.subject_manager.click_count == 1):
                self.UI.select_subjects_thread = threading.Thread(target=self.subject_manager.subject_panel.subject_display.setCurrentGIF, args=(self.UI.selected_subjects[0],))
                self.UI.select_subjects_thread.start()
            else:
                # Create a thread which waits for the first gif to finish displaying before displaying the next gif
                def wait_and_display():
                    self.UI.select_subjects_thread.join()

                    for index in self.subject_list_box.curselection():
                        subject_item = self.subject_list_box.get(index)
                        # Get the subject id from the subject item
                        self.UI.selected_subjects.append(self.getSubjectIDFromFormattedSubjectID(subject_item))

                    self.UI.select_subjects_thread = threading.Thread(target=self.subject_manager.subject_panel.subject_display.setCurrentGIF, args=(self.UI.selected_subjects[0],))
                    self.UI.select_subjects_thread.start()

                threading.Thread(target=wait_and_display).start()

        except IndexError:
            pass

        self.subject_manager.click_count = 0

    def unselectSubjects(self):
        self.UI.selected_subjects = []
        self.subject_list_box.selection_clear(0, tk.END)

    def getAllSubjects(self):
        self.UI.selected_subjects = []
        self.subject_list_box.selection_set(0, tk.END)

        for index in self.subject_list_box.curselection():
            subject_item = self.subject_list_box.get(index)
            # Get the subject id from the subject item
            self.UI.selected_subjects.append(self.getSubjectIDFromFormattedSubjectID(subject_item))

class SubjectPanel:
    def __init__(self, subject_manager):
        self.subject_manager = subject_manager
        self.UI = subject_manager.UI
        self.initializeUIElements()

    def initializeUIElements(self):
        #self.subject_metadata_panel_frame = ttk.Frame(master=self.subject_manager.subject_window_frame)
        #self.UI.configureFrame(self.subject_metadata_panel_frame, 2, 1, self.UI.background_color_hex)
        pass

    def place(self):
        self.subject_page = SubjectPage(self.subject_manager)
        self.subject_display = SubjectDisplay(self.subject_manager)
        #self.subject_metadata_panel_frame.grid(row=0, column=1, sticky=tk.E)
        self.setPanel()

    def setPanel(self):
        if(self.UI.subjectInfoType.get() == "Metadata"):
            self.subject_display.hide()
            self.subject_page.place()
        elif(self.UI.subjectInfoType.get() == "Flipbook"):
            self.subject_page.hide()
            self.subject_display.place()
        else:
            raise Exception("Invalid subject info type.")

class SubjectPage:
    def __init__(self, subject_manager):
        self.subject_manager = subject_manager
        self.UI = subject_manager.UI
        self.current_subject_id = None
        self.initializeUIElements()

    def initializeUIElements(self):
        # Create UI elements to show the metadata of the currently selected subject (or first subject in the selected list)
        self.subject_metadata_page_frame = ttk.Frame(master=self.subject_manager.subject_window_frame)
        self.UI.configureFrame(self.subject_metadata_page_frame, 2, 1, self.UI.background_color_hex)

        self.subject_metadata_scrolled_text = ScrolledText(master=self.subject_metadata_page_frame, wrap=tk.WORD, width=60, height=25, padx=0, pady=0, font=("consolas", "8", "normal"))

        self.subject_info_type_radio_button_frame = ttk.Frame(master=self.subject_metadata_page_frame)
        self.UI.configureFrame(self.subject_info_type_radio_button_frame, 1, 2, self.UI.background_color_hex)

        self.UI.style.configure("BW.TRadiobutton", background=self.UI.background_color_hex)
        # Add two radio buttons to switch between metadata and flipbooks
        self.metadata_radio_button = ttk.Radiobutton(master=self.subject_info_type_radio_button_frame, text="Metadata", variable=self.UI.subjectInfoType, value="Metadata", takefocus=0, style="BW.TRadiobutton", command=self.subject_manager.subject_panel.setPanel)

        self.flipbook_radio_button = ttk.Radiobutton(master=self.subject_info_type_radio_button_frame, text="Flipbook", variable=self.UI.subjectInfoType, value="Flipbook", takefocus=0, style="BW.TRadiobutton", command=self.subject_manager.subject_panel.setPanel)

        self.subject_metadata_scrolled_text.configure(state=tk.NORMAL)
        self.subject_metadata_scrolled_text.insert(tk.END, "Subject Metadata")
        self.subject_metadata_scrolled_text.configure(state=tk.DISABLED)

        self.update()

    def update(self):

        if (self.UI.sessionType.get() != "manipulate"):
            self.current_subject_id = None
            return

        try:
            if(len(self.UI.selected_subjects) > 0):
                if(self.current_subject_id != self.UI.selected_subjects[0]):
                    self.current_subject_id = self.UI.selected_subjects[0]
                    self.showSubjectMetadata(self.current_subject_id)
            else:
                self.current_subject_id = None
                self.clear()

            self.UI.window.after(self.UI.refresh_rate, self.update)
        except tk.TclError:
            pass

    def place(self):
        self.subject_metadata_page_frame.grid(row=0, column=1, sticky="nse")
        self.subject_metadata_scrolled_text.grid(row=0, column=0, sticky="nse")
        self.subject_info_type_radio_button_frame.grid(row=1, column=0, sticky="nse")
        self.metadata_radio_button.grid(row=0, column=0, sticky="nse")
        self.flipbook_radio_button.grid(row=0, column=1, sticky="nse")

    def showSubjectMetadata(self, subject_id):
        # Get the metadata of the subject
        subject_dict = self.subject_manager.subjects_dict[subject_id]
        subject_metadata = subject_dict['metadata']

        self.subject_metadata_scrolled_text.configure(state=tk.NORMAL)
        self.subject_metadata_scrolled_text.delete(1.0, tk.END)
        self.subject_metadata_scrolled_text.insert(tk.END, f"Subject ID: {subject_id}\n\n")
        for key, value in subject_metadata.items():
            self.subject_metadata_scrolled_text.insert(tk.END, f"{key}: {value}\n\n")
        self.subject_metadata_scrolled_text.configure(state=tk.DISABLED)

    def clear(self):
        # Check if the scrolled text widget is already empty and if not, clear it
        if(len(self.subject_metadata_scrolled_text.get(1.0, tk.END)) != 1):
            self.subject_metadata_scrolled_text.configure(state=tk.NORMAL)
            self.subject_metadata_scrolled_text.delete(1.0, tk.END)
            self.subject_metadata_scrolled_text.configure(state=tk.DISABLED)

    def hide(self):
        # Hide the subject metadata page and radio buttons
        self.subject_metadata_page_frame.grid_forget()
        self.subject_info_type_radio_button_frame.grid_forget()

class SubjectDisplay:
    def __init__(self, subject_manager):
        self.subject_manager = subject_manager
        self.UI = subject_manager.UI
        self.default_canvas_size = (378, 320)
        self.frame_index = 0
        self.displaying = False
        self.initializeUIElements()
        self.start_time = None
        self.first_display = False

    def initializeUIElements(self):
        # Create UI elements to display the gif of the currently selected subject
        self.subject_display_frame = ttk.Frame(master=self.subject_manager.subject_window_frame)
        self.UI.configureFrame(self.subject_display_frame, 3, 1, self.UI.background_color_hex)
        canvas_width, canvas_height = self.default_canvas_size

        self.canvas_frame = ttk.Frame(master=self.subject_display_frame)
        self.UI.configureFrame(self.canvas_frame, 1, 1, self.UI.background_color_hex)
        # Set the size of the canvas frame to the default canvas size
        self.canvas_frame.config(width=canvas_width, height=canvas_height)
        self.canvas_frame.grid_propagate(False)

        self.subject_display_canvas = tk.Canvas(master=self.canvas_frame, width=canvas_width, height=canvas_height, bg="white")

        # Add a frame and slider for the gif speed
        self.subject_display_speed_frame = ttk.Frame(master=self.subject_display_frame)
        self.UI.configureFrame(self.subject_display_speed_frame, 1, 1, self.UI.background_color_hex)
        self.subject_display_speed_frame.config(width=canvas_width, height=15)
        self.subject_display_speed_frame.grid_propagate(False)

        self.gif_speed_slider = ttk.Scale(master=self.subject_display_speed_frame, from_=0.0, to=10.0, orient=tk.HORIZONTAL, variable=self.UI.gifSliderValue, takefocus=0)

        self.subject_info_type_radio_button_frame = ttk.Frame(master=self.subject_display_frame)
        self.UI.configureFrame(self.subject_info_type_radio_button_frame, 1, 2, self.UI.background_color_hex)

        self.UI.style.configure("BW.TRadiobutton", background=self.UI.background_color_hex)
        # Add two radio buttons to switch between metadata and flipbooks
        self.metadata_radio_button = ttk.Radiobutton(master=self.subject_info_type_radio_button_frame, text="Metadata", variable=self.UI.subjectInfoType, value="Metadata", takefocus=0, style="BW.TRadiobutton", command=self.subject_manager.subject_panel.setPanel)

        self.flipbook_radio_button = ttk.Radiobutton(master=self.subject_info_type_radio_button_frame, text="Flipbook", variable=self.UI.subjectInfoType, value="Flipbook", takefocus=0, style="BW.TRadiobutton", command=self.subject_manager.subject_panel.setPanel)

        self.UI.window.after(self.UI.refresh_rate, self.update)

    def update(self):

        if(self.UI.sessionType.get() != "manipulate"):
            self.UI.current_gif_frames = []
            return

        if(not self.displaying):
            self.start_time = time.time()
            self.displayCurrentGIF()

        if(len(self.UI.selected_subjects) > 0):
            self.displaying = True
        else:
            self.clearCanvas()
            self.displaying = False
            self.UI.current_gif_frames = []

        self.UI.window.after(self.UI.refresh_rate, self.update)

    def displayCurrentGIF(self):
        try:
            if(len(self.UI.current_gif_frames) > 0):
                try:
                    gif = self.UI.current_gif_frames[self.frame_index]
                    gif_fps = self.UI.current_gif_fps * self.UI.gifSliderValue.get()
                    if(gif_fps != 0):
                        ms_delay = int(1000/gif_fps)
                    else:
                        ms_delay = 4294967296

                    # Check if the canvas is currently displaying a gif
                    if(not self.first_display):
                        if(time.time() - self.start_time < ms_delay/1000):
                            self.UI.window.after(1, self.displayCurrentGIF)
                            return

                    self.canvas_frame.config(width=gif.width(), height=gif.height())
                    self.subject_display_canvas.config(width=gif.width(), height=gif.height())
                    new_canvas_width = self.subject_display_canvas.winfo_width()
                    new_canvas_height = self.subject_display_canvas.winfo_height()

                    center_x = int(new_canvas_width / 2)
                    center_y = int(new_canvas_height / 2)

                    # Set the size of the canvas to the size of the gif
                    self.subject_display_canvas.delete("all")
                    self.subject_display_canvas.create_image(center_x, center_y, anchor=tk.CENTER, image=gif)
                    self.first_display = False

                    if(self.frame_index < len(self.UI.current_gif_frames) - 1):
                        self.frame_index += 1
                    else:
                        self.frame_index = 0

                    self.start_time = time.time()
                except IndexError:
                    pass

                self.UI.window.after(self.UI.refresh_rate, self.displayCurrentGIF)
        except tk.TclError:
            pass

    def clearCanvas(self):
        self.subject_display_canvas.delete("all")

    def getGIFFrames(self, gif_filepath):
        gif = Image.open(gif_filepath)

        def get_gif_fps(gif_image):
            # Open the GIF file
            frames = gif_image.n_frames

            # Calculate total duration in milliseconds
            total_duration = sum([gif_image.info['duration'] for frame in range(frames)])

            # Calculate the average FPS
            average_fps = frames / (total_duration / 1000)

            return average_fps

        self.UI.current_gif_fps = get_gif_fps(gif)

        gif_width, gif_height = gif.width, gif.height

        gif_aspect_ratio = gif_width / gif_height

        # Resize the gif to fit the canvas size while maintaining the aspect ratio

        # Scale the size of the gif until its width or height matches the canvas width or height
        canvas_width, canvas_height = self.default_canvas_size

        # Scale by height
        new_height = canvas_height
        new_width = int(new_height * gif_aspect_ratio)

        # Get the width and height of the gif
        image_size = (new_width, new_height)

        # Set the canvas size to the new width and height
        self.subject_display_canvas.config(width=new_width, height=new_height)

        width_diff = new_width - canvas_width

        if(width_diff > 0):
            self.UI.window.geometry(f"{self.UI.window.winfo_width() + width_diff}x{self.UI.window.winfo_height()}")
        else:
            self.UI.window.geometry("550x920")

        frames = [ImageTk.PhotoImage(frame.copy().resize(image_size, Image.ANTIALIAS)) for frame in ImageSequence.Iterator(gif)]

        return frames

    def getSubjectGIFFrames(self, subject_id):
        gif_filepath = self.subject_manager.generateSubjectGIF(subject_id, duration=5)
        frames = self.getGIFFrames(gif_filepath)
        return frames

    def setCurrentGIF(self, subject_id):
        self.UI.current_gif_frames = self.getSubjectGIFFrames(subject_id)
        self.frame_index = 0
        self.first_display = True

    def place(self):
        self.subject_display_frame.grid(row=0, column=1, sticky="nse")
        self.canvas_frame.grid(row=0, column=0)
        self.subject_display_canvas.grid(row=0, column=0)
        self.subject_display_speed_frame.grid(row=1, column=0)
        self.gif_speed_slider.grid(row=0, column=0, sticky="ew")
        self.subject_info_type_radio_button_frame.grid(row=2, column=0, sticky="nse")
        self.metadata_radio_button.grid(row=0, column=0, sticky="nse")
        self.flipbook_radio_button.grid(row=0, column=1, sticky="nse")

    def hide(self):
        # Hide the subject display page and radio buttons
        self.subject_display_frame.grid_forget()
        self.subject_info_type_radio_button_frame.grid_forget()










