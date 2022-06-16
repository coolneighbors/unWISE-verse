# -*- coding: utf-8 -*-
"""
Created on Mon Jun 13 10:14:59 2022

@author: Noah Schapera
"""
import os
import threading
import tkinter as tk
from copy import copy
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo
from ZooniversePipeline import fullPipeline, generateManifest, publishToZooniverse
import pickle

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
        self.configWindow(4,4,'Data Pipeline')
        self.varInit()
        self.frameInit()
        self.buttonInit()
        self.layoutInit()
        self.session = Session(self)
        self.window.protocol("WM_DELETE_WINDOW",self.quit)
        self.window.mainloop()


    '''
    STATE FUNCTIONS: 
    
    Called by buttons to modify program state. 
    '''
    def stateM(self):
        self.state.set('m')
    def stateU(self):
        self.state.set('u')
    def stateF(self):
        self.state.set('f')
        
    def quit(self):
        if(self.saveSession.get()):
            self.session.save(self)
            print("Session saved.")
        else:
            self.session.delete()

        self.window.destroy()


    def varInit(self):
        '''
        Initializes variables modified throughout program runtime. 

        Returns
        -------
        None.

        '''

        #TKinter Variables
        self.state = tk.StringVar(value="")
        self.username = tk.StringVar(value="")
        self.password = tk.StringVar(value="")
        self.projectID = tk.StringVar(value="")
        self.subjectSetID = tk.StringVar(value="")
        self.targetFile = tk.StringVar(value="")
        self.manifestFile = tk.StringVar(value="")
        self.printProgress = tk.BooleanVar(value=False)
        self.saveSession = tk.BooleanVar(value=False)
        self.overwriteManifest = tk.BooleanVar(value=False)

    def frameInit(self):
        '''
        Creates all of the entry frames (label and text entry) by calling the makeEntryField function

        Returns
        -------
        None.

        '''
        
        # username entry
        self.username_frame,self.username_entry=self.makeEntryField('Zooniverse Username',self.username)
        #password entry
        self.password_frame,self.password_entry=self.makeEntryField('Zooniverse Password',self.password,hide=True)
        #proj ID entry
        self.projectID_frame,self.projectID_entry=self.makeEntryField('Project ID',self.projectID)
        #set ID entry
        self.subjectSetID_frame,self.subjectSetID_entry=self.makeEntryField('Subject Set ID',self.subjectSetID)
        #targets entry
        self.targetFile_frame,self.targetFile_entry=self.makeEntryField('Target List Filename',self.targetFile)
        #manifest entry
        self.manifestFile_frame,self.manifestFile_entry=self.makeEntryField('Manifest Filename',self.manifestFile)
        
    def layoutInit(self):
        '''
        Lays out all of the widgets onto the window using the grid align functionality.
        
        Window is 4x4 array. 
        
        -------------------------------------------------
        | username |  projID  | targetFile | tarSearch  |
        -------------------------------------------------
        | password |  setID   |manifestFile| manSearch  |
        -------------------------------------------------
        |   help   |  submit  |            |            |
        -------------------------------------------------
        | manifest |  upload  |    full    |            |
        -------------------------------------------------
        

        Returns
        -------
        None.

        '''
        
        self.username_frame.grid(row=0,column=0,padx=10,pady=10)
        self.password_frame.grid(row=1,column=0,padx=10,pady=10)
        
        self.projectID_frame.grid(row=0,column=1,padx=10,pady=10)
        self.subjectSetID_frame.grid(row=1,column=1,padx=10,pady=10)
        
        self.targetFile_frame.grid(row=0,column=2,padx=10,pady=10)
        self.manifestFile_frame.grid(row=1,column=2,padx=10,pady=10)
        
        self.help_button.grid(row=2,column=0,padx=10,pady=10)
        self.submit_button.grid(row=2,column=1,padx=10,pady=10)
        
        self.manifest_button.grid(row=3,column=0,padx=10,pady=10)
        self.upload_button.grid(row=3,column=1,padx=10,pady=10)
        self.full_button.grid(row=3,column=2,padx=10,pady=10)
        
        self.targetFile_button.grid(row=0,column=3,padx=10,pady=10)
        self.manifestFile_button.grid(row=1,column=3,padx=10,pady=10)

        self.printProgress_check_button.grid(row=2, column=3, padx=10, pady=10)
        self.saveSession_check_button.grid(row=3, column=3, padx=10, pady=10)
        
    def buttonInit(self):

        '''
        Makes all the buttons we use for the UI - connects each button to a function
        Note - button functions cannot have arguments which is why I had to wrap this all in a class. Ugh. 

        Returns
        -------
        None.

        '''

        self.submit_button = tk.Button(master = self.window, text = "Submit",command= lambda: threading.Thread(target=self.performState).start())
        self.help_button = tk.Button(master = self.window, text = "Help", command=self.open_help_popup)
        
        self.manifest_button = tk.Button(master = self.window, text = "Manifest", command=self.stateM)
        self.upload_button = tk.Button(master = self.window, text = "Upload", command=self.stateU)
        self.full_button = tk.Button(master = self.window, text = "Full", command=self.stateF)
        
        self.targetFile_button = tk.Button(master = self.window, text = "Search", command=self.select_file_target)
        self.manifestFile_button = tk.Button(master = self.window, text = "Search", command=self.select_file_manifest)

        self.printProgress_check_button = tk.Checkbutton(master = self.window, text="Print Progress", variable=self.printProgress, onvalue=1, offvalue=0)
        self.saveSession_check_button = tk.Checkbutton(master = self.window, text="Save Session", variable=self.saveSession, onvalue=1, offvalue=0)

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

    def open_overwrite_manifest_popup(self):
        '''
        Generates a help popup with instructions on how to use the program

        Returns
        -------
        None.

        '''

        top = tk.Toplevel(self.window)
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

        if self.state.get() == '':
            warningFlag=1
            whatToSay='Please select a program state!'
        elif (self.state.get() == 'm') and ((self.targetFile.get() == '' or self.manifestFile.get() == '')):
            warningFlag=2
            whatToSay='Target file and manifest file fields need values!'
        elif (self.state.get() == 'u') and ((self.username.get() == '' or self.password.get() == '' or self.projectID.get() == '' or self.subjectSetID.get() == '' or self.manifestFile.get() == '')):
            warningFlag=3
            whatToSay='Username, password, projet ID, set ID, and manifest filename fields need values!'
        elif (self.state.get() == 'f') and ((self.username.get() == '' or self.password.get() == '' or self.projectID.get() == '' or self.subjectSetID.get() == '' or self.manifestFile.get() == '' or self.targetFile.get() == '')):
            warningFlag=4
            whatToSay='All fields need to be filled out!'
        else:
            return False

        if warningFlag!=0:
            war= tk.Toplevel(self.window)
            war.title("Warning!")
            tk.Label(war,text=whatToSay).pack()
            return True
            
                                
    def configWindow(self,rows,cols,title):
        '''
        Initializes a window object which holds all of the frames and buttons. Can store rows*cols widgets

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
        self.window = tk.Tk()
        self.window.title(title)
        self.window.rowconfigure(list(range(rows)),minsize=50,weight=1)
        self.window.columnconfigure(list(range(cols)), minsize=50, weight=1)
        

    def validateLogin(self):
        '''
        Validates form input and returns a boolean

        Returns
        -------
        None.

        '''
        
        isError=self.warning()

        return not isError

    def performState(self):
        if(self.validateLogin()):
            if (self.state.get() == 'f'):
                fullPipeline(self)
            elif (self.state.get() == 'm'):
                generateManifest(self)
            elif (self.state.get() == 'u'):
                publishToZooniverse(self)
            # Calls interface to determine how the program should run.
            else:
                print("You broke the pipeline :(")

            
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



    def makeEntryField(self,label_title, variable, hide=False):
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
        
        frame =tk.Frame(master=self.window)
        if(not hide):
            entry=tk.Entry(master=frame,width=10,textvariable=variable)
        else:
            entry=tk.Entry(master=frame,show='*',width=10,textvariable=variable)
        label=tk.Label(master=frame,text=label_title)
        
        label.grid(row=0,column=0,sticky='s')
        entry.grid(row=1,column=0,sticky='n')
        
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


if __name__ == "__main__":
    ui=UserInterface()
    ui.printout()

