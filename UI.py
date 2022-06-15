# -*- coding: utf-8 -*-
"""
Created on Mon Jun 13 10:14:59 2022

@author: Noah Schapera
"""
import threading
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo
from ZooniversePipeline import fullPipeline, generateManifest, publishToZooniverse

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
    
class UI_obj:
    
    def __init__(self):
        self.configWindow(4,4,'Data Pipeline')
        self.varInit()
        self.frameInit()
        self.buttonInit()
        self.layoutInit()
        self.window.mainloop()


    '''
    STATE FUNCTIONS: 
    
    Called by buttons to modify program state. 
    '''
    def stateM(self):
        self.state='m'
    def stateU(self):
        self.state='u'
    def stateF(self):
        self.state='f'
        
        
    def varInit(self):
        '''
        Initializes variables modified throughout program runtime. 

        Returns
        -------
        None.

        '''
        #internal variables
        self.state=''
        
        #accesible variables
        self.acc_state=''
        self.acc_username=''
        self.acc_password=''
        self.acc_projectID=''
        self.acc_setID=''
        self.acc_targetFile=''
        self.acc_manifestFile=''
        self.printProgress = tk.IntVar(value=0)

    def frameInit(self):
        '''
        Creates all of the entry frames (label and text entry) by calling the makeEntryField function

        Returns
        -------
        None.

        '''
        self.frm_username,self.ent_username=self.makeEntryField('Zooniverse Username')
        #password entry
        self.frm_password,self.ent_password=self.makeEntryField('Zooniverse Password',hide=True)
        #proj ID entry
        self.frm_projID,self.ent_projID=self.makeEntryField('Project ID')
        #set ID entry
        self.frm_setID,self.ent_setID=self.makeEntryField('Set ID')
        #targets entry
        self.frm_targetFile,self.ent_targetFile=self.makeEntryField('Target List Filename')
        #manifest entry
        self.frm_manifestFile,self.ent_manifestFile=self.makeEntryField('Manifest Filename')
        
    def layoutInit(self):
        '''
        Lays out all of the widgets onto the window using the grid allign functionality. 
        
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
        
        self.frm_username.grid(row=0,column=0,padx=10,pady=10)
        self.frm_password.grid(row=1,column=0,padx=10,pady=10)
        
        self.frm_projID.grid(row=0,column=1,padx=10,pady=10)
        self.frm_setID.grid(row=1,column=1,padx=10,pady=10)
        
        self.frm_targetFile.grid(row=0,column=2,padx=10,pady=10)
        self.frm_manifestFile.grid(row=1,column=2,padx=10,pady=10)
        
        self.btn_help.grid(row=2,column=0,padx=10,pady=10)
        self.btn_submit.grid(row=2,column=1,padx=10,pady=10)
        
        self.btn_manifest.grid(row=3,column=0,padx=10,pady=10)
        self.btn_upload.grid(row=3,column=1,padx=10,pady=10)
        self.btn_full.grid(row=3,column=2,padx=10,pady=10)
        
        self.btn_tarFile.grid(row=0,column=3,padx=10,pady=10)
        self.btn_manFile.grid(row=1,column=3,padx=10,pady=10)

        self.btn_printProgress.grid(row=2, column=3, padx=10, pady=10)
        
    def buttonInit(self):

        '''
        Makes all the buttons we use for the UI - connects each button to a function
        Note - button functions cannot have arguments which is why I had to wrap this all in a class. Ugh. 

        Returns
        -------
        None.

        '''

        self.btn_submit = tk.Button(master = self.window, text = "Submit",command= lambda: threading.Thread(target=self.performState).start())
        self.btn_help = tk.Button(master = self.window, text = "Help", command=self.open_popup)
        
        self.btn_manifest = tk.Button(master = self.window, text = "Manifest", command=self.stateM)
        self.btn_upload = tk.Button(master = self.window, text = "Upload", command=self.stateU)
        self.btn_full = tk.Button(master = self.window, text = "Full", command=self.stateF)
        
        self.btn_tarFile = tk.Button(master = self.window, text = "Search", command=self.select_file_target)
        self.btn_manFile = tk.Button(master = self.window, text = "Search", command=self.select_file_manifest)

        self.btn_printProgress = tk.Checkbutton(master = self.window, text="Print Progress", variable=self.printProgress, onvalue=1, offvalue=0)

    def select_file_manifest(self):
        filetypes = (
            ('CSV files', '*.csv'),
            ('All files', '*.*')
        )

        filename = fd.askopenfilename(
            title='Open a file',
            initialdir='/',
            filetypes=filetypes)
        
        self.ent_manifestFile.delete(0,tk.END)
        self.ent_manifestFile.insert(0,filename)
        
    def select_file_target(self):
        filetypes = (
            ('CSV files', '*.csv'),
            ('All files', '*.*')
        )

        filename = fd.askopenfilename(
            title='Open a file',
            initialdir='/',
            filetypes=filetypes)
        
        self.ent_targetFile.delete(0,tk.END)
        self.ent_targetFile.insert(0,filename)
        

    def open_popup(self):
       '''
        Generates a help popup with instructions on how to use the program

        Returns
        -------
        None.

        '''
       top= tk.Toplevel(self.window)
       top.title("Help")
       tk.Label(top, text= 'How to use: Select pipeline mode using top row of buttons. \n \
                * Generate a manifest / data without publishing - [manifest] \n \
                * Upload an existing manifest and data to zooniverse -[upload] \n \
                * Run the whole pipeline to generate a manifest / data from target list and upload to zooniverse -[full] \n \
                \n \
                For : [manifest] : Only target filename and manifest filename field are required.\n \
                : [upload]   : Only username, password, project ID, subject set ID, and manifest filename are requred\n \
                : [full]     : All fields are required.').pack()

    def warning(self):
        '''
         Warning

         Returns
         -------
         True -- not enough fields filled out
         False -- No error, proceed

         '''
        warningFlag=0
        if self.state == '':
            warningFlag=1
            whatToSay='Please select a program state!'

            
        elif (self.state == 'm') and ((self.targetFile == '' or self.manifestFile == '')):
            warningFlag=2
            whatToSay='Target file and manifest file fields need values!'
        elif (self.state == 'u') and ((self.username == '' or self.password == '' or self.projectID == '' or self.setID == '' or self.manifestFile == '')):
            warningFlag=3
            whatToSay='Username, password, projet ID, set ID, and manifest filename fields need values!'
        elif (self.state == 'f') and ((self.username == '' or self.password == '' or self.projectID == '' or self.setID == '' or self.manifestFile == '' or self.targetFile == '')):
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
         
        self.username = self.ent_username.get()
        self.password = self.ent_password.get()
        self.projectID = self.ent_projID.get()
        self.setID = self.ent_setID.get()
        self.targetFile = self.ent_targetFile.get()
        self.manifestFile = self.ent_manifestFile.get()
        
        isError=self.warning()
        
        if not isError:
            self.acc_state = self.state
            self.acc_username = self.username
            self.acc_password = self.password
            self.acc_projectID = self.projectID
            self.acc_setID = self.setID
            self.acc_targetFile = self.targetFile
            self.acc_manifestFile = self.manifestFile

        return not isError

    def performState(self):
        if(self.validateLogin()):
            if (self.acc_state == 'f'):
                fullPipeline(self)
            elif (self.acc_state == 'm'):
                generateManifest(self)
            elif (self.acc_state == 'u'):
                publishToZooniverse(self)
            # Calls interface to determine how the program should run.
            else:
                print("You broke the pipeline :(")

            
    def printout(self):
            print('user: '+self.acc_username)
            print('pass: '+self.acc_password)
            print('proj: '+self.acc_projectID)
            print('set: '+self.acc_setID)
            print('target: '+self.acc_targetFile)
            print('manifest: '+self.acc_manifestFile)
            print('state: '+self.acc_state)



    def makeEntryField(self,label,hide=False):
        frm=tk.Frame(master=self.window)
        if hide == False:
            ent=tk.Entry(master=frm,width=10)
        else:
            ent=tk.Entry(master=frm,show='*',width=10)
        lbl=tk.Label(master=frm,text=label)
        
        lbl.grid(row=0,column=0,sticky='s')
        ent.grid(row=1,column=0,sticky='n')
        
        return frm, ent

if __name__ == "__main__":
    ui=UI_obj()
    ui.printout()