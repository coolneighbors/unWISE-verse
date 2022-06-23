"""
Created on Thursday, June 9th

@author: Austin Humphreys
"""

import csv
import math
from copy import copy
from flipbooks import wv
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

        if (len(self.metadata_list) == 0):
            for data in self.data_list:
                self.metadata_list.append(Metadata(["!no_metadata"], [""]))

        if(len(self.data_list) != len(self.metadata_list)):
            raise MismatchedDataAndMetadataError(self.data_list,self.metadata_list)

        for data in self.data_list:
            for other_data in self.data_list:
                if(require_uniform_fields):
                    if(not data.have_equal_fields(other_data)):
                        raise NonUniformFieldsError(data, other_data)
                else:
                    if (not data.have_equal_fields(other_data)):
                        data.resolve_missing_fields(other_data)
        self.data_field_names = self.data_list[0].field_names

        for metadata in self.metadata_list:
            for other_metadata in self.metadata_list:
                if (require_uniform_fields):
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
    def __init__(self, dataset_filename, require_uniform_fields = True, display_printouts = False, UI = None):
        """
        Initializes a Zooniverse_Dataset object (child Class of Dataset), a container which holds a list of Data objects and a list of Metadata
        objects. When accessing, per index a dictionary containing the corresponding Data object and Metadata object
        will be given. Generated through an existing dataset file which contains at least Metadata values for RA and DEC.

        Parameters
        ----------
            dataset_filename : str
                The full path filename of the dataset CSV file to be used for the Zooniverse_Dataset object.
            require_uniform_fields : A boolean determining whether to require all data and metadata objects to have the
            exact same field names
            display_printouts : bool, optional
                Used to determine whether to display progress information in the console.
            UI : UI object, optional
                User interface object to request information from the user if the user interface is being used
        Notes
        -----
            The container structure of the Zooniverse_Dataset object is equivalent to an ordered list of dictionaries, each of which each contain
            a Data object and a Metadata object and can be accessed via the keys: data, metadata.

            The dataset CSV should be of the following form:

            RA,DEC,metadata3,...
            x,y,z,...

            Any additional metadata besides RA and DEC is optional.

        """

        data_list = []
        metadata_list = []

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
                count+=1
                RA = row['RA']
                DEC = row['DEC']
                PNG_DIRECTORY = row[f'{Metadata.privatization_symbol}PNG_DIRECTORY']

                row_metadata = []

                for key in row:
                    row_metadata.append(row[key])
                metadata_list.append(Metadata(metadata_field_names, row_metadata))

                # set WV parameters to RA and DEC
                wise_view_parameters = wv.custom_params(RA=RA, DEC=DEC)

                # Save all images for parameter set, add grid if toggled for that image
                flist = wv.png_set(wise_view_parameters, PNG_DIRECTORY)

                if (display_printouts):
                    if(UI is None):
                        print(f"Row {count} out of {total_data_rows} in {dataset_filename} has been downloaded.")
                    elif (isinstance(UI, UserInterface.UserInterface)):
                        UI.updateConsole(f"Row {count} out of {total_data_rows} has been downloaded.")
                data_field_names = []
                for i in range(len(flist)):
                    data_field_names.append("f" + str(i+1))
                data_list.append(Data(data_field_names, flist))

        if (display_printouts):
            if (UI is None):
                print("Dataset created.")
            elif (isinstance(UI, UserInterface.UserInterface)):
                UI.updateConsole("Dataset created.")

        super(Zooniverse_Dataset, self).__init__(data_list, metadata_list, require_uniform_fields)


class CN_Dataset(Zooniverse_Dataset):
    def __init__(self, dataset_filename, require_uniform_fields = True, display_printouts = False, UI = None):
        """
        Initializes a CN_Dataset object (child Class of Zooniverse_Dataset), a container which holds a list of Data
        objects and a list of Metadata objects. When accessing, per index a dictionary containing the corresponding Data
        object and Metadata object will be given. Generated through an existing dataset file which contains at least
        Metadata values for RA, DEC, and !GRID.

        Parameters
        ----------
            dataset_filename : str
                The full path filename of the dataset CSV file to be used for the CN_Dataset object.
            require_uniform_fields : A boolean determining whether to require all data and metadata objects to have the
            exact same field names
            display_printouts : bool, optional
                Used to determine whether to display progress information in the console.
            UI : UI object, optional
                User interface object to request information from the user if the user interface is being used
        Notes
        -----
            The container structure of the CN_Dataset object is equivalent to an ordered list of dictionaries, each of which each contain
            a Data object and a Metadata object and can be accessed via the keys: data, metadata.

            The dataset CSV should be of the following form:

            RA,DEC,!GRID,...
            x,y,z,...

            Any additional metadata besides RA, DEC, and !GRID is optional.

            The number of required pieces of metadata will most likely change throughout development, so make sure to
            keep updating this documentation regularly.
        """

        data_list = []
        metadata_list = []

        # Currently is only able to use CSV files

        total_data_rows = 0
        with open(dataset_filename, newline='') as dataset_file:
            total_data_rows = len(list(dataset_file)) - 1

        with open(dataset_filename, newline='') as dataset_file:
            reader = csv.DictReader(dataset_file)
            count = 0
            for row in reader:
                count+=1
                # Get metadata-targets metadata
                RA = float(row['RA'])
                DEC = float(row['DEC'])
                PNG_DIRECTORY = row[f'{Metadata.privatization_symbol}PNG_DIRECTORY']
                GRID = int(row[f'{Metadata.privatization_symbol}GRID'])
                SCALE = row[f'{Metadata.privatization_symbol}SCALE']
                FOV = float(row['FOV'])

                # arc-seconds per pixel
                unWISE_pixel_ratio = 2.75

                # pixel side-length of the images
                SIZE = int(FOV/unWISE_pixel_ratio)

                # scale factor of modified images
                if SCALE != '':
                    SCALE = int(SCALE)
                else:
                    SCALE = 1

                # parse GRID into boolean values, only accept 1 as True, otherwise GRID is False.
                if (GRID == 1):
                    GRID = True
                else:
                    GRID = False

                # set WV parameters to RA and DEC
                wise_view_parameters = wv.custom_params(RA=RA, DEC=DEC, size=SIZE)

                # Set generated metadata
                row['FOV'] = f"~{FOV} x ~{FOV} arcseconds"
                row['Data Source'] = "http://unwise.me/"
                row['unWISE Pixel Scale'] = f"~{unWISE_pixel_ratio} arcseconds per pixel"
                row['WISEVIEW'] = wv.generate_wv_url(wise_view_parameters)

                # Radius is the smallest circle radius which encloses the square image.
                # This is done to ensure he entire image frame is searched.
                radius = (math.sqrt(2)/2)*FOV
                row['SIMBAD'] = MetadataPointers.generate_SIMBAD_url(RA, DEC, radius)

                row['Legacy Surveys'] = MetadataPointers.generate_legacy_survey_url(RA, DEC)
                row['VizieR'] = MetadataPointers.generate_VizieR_url(RA, DEC, FOV)
                row['IRSA'] = MetadataPointers.generate_IRSA_url(RA, DEC)
                row_metadata = list(row.values())
                metadata_field_names = list(row.keys())
                metadata_list.append(Metadata(metadata_field_names, row_metadata))

                # Save all images for parameter set, add grid if toggled for that image
                flist = wv.png_set(wise_view_parameters, PNG_DIRECTORY, scale_factor=SCALE, addGrid=GRID)

                if (display_printouts):
                    if (UI is None):
                        print(f"Row {count} out of {total_data_rows} in {dataset_filename} has been downloaded.")
                    elif (isinstance(UI, UserInterface.UserInterface)):
                        UI.updateConsole(f"Row {count} out of {total_data_rows} has been downloaded.")
                data_field_names = []
                for i in range(len(flist)):
                    data_field_names.append("f" + str(i + 1))
                data_list.append(Data(data_field_names, flist))

        if(display_printouts):
            if (UI is None):
                print("Dataset created.")
            elif (isinstance(UI, UserInterface.UserInterface)):
                UI.updateConsole("Dataset created.")

        super(Zooniverse_Dataset, self).__init__(data_list, metadata_list, require_uniform_fields)

import UserInterface