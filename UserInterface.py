# -*- coding: utf-8 -*-
"""
Created on Mon Jun 13 10:14:59 2022

@author: Noah Schapera
"""
import os
import sys
import threading
from tkinter import ttk
import tkinter as tk
from copy import copy
from tkinter import filedialog as fd
from tkinter.scrolledtext import ScrolledText
from tkinter.colorchooser import askcolor
import ZooniversePipeline
import pickle
import Data
from datetime import datetime

'''
full pipeline:
    username
    password
    project ID
    subject set ID
    target set name
    manifest name


generate manifest:
    target set name
    manifest name
    
publish to zooniverse:
    username
    password
    project ID
    subject set ID
    manifest name
    
'''
    
class UserInterface:
    
    def __init__(self):
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
        self.varInit()

        if(self.rememberMe.get()):
            self.attemptLogin()
        else:
            self.openLoginWindow()

        self.center_window(self.window)
        self.window.mainloop()

    def quit(self, display=True):
        if(display):
            self.updateConsole("Attempting to quit...")
        if(self.canSafelyQuit):
            self.exitRequested = True
            if (self.saveSession.get()):
                self.session.save(self)
                if(display):
                    print("Session saved.")
            else:
                self.session.delete()

            def destroy_window(window):
                for thread in threading.enumerate():
                    if(thread != threading.main_thread() and thread != threading.current_thread()):
                        thread.join()
                window.quit()


            # Create a thread to wait for all threads to finish and then destroy the window
            threading.Thread(target=destroy_window, args=(self.window,)).start()
        else:
            self.window.after_idle(self.quit, False)



    def configure_login_window(self, window, title, rows, cols, background_color):
        '''
        Configures a window object which holds all of the frames and buttons. Can store rows*cols widgets

        Parameters
        ----------
        rows : int
            Number of rows in the window
        cols : int
            Number of columns in the window
        title : string
            Title of the window

        Returns
        -------
        None.

        '''
        window.title(title)
        window.configure(background=background_color)
        window.rowconfigure(list(range(rows)),minsize=50,weight=1)
        window.columnconfigure(list(range(cols)), minsize=50, weight=1)

    def openLoginWindow(self):
        self.configure_login_window(self.window, 'Data Pipeline: Login', 3, 1, self.background_color_hex)

        login_input_frame = ttk.Frame(self.window)
        self.style.configure("BW.TLabel", background=self.background_color_hex)
        login_label = ttk.Label(self.window,text="ZPipe",font=("Arial", 75), style="BW.TLabel")
        login_label.grid(row=0,column=0)

        self.configure_frame(login_input_frame,1,2,self.background_color_hex)

        # username frame and entry
        self.username_frame, self.username_entry = self.makeEntryField(login_input_frame, 'Zooniverse Username',self.username, self.background_color_hex)
        # password frame and entry
        self.password_frame, self.password_entry = self.makeEntryField(login_input_frame, 'Zooniverse Password', self.password, self.background_color_hex, hide=True)

        self.username_frame.grid(row=0, column=0, padx=10)
        self.password_frame.grid(row=0, column=1, padx=10)

        login_input_frame.grid(row=1, column=0)

        login_button_frame = ttk.Frame(self.window)
        self.configure_frame(login_button_frame,1,2,self.background_color_hex)

        login_button = ttk.Button(master=login_button_frame, text="Login", command=self.attemptLogin)
        login_button.grid(row=0, column=0,padx=50)

        self.style.configure("BW.TCheckbutton", background=self.background_color_hex)
        remember_me_check_button = ttk.Checkbutton(master=login_button_frame, text="Remember Me", variable=self.rememberMe, onvalue=1, offvalue=0, style="BW.TCheckbutton")
        remember_me_check_button.grid(row=0,column=1,padx=20)

        login_button_frame.grid(row=2, column=0)

    def attemptLogin(self):
        if(ZooniversePipeline.verifyLogin(self)):
            self.openMainWindow()
        else:
            self.open_invalid_login_popup()

    def configure_main_window(self, window, title, rows, cols, background_color):
        '''
        Configures a window object which holds all of the frames and buttons. Can store rows*cols widgets

        Parameters
        ----------
        rows : int
            Number of rows in the window
        cols : int
            Number of columns in the window
        title : string
            Title of the window

        Returns
        -------
        None.

        '''
        window.title(title)
        window.configure(background=background_color)
        window.geometry(self.default_window_size)
        window.rowconfigure(list(range(rows)),minsize=50,weight=1)
        window.columnconfigure(list(range(cols)), minsize=50, weight=1)
        window.rowconfigure(4, minsize=400, weight=1)

    def openMainWindow(self):
        self.clear_window(self.window)
        self.configure_main_window(self.window,"Data Pipeline",4,4, self.background_color_hex)
        self.center_window(self.window)
        self.setupMainWindow()

    def clear_window(self,window):
        for widget in window.winfo_children():
            widget.destroy()

    def center_window(self,window):
        window.update_idletasks()
        # get screen width and height
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()

        # calculate position x and y coordinates
        x = (screen_width / 2) - (window.winfo_width() / 2)
        y = (screen_height / 2) - (window.winfo_height() / 2)

        window.geometry("+%d+%d" %(x,y))

    def configure_frame(self, frame, rows, cols, background_color):
        '''
        Configures a frame object which holds all of the frames and buttons. Can store rows*cols widgets

        Parameters
        ----------
        rows : int
            Number of rows in the window
        cols : int
            Number of columns in the window
        title : string
            Title of the window

        Returns
        -------
        None.

        '''
        self.style.configure("BW.TFrame", background=background_color)
        frame.configure(style="BW.TFrame")
        frame.rowconfigure(list(range(rows)), weight=1)
        frame.columnconfigure(list(range(cols)), weight=1)

    def setState(self, value):
        self.state.set(value)

    def varInit(self):
        '''
        Initializes variables modified throughout program runtime. 

        Returns
        -------
        None.

        '''

        #TKinter Variables
        self.state = tk.StringVar(value="f")
        self.username = tk.StringVar(value="")
        self.password = tk.StringVar(value="")
        self.projectID = tk.StringVar(value="")
        self.subjectSetID = tk.StringVar(value="")
        self.targetFile = tk.StringVar(value="")
        self.manifestFile = tk.StringVar(value="")
        self.scaleFactor = tk.StringVar(value="12")
        self.FOV = tk.StringVar(value="120")
        self.pngDirectory = tk.StringVar(value="pngs")
        self.minBright = tk.StringVar(value="-15")
        self.maxBright = tk.StringVar(value="120")
        self.gridCount = tk.StringVar(value="5")
        self.gridType = tk.StringVar(value="Solid")

        self.printProgress = tk.BooleanVar(value=False)
        self.saveSession = tk.BooleanVar(value=True)
        self.overwriteManifest = tk.BooleanVar(value=False)
        self.addGrid = tk.BooleanVar(value=True)
        self.ignorePartialCutouts = tk.BooleanVar(value=True)
        self.rememberMe = tk.BooleanVar(value=False)

        self.gridColor = (128,0,0)

        self.session = Session(self)

        self.canSafelyQuit = True

        self.performingState = False

        self.exitRequested = False
        

    def frameInit(self):
        '''
        Creates all of the entry frames (label and text entry) by calling the makeEntryField function

        Returns
        -------
        None.

        '''

        #proj ID entry
        self.projectID_frame,self.projectID_entry=self.makeEntryField(self.window,'Project ID',self.projectID, self.background_color_hex)
        #set ID entry
        self.subjectSetID_frame,self.subjectSetID_entry=self.makeEntryField(self.window,'Subject Set ID',self.subjectSetID, self.background_color_hex)
        #targets entry
        self.targetFile_frame,self.targetFile_entry=self.makeEntryField(self.window,'Target List Filename',self.targetFile, self.background_color_hex)
        #manifest entry
        self.manifestFile_frame,self.manifestFile_entry=self.makeEntryField(self.window,'Manifest Filename',self.manifestFile,self.background_color_hex)
        # png directory entry
        self.pngDirectory_frame, self.pngDirectory_entry = self.makeEntryField(self.window, 'PNG Directory',self.pngDirectory,self.background_color_hex)

        #console printouts
        self.console_scrolled_text_frame = ttk.Frame(master=self.window)
        self.console_scrolled_text = ScrolledText(master=self.console_scrolled_text_frame, height=30, width=90, font=("consolas", "8", "normal"),state=tk.DISABLED)
        
    def setupMainWindow(self):
        self.frameInit()
        self.buttonInit()
        '''
        Lays out all of the widgets onto the window using the grid align functionality.
        
        Window is 4x4 array.
        
        ----------------------------------------------------
        | projectID | targetFile | tarSearch  |  print out |
        ----------------------------------------------------
        |   setID   |manifestFile| manSearch  |save session|
        ----------------------------------------------------
        |   help    |pngDirectory| dirSearch  |  metadata  |
        ----------------------------------------------------
        | manifest  |   upload   |    full    |   submit   |
        ----------------------------------------------------
        |  console  |  console   |  console   |   console  |
        ----------------------------------------------------

        Returns
        -------
        None.

        '''
        
        self.projectID_frame.grid(row=0, column=0, padx=10)
        self.subjectSetID_frame.grid(row=1, column=0, padx=10)
        
        self.targetFile_frame.grid(row=0, column=1, padx=10)
        self.manifestFile_frame.grid(row=1, column=1, padx=10)
        self.pngDirectory_frame.grid(row=2, column=1, padx=10)

        self.help_button.grid(row=2, column=0, padx=10)
        self.submit_button.grid(row=3, column=3, padx=10)
        
        self.manifest_button.grid(row=3, column=0, padx=10)
        self.upload_button.grid(row=3, column=1, padx=10)
        self.full_button.grid(row=3, column=2, padx=10)
        
        self.targetFile_button.grid(row=0, column=2, padx=10)
        self.manifestFile_button.grid(row=1, column=2, padx=10)
        self.pngDirectory_button.grid(row=2, column=2, padx=10)

        self.printProgress_check_button.grid(row=0, column=3, padx=10)
        self.saveSession_check_button.grid(row=1, column=3, padx=10)

        self.metadata_button.grid(row=2, column=3, padx=10, pady=10)

        self.toggleConsole()

    def buttonInit(self):

        '''
        Makes all the buttons we use for the UI - connects each button to a function
        Note - button functions cannot have arguments which is why I had to wrap this all in a class. Ugh. 

        Returns
        -------
        None.

        '''

        self.submit_button = ttk.Button(master=self.window, text="Submit",command= lambda: threading.Thread(target=self.performState).start())
        self.help_button = ttk.Button(master=self.window, text="Help", command=self.open_help_popup)

        self.style.configure("BW.TRadiobutton", background=self.background_color_hex)
        self.manifest_button = ttk.Radiobutton(master=self.window, text="Manifest", variable=self.state, value="m", style="BW.TRadiobutton")
        self.upload_button = ttk.Radiobutton(master=self.window, text="Upload", variable=self.state, value="u", style="BW.TRadiobutton")
        self.full_button = ttk.Radiobutton(master=self.window, text="Full", variable=self.state,value="f", style="BW.TRadiobutton")

        self.targetFile_button = ttk.Button(master=self.window, text="Search", command=self.select_file_target)
        self.manifestFile_button = ttk.Button(master=self.window, text="Search", command=self.select_file_manifest)
        self.pngDirectory_button = ttk.Button(master=self.window, text="Search", command=self.select_png_directory)

        self.metadata_button = ttk.Button(master=self.window, text="Metadata", command=self.open_metadata_popup)

        self.style.configure("BW.TCheckbutton", background=self.background_color_hex)
        self.printProgress_check_button = ttk.Checkbutton(master=self.window, text="Print Progress", command=self.toggleConsole, variable=self.printProgress, onvalue=1, offvalue=0, style="BW.TCheckbutton")
        self.saveSession_check_button = ttk.Checkbutton(master=self.window, text="Save Session", variable=self.saveSession, onvalue=1, offvalue=0, style="BW.TCheckbutton")

    def toggleConsole(self):
        if (self.printProgress.get()):
            self.window.geometry("600x625")
            self.console_scrolled_text_frame.grid(row=4, column=0, columnspan=5)
            self.console_scrolled_text.grid(row=0,column=0)
        else:
            self.console_scrolled_text_frame.destroy()
            self.window.geometry(self.default_window_size)
            self.console_scrolled_text_frame = ttk.Frame(master=self.window)
            self.console_scrolled_text = ScrolledText(master=self.console_scrolled_text_frame, height=30, width=90, font=("consolas", "8", "normal"), state=tk.DISABLED)

    def select_file_manifest(self):
        filetypes = (
            ('CSV files', '*.csv'),
            ('All files', '*.*')
        )

        filename = fd.askopenfilename(
            title='Open a file',
            initialdir='/',
            filetypes=filetypes)
        
        self.manifestFile_entry.delete(0,tk.END)
        self.manifestFile_entry.insert(0,filename)
        
    def select_file_target(self):
        filetypes = (
            ('CSV files', '*.csv'),
            ('All files', '*.*')
        )

        filename = fd.askopenfilename(
            title='Open a file',
            initialdir='/',
            filetypes=filetypes)
        
        self.targetFile_entry.delete(0,tk.END)
        self.targetFile_entry.insert(0,filename)

    def select_png_directory(self):
        filename = fd.askdirectory(
            title='Select a directory',
            initialdir='/')

        self.pngDirectory_entry.delete(0, tk.END)
        self.pngDirectory_entry.insert(0, filename)

    def open_help_popup(self):
       '''
        Generates a help popup with instructions on how to use the program

        Returns
        -------
        None.

        '''

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

       self.center_window(top)

    def open_overwrite_manifest_popup(self):
        '''
        Generates an overwrite manifest popup

        Returns
        -------
        None.

        '''

        top = tk.Toplevel(self.window, background=self.background_color_hex)

        self.center_window(top)

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
        label2 = ttk.Label(master=top, text="Would you like to overwrite the exsiting manifest?", style="BW.TLabel")
        yesButton = ttk.Button(master=frame, text="Yes", command= lambda : self.overwriteManifestButtonPressed(True,top))
        noButton = ttk.Button(master=frame, text="No", command=lambda: self.overwriteManifestButtonPressed(False,top))

        label1.grid(row=0, column=2)
        label2.grid(row=1,column=2)
        yesButton.grid(row=1, column=0, padx=5)
        noButton.grid(row=1, column=1, padx=5)

        frame.grid(row=2, column=2)
        yesButton.wait_variable(self.overwriteManifest)

    def open_invalid_login_popup(self):
        '''
        Generates an invalid login popup

        Returns
        -------
        None.

        '''

        top = tk.Toplevel(self.window)
        top.configure(background=self.background_color_hex)
        top.geometry("100x50")
        self.center_window(top)

        top.rowconfigure(list(range(1)), minsize=20, weight=1)
        top.columnconfigure(list(range(1)), minsize=20, weight=1)
        top.grab_set()
        top.title("Invalid Login")

        self.style.configure("BW.TLabel", background=self.background_color_hex)
        label = ttk.Label(master=top, text="Invalid login.", style="BW.TLabel")

        label.grid(row=0, column=0)

    def open_metadata_popup(self):
        '''
        Generates a metadata popup

        Returns
        -------
        None.

        '''

        top = tk.Toplevel(self.window, background=self.background_color_hex)
        top.geometry("440x300")
        self.center_window(top)

        top.rowconfigure(list(range(2)), weight=1)
        top.columnconfigure(list(range(1)), weight=1)
        top.grab_set()
        
        top.title("Metadata")

        self.style.configure("BW.TLabel", background=self.background_color_hex)
        metadata_label = ttk.Label(master=top, text="Metadata",font=("Arial", 28), style="BW.TLabel")
        metadata_label.grid(row=0,column=0)
        self.style.configure("BW.TFrame", background=self.background_color_hex)
        input_frame = ttk.Frame(master=top, style="BW.TFrame")
        input_frame.rowconfigure(list(range(4)), weight=1)
        input_frame.columnconfigure(list(range(3)), weight=1)
        input_frame.grid(row=1,column=0)

        # add grid checkbox
        self.style.configure("BW.TCheckbutton", background=self.background_color_hex)
        self.addGrid_check_button = ttk.Checkbutton(master=input_frame, text='Add Grid', variable=self.addGrid, onvalue=1, offvalue=0, style="BW.TCheckbutton")
        self.addGrid_check_button.grid(row=1, column=0,padx=10,pady=10)

        # grid count entry
        self.gridCount_frame, self.gridCount_entry = self.makeEntryField(input_frame, 'Grid Count', self.gridCount, self.background_color_hex)
        self.gridCount_entry.config(width=15)
        self.gridCount_frame.grid(row=1,column=1,padx=10,pady=10)

        # grid type option menu
        options = ["Solid","Intersection","Dashed"]
        self.gridTypeOptionMenu_frame, self.gridTypeOptionMenu = self.makeOptionMenuField(input_frame, "Grid Type", self.gridType, options, self.background_color_hex)
        self.gridTypeOptionMenu_frame.grid(row=1, column=2, padx=10, pady=10)

        # grid color selector button
        self.colorSelectorButton = ttk.Button(master=input_frame, text="Grid Color", command=self.getGridColor)
        self.colorSelectorButton.grid(row=2, column=2, padx=10, pady=10)

        # ignore partial cutouts checkbox
        self.style.configure("BW.TCheckbutton", background=self.background_color_hex)
        self.ignorePartialCutouts_check_button = ttk.Checkbutton(master=input_frame, text='Ignore Partial Cutouts', variable=self.ignorePartialCutouts, onvalue=1, offvalue=0, style="BW.TCheckbutton")
        self.ignorePartialCutouts_check_button.grid(row=3, column=2, padx=10, pady=10)

        # scale factor entry
        self.scaleFactor_frame, self.scaleFactor_entry = self.makeEntryField(input_frame, 'Scale Factor',self.scaleFactor, self.background_color_hex)
        self.scaleFactor_entry.config(width=15)
        self.scaleFactor_frame.grid(row=2, column=0,padx=10,pady=10)

        # FOV entry
        self.FOV_frame, self.FOV_entry = self.makeEntryField(input_frame, 'FOV (arcseconds)', self.FOV, self.background_color_hex)
        self.FOV_entry.config(width=15)
        self.FOV_frame.grid(row=3, column=0,padx=10,pady=10)

        self.minBright_frame, self.minBright_entry = self.makeEntryField(input_frame, 'Minbright (Vega nmags)', self.minBright, self.background_color_hex)
        self.minBright_entry.config(width=15)
        self.minBright_frame.grid(row=2, column=1,padx=10,pady=10)
        
        self.maxBright_frame, self.maxBright_entry = self.makeEntryField(input_frame, 'Maxbright (Vega nmags)', self.maxBright, self.background_color_hex)
        self.maxBright_entry.config(width=15)
        self.maxBright_frame.grid(row=3, column=1,padx=10,pady=10)

    def getGridColor(self):
        color_representations = askcolor(title="Choose a grid color", initialcolor=self.gridColor)
        if(color_representations == (None,None)):
            return
        else:
            RGB_color, hex_color = color_representations
            self.gridColor = RGB_color

    def overwriteManifestButtonPressed(self, value, popup):
        self.overwriteManifest.set(value)
        popup.destroy()

    def warning(self):
        '''
         Warning

         Returns
         -------
         True -- not enough fields filled out or filled out correctly
         False -- No error, proceed

         '''
        warningFlag=0
        
        try:
            int(self.scaleFactor.get())
        except ValueError:
            warningFlag=5

        try:
            float(self.FOV.get())
        except:
            warningFlag=6

        if (not os.path.isdir(self.pngDirectory.get())):
            try:
                os.mkdir(self.pngDirectory.get())
            except:
                warningFlag = 7

        try:
            int(self.gridCount.get())
        except ValueError:
            warningFlag=8

        if self.state.get() == '':
            warningFlag=1
            whatToSay='Please select a program state!'
        elif (self.state.get() == 'm') and ((self.targetFile.get() == '' or self.manifestFile.get() == '')):
            warningFlag=2
            whatToSay='Target file and manifest file fields need values!'
        elif (self.state.get() == 'u') and ((self.username.get() == '' or self.password.get() == '' or self.projectID.get() == '' or self.subjectSetID.get() == '' or self.manifestFile.get() == '')):
            warningFlag=3
            whatToSay='Username, password, project ID, subject set ID, and manifest filename fields need values!'
        elif (self.state.get() == 'f') and ((self.username.get() == '' or self.password.get() == '' or self.projectID.get() == '' or self.subjectSetID.get() == '' or self.manifestFile.get() == '' or self.targetFile.get() == '')):
            warningFlag=4
            whatToSay='All fields need to be filled out!'
        elif warningFlag==5:
            whatToSay='Input an integer scaling factor!'
        elif warningFlag==6:
            whatToSay='Input a single numerical value for FOV!'
        elif warningFlag==7:
            whatToSay='Input a valid directory!'
        elif warningFlag==8:
            whatToSay='Input a numerical value for grid count!'
        else:
            return False

        if warningFlag!=0:
            warning_window = tk.Toplevel(self.window)
            warning_window.title("Warning!")
            ttk.Label(warning_window,text=whatToSay).pack()
            self.center_window(warning_window)
            return True

    def verifyInputs(self):
        '''
        Validates form input and returns a boolean

        Returns
        -------
        None.

        '''
        
        isError=self.warning()

        return not isError

    def performState(self):
        if(not self.performingState):
            if (self.verifyInputs()):
                if(self.printProgress.get()):
                    now = datetime.now()
                    self.updateConsole(f"Started pipeline at: {now}")
                metadata_dict = {f"{Data.Metadata.privatization_symbol}ADDGRID": int(self.addGrid.get()),
                                 f"{Data.Metadata.privatization_symbol}SCALE": self.scaleFactor.get(),
                                 "FOV": self.FOV.get(),
                                 f"{Data.Metadata.privatization_symbol}PNG_DIRECTORY": self.pngDirectory.get(),
                                 f"{Data.Metadata.privatization_symbol}MINBRIGHT": self.minBright.get(),
                                 f"{Data.Metadata.privatization_symbol}MAXBRIGHT": self.maxBright.get(),
                                 f"{Data.Metadata.privatization_symbol}GRIDCOUNT": int(self.gridCount.get()),
                                 f"{Data.Metadata.privatization_symbol}GRIDTYPE": self.gridType.get(),
                                 f"{Data.Metadata.privatization_symbol}GRIDCOLOR": str(self.gridColor)}

                # Creates metadata-target csv file
                metadata_target_filename = self.targetFile.get().split('.')[0] + '-metadata-target.csv'
                self.metadataTargetFile = tk.StringVar(value=metadata_target_filename)
                ZooniversePipeline.mergeTargetsAndMetadata(self.targetFile.get(), metadata_dict, self.metadataTargetFile.get())

                if (self.state.get() == 'f'):
                    self.performingState = True
                    ZooniversePipeline.fullPipeline(self)
                    self.performingState = False
                elif (self.state.get() == 'm'):
                    self.performingState = True
                    ZooniversePipeline.generateManifest(self)
                    self.performingState = False
                elif (self.state.get() == 'u'):
                    self.performingState = True
                    ZooniversePipeline.publishToZooniverse(self)
                    self.performingState = False
                # Calls interface to determine how the program should run.
                else:
                    print("You broke the pipeline :(")
        else:
            self.updateConsole("Pipeline is already active. Please wait until it is finished.")

    def updateConsole(self, new_text):
        self.console_scrolled_text.config(state=tk.NORMAL)
        self.console_scrolled_text.insert(tk.END, f"{new_text}\n")
        self.console_scrolled_text.see(tk.END)
        self.console_scrolled_text.config(state=tk.DISABLED)
            
    def printout(self):
        '''
        Prints out all fields for the UI to console

        Returns
        -------
        None.

        '''
        print('user: '+self.username.get())
        print('pass: '+self.password.get())
        print('proj: '+self.projectID.get())
        print('set: '+self.subjectSetID.get())
        print('target: '+self.targetFile.get())
        print('manifest: '+self.manifestFile.get())
        print('state: '+self.state.get())
        print('print progress: ' + str(self.printProgress.get()))
        print('save session: ' + str(self.saveSession.get()))

    def makeEntryField(self, window, label_title, variable, background_color, hide=False):
        '''
        Generates a new frame with label and text entry field. 

        Parameters
        ----------
        label_title : string
            The title for the frame, displayed above the text entry.
        hide : boolean, optional
            Shows * in the text entry (e.g. to hide a password). The default is False.

        Returns
        -------
        frame : tkinter Frame object
            Contains Entry and Label widget
        entry : tkinter Entry widget
            User entry field.
        '''
        self.style.configure("BW.TFrame", background=background_color)
        frame =ttk.Frame(master=window, style="BW.TFrame")

        if(not hide):
            entry=ttk.Entry(master=frame, textvariable=variable)
        else:
            entry=ttk.Entry(master=frame, show='*', textvariable=variable)
        self.style.configure("BW.TLabel", background=background_color)
        label=ttk.Label(master=frame, text=label_title, style="BW.TLabel")
        
        label.grid(row=0, column=0)
        entry.grid(row=1, column=0)
        
        return frame, entry

    def makeOptionMenuField(self, window, label_title, variable, options_list, background_color):
        '''
        Generates a new frame with label and option menu field.

        Parameters
        ----------
        label_title : string
            The title for the frame, displayed above the text entry.

        Returns
        -------
        frame : tkinter Frame object
            Contains Option menu and Label widget
        entry : tkinter OptionMenu widget
            Option menu field
        '''
        self.style.configure("BW.TFrame", background=background_color)
        frame = ttk.Frame(master=window, style="BW.TFrame")

        self.style.configure("BW.TMenubutton", background="white")
        option_menu = ttk.OptionMenu(frame, variable, "Solid", *options_list)
        option_menu.config(style="BW.TMenubutton")
        self.style.configure("BW.TLabel", background=background_color)
        label = ttk.Label(master=frame, text=label_title, style="BW.TLabel")

        label.grid(row=0, column=0)
        option_menu.grid(row=1, column=0)

        return frame, option_menu

class Session():

    def __init__(self, UI):
        self.reviveSession(UI)

    def saveUIVariables(self, UI):
        self.state = copy(UI.state.get())
        self.username = copy(UI.username.get())
        self.password = copy(UI.password.get())
        self.projectID = copy(UI.projectID.get())
        self.subjectSetID = copy(UI.subjectSetID.get())
        self.targetFile = copy(UI.targetFile.get())
        self.manifestFile = copy(UI.manifestFile.get())
        self.printProgress = copy(UI.printProgress.get())
        self.saveSession = copy(UI.saveSession.get())
        self.scaleFactor = copy(UI.scaleFactor.get())
        self.addGrid = copy(UI.addGrid.get())
        self.rememberMe = copy(UI.rememberMe.get())
        self.FOV = copy(UI.FOV.get())
        self.pngDirectory = copy(UI.pngDirectory.get())
        self.minBright = copy(UI.minBright.get())
        self.maxBright = copy(UI.maxBright.get())
        self.gridCount = copy(UI.gridCount.get())
        self.gridColor = copy(UI.gridColor)
        self.ignorePartialCutouts = copy(UI.ignorePartialCutouts.get())

    def setUIVariables(self, UI):
        UI.state.set(copy(self.state))
        UI.username.set(copy(self.username))
        UI.password.set(copy(self.password))
        UI.projectID.set(copy(self.projectID))
        UI.subjectSetID.set(copy(self.subjectSetID))
        UI.targetFile.set(copy(self.targetFile))
        UI.manifestFile.set(copy(self.manifestFile))
        UI.printProgress.set(copy(self.printProgress))
        UI.saveSession.set(copy(self.saveSession))
        UI.scaleFactor.set(copy(self.scaleFactor))
        UI.addGrid.set(copy(self.addGrid))
        UI.rememberMe.set(copy(self.rememberMe))
        UI.FOV.set(copy(self.FOV))
        UI.pngDirectory.set(copy(self.pngDirectory))
        UI.minBright.set(copy(self.minBright))
        UI.maxBright.set(copy(self.maxBright))
        UI.gridCount.set(copy(self.gridCount))
        UI.gridColor = copy(self.gridColor)
        UI.ignorePartialCutouts.set(copy(self.ignorePartialCutouts))

    def save(self,UI):
        self.saveUIVariables(UI)
        saved_session_file = open("saved_session.pickle", "wb")
        pickle.dump(self, saved_session_file)
        saved_session_file.close()

    def savedSessionExists(self):
        return os.path.exists("saved_session.pickle")

    def reviveSession(self, UI):
        if(self.savedSessionExists()):
            saved_session_file = open("saved_session.pickle", "rb")
            revived_session = pickle.load(saved_session_file)
            saved_session_file.close()

            # Bring back saved variables
            revived_session.setUIVariables(UI)
        else:
            self.saveUIVariables(UI)

    def delete(self):
        if(self.savedSessionExists()):
            os.remove("saved_session.pickle")
