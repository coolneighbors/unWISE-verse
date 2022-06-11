# -*- coding: utf-8 -*-
"""
Created on Fri Jun 10 14:53:00 2022

@author: Noah Schapera
"""

import multiprocessing as mp
import wv
import postProcessing





def downloadingData(url,i,ra,dec,outdir):
    
    fieldName='field-RA'+str(ra)+'-DEC'+str(dec)+'-'+str(i)+'.png'
    fname_dest = wv._download_one_png(url, outdir, fieldName)
    return fname_dest


def downloadHandler(urls,ra,dec,outdir):    
    pool = mp.Pool()

    processes = [pool.apply_async(downloadingData, args=(urls[i],i,ra,dec,outdir)) for i in range(len(urls))]
    flist = [p.get() for p in processes]

    #print(f"Program finished in {finish_time-start_time} seconds")
    return flist

def scaleHandler(flist,scale_factor):
    pool = mp.Pool()
    processes = [pool.apply_async(postProcessing.rescale, args=(f,scale_factor)) for f in flist]
    
    
    
def gridHandlder(flist,gridSize):
    pool = mp.Pool()
    processes = [pool.apply_async(postProcessing.addGrid, args=(f,gridSize)) for f in flist]
    