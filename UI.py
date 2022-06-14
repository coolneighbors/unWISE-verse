# -*- coding: utf-8 -*-
"""
Created on Mon Jun 13 10:14:59 2022

@author: Noah Schapera
"""

import tkinter as tk
from functools import partial
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


def configWindow(rows,cols,title):
    window = tk.Tk()
    window.title(title)
    window.rowconfigure(list(range(rows)),minsize=50,weight=1)
    window.columnconfigure(list(range(cols)), minsize=50, weight=1)
    
    return window
    

def validateLogin(ent_user,ent_pass):
    username = ent_user.get()
    password = ent_pass.get()
    
    print(username)
    print(password)


def makeEntryField(label,window,outputVar,hide=False):
    frm=tk.Frame(master=window)
    if hide == False:
        ent=tk.Entry(master=frm,textvariable=outputVar,width=10)
    else:
        ent=tk.Entry(master=frm,textvariable=outputVar,show='*',width=10)
    lbl=tk.Label(master=frm,text=label)
    
    lbl.grid(row=0,column=0,sticky='s')
    ent.grid(row=1,column=0,sticky='n')
    
    return frm, ent


    
    

def main(validateLogin):
    
    window = configWindow(3,3,'Data Pipeline')

    #user entry
    username=tk.StringVar()
    frm_username,ent_username=makeEntryField('Zooniverse Username',window,username)

    
    #password entry
    password = tk.StringVar()
    frm_password,ent_password=makeEntryField('Zooniverse Password',window,password,hide=True)
    


    
    #proj ID entry
    projID = tk.StringVar()
    frm_projID,ent_projID=makeEntryField('Project ID',window,projID)
    
    #set ID entry
    setID = tk.StringVar()
    frm_setID,ent_setID=makeEntryField('Set ID',window,setID)
    
    
    
    #targets entry
    targetFile=tk.StringVar()
    frm_targetFile,ent_targetFile=makeEntryField('Target List Filename',window,targetFile)
    
    #manifest entry
    manifestFile = tk.StringVar()
    frm_manifestFile,ent_manifestFile=makeEntryField('Manifest Filename',window,manifestFile)
    
    
       
    
    #button
    btn_submit = tk.Button(master = window, text = "Submit", command=partial(validateLogin,ent_username,ent_password))
    
    
    
    
    
    
    frm_username.grid(row=0,column=0,pady=10,padx=10)
    frm_password.grid(row=1,column=0,pady=10,padx=10)
    
    frm_projID.grid(row=0,column=1,pady=10,padx=10)
    frm_setID.grid(row=1,column=1,pady=10,padx=10)
    
    frm_targetFile.grid(row=0,column=2,pady=10,padx=10)
    frm_manifestFile.grid(row=1,column=2,pady=10,padx=10)
    
    btn_submit.grid(row=2,column=1,pady=10,padx=10)
    
    window.mainloop()

    
if __name__ == "__main__":
    main(validateLogin)