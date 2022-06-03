# -*- coding: utf-8 -*-
"""
Created on Sat May 14 16:58:34 2022

@author: Noah Schapera
"""

import os
import matplotlib.pyplot as plt
import numpy as np
import numpy.random as nprnd


#load stars into ax
def plotStars(ax,N,starsX,starsY,rads,obj):
    for i in range(N):
        
        circle1 = plt.Circle((starsX[i], starsY[i]), rads[i], color='black')
        ax.add_patch(circle1)

    cenCir = plt.Circle((obj[0], obj[1]), objRad, color='black')
    ax.add_patch(cenCir)
    
    
    circle2 = plt.Circle((50,50), 2, color='b', fill=False)
    ax.add_patch(circle2)
    
    return ax

iterations = int(input('Number of fields: '))



#info for 'brown dwarf'
obj=[50,50]
objRad = 0.5

#info for background stars
N = 50


#initialize matplotlib objects
fig,ax = plt.subplots(figsize=(10,10))





for instance in range(iterations):
    #reset brown dwarf loc
    obj=[50,50]
    
    #define background stars
    starsX = nprnd.rand(N)*100
    starsY = nprnd.rand(N)*100 
    rads = nprnd.rand(N)
    
    #this section will run twice for each instance
    for i in range(2):
        ax.clear()
        #plot stars, object
        ax = plotStars(ax,N,starsX,starsY,rads,obj)
        
        #change graph style settings to look like 'space'
        ax.set(xlim=(0,100),ylim=(0,100))
        ax.axis('Square')
        #plt.style.use('dark_background')
        
        #save figure
        plt.savefig('TestData\Field-'+str(instance)+'-'+str(i))
        #run 1 - T=0 image
        #run 2 - T=T image
        
        #offset object
        obj[0]=obj[0]+(nprnd.rand()-0.5)*10
        obj[1]=obj[1]+(nprnd.rand()-0.5)*10
        
        

print('Generated Star Fields')
os.system(f"ManifestMaker.py {iterations}")
print('Program Complete')





























































