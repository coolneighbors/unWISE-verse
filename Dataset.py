"""
Created on Thursday, June 9th

@author: Austin Humphreys
"""

import csv
import math
import os
from copy import copy
from statistics import mean

import astropy
from astropy import time
from astropy import units as u
from astropy.coordinates import SkyCoord
from flipbooks import WiseViewQuery
import MetadataPointers

from Data import Data, Metadata

# Errors
class NonUniformFieldsError(Exception):
    def __init__(self,data, other_data):
        super(NonUniformFieldsError, self).__init__(f"The field names are not uniform for all data and/or metadata objects: {data} , {other_data}")

class MismatchedDataAndMetadataError(Exception):
    def __init__(self,data_list, metadata_list):
        super(MismatchedDataAndMetadataError, self).__init__(f"The number of data objects does not match the number of metadata objects: {len(data_list)} , {len(metadata_list)}")

class Dataset():
    def __init__(self, data_list, metadata_list = [], require_uniform_fields = True):
        """
        Initializes a Dataset object, a container which holds a list of Data objects and a list of Metadata objects.
        When accessing, per index a dictionary containing the corresponding Data object and Metadata
        object will be given.

        Parameters
        ----------
            data_list : List of Data objects
                A list of Data objects.
            metadata_list : List of Metadata objects, optional
                A list of Metadata objects.
            require_uniform_fields : A boolean determining whether to require all data and metadata objects to have the
            exact same field names

        Notes
        -----
            The container structure of the Dataset object is equivalent to an ordered list of dictionaries, each of which each contain
            a Data object and a Metadata object and can be accessed via the keys: data, metadata.
        """

        self.data_list = copy(data_list)
        self.metadata_list = copy(metadata_list)
        self.require_uniform_fields = copy(require_uniform_fields)

        if (len(self.metadata_list) == 0):
            for data in self.data_list:
                self.metadata_list.append(Metadata(["!no_metadata"], [""]))

        if(len(self.data_list) != len(self.metadata_list)):
            raise MismatchedDataAndMetadataError(self.data_list,self.metadata_list)

        for data in self.data_list:
            for other_data in self.data_list:
                if(self.require_uniform_fields):
                    if(not data.have_equal_fields(other_data)):
                        raise NonUniformFieldsError(data, other_data)
                else:
                    if (not data.have_equal_fields(other_data)):
                        data.resolve_missing_fields(other_data)
        self.data_field_names = self.data_list[0].field_names

        for metadata in self.metadata_list:
            for other_metadata in self.metadata_list:
                if (self.require_uniform_fields):
                    if (not metadata.have_equal_fields(other_metadata)):
                        raise NonUniformFieldsError(metadata, other_metadata)
                else:
                    if (not metadata.have_equal_fields(other_metadata)):
                        metadata.resolve_missing_fields(other_metadata)
        self.metadata_field_names = self.metadata_list[0].getAdjustedFieldNames()

    def __str__(self):
        """
        Overloads the str() function for the Dataset object such that a string of the Data objects and the Metadata
        objects is provided.

        Returns
        -------
        string : str
            Provides a string of the form, f"Data List: {self.data_list} , Metadata List: {self.metadata_list}".

        Notes
        -----

        """

        return f"Data List: {self.data_list} , Metadata List: {self.metadata_list}"

    def __len__(self):
        """
        Overloads the len() function for the Dataset object such that the length is the number of Data objects
        (which should be equal to the number of Metadata objects, otherwise the Dataset object could not have been
        initialized).

        Returns
        -------
        len(self.data_list) : int
            An integer value based on the the number of Data objects.

        Notes
        -----

        """

        return len(self.data_list)

    def __getitem__(self, index):
        """
        Overloads the [] operator for the Dataset object such that each index corresponds to a dictionary of a Data
        object and a Metadata object corresponding to that index.

        Returns
        -------
        dataset_dict : dict
            A dictionary of the form, {"data" : Data object, "metadata" : Metadata object}
            An index of the Dataset object, from 0 to len(Dataset object)-1.
        Notes
        -----

        """

        data = self.data_list[index]
        metadata = self.metadata_list[index]
        dataset_dict = {"data": data,"metadata": metadata}
        return dataset_dict

    @classmethod
    def generateDataset(cls,data_csv_filename, metadata_csv_filename):
        data_list = []
        with open(data_csv_filename, newline='') as data_file:
            reader = csv.DictReader(data_file)
            for row in reader:
                data_list.append(Data.createFromDictionary(row))

        metadata_list = []
        with open(metadata_csv_filename, newline='') as metadata_file:
            reader = csv.DictReader(metadata_file)
            for row in reader:
                metadata_list.append(Metadata.createFromDictionary(row))

        return Dataset(data_list,metadata_list)

class Zooniverse_Dataset(Dataset):

    def __init__(self, dataset_filename, ignore_partial_cutouts = False, require_uniform_fields = True, display_printouts = False, UI = None):
        """
        Initializes a Zooniverse_Dataset object (child Class of Dataset), a container which holds a list of Data objects and a list of Metadata
        objects. When accessing, per index a dictionary containing the corresponding Data object and Metadata object
        will be given. Generated through an existing dataset file which contains at least Metadata values for RA and DEC.

        Parameters
        ----------
            dataset_filename : str
                The full path filename of the dataset CSV file to be used for the Zooniverse_Dataset object.
            ignore_partial_cutouts : bool, optional
                Determines whether to ignore non-square cutouts.
            require_uniform_fields : A boolean determining whether to require all data and metadata objects to have the
            exact same field names
            display_printouts : bool, optional
                Used to determine whether to display progress information in the console.
            UI : UI object, optional
                User interface object to send progress information to.
        Notes
        -----
            The container structure of the Zooniverse_Dataset object is equivalent to an ordered list of dictionaries, each of which each contain
            a Data object and a Metadata object and can be accessed via the keys: data, metadata.

            The dataset CSV should be of the following form:

            RA,DEC,metadata3,...
            x,y,z,...

            Any additional metadata besides RA and DEC is optional.

            Use Zooniverse_Dataset as the parent class of all other types of potential specific datasets associated with Zooniverse projects.
            In order to add specific functionality with some predetermined set of metadata/data, override the generateDataAndMetadataLists function with your own functionality.
            It should work as long as you properly return a list of Data objects and a list of Metadata objects.

        """
        self.require_uniform_fields = copy(require_uniform_fields)
        data_list, metadata_list = self.generateDataAndMetadataLists(dataset_filename, ignore_partial_cutouts, display_printouts, UI)
        super(Zooniverse_Dataset, self).__init__(data_list, metadata_list, require_uniform_fields)

        if (display_printouts):
            if (UI is None):
                print("Dataset created.")
            elif (isinstance(UI, UserInterface.UserInterface)):
                UI.updateConsole("Dataset created.")

    def generateDataAndMetadataLists(self, dataset_filename, ignore_partial_cutouts = False, display_printouts=False, UI=None):
        data_list = []
        metadata_list = []

        ignored_data_list = []
        ignored_metadata_list = []

        # Currently is only able to use CSV files

        total_data_rows = 0
        with open(dataset_filename, newline='') as dataset_file:
            total_data_rows = len(list(dataset_file)) - 1

        metadata_field_names = []
        with open(dataset_filename, newline='') as dataset_file:
            reader = csv.DictReader(dataset_file)
            metadata_field_names = reader.fieldnames

        with open(dataset_filename, newline='') as dataset_file:
            reader = csv.DictReader(dataset_file)
            count = 0
            for row in reader:
                count += 1
                RA = row['RA']
                DEC = row['DEC']

                row_metadata = list(row.values())
                metadata_field_names = list(row.keys())

                # set WV parameters to RA and DEC
                wise_view_query = WiseViewQuery.WiseViewQuery(RA=RA, DEC=DEC)

                # Save all images for parameter set, add grid if toggled for that image

                flist, size_list = wise_view_query.downloadWiseViewData("pngs")

                is_partial_cutout = False
                for size in size_list:
                    width, height = size
                    if (width != height):
                        is_partial_cutout = True
                        break

                if (display_printouts):
                    if (is_partial_cutout and ignore_partial_cutouts):
                        if (UI is None):
                            print(
                                f"Row {count} out of {total_data_rows} in {dataset_filename} with (RA,DEC): ({RA}, {DEC}) is a partial cutout and has been ignored.")
                        elif (isinstance(UI, UserInterface.UserInterface)):
                            UI.updateConsole(
                                f"Row {count} out of {total_data_rows} in {dataset_filename} with (RA,DEC): ({RA}, {DEC}) is a partial cutout and has been ignored.")
                    else:
                        if (UI is None):
                            print(f"Row {count} out of {total_data_rows} has been downloaded.")
                        elif (isinstance(UI, UserInterface.UserInterface)):
                            UI.updateConsole(f"Row {count} out of {total_data_rows} has been downloaded.")

                data_field_names = []
                for i in range(len(flist)):
                    data_field_names.append("f" + str(i + 1))

                if (not is_partial_cutout or not ignore_partial_cutouts):
                    data_list.append(Data(data_field_names, flist))
                    metadata_list.append(Metadata(metadata_field_names, row_metadata))
                else:
                    ignored_data_list.append(Data(data_field_names, flist))
                    ignored_metadata_list.append(Metadata(["Original Row: ", *metadata_field_names], [count, *row_metadata]))

        if (len(ignored_data_list) != 0):
            self.generateIgnoredTargetsCSV(ignored_data_list, ignored_metadata_list)
        elif (os.path.exists("ignored-targets.csv")):
            os.remove("ignored-targets.csv")

        return data_list, metadata_list

    def generateIgnoredTargetsCSV(self, ignored_data_list, ignored_metadata_list):
        temp_dataset = Dataset(ignored_data_list,ignored_metadata_list,self.require_uniform_fields)
        with open("ignored-targets.csv", "w", newline='') as ignored_targets_file:
            writer = csv.DictWriter(ignored_targets_file, [*temp_dataset.metadata_field_names,*temp_dataset.data_field_names])
            writer.writeheader()
            for dataset_dict in temp_dataset:
                writer.writerow(dataset_dict["metadata"].toDictionary() | dataset_dict["data"].toDictionary())

class CN_Dataset(Zooniverse_Dataset):

    def __init__(self, dataset_filename, ignore_partial_cutouts=False, require_uniform_fields = True, display_printouts = False, UI = None):
        """
        Initializes a CN_Dataset object (child Class of Zooniverse_Dataset), a container which holds a list of Data
        objects and a list of Metadata objects. When accessing, per index a dictionary containing the corresponding Data
        object and Metadata object will be given. Generated through an existing dataset file which contains at least
        Metadata values for RA, DEC, #PNG_DIRECTORY, #GRID, #SCALE, FOV, #MINBRIGHT, and #MAXBRIGHT.

        Parameters
        ----------
            dataset_filename : str
                The full path filename of the dataset CSV file to be used for the CN_Dataset object.
            ignore_partial_cutouts : bool, optional
                Determines whether to ignore non-square cutouts.
            require_uniform_fields : A boolean determining whether to require all data and metadata objects to have the
            exact same field names
            display_printouts : bool, optional
                Used to determine whether to display progress information in the console.
            UI : UI object, optional
                User interface object to send progress information to.

        Notes
        -----
            The container structure of the CN_Dataset object is equivalent to an ordered list of dictionaries, each of which each contain
            a Data object and a Metadata object and can be accessed via the keys: data, metadata.

            The dataset CSV should be of the following form:

            RA,DEC,#PNG_DIRECTORY,...
            x,y,z,...

            Any additional metadata besides RA, DEC, #PNG_DIRECTORY, #GRID, #SCALE, FOV, #MINBRIGHT, and #MAXBRIGHT is optional.

            The number of required pieces of metadata will most likely change throughout development, so make sure to
            keep updating this documentation regularly.
        """
        super(CN_Dataset, self).__init__(dataset_filename,ignore_partial_cutouts, require_uniform_fields, display_printouts, UI)

    def generateDataAndMetadataLists(self, dataset_filename, ignore_partial_cutouts = False, display_printouts=False, UI=None):
        data_list = []
        metadata_list = []

        ignored_data_list = []
        ignored_metadata_list = []

        sub_directory_limit = 9999
        sub_directory_threshold = 1000

        if(UI is not None):
            ignore_partial_cutouts = UI.ignorePartialCutouts.get()

        # Currently is only able to use CSV files
        total_data_rows = 0
        with open(dataset_filename, newline='') as dataset_file:
            total_data_rows = len(list(dataset_file)) - 1

        with open(dataset_filename, newline='') as dataset_file:
            reader = csv.DictReader(dataset_file)
            count = 0
            png_count = 0

            for row in reader:
                # Get metadata
                RA = float(row['RA'])
                DEC = float(row['DEC'])
                PNG_DIRECTORY = row[f'{Metadata.privatization_symbol}PNG_DIRECTORY']
                ADDGRID = int(row[f'{Metadata.privatization_symbol}ADDGRID'])
                GRIDCOUNT= int(row[f'{Metadata.privatization_symbol}GRIDCOUNT'])
                SCALE = int(row[f'{Metadata.privatization_symbol}SCALE'])
                FOV = float(row['FOV'])
                MINBRIGHT = int(row[f'{Metadata.privatization_symbol}MINBRIGHT'])
                MAXBRIGHT = int(row[f'{Metadata.privatization_symbol}MAXBRIGHT'])
                GRIDTYPE = row[f'{Metadata.privatization_symbol}GRIDTYPE']
                RGB_list = []
                for s in row[f'{Metadata.privatization_symbol}GRIDCOLOR'][1:][:-1].split(","):
                    RGB_list.append(int(s))
                GRIDCOLOR = tuple(RGB_list)

                if(count == 0):
                    sub_directory_values = []
                    for sub_directory_name in os.listdir(PNG_DIRECTORY):
                        sub_directory_values.append(int(sub_directory_name))
                    max_value = max(sub_directory_values, default=-1)
                    max_value = max_value + 1
                    if(max_value > sub_directory_limit):
                        raise OverflowError(f"Subdirectories with indexes greater than the sub directory limit ({sub_directory_limit}) are trying to be created.")
                    sub_directory = str(max_value)
                    for i in range(len(str(sub_directory_limit)) - len(sub_directory)):
                        if (len(sub_directory) < len(str(sub_directory_limit))):
                            sub_directory = "0" + sub_directory

                count += 1

                # pixel side-length of the images
                SIZE = WiseViewQuery.WiseViewQuery.FOVToPixelSize(FOV)
                # parse GRID into boolean values, only accept 1 as True, otherwise GRID is False.
                if (ADDGRID == 1):
                    ADDGRID = True
                else:
                    ADDGRID = False

                # set WV parameters to RA and DEC
                wise_view_query = WiseViewQuery.WiseViewQuery(RA=RA, DEC=DEC, size=SIZE, minbright=MINBRIGHT, maxbright=MAXBRIGHT)

                # Set generated metadata
                row['FOV'] = f"~{FOV} x ~{FOV} arcseconds"
                row['Data Source'] = f"[unWISE](+tab+http://unwise.me/)"
                row['unWISE Pixel Scale'] = f"~{WiseViewQuery.unWISE_pixel_ratio} arcseconds per pixel"
                modified_julian_date_pairs = wise_view_query.requestMetadata("mjds")
                date_str = ""
                for i in range(len(modified_julian_date_pairs)):
                    for j in range(len(wise_view_query.requestMetadata("mjds")[i])):
                        if(j == 0):
                            time_start = time.Time(wise_view_query.requestMetadata("mjds")[i][j],format="mjd").to_value("decimalyear")
                        if(j == len(wise_view_query.requestMetadata("mjds")[i])-1):
                            time_end = time.Time(wise_view_query.requestMetadata("mjds")[i][j],format="mjd").to_value("decimalyear")
                    if(time_start == time_end):
                        if(i != len(modified_julian_date_pairs)-1):
                            date_str = date_str + f"Frame {i+1}: {round(time_start,2)}, "
                        else:
                            date_str = date_str + f"Frame {i+1}: {round(time_start,2)}"
                    else:
                        if(i != len(modified_julian_date_pairs)-1):
                            date_str = date_str + f"Frame {i+1}: {round(mean([time_start,time_end]),2)}, "
                        else:
                            date_str = date_str + f"Frame {i+1}: {round(mean([time_start,time_end]),2)}"

                row["Decimal Year Epochs"] = date_str

                ICRS_coordinates = SkyCoord(ra=RA*u.degree, dec=DEC*u.degree, frame='icrs')

                galactic_coordinates = ICRS_coordinates.transform_to(frame="galactic")
                row['Galactic Coordinates'] = galactic_coordinates.to_string("decimal")

                ecliptic_coordinates = ICRS_coordinates.transform_to(frame=astropy.coordinates.GeocentricMeanEcliptic)
                row['Ecliptic Coordinates'] = ecliptic_coordinates.to_string("decimal")

                row['WISEVIEW'] = f"[WiseView](+tab+{wise_view_query.generateWiseViewURL()})"

                # Radius is the smallest circle radius which encloses the square image.
                # This is done to ensure the entire image frame is searched.
                radius = (math.sqrt(2) / 2) * FOV
                row['SIMBAD'] = f"[SIMBAD](+tab+{MetadataPointers.generate_SIMBAD_url(RA, DEC, radius)})"

                row['Legacy Surveys'] = f"[Legacy Surveys](+tab+{MetadataPointers.generate_legacy_survey_url(RA, DEC)})"

                row['VizieR'] = f"[VizieR](+tab+{MetadataPointers.generate_VizieR_url(RA, DEC, FOV)})"

                row['IRSA'] = f"[IRSA](+tab+{MetadataPointers.generate_IRSA_url(RA, DEC)})"

                row_metadata = list(row.values())
                metadata_field_names = list(row.keys())


                if (png_count >= sub_directory_threshold):
                    sub_directory = str(int(sub_directory) + 1)
                    if (int(sub_directory) + 1 > sub_directory_limit):
                        raise OverflowError(f"Subdirectories with indexes greater than the sub directory limit ({sub_directory_limit}) are trying to be created.")
                    for i in range(len(str(sub_directory_limit))-len(sub_directory)):
                        if (len(sub_directory) < len(str(sub_directory_limit))):
                            sub_directory = "0" + sub_directory
                    png_count = 0

                # Save all images for parameter set, add grid if toggled for that image
                flist, size_list = wise_view_query.downloadWiseViewData(PNG_DIRECTORY + "\\" + sub_directory, scale_factor=SCALE, addGrid=ADDGRID, gridCount=GRIDCOUNT, gridType=GRIDTYPE, gridColor=GRIDCOLOR)
                png_count += len(flist)

                is_partial_cutout = False
                for size in size_list:
                    width, height = size
                    if (width != height):
                        is_partial_cutout = True
                        break


                if (display_printouts):
                    if (is_partial_cutout and ignore_partial_cutouts):
                        if (UI is None):
                            print(f"Row {count} out of {total_data_rows} in {dataset_filename} with (RA,DEC): ({RA}, {DEC}) is a partial cutout and has been ignored.")
                        elif (isinstance(UI, UserInterface.UserInterface)):
                            UI.updateConsole(f"Row {count} out of {total_data_rows} in {dataset_filename} with (RA,DEC): ({RA}, {DEC}) is a\npartial cutout and has been ignored.")
                    else:
                        if (UI is None):
                            print(f"Row {count} out of {total_data_rows} has been downloaded.")
                        elif (isinstance(UI, UserInterface.UserInterface)):
                            UI.updateConsole(f"Row {count} out of {total_data_rows} has been downloaded.")

                data_field_names = []
                for i in range(len(flist)):
                    data_field_names.append("f" + str(i + 1))

                if (not is_partial_cutout or not ignore_partial_cutouts):
                    data_list.append(Data(data_field_names, flist))
                    metadata_list.append(Metadata(metadata_field_names, row_metadata))
                else:
                    ignored_data_list.append(Data(data_field_names, flist))
                    ignored_metadata_list.append(Metadata(["Original Row: ", *metadata_field_names], [count, *row_metadata]))

        if (len(ignored_data_list) != 0):
            self.generateIgnoredTargetsCSV(ignored_data_list, ignored_metadata_list)
        elif(os.path.exists("ignored-targets.csv")):
            os.remove("ignored-targets.csv")

        return data_list, metadata_list

import UserInterface