# -*- coding: utf-8 -*-
"""
Created on Mon Jun 13 10:14:59 2022

@author: Noah Schapera, Austin Humphreys
"""

import io
import logging
import multiprocessing
import os
import platform
import re
import threading
from tkinter import ttk
import tkinter as tk
from copy import copy
from tkinter import filedialog as fd
from tkinter.scrolledtext import ScrolledText
import pickle
from datetime import datetime
from tqdm import tqdm
import time
from PIL import Image, ImageTk, ImageSequence

import unWISE_verse
from unWISE_verse.ActionManager import ActionManager
from unWISE_verse.ClassificationManager import ClassificationManager
from unWISE_verse.Data import Data
from unWISE_verse.Dataset import get_available_astronomy_datasets
from unWISE_verse.Login import Login
from unWISE_verse.Spout import Spout
from unWISE_verse.SubjectManager import SubjectManager
from ActionManager import getAssociatedUIAttributeDict, getAllMutableColumns

class UserInterface:
    
    def __init__(self, logger=None):
        self.window = tk.Tk()

        # Set the background color hex to "Cosmic Latte"
        # Cosmic Latte: https://en.wikipedia.org/wiki/Cosmic_latte
        # Color Credit: By Karl Glazebrook & Ivan Baldry (JHU)
        self.background_color_hex = '#FFF8E7'

        # Makes use of awlight theme from awthemes
        # Author: Brad Lanam
        # License: zlib/libpng
        self.style = ttk.Style(self.window)
        self.window.tk.call('lappend', 'auto_path', 'themes/awthemes-10.4.0')
        self.window.tk.call('package', 'require', 'awlight')
        self.style.theme_use('awlight')
        self.window.protocol("WM_DELETE_WINDOW", self.quit)
        self.default_window_size = "600x200"
        self.window.resizable(True,True)
        self.refresh_rate = 100
        self.initializeVariables()
        self.logger = logger

        if(self.rememberMe.get()):
            self.attemptLogin()
        else:
            self.openLoginWindow()

        self.centerWindow(self.window)

        self.window.mainloop()

    # Initialization functions
    def initializeVariables(self):
        """
        Initializes variables which can be modified throughout the program runtime.
        """

        # Session Variables
        self.sessionType = tk.StringVar(value="")
        self.saveSession = tk.BooleanVar(value=True)
        self.canSafelyQuit = True
        self.exitRequested = False
        self.termination_event = multiprocessing.Event()
        self.progress = None

        # Action Manager Variables
        self.action_state = tk.StringVar(value="")

        # Metadata Variables
        self.scale = tk.StringVar(value="22")
        self.FOV = tk.StringVar(value="120")
        self.pngDirectory = tk.StringVar(value="pngs")
        self.minBright = tk.StringVar(value="")
        self.maxBright = tk.StringVar(value="")
        self.addGrid = tk.BooleanVar(value=True)
        self.gridCount = tk.StringVar(value="5")
        self.gridType = tk.StringVar(value="Solid")
        self.gridColor = tk.StringVar(value="(128,0,0)")
        self.ignorePartialCutouts = tk.BooleanVar(value=False)
        self.imageType = tk.StringVar(value="Both")
        self.zoom = tk.StringVar(value="14")
        self.layer = tk.StringVar(value="sdss")
        self.blink = tk.StringVar(value="ls-dr10")

        # Connectivity Variables
        self.username = tk.StringVar(value="")
        self.password = tk.StringVar(value="")
        self.projectID = tk.StringVar(value="")
        self.subjectSetID = tk.StringVar(value="")
        self.rememberMe = tk.BooleanVar(value=False)
        self.login = None

        # File Variables
        self.targetFile = tk.StringVar(value="")
        self.manifestFile = tk.StringVar(value="manifest.csv")

        # Pipeline-specific Variables
        self.datasetType = tk.StringVar(value="")
        self.overwriteManifest = tk.BooleanVar(value=False)
        self.pipelineState = tk.StringVar(value="")

        # Session and managers must be initialized last
        self.subject_manager = SubjectManager(self)
        self.classification_manager = ClassificationManager(self)
        self.session = Session(self)

    def initializeFrames(self):
        """
        Creates all the entry frames (label and text entry) for the main window along with the console and progress bar.
        """

        # Project ID entry
        self.projectID_frame, self.projectID_entry = self.makeEntryField(self.window,'Project ID',self.projectID, self.background_color_hex)

        # Subject Set ID entry
        self.subjectSetID_frame, self.subjectSetID_entry = self.makeEntryField(self.window,'Subject Set ID',self.subjectSetID, self.background_color_hex)

        # Target file entry
        self.targetFile_frame, self.targetFile_entry = self.makeEntryField(self.window,'Target List Filename',self.targetFile, self.background_color_hex)

        # Manifest file entry
        self.manifestFile_frame, self.manifestFile_entry = self.makeEntryField(self.window,'Manifest Filename',self.manifestFile,self.background_color_hex)

        # PNG directory entry
        self.pngDirectory_frame, self.pngDirectory_entry = self.makeEntryField(self.window, 'PNG Directory',self.pngDirectory,self.background_color_hex)

        # Dataset Type Option Menu
        dataset_type_options = list(get_available_astronomy_datasets().keys())
        dataset_type_options.sort(key=lambda x: x.lower())
        if(self.datasetType.get() == ""):
            self.datasetType.set(dataset_type_options[0])
        self.datasetTypeOptionMenu_frame, self.datasetTypeOptionMenu = self.makeOptionMenuField(self.window, "Dataset Type", self.datasetType, dataset_type_options, self.background_color_hex)

        def save_session(event):
            self.session.save(self)

        self.projectID_entry.bind_all("<Leave>", save_session)

    def initializeButtons(self):
        """
        Makes all the buttons we use for the UI and provides them with their respective commands for when they are clicked.
        """

        def submit():
            self.perform(self.pipelineState.get())

        # Submit Button
        self.submit_button = ttk.Button(master=self.window, text="Submit", command=submit, takefocus=0)

        # Help Button
        #self.help_button = ttk.Button(master=self.window, text="Help", command=self.openHelpWindow)

        # Check-box Buttons
        self.style.configure("BW.TCheckbutton", background=self.background_color_hex)
        self.sessionSelectionMenu_button = ttk.Button(master=self.window, text="Selection Menu", command=self.openSessionSelectionWindow, takefocus=0)
        self.saveSession_check_button = ttk.Checkbutton(master=self.window, text="Save Session", variable=self.saveSession, onvalue=1, offvalue=0, style="BW.TCheckbutton", takefocus=0)

        # File/Directory Search Buttons
        def selectManifestFile():
            filetypes = (
                ('CSV files', '*.csv'),
                ('All files', '*.*')
            )

            filename = fd.askopenfilename(
                title='Open a file',
                initialdir=os.getcwd(),
                filetypes=filetypes)

            self.manifestFile_entry.delete(0, tk.END)
            self.manifestFile_entry.insert(0, filename)

        self.manifestFile_button = ttk.Button(master=self.window, text="Search", command=selectManifestFile, takefocus=0)

        def selectTargetFile():
            filetypes = (
                ('CSV files', '*.csv'),
                ('All files', '*.*')
            )

            filename = fd.askopenfilename(
                title='Open a file',
                initialdir=os.getcwd(),
                filetypes=filetypes)

            self.targetFile_entry.delete(0, tk.END)
            self.targetFile_entry.insert(0, filename)

        self.targetFile_button = ttk.Button(master=self.window, text="Search", command=selectTargetFile, takefocus=0)

        def selectPNGDirectory():
            filename = fd.askdirectory(
                title='Select a directory',
                initialdir=os.getcwd())

            self.pngDirectory_entry.delete(0, tk.END)
            self.pngDirectory_entry.insert(0, filename)

        self.pngDirectory_button = ttk.Button(master=self.window, text="Search", command=selectPNGDirectory, takefocus=0)

        # Set-action state Radio Buttons
        self.style.configure("BW.TRadiobutton", background=self.background_color_hex)
        self.manifest_button = ttk.Radiobutton(master=self.window, text="Manifest", variable=self.pipelineState, value="Generate Manifest", style="BW.TRadiobutton", takefocus=0)
        self.upload_button = ttk.Radiobutton(master=self.window, text="Upload", variable=self.pipelineState, value="Upload Manifest", style="BW.TRadiobutton", takefocus=0)
        self.full_button = ttk.Radiobutton(master=self.window, text="Full", variable=self.pipelineState, value="Full Pipeline", style="BW.TRadiobutton", takefocus=0)

        # Metadata Button
        self.metadata_button = ttk.Button(master=self.window, text="Metadata", command=self.openMetadataWindow, takefocus=0)

    # Window helper functions
    @staticmethod
    def clearWindow(window):

        def destroy(widget):
            for child in widget.winfo_children():
                destroy(child)

            widget.destroy()

        # Recursively destroy all widgets in the window
        for widget in window.winfo_children():
            destroy(widget)

        rows = window.grid_size()[1]
        cols = window.grid_size()[0]

        if(rows > 0):
            window.rowconfigure(list(range(rows)), minsize=0, weight=0)
        if(cols > 0):
            window.columnconfigure(list(range(cols)), minsize=0, weight=0)

    @staticmethod
    def centerWindow(window):
        window.update_idletasks()
        # get screen width and height
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()

        # calculate position x and y coordinates
        x = (screen_width / 2) - (window.winfo_width() / 2)
        y = (screen_height / 2) - (window.winfo_height() / 2)

        window.geometry("+%d+%d" %(x,y))

    def quit(self, display=True):
        if(display):
            self.display("Attempting to quit...")

        if(self.canSafelyQuit):
            self.exitRequested = True
            self.termination_event.set()

            if (self.saveSession.get()):
                self.session.save(self)
                if(display):
                    print("Session saved.")
            else:
                self.session.delete()

            def destroyWindow(window):
                for thread in threading.enumerate():
                    if(thread != threading.main_thread() and thread != threading.current_thread()):
                        if(not thread.daemon):
                            thread.join()
                window.quit()

            # Create a thread to wait for all threads to finish and then destroy the window
            threading.Thread(target=destroyWindow, args=(self.window,)).start()
        else:
            self.window.after_idle(self.quit, False)

    def display(self, text, level=logging.INFO):
        if(self.action_manager is not None):
            self.action_manager.display(text, level)

    # User-input field functions
    def makeEntryField(self, window, label_title, variable, background_color, hide=False, placeholder_text="", **kwargs):
        """
        Generates a new frame with label and text entry field.

        Parameters
        ----------
        window : tk.Tk
            Window object to place the frame in.
        label_title : string
            The title for the frame, displayed above the text entry.
        variable : tk.StringVar
            The variable to store the text entry.
        background_color : tuple of int
            RGB tuple for the background color of the frame.
        hide : boolean, optional
            Shows * in the text entry (e.g. to hide a password). The default is False.
        placeholder_text : string, optional
            Text to display in the entry field when it is empty. The default is "".
        **kwargs : dict
            Additional keyword arguments to pass to the Entry widget.

        Returns
        -------
        frame : tkinter Frame object
            Contains Entry and Label widget
        entry : tkinter Entry widget
            User entry field.
        """

        self.style.configure("BW.TFrame", background=background_color)
        frame = ttk.Frame(master=window, style="BW.TFrame")

        def on_focus_in(event):
            if entry.get() == placeholder_text:
                entry.delete(0, tk.END)
                entry.config(foreground='black')

        def on_focus_out(event):
            if entry.get() == '':
                entry.insert(0, placeholder_text)
                entry.config(foreground='grey')

        def on_map(event):
            if entry.get() == '':
                entry.insert(0, placeholder_text)
                entry.config(foreground='grey')

        if(not hide):
            entry = ttk.Entry(master=frame, textvariable=variable, **kwargs)
        else:
            entry = ttk.Entry(master=frame, show='*', textvariable=variable, **kwargs)
        self.style.configure("BW.TLabel", background=background_color)

        if(label_title != ''):
            label = ttk.Label(master=frame, text=label_title, style="BW.TLabel")
            label.grid(row=0, column=0)
            entry.grid(row=1, column=0)
        else:
            entry.grid(row=0, column=0)

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
        entry.bind("<Map>", on_map)

        return frame, entry

    def makeOptionMenuField(self, window, label_title, variable, options_list, background_color):
        """
        Generates a new frame with label and option menu field.

        Parameters
        ----------
        label_title : string
            The title for the frame, displayed above the text entry.

        Returns
        -------
        frame : tk.Frame
            Contains Option menu and Label widget
        entry : tkinter OptionMenu widget
            Option menu field
        """

        self.style.configure("BW.TFrame", background=background_color)
        frame = ttk.Frame(master=window, style="BW.TFrame")

        self.style.configure("BW.TMenubutton", background="white")

        option_menu = ttk.OptionMenu(frame, variable, variable.get(), *options_list)
        option_menu.config(style="BW.TMenubutton")
        self.style.configure("BW.TLabel", background=background_color)
        label = ttk.Label(master=frame, text=label_title, style="BW.TLabel")

        label.grid(row=0, column=0)
        option_menu.grid(row=1, column=0)

        return frame, option_menu

    def makeRadioButtonsField(self, window, label_title, variable, options_list, background_color, values_list=None):
        """
        Generates a new frame with label and radio button field.

        Parameters
        ----------
        label_title : string
            The title for the frame, displayed above the text entry.
        variable : tk.StringVar
            The variable to store the radio button selection.
        options_list : list of strings
            The options to display in the radio buttons.
        background_color : tuple of int
            RGB tuple for the background color of the frame.
        values_list : list of strings, optional
            The values to store in the variable when the radio button is selected. The default is None.

        Returns
        -------
        frame : tk.Frame
            Contains Radio button and Label widget
        entry : list of tkinter Radiobutton widgets
            Radio button fields
        """

        radio_buttons = []

        self.style.configure("BW.TFrame", background=background_color)
        frame = ttk.Frame(master=window, style="BW.TFrame")

        if(label_title == '' or label_title is None):
            pass
        else:
            self.style.configure("BW.TLabel", background=background_color)
            label = ttk.Label(master=frame, text=label_title, style="BW.TLabel")
            label.pack(side=tk.TOP)

        if(values_list is None):
            values_list = options_list

        for option, value in zip(options_list, values_list):
            self.style.configure("BW.TRadiobutton", background=background_color)
            radio_button = ttk.Radiobutton(frame, variable=variable, value=value, text=option, style="BW.TRadiobutton", takefocus=0)
            radio_button.pack(side=tk.LEFT)
            radio_buttons.append(radio_button)

        return frame, radio_buttons

    # Arbitrary frame configuration function
    def configureFrame(self, frame, rows, cols, background_color):
        """
        Configures a frame object which holds all the frames and buttons. Can store rows*cols widgets

        Parameters
        ----------
        frame : tk.Frame
            Frame object to configure
        rows : int
            Number of rows in the frame
        cols : int
            Number of columns in the frame
        background_color : string
            Hex code or RGB tuple for the background color of the frame

        """

        self.style.configure("BW.TFrame", background=background_color)
        frame.configure(style="BW.TFrame")
        frame.rowconfigure(list(range(rows)), weight=1)
        frame.columnconfigure(list(range(cols)), weight=1)

    # Login window functions
    def configureLoginWindow(self, window, title, rows, cols, background_color):
        """
        Configures a window object which holds all the frames and buttons. Can store rows*cols widgets

        Parameters
        ----------
        window : tk.Tk
            Window object to configure
        title : string
            Title of the window
        rows : int
            Number of rows in the window
        cols : int
            Number of columns in the window
        background_color : string
            Hex code or RGB tuple for the background color of the window
        """
        
        window.title(title)
        window.configure(background=background_color)
        window.rowconfigure(list(range(rows)),minsize=50,weight=1)
        window.columnconfigure(list(range(cols)), minsize=50, weight=1)

    def openLoginWindow(self):
        self.configureLoginWindow(self.window, 'Login', 3, 1, self.background_color_hex)

        login_input_frame = ttk.Frame(self.window)
        self.style.configure("BW.TLabel", background=self.background_color_hex)
        login_label = ttk.Label(self.window,text="unWISE-verse",font=("Arial", 75), style="BW.TLabel")
        login_label.grid(row=0,column=0)

        self.configureFrame(login_input_frame,1,2,self.background_color_hex)

        # username frame and entry
        self.username_frame, self.username_entry = self.makeEntryField(login_input_frame, 'Zooniverse Username',self.username, self.background_color_hex)
        # password frame and entry
        self.password_frame, self.password_entry = self.makeEntryField(login_input_frame, 'Zooniverse Password', self.password, self.background_color_hex, hide=True)

        self.username_frame.grid(row=0, column=0, padx=10)
        self.password_frame.grid(row=0, column=1, padx=10)

        login_input_frame.grid(row=1, column=0)

        login_button_frame = ttk.Frame(self.window)
        self.configureFrame(login_button_frame,1,2,self.background_color_hex)

        login_button = ttk.Button(master=login_button_frame, text="Login", command=self.attemptLogin)
        login_button.grid(row=0, column=0,padx=50)

        self.style.configure("BW.TCheckbutton", background=self.background_color_hex)
        remember_me_check_button = ttk.Checkbutton(master=login_button_frame, text="Remember Me", variable=self.rememberMe, onvalue=1, offvalue=0, style="BW.TCheckbutton")
        remember_me_check_button.grid(row=0,column=1,padx=20)

        login_button_frame.grid(row=2, column=0)

    def openInvalidLoginWindow(self):
        """
        Generates an invalid login window
        """

        top = tk.Toplevel(self.window)
        top.configure(background=self.background_color_hex)
        top.geometry("100x50")
        self.centerWindow(top)

        top.rowconfigure(list(range(1)), minsize=20, weight=1)
        top.columnconfigure(list(range(1)), minsize=20, weight=1)
        top.grab_set()
        top.title("Invalid Login")

        self.style.configure("BW.TLabel", background=self.background_color_hex)
        label = ttk.Label(master=top, text="Invalid login.", style="BW.TLabel")

        label.grid(row=0, column=0)

    def attemptLogin(self):
        self.login = Login(self.username.get(), self.password.get())
        if(Spout.verifyLogin(self.login)):
            self.subject_manager.createSpout()
            if(self.sessionType.get() == ""):
                self.openSessionSelectionWindow()
            else:
                self.openMainWindow()
        else:
            self.openInvalidLoginWindow()

    # Session Selection window functions
    def configureSessionSelectionWindow(self, window, title, rows, cols, background_color):
        """
        Configures a window object which holds all the frames and buttons. Can store rows*cols widgets

        Parameters
        ----------
        window : tk.Tk
            Window object to configure
        title : string
            Title of the window
        rows : int
            Number of rows in the window
        cols : int
            Number of columns in the window
        background_color : string
            Hex code or RGB tuple for the background color of the window
        """

        self.sessionType.set("")

        window.title(title)
        window.configure(background=background_color)
        window.geometry("500x300")
        window.rowconfigure(list(range(rows)), minsize=50,weight=1)
        window.columnconfigure(list(range(cols)), minsize=50, weight=1)

    def openSessionSelectionWindow(self):

        if(hasattr(self, 'action_manager')):
            if(self.action_manager.active):
                self.display("Please wait for the current action to finish before selecting a new session.")
                return

            if(self.action_manager.getActionState() != "" and not self.action_manager.active):
                self.action_manager.setActionState("")

        self.clearWindow(self.window)
        self.configureSessionSelectionWindow(self.window, 'Session Selection', 2, 1, self.background_color_hex)

        self.style.configure("BW.TLabel", background=self.background_color_hex)
        session_label = ttk.Label(self.window,text="Session Selection",font=("Arial", 45), style="BW.TLabel")
        session_label.grid(row=0,column=0)

        button_frame = ttk.Frame(self.window)
        self.configureFrame(button_frame,2,3, self.background_color_hex)
        button_frame.grid(row=1, column=0)

        pipeline_button = ttk.Button(master=button_frame, text="Pipeline", command=lambda: self.setSessionType("pipeline"), style="BW.TButton", width=15)

        def logout():
            self.login = None
            self.username.set("")
            self.password.set("")
            self.rememberMe.set(False)

            self.clearWindow(self.window)
            self.window.geometry("650x200")
            self.openLoginWindow()

        logout_button = ttk.Button(master=button_frame, text="Logout", command=logout, style="BW.TButton")
        manipulate_button = ttk.Button(master=button_frame, text="Manipulate", command=lambda: self.setSessionType("manipulate"), style="BW.TButton", width=15)

        classifications_button = ttk.Button(master=button_frame, text="Classifications", command=lambda: self.setSessionType("classifications"), style="BW.TButton", width=15)

        logout_button.grid(row=0, column=1, padx=10, pady=10)
        pipeline_button.grid(row=1, column=0, padx=10)
        manipulate_button.grid(row=1, column=1, padx=10)
        classifications_button.grid(row=1, column=2, padx=10)

    def setSessionType(self, sessionType):
        self.sessionType.set(sessionType)
        self.openMainWindow()

    # Main window functions
    def configureMainWindow(self, window, title, rows, cols, background_color):
        """
        Configures a window object which holds all the frames and buttons. Can store rows*cols widgets

        Parameters
        ----------
        window : tk.Tk
            Window object to configure
        title : string
            Title of the window
        rows : int
            Number of rows in the window
        cols : int
            Number of columns in the window
        background_color : string
            Hex code or RGB tuple for the background color of the window
        """
        
        window.title(title)
        window.configure(background=background_color)
        window.geometry(self.default_window_size)
        window.rowconfigure(list(range(rows)), weight=1)
        window.columnconfigure(list(range(cols)), weight=1)

        # Get the index of the second to last row
        last_row = window.grid_size()[1] - 1
        #window.rowconfigure(last_row, minsize=400, weight=1)

    def openMainWindow(self):
        self.clearWindow(self.window)

        self.initializeFrames()
        self.initializeButtons()

        self.action_manager = ActionManager(self)

        if(self.sessionType.get() == "pipeline"):
            rows = 5
            cols = 4

            self.configureMainWindow(self.window, "unWISE-verse Pipeline", rows, cols, self.background_color_hex)

            """
            Lays out all the widgets onto the window using the grid align functionality.
            
            Window is 6x4 array.
            
            ----------------------------------------------------
            | projectID | targetFile | tarSearch  |session menu|
            ----------------------------------------------------
            |   setID   |manifestFile| manSearch  |save session|
            ----------------------------------------------------
            |datasettype|pngDirectory| dirSearch  |  metadata  |
            ----------------------------------------------------
            | manifest  |   upload   |    full    |   submit   |
            ----------------------------------------------------
            |  console  |  console   |  console   |   console  |
            ----------------------------------------------------
            |  progress |  progress  |  progress  |  progress  |
            ----------------------------------------------------
            """

            self.window.geometry("570x610")

            self.projectID_frame.grid(row=0, column=0, padx=10)
            self.subjectSetID_frame.grid(row=1, column=0, padx=10)

            self.targetFile_frame.grid(row=0, column=1, padx=10)
            self.manifestFile_frame.grid(row=1, column=1, padx=10)
            self.pngDirectory_frame.grid(row=2, column=1, padx=10)

            self.submit_button.grid(row=3, column=3, padx=10)

            self.manifest_button.grid(row=3, column=0, padx=10)
            self.upload_button.grid(row=3, column=1, padx=10)
            self.full_button.grid(row=3, column=2, padx=10)

            self.targetFile_button.grid(row=0, column=2, padx=10)
            self.manifestFile_button.grid(row=1, column=2, padx=10)
            self.pngDirectory_button.grid(row=2, column=2, padx=10)

            self.sessionSelectionMenu_button.grid(row=0, column=3, padx=10)
            self.saveSession_check_button.grid(row=1, column=3, padx=10)

            self.metadata_button.grid(row=2, column=3, padx=10, pady=10)
            self.datasetTypeOptionMenu_frame.grid(row=2, column=0, padx=10)

            self.action_manager.action_monitor.console.place(placement_type="grid")
            self.action_manager.action_monitor.progress_bar.place(placement_type="grid")

        elif(self.sessionType.get() == "manipulate"):
            rows = 1
            cols = 3

            self.configureMainWindow(self.window, "unWISE-verse Manipulation", rows, cols, self.background_color_hex)

            """
            Lays out all the widgets onto the window using the grid align functionality.
            
            Window is 6x4 array.
            
            ----------------------------------------------------
            | projectID | targetFile | tarSearch  |session menu|
            ----------------------------------------------------
            |   setID   |manifestFile| manSearch  |save session|
            ----------------------------------------------------
            |   help    |pngDirectory| dirSearch  |  metadata  |
            ----------------------------------------------------
            | manifest  |   upload   |    full    |   submit   |
            ----------------------------------------------------
            |  console  |  console   |  console   |   console  |
            ----------------------------------------------------
            |  progress |  progress  |  progress  |  progress  |
            ----------------------------------------------------
            """

            # Upper menu frame
            upper_menu_frame = ttk.Frame(self.window)
            self.configureFrame(upper_menu_frame, 1, 1, self.background_color_hex)
            upper_menu_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

            # Entry container frame
            entry_container_frame = ttk.Frame(upper_menu_frame)
            self.configureFrame(entry_container_frame, 2, 1, self.background_color_hex)

            # Set the entry container frame as the new parent frame of self.projectID_frame and self.subjectSetID_frame
            # Project ID entry
            self.projectID_frame, self.projectID_entry = self.makeEntryField(entry_container_frame, 'Project ID', self.projectID, self.background_color_hex)

            # Subject Set ID entry
            self.subjectSetID_frame, self.subjectSetID_entry = self.makeEntryField(entry_container_frame, 'Subject Set ID', self.subjectSetID, self.background_color_hex)

            # Reconfigure the projectID_frame and subjectSetID_frame to be in the new parent frame
            self.projectID_frame.grid(row=0, column=0, pady=6)
            self.subjectSetID_frame.grid(row=1, column=0, pady=6)

            entry_container_frame.pack(side=tk.LEFT)

            button_container_frame = ttk.Frame(upper_menu_frame)
            self.configureFrame(button_container_frame, 3, 1, self.background_color_hex)
            button_container_frame.pack(side=tk.RIGHT)

            self.sessionSelectionMenu_button = ttk.Button(master=button_container_frame, text="Selection Menu", command=self.openSessionSelectionWindow, style="BW.TButton", takefocus=0)
            self.saveSession_check_button = ttk.Checkbutton(master=button_container_frame, text="Save Session", variable=self.saveSession, onvalue=1, offvalue=0, style="BW.TCheckbutton", takefocus=0)

            self.sessionSelectionMenu_button.pack(pady=6)

            # Action Menu Button
            self.action_menu_button = ttk.Button(master=button_container_frame, text="Action Menu", command=self.openActionMenu, style="BW.TButton", takefocus=0)
            self.action_menu_button.pack(side=tk.TOP, pady=6)

            self.saveSession_check_button.pack(pady=6)

            self.subject_manager.place()

            self.action_manager.action_monitor.progress_bar.place(placement_type="pack")
            self.action_manager.action_monitor.console.place(placement_type="pack")

            self.window.geometry("570x920")

        elif(self.sessionType.get() == "classifications"):
            rows = 1
            cols = 3

            self.configureMainWindow(self.window, "unWISE-verse Classifications", rows, cols, self.background_color_hex)

            """
            Lays out all the widgets onto the window using the grid align functionality.

            Window is 6x4 array.

            ----------------------------------------------------
            | projectID | targetFile | tarSearch  |session menu|
            ----------------------------------------------------
            |   setID   |manifestFile| manSearch  |save session|
            ----------------------------------------------------
            |   help    |pngDirectory| dirSearch  |  metadata  |
            ----------------------------------------------------
            | manifest  |   upload   |    full    |   submit   |
            ----------------------------------------------------
            |  console  |  console   |  console   |   console  |
            ----------------------------------------------------
            |  progress |  progress  |  progress  |  progress  |
            ----------------------------------------------------
            """

            # Upper menu frame
            upper_menu_frame = ttk.Frame(self.window)
            self.configureFrame(upper_menu_frame, 1, 1, self.background_color_hex)
            upper_menu_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

            # Entry container frame
            entry_container_frame = ttk.Frame(upper_menu_frame)
            self.configureFrame(entry_container_frame, 2, 1, self.background_color_hex)

            # Set the entry container frame as the new parent frame of self.projectID_frame and self.subjectSetID_frame
            # Project ID entry
            self.projectID_frame, self.projectID_entry = self.makeEntryField(entry_container_frame, 'Project ID',
                                                                             self.projectID, self.background_color_hex)

            # workflow ID entry
            self.workflowID_frame, self.workflowID_entry = self.makeEntryField(entry_container_frame, 'Workflow ID', self.workflowID, self.background_color_hex)

            self.classification_manager.place()

            # Reconfigure the projectID_frame and subjectSetID_frame to be in the new parent frame
            self.projectID_frame.grid(row=0, column=0, pady=6)
            self.workflowID_frame.grid(row=1, column=0, pady=6)

            entry_container_frame.pack(side=tk.LEFT)

            button_container_frame = ttk.Frame(upper_menu_frame)
            self.configureFrame(button_container_frame, 3, 1, self.background_color_hex)
            button_container_frame.pack(side=tk.RIGHT)

            self.sessionSelectionMenu_button = ttk.Button(master=button_container_frame, text="Selection Menu",
                                                          command=self.openSessionSelectionWindow, style="BW.TButton",
                                                          takefocus=0)
            self.saveSession_check_button = ttk.Checkbutton(master=button_container_frame, text="Save Session",
                                                            variable=self.saveSession, onvalue=1, offvalue=0,
                                                            style="BW.TCheckbutton", takefocus=0)

            self.sessionSelectionMenu_button.pack(pady=6)

            self.saveSession_check_button.pack(pady=6)

            self.action_manager.action_monitor.progress_bar.place(placement_type="pack")
            self.action_manager.action_monitor.console.place(placement_type="pack")

            self.window.geometry("570x920")

    # Help window function
    def openHelpWindow(self):
        """
        Generates a help window with instructions on how to use the program
        """
        
        top= tk.Toplevel(self.window, background=self.background_color_hex)
        top.title("Help")

        self.style.configure("BW.TLabel", background=self.background_color_hex)
        ttk.Label(top, text=
                'How to use: Select pipeline mode from radio buttons. \n \
                * Download the unWISE data and generate a Zooniverse manifest without publishing - [manifest] \n \
                * Upload an existing manifest and its associated data to Zooniverse -[upload] \n \
                * Run the whole pipeline to generate a manifest from target list and then upload it to Zooniverse -[full] \n \
                \n \
                [manifest] : Only target filename and manifest filename field are required.\n \
                [upload] : Only project ID, subject set ID, and manifest filename are requred\n \
                [full] : All fields are required.',style="BW.TLabel").pack()

        self.centerWindow(top)

    # Overwrite manifest window functions
    def openOverwriteManifestWindow(self):
        """
        Generates an overwrite manifest window to confirm that the user wants to overwrite the preexisting manifest file.
        """

        top = tk.Toplevel(self.window, background=self.background_color_hex)

        self.centerWindow(top)

        top.rowconfigure(list(range(4)), minsize=20, weight=1)
        top.columnconfigure(list(range(6)), minsize=20, weight=1)

        top.grab_set()

        top.title("Warning")

        self.style.configure("BW.TFrame", background=self.background_color_hex)
        frame = ttk.Frame(master=top, style="BW.TFrame")
        frame.rowconfigure(list(range(1)), minsize=20, weight=1)
        frame.columnconfigure(list(range(2)), minsize=20, weight=1)

        self.style.configure("BW.TLabel", background=self.background_color_hex)
        label1 = ttk.Label(master=top, text=f"Warning: You are attempting to overwrite an existing manifest: {self.manifestFile.get()}", style="BW.TLabel")
        label2 = ttk.Label(master=top, text="Would you like to overwrite the existing manifest?", style="BW.TLabel")

        def overwriteManifestButtonPressed(value, popup):
            self.overwriteManifest.set(value)
            popup.destroy()

        yesButton = ttk.Button(master=frame, text="Yes", command= lambda : overwriteManifestButtonPressed(True,top))
        noButton = ttk.Button(master=frame, text="No", command=lambda: overwriteManifestButtonPressed(False,top))

        label1.grid(row=0, column=2)
        label2.grid(row=1,column=2)
        yesButton.grid(row=1, column=0, padx=5)
        noButton.grid(row=1, column=1, padx=5)

        frame.grid(row=2, column=2)
        yesButton.wait_variable(self.overwriteManifest)

    # Metadata window function
    def openMetadataWindow(self):
        """
        Generates a metadata window to allow the user to input metadata values for the currently selected dataset.
        """

        metadata_window = tk.Toplevel(self.window, background=self.background_color_hex)
        self.centerWindow(metadata_window)

        dataset_dict = get_available_astronomy_datasets()
        dataset_type = dataset_dict.get(self.datasetType.get(), None)

        if (dataset_type is None):
            self.display(f"Error: Dataset '{self.datasetType.get()}' not found.")
            return

        mutable_metadata_dict = dataset_type.mutable_columns_dict

        mutable_metadata = list(mutable_metadata_dict.keys())
        total_number_of_metadata = len(mutable_metadata)

        metadata_window.grab_set()
        metadata_window.title("Metadata")

        self.style.configure("BW.TLabel", background=self.background_color_hex)
        metadata_label = ttk.Label(master=metadata_window, text="Metadata", font=("Arial", 28), style="BW.TLabel")

        input_frame = ttk.Frame(master=metadata_window, style="BW.TFrame")

        # Configure the rows and columns of the window
        attribute_column_association_dict = self.action_manager.attribute_column_association_dict

        padx = 10
        pady = 0

        index = 0
        # Place the frame in the window at the next grid position, from the top left corner to the bottom right corner
        for metadata in mutable_metadata:
            input_field = mutable_metadata_dict[metadata]
            variable_name = attribute_column_association_dict.get(metadata, None)
            if(variable_name is None):
                self.display(f"Error: No UI variable found for column '{metadata}'.")
                continue

            variable = getattr(self, variable_name)

            input_field_frame, input_field_widget = input_field.create(input_frame, variable)


            # Place the input field in the window
            input_field_frame.grid(row=index // 4 + 2, column=index % 4, padx=padx, pady=pady)
            index += 1

        # Center the label and input frame in the window
        metadata_label.grid(row=0, column=0, columnspan=min(total_number_of_metadata, 4))
        input_frame.grid(row=1, column=0, columnspan=min(total_number_of_metadata, 4))

    # Action-related functions
    def openActionMenu(self):
        """
        Generates an action menu window to allow the user to select an action to perform.
        """

        top = tk.Toplevel(self.window, background=self.background_color_hex)
        top.geometry("400x200")
        self.centerWindow(top)

        top.rowconfigure(list(range(3)), weight=1)
        top.columnconfigure(list(range(1)), weight=1)

        top.title("Action Menu")

        self.style.configure("BW.TLabel", background=self.background_color_hex)
        action_label = ttk.Label(master=top, text="Action Menu",font=("Arial", 28), style="BW.TLabel")
        action_label.grid(row=0,column=0)

        # Create the buttons for the action menu
        self.current_action_submit_button = None

        self.current_action_field_inputs_dict = {}

        def createActionSubMenu(action_name, input_names):
            top.destroy()

            sub_menu = tk.Toplevel(self.window, background=self.background_color_hex)
            sub_menu.geometry("400x240")
            self.centerWindow(sub_menu)

            sub_menu.rowconfigure(list(range(3)), weight=1)
            sub_menu.columnconfigure(list(range(1)), weight=1)

            sub_menu.title(action_name)

            self.style.configure("BW.TLabel", background=self.background_color_hex)
            sub_menu_label = ttk.Label(master=sub_menu, text=action_name,font=("Arial", 28), style="BW.TLabel")
            sub_menu_label.pack(side=tk.TOP, pady=10)

            # Create the buttons for the sub menu
            for input_name in input_names:
                input_entry_frame, input_entry = self.makeEntryField(sub_menu, input_name, tk.StringVar(), self.background_color_hex)
                input_entry_frame.pack()
                self.current_action_field_inputs_dict.update({input_name: input_entry})

            # Create the submit button

            def submit_action():
                self.perform(action_name)

            self.current_action_submit_button = ttk.Button(master=sub_menu, text="Submit", command=submit_action, style="BW.TButton", takefocus=0)
            self.current_action_submit_button.pack(side=tk.BOTTOM, pady=10)

        # Make a button frame
        button_frame = ttk.Frame(master=top)

        self.configureFrame(button_frame, 3, 2, self.background_color_hex)

        button_frame.grid(row=1, column=0)

        # Create modify field name button
        modify_field_name_button = ttk.Button(master=button_frame, text="Modify Field Name", command=lambda: createActionSubMenu("Modify Field Name", ["Current Field Names", "New Field Names"]), style="BW.TButton", takefocus=0)
        modify_field_name_button.grid(row=0, column=0, pady=10)

        # Create modify field value button
        modify_field_value_button = ttk.Button(master=button_frame, text="Modify Field Value", command=lambda: createActionSubMenu("Modify Field Value", ["Field Names", "New Values"]), style="BW.TButton", takefocus=0)
        modify_field_value_button.grid(row=1, column=0, pady=10)

        # Download Subject Gif
        download_gif_button = ttk.Button(master=button_frame, text="Download Subject GIF", command=lambda: createActionSubMenu("Download Subject GIF", ["Download Directory", "Speed (ms/frame)"]), style="BW.TButton", takefocus=0)
        download_gif_button.grid(row=2, column=0, pady=10)

        # Remove subjects from subject set
        remove_subjects_button = ttk.Button(master=button_frame, text="Remove Subjects", command=lambda: createActionSubMenu("Remove Subjects", []), style="BW.TButton", takefocus=0)
        remove_subjects_button.grid(row=0, column=1, pady=10)

        # Delete subjects from subject set
        delete_subjects_button = ttk.Button(master=button_frame, text="Delete Subjects", command=lambda: createActionSubMenu("Delete Subjects", []), style="BW.TButton", takefocus=0)
        delete_subjects_button.grid(row=1, column=1, pady=10)

    def openConfirmationWindow(self, confirmation_text, user_response):
        """
        Generates a confirmation window to confirm that the user wants to perform an action.

        Parameters
        ----------
        confirmation_text : string
            The text to display in the confirmation window.
        user_response : tk.BooleanVar
            The variable to store the user's response.
        """

        top = tk.Toplevel(self.window, background=self.background_color_hex)
        top.geometry("400x200")
        self.centerWindow(top)

        top.rowconfigure(list(range(3)), weight=1)
        top.columnconfigure(list(range(1)), weight=1)

        top.title("Confirmation")

        self.style.configure("BW.TLabel", background=self.background_color_hex)
        label = ttk.Label(master=top, text=confirmation_text, style="BW.TLabel")
        label.grid(row=0, column=0)

        # Button Frame
        button_frame = ttk.Frame(master=top)
        button_frame.grid(row=1, column=0)

        yes_button = ttk.Button(master=button_frame, text="Yes", command=lambda: user_response.set(True))
        no_button = ttk.Button(master=button_frame, text="No", command=lambda: user_response.set(False))

        yes_button.grid(row=0, column=0)
        no_button.grid(row=0, column=1)

        top.grab_set()
        yes_button.wait_variable(user_response)

        # Close the window
        top.destroy()

    def perform(self, action_name):
        self.action_manager.setActionState(action_name)
        action_thread = threading.Thread(target=self.performAction)
        action_thread.start()

    def performAction(self):
        if(not self.action_manager.active):
            time_format = "%Y-%m-%d %H:%M:%S"
            start = datetime.now()
            self.display(f"Started process at {start.strftime(time_format)}")
            self.action_manager.perform()
            end = datetime.now()
            self.display(f"Ended process at {end.strftime(time_format)}")
            total_seconds = round((end - start).total_seconds(), 2)

            def formatTime(seconds):
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                seconds = round(seconds % 60, 2)
                return hours, minutes, seconds

            # Format the time as a string
            hours, minutes, seconds = formatTime(total_seconds)

            if (hours > 0):
                hours_str = "hours" if hours > 1 else "hour"
                minutes_str = "minutes" if minutes > 1 else "minute"
                seconds_str = "seconds" if(seconds > 1 or seconds < 1) else "second"
                self.display(f"Total time elapsed: {hours} {hours_str}, {minutes} {minutes_str}, {seconds} {seconds_str}")

            elif (minutes > 0):
                minutes_str = "minutes" if minutes > 1 else "minute"
                seconds_str = "seconds" if (seconds > 1 or seconds < 1) else "second"
                self.display(f"Total time elapsed: {minutes} {minutes_str}, {seconds} {seconds_str}")
            else:
                seconds_str = "seconds" if (seconds > 1 or seconds < 1) else "second"
                self.display(f"Total time elapsed: {seconds} {seconds_str}")

class Session():

    def __init__(self, UI):

        # List of the variable names to save
        self.variable_names = ['action_state', 'login', 'projectID', 'subjectSetID', 'workflowID', 'targetFile', 'manifestFile', 'pngDirectory', 'saveSession', 'rememberMe', 'datasetType', 'sessionType', 'requestOnline', 'gifSliderValue']

        # Add all the metadata variables to the list of variable names
        mutable_columns = getAllMutableColumns()
        attribute_column_association_dict = getAssociatedUIAttributeDict(UI, mutable_columns)

        for variable_name in attribute_column_association_dict.values():
            self.variable_names.append(variable_name)

        self.variable_types_dict = {}

        self.reviveSession(UI)

    def saveUIVariables(self, UI):
        for name in self.variable_names:
            attribute = getattr(UI, name)
            self.variable_types_dict[name] = type(attribute)
            if(isinstance(attribute, tk.Variable)):
                setattr(self, name, copy(attribute.get()))
            else:
                setattr(self, name, copy(attribute))

    def setUIVariables(self, UI):
        for name in self.variable_names:
            attribute = getattr(self, name)
            if(issubclass(self.variable_types_dict[name], tk.Variable)):
                UI.__dict__[name].set(copy(attribute))
            else:
                setattr(UI, name, copy(attribute))

    def save(self, UI):

        if(not UI.rememberMe.get()):
            UI.login = None

        self.saveUIVariables(UI)
        saved_session_file = open("saved_session.pickle", "wb")
        pickle.dump(self, saved_session_file)
        saved_session_file.close()

    def periodicSaveSession(self, UI, delay=10):
        while(not UI.exitRequested):
            self.save(UI)
            time.sleep(delay)

    def savedSessionExists(self):
        return os.path.exists("saved_session.pickle")

    def reviveSession(self, UI):
        if(self.savedSessionExists()):
            saved_session_file = open("saved_session.pickle", "rb")
            revived_session = pickle.load(saved_session_file)
            saved_session_file.close()

            # Bring back saved variables
            revived_session.setUIVariables(UI)

            if(UI.rememberMe.get()):
                UI.username.set(UI.login.username)
                UI.password.set(UI.login.password)

        else:
            self.saveUIVariables(UI)

    def delete(self):
        if(self.savedSessionExists()):
            os.remove("saved_session.pickle")
