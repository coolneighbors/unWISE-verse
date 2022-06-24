# -*- coding: utf-8 -*-
"""
Created on Mon Jun 13 10:14:59 2022

@author: Noah Schapera
"""
import os
import threading
import tkinter as tk
from copy import copy
from tkinter import filedialog as fd
from tkinter.scrolledtext import ScrolledText
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

    def quit(self):
        if(self.saveSession.get()):
            self.session.save(self)
            print("Session saved.")
        else:
            self.session.delete()

        self.window.destroy()

    def configure_login_window(self, window, title, rows, cols):
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
        window.rowconfigure(list(range(rows)),minsize=50,weight=1)
        window.columnconfigure(list(range(cols)), minsize=50, weight=1)

    def openLoginWindow(self):
        self.configure_login_window(self.window, 'Data Pipeline: Login', 3, 1)

        login_input_frame = tk.Frame(self.window)

        login_label = tk.Label(self.window,text="ZPipe",font=("Arial", 75))
        login_label.grid(row=0,column=0)

        self.configure_frame(login_input_frame,1,2)

        # username frame and entry
        self.username_frame, self.username_entry = self.makeEntryField(login_input_frame, 'Zooniverse Username',self.username)
        # password frame and entry
        self.password_frame, self.password_entry = self.makeEntryField(login_input_frame, 'Zooniverse Password', self.password, hide=True)

        self.username_frame.grid(row=0, column=0, padx=10)
        self.password_frame.grid(row=0, column=1, padx=10)

        login_input_frame.grid(row=1, column=0)

        login_button_frame = tk.Frame(self.window,)
        self.configure_frame(login_button_frame,1,2)

        login_button = tk.Button(master=login_button_frame, text="Login", command=self.attemptLogin)
        login_button.grid(row=0, column=0,padx=50)

        remember_me_check_button = tk.Checkbutton(master=login_button_frame, text="Remember Me", variable=self.rememberMe, onvalue=1, offvalue=0)
        remember_me_check_button.grid(row=0,column=1,padx=20)

        login_button_frame.grid(row=2, column=0)

    def attemptLogin(self):
        if(ZooniversePipeline.verifyLogin(self)):
            self.openMainWindow()
        else:
            self.open_invalid_login_popup()

    def configure_main_window(self, window, title, rows, cols):
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
        window.geometry(self.default_window_size)
        window.rowconfigure(list(range(rows)),minsize=50,weight=1)
        window.columnconfigure(list(range(cols)), minsize=50, weight=1)
        window.rowconfigure(4, minsize=400, weight=1)

    def openMainWindow(self):
        self.clear_window(self.window)
        self.configure_main_window(self.window,"Data Pipeline",4,4)
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

    def configure_frame(self, frame, rows, cols):
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
        self.scaleFactor = tk.StringVar(value="1")
        self.FOV = tk.StringVar(value="120")
        self.pngDirectory = tk.StringVar(value="pngs")
        self.minBright = tk.StringVar(value="-15")
        self.maxBright = tk.StringVar(value="120")

        self.printProgress = tk.BooleanVar(value=False)
        self.saveSession = tk.BooleanVar(value=True)
        self.overwriteManifest = tk.BooleanVar(value=False)
        self.addGrid = tk.BooleanVar(value=False)
        self.rememberMe = tk.BooleanVar(value=False)

        self.metadataTargetFile = tk.StringVar(value="metadata-target.csv")

        self.session = Session(self)
        

    def frameInit(self):
        '''
        Creates all of the entry frames (label and text entry) by calling the makeEntryField function

        Returns
        -------
        None.

        '''

        #proj ID entry
        self.projectID_frame,self.projectID_entry=self.makeEntryField(self.window,'Project ID',self.projectID)
        #set ID entry
        self.subjectSetID_frame,self.subjectSetID_entry=self.makeEntryField(self.window,'Subject Set ID',self.subjectSetID)
        #targets entry
        self.targetFile_frame,self.targetFile_entry=self.makeEntryField(self.window,'Target List Filename',self.targetFile)
        #manifest entry
        self.manifestFile_frame,self.manifestFile_entry=self.makeEntryField(self.window,'Manifest Filename',self.manifestFile)
        # png directory entry
        self.pngDirectory_frame, self.pngDirectory_entry = self.makeEntryField(self.window, 'PNG Directory',self.pngDirectory)

        
        #console printouts
        self.console_scrolled_text_frame = tk.Frame(master=self.window)
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
        |   help    |   submit   |            |            |
        ----------------------------------------------------
        | manifest  |   upload   |    full    |  metadata  |
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

        self.submit_button = tk.Button(master=self.window, text="Submit",command= lambda: threading.Thread(target=self.performState).start())
        self.help_button = tk.Button(master=self.window, text="Help", command=self.open_help_popup)

        self.manifest_button = tk.Radiobutton(master=self.window, text="Manifest", variable=self.state, value="m")
        self.upload_button = tk.Radiobutton(master=self.window, text="Upload", variable=self.state, value="u")
        self.full_button = tk.Radiobutton(master=self.window, text="Full", variable=self.state,value="f")

        self.targetFile_button = tk.Button(master=self.window, text="Search", command=self.select_file_target)
        self.manifestFile_button = tk.Button(master=self.window, text="Search", command=self.select_file_manifest)
        self.pngDirectory_button = tk.Button(master=self.window, text="Search", command=self.select_png_directory)

        self.metadata_button = tk.Button(master=self.window, text="Metadata", command=self.open_metadata_popup)

        self.printProgress_check_button = tk.Checkbutton(master=self.window, text="Print Progress", command=self.toggleConsole, variable=self.printProgress, onvalue=1, offvalue=0)
        self.saveSession_check_button = tk.Checkbutton(master=self.window, text="Save Session", variable=self.saveSession, onvalue=1, offvalue=0)

    def toggleConsole(self):
        if (self.printProgress.get()):
            self.window.geometry("600x625")
            self.console_scrolled_text_frame.grid(row=4, column=0, columnspan=5)
            self.console_scrolled_text.grid(row=0,column=0)
        else:
            self.console_scrolled_text_frame.destroy()
            self.window.geometry(self.default_window_size)
            self.console_scrolled_text_frame = tk.Frame(master=self.window)
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
       top= tk.Toplevel(self.window)


       top.title("Help")
       tk.Label(top, text= 'How to use: Select pipeline mode using bottom row of buttons. \n \
                * Generate a manifest / data without publishing - [manifest] \n \
                * Upload an existing manifest and data to zooniverse -[upload] \n \
                * Run the whole pipeline to generate a manifest / data from target list and upload to zooniverse -[full] \n \
                \n \
                For : [manifest] : Only target filename and manifest filename field are required.\n \
                : [upload]   : Only username, password, project ID, subject set ID, and manifest filename are requred\n \
                : [full]     : All fields are required.').pack()

       self.center_window(top)

    def open_overwrite_manifest_popup(self):
        '''
        Generates an overwrite manifest popup

        Returns
        -------
        None.

        '''

        top = tk.Toplevel(self.window)
        self.center_window(top)

        top.rowconfigure(list(range(3)), minsize=20, weight=1)
        top.columnconfigure(list(range(6)), minsize=20, weight=1)
        top.grab_set()
        top.title("Warning")
        frame = tk.Frame(master=top)
        frame.rowconfigure(list(range(1)), minsize=20, weight=1)
        frame.columnconfigure(list(range(2)), minsize=20, weight=1)

        label = tk.Label(master=top, text=f"Warning: You are attempting to overwrite an existing manifest: {self.manifestFile.get()} \n \n Would you like to overwrite the exsiting manifest?")
        yesButton = tk.Button(master=frame, text="Yes", command= lambda : self.overwriteManifestButtonPressed(True,top))
        noButton = tk.Button(master=frame, text="No", command=lambda: self.overwriteManifestButtonPressed(False,top))

        label.grid(row=0, column=2)
        yesButton.grid(row=1, column=0, padx=5)
        noButton.grid(row=1, column=1, padx=5)

        frame.grid(row=1, column=2)
        yesButton.wait_variable(self.overwriteManifest)

    def open_invalid_login_popup(self):
        '''
        Generates an invalid login popup

        Returns
        -------
        None.

        '''

        top = tk.Toplevel(self.window)
        top.geometry("100x50")
        self.center_window(top)

        top.rowconfigure(list(range(1)), minsize=20, weight=1)
        top.columnconfigure(list(range(1)), minsize=20, weight=1)
        top.grab_set()
        top.title("Invalid Login")

        label = tk.Label(master=top, text="Invalid login.")

        label.grid(row=0, column=0)

    def open_metadata_popup(self):
        '''
        Generates a metadata popup

        Returns
        -------
        None.

        '''

        top = tk.Toplevel(self.window)
        top.geometry("300x300")
        self.center_window(top)
        
        
        top.rowconfigure(list(range(4)), minsize=50,weight=1)
        top.columnconfigure(list(range(2)), minsize = 50, weight=1)
        top.grab_set()
        
        top.title("Metadata")
        
        
        
        metadata_label = tk.Label(master=top, text="Metadata",font=("Arial", 18))
        metadata_label.grid(row=0,column=0,padx=10,pady=10, columnspan=2)

        # add grid checkbox
        self.addGrid_check_button = tk.Checkbutton(master=top, text='Add Grid', variable=self.addGrid, onvalue=1, offvalue=0)
        self.addGrid_check_button.grid(row=1, column=0,padx=10,pady=10)

        # scale factor entry
        self.scaleFactor_frame, self.scaleFactor_entry = self.makeEntryField(top, 'Scale Factor',self.scaleFactor)
        self.scaleFactor_entry.config(width=15)
        self.scaleFactor_frame.grid(row=2, column=0,padx=10,pady=10)

        # FOV entry
        self.FOV_frame, self.FOV_entry = self.makeEntryField(top, 'FOV (arcseconds)', self.FOV)
        self.FOV_entry.config(width=15)
        self.FOV_frame.grid(row=3, column=0,padx=10,pady=10)
        
        
        self.minBright_frame, self.minBright_entry = self.makeEntryField(top, 'Minbright (vega mmags)', self.minBright)
        self.minBright_entry.config(width=15)
        self.minBright_frame.grid(row=2, column=1,padx=10,pady=10)
        
        self.maxBright_frame, self.maxBright_entry = self.makeEntryField(top, 'Maxbright (vega mmags)', self.maxBright)
        self.maxBright_entry.config(width=15)
        self.maxBright_frame.grid(row=3, column=1,padx=10,pady=10)
        


    def overwriteManifestButtonPressed(self, value, popup):
        self.overwriteManifest.set(value)
        popup.destroy()

    def warning(self):
        '''
         Warning

         Returns
         -------
         True -- not enough fields filled out
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
        
        try:
            int(self.minBright.get())
        except ValueError:
            warningFlag=8
       
        try:
            int(self.maxBright.get())
        except ValueError:
            warningFlag=9

        if(not os.path.isdir(self.pngDirectory.get())):
            try:
                os.mkdir(self.pngDirectory.get())
            except:
                warningFlag=7

            

        
                    

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
            whatToSay='Input a numerical value for minbright!'
        elif warningFlag==9:
            whatToSay='Input a numerical value for maxbright!'
        else:
            return False

        if warningFlag!=0:
            warning_window = tk.Toplevel(self.window)
            warning_window.title("Warning!")
            tk.Label(warning_window,text=whatToSay).pack()
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
        if (self.verifyInputs()):
            if(self.printProgress.get()):
                now = datetime.now()
                self.updateConsole(f"Started pipeline at: {now}")
            
            metadata_dict = {f"{Data.Metadata.privatization_symbol}GRID": int(self.addGrid.get()),
                             f"{Data.Metadata.privatization_symbol}SCALE": self.scaleFactor.get(),
                             "FOV" : self.FOV.get(),
                             f"{Data.Metadata.privatization_symbol}PNG_DIRECTORY" : self.pngDirectory.get(),
                             f"{Data.Metadata.privatization_symbol}MINBRIGHT" : int(self.minBright.get()),
                             f"{Data.Metadata.privatization_symbol}MAXBRIGHT" : int(self.maxBright.get())}

            # Creates metadata-target.csv
            ZooniversePipeline.mergeTargetsAndMetadata(self.targetFile.get(), metadata_dict, self.metadataTargetFile.get())

            if (self.state.get() == 'f'):
                ZooniversePipeline.fullPipeline(self)
            elif (self.state.get() == 'm'):
                ZooniversePipeline.generateManifest(self)
            elif (self.state.get() == 'u'):
                ZooniversePipeline.publishToZooniverse(self)
            # Calls interface to determine how the program should run.
            else:
                print("You broke the pipeline :(")

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

    def makeEntryField(self, window, label_title, variable, hide=False):
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
        
        frame =tk.Frame(master=window)

        if(not hide):
            entry=tk.Entry(master=frame, textvariable=variable)
        else:
            entry=tk.Entry(master=frame, show='*', textvariable=variable)
        label=tk.Label(master=frame, text=label_title)
        
        label.grid(row=0, column=0)
        entry.grid(row=1, column=0)
        
        return frame, entry

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
