# -*- coding: utf-8 -*-
"""
Created on Mon Jun 20 14:31:51 2022
Modified on July 12th, 2022
@author: Noah Schapera
"""

import numpy as np
import numpy.random as nprnd
import csv
from astropy.coordinates import SkyCoord
def main():  
    
    numOfTargets=input("Number of targets: ")
    try:
        numOfTargets = int(numOfTargets)
    except ValueError:
        raise ValueError("Please enter an integer.")

    coordinateType = input("Coordinate type (ICRS, Galactic): ").lower()
    if(coordinateType != "icrs" and coordinateType != "galactic"):
        raise ValueError("Coordinate type must be ICRS or Galactic")

    custom_limits_response = input(f"Set custom limits? (y/n): ")
    if (custom_limits_response.lower() == "y" or custom_limits_response.lower() == "yes"):
        custom_limits = True
    else:
        custom_limits = False
    if(custom_limits):
        if(coordinateType == "icrs"):
            lower_limit_horizontal = input("Lower limit of RA (in degrees): ")
            try:
                lower_limit_horizontal = float(lower_limit_horizontal)
            except ValueError:
                raise ValueError("Please enter a float.")

            upper_limit_horizontal = input("Upper limit of RA (in degrees): ")
            try:
                upper_limit_horizontal = float(upper_limit_horizontal)
            except ValueError:
                raise ValueError("Please enter a float.")

            lower_limit_vertical = input("Lower limit of Dec (in degrees): ")
            try:
                lower_limit_vertical = float(lower_limit_vertical)
            except ValueError:
                raise ValueError("Please enter a float.")

            upper_limit_vertical = input("Upper limit of Dec (in degrees): ")
            try:
                upper_limit_vertical = float(upper_limit_vertical)
            except ValueError:
                raise ValueError("Please enter a float.")
        elif(coordinateType == "galactic"):
            lower_limit_horizontal = input("Lower limit of l (in degrees): ")
            try:
                lower_limit_horizontal = float(lower_limit_horizontal)
            except ValueError:
                raise ValueError("Please enter a float.")

            upper_limit_horizontal = input("Upper limit of l (in degrees): ")
            try:
                upper_limit_horizontal = float(upper_limit_horizontal)
            except ValueError:
                raise ValueError("Please enter a float.")

            lower_limit_vertical = input("Lower limit of b (in degrees): ")
            try:
                lower_limit_vertical = float(lower_limit_vertical)
            except ValueError:
                raise ValueError("Please enter a float.")

            upper_limit_vertical = input("Upper limit of b (in degrees): ")
            try:
                upper_limit_vertical = float(upper_limit_vertical)
            except ValueError:
                raise ValueError("Please enter a float.")

    else:
        if(coordinateType == "icrs"):
            lower_limit_horizontal = 0
            upper_limit_horizontal = 360
            lower_limit_vertical = -90.0
            upper_limit_vertical = 90.0
        elif(coordinateType == "galactic"):
            lower_limit_horizontal = 0
            upper_limit_horizontal = 360
            lower_limit_vertical = -90.0
            upper_limit_vertical = 90.0

    otherCoordinateType = "Galactic" if coordinateType == "icrs" else "ICRS"

    convert_response = input(f"Convert to {otherCoordinateType} (y/n): ")
    otherCoordinateType = otherCoordinateType.lower()

    convert = False
    if(convert_response.lower() == "y" or convert_response.lower() == "yes"):
        convert = True
    else:
        convert = False

    print('Begin')
    skyCoords = SkyCoord(nprnd.uniform(lower_limit_horizontal, upper_limit_horizontal, numOfTargets), nprnd.uniform(lower_limit_vertical, upper_limit_vertical, numOfTargets), frame=coordinateType, unit='deg')
    if (convert):
        skyCoords = skyCoords.transform_to(otherCoordinateType)
        coordinateType = otherCoordinateType

    if (coordinateType == "icrs"):
        header = ['RA', 'DEC']
    elif (coordinateType == "galactic"):
        header = ['l', 'b']

    print('Initialized')
    # open the file in the write mode
    try:
        with open('fake-targets.csv', 'w', newline='') as f:
            print('File Created')
            # create the csv writer
            writer = csv.writer(f)
            print('Header Written')

            writer.writerow(header)
            print("Starting to write data")
            for i in range(numOfTargets):
                #write a row to the csv file

                if (coordinateType == "icrs"):
                    writer.writerow([str(skyCoords[i].ra.deg), str(skyCoords[i].dec.deg)])
                elif(coordinateType == "galactic"):
                    writer.writerow([str(skyCoords[i].l.deg), str(skyCoords[i].b.deg)])
    except(PermissionError):
        raise PermissionError("Please close fake-targets.csv before running the program.")
    
    print('Done')
    
if __name__ == "__main__":
    main()
    

