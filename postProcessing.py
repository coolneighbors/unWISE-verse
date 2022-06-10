# -*- coding: utf-8 -*-
"""
Created on Thu Jun  9 15:15:09 2022

@author: Noah Schapera
"""
from PIL import Image, ImageDraw

def addGrid(imname, step_count = 10):
    '''
    
    Post processing "shader" that adds a grid to an image.
    

    Parameters
    ----------
    imname : TYPE
        image filename.
    step_count : TYPE, optional
        The number of grid lines to generate on the image (height and width). The default is 10.

    Returns
    -------
    None.

    '''
    
    
    with Image.open(imname) as image:

        # Draw some lines
        draw = ImageDraw.Draw(image)
        y_start = 0
        y_end = image.height
        step_size = int(image.width / step_count)
    
        for x in range(0, image.width, step_size):
            line = ((x, y_start), (x, y_end))
            draw.line(line, fill=128)
    
        x_start = 0
        x_end = image.width
    
        for y in range(0, image.height, step_size):
            line = ((x_start, y), (x_end, y))
            draw.line(line, fill=128)
    
        del draw
    
        image.save(imname)

if __name__ == '__main__':
    addGrid(input('Input Image Filename: '))
