# -*- coding: utf-8 -*-
"""
Created on Mon Jun 13 10:14:59 2022

@author: Noah Schapera
"""

import tkinter as tk
from functools import partial


    

def validateLogin(ent_user,ent_pass):
    username = ent_user.get()
    password = ent_pass.get()
    
    print(username)
    print(password)
    
    return


def makeEntryField(label,window,outputVar,hide=False):
    frm=tk.Frame(master=window)
    if hide == False:
        ent=tk.Entry(master=frm,textvariable=outputVar,width=10)
    else:
        ent=tk.Entry(master=frm,textvariable=outputVar,show='*',width=10)
    lbl=tk.Label(master=frm,text=label)
    
    lbl.grid(row=0,column=0,sticky='s')
    ent.grid(row=1,column=0,sticky='n')
    
    return frm
    
def rmFrm(window, frm):
    frm.grid_forget()
    
def restFrm(window,frm):
    frm.grid(row=0,column=0,padx=10,pady=10)
    
    

def main(validateLogin,rmFrm,restFrm):
    window = tk.Tk()
    window.title("Test Entry")
    window.rowconfigure([0,1],minsize=50,weight=1)
    window.columnconfigure([0,1,2], minsize=50, weight=1)
    
    #user entry
    username=tk.StringVar()
    userFrm2=makeEntryField('Username2',window,username)

    
    #password entry
    password = tk.StringVar()
    
    passFrm2=makeEntryField('Password2',window,password,hide=True)
    
    
    validateLogin=partial(validateLogin,username,password)
    rmFrm = partial(rmFrm,window,userFrm2)
    restFrm = partial(restFrm,window,userFrm2)    
    
    #button
    btn_submit = tk.Button(master = window, text = "Submit", command=validateLogin)
    btn_remove = tk.Button(master = window, text = "Remove", command=rmFrm)
    btn_restore =tk.Button(master = window, text = "Restore", command=restFrm)
    
    btn_submit.grid(row=0,column=2,pady=10,padx=10)
    passFrm2.grid(row=0,column=1,pady=10,padx=10)
    userFrm2.grid(row=0,column=0,pady=10,padx=10)
    btn_remove.grid(row=1,column=0,pady=10,padx=10)
    btn_restore.grid(row=1,column=1,pady=10,padx=10)
    
    
    
    
    window.mainloop()

    
if __name__ == "__main__":
    main(validateLogin,rmFrm,restFrm)