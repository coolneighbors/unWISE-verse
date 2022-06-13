"""
Created on Thursday, June 9th

@author: Austin Humphreys
"""

import csv
from copy import copy
from flipbooks import wv
from Data import Data, Metadata

# Errors
class NonUniformFieldsError(Exception):
    def __init__(self,data, other_data):
        super(NonUniformFieldsError, self).__init__(f"The field names are not uniform for all data and/or metadata objects: {data} , {other_data}")

class MismatchedDataAndMetadataError(Exception):
    def __init__(self,data_list, metadata_list):
        super(MismatchedDataAndMetadataError, self).__init__(f"The number of data objects does not match the number of metadata objects: {len(data_list)} , {len(metadata_list)}")

class Dataset():
    def __init__(self, data_list, metadata_list):
        """
        Initializes a Dataset object, a container which holds a list of Data objects and a list of Metadata objects.
        When accessing, per index a dictionary containing the corresponding Data object and Metadata
        object will be given.

        Parameters
        ----------
            data_list : List of Data objects
                A list of Data objects.
            metadata_list : List of Metadata objects
                A list of Metadata objects.

        Notes
        -----
            The container structure of the Dataset object is equivalent to an ordered list of dictionaries, each of which each contain
            a Data object and a Metadata object and can be accessed via the keys: data, metadata.
        """

        self.data_list = copy(data_list)
        self.metadata_list = copy(metadata_list)
        if(len(data_list) != len(metadata_list)):
            raise MismatchedDataAndMetadataError(data_list,metadata_list)

        for data in data_list:
            for other_data in data_list:
                if(not data.have_equal_fields(other_data)):
                    raise NonUniformFieldsError(data, other_data)
        self.data_field_names = self.data_list[0].field_names

        for metadata in metadata_list:
            for other_metadata in metadata_list:
                if (not metadata.have_equal_fields(other_metadata)):
                    raise NonUniformFieldsError(metadata,other_metadata)
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

class Zooniverse_Dataset(Dataset):
    def __init__(self, dataset_filename):
        """
        Initializes a Zooniverse_Dataset object (child Class of Dataset), a container which holds a list of Data objects and a list of Metadata
        objects. When accessing, per index a dictionary containing the corresponding Data object and Metadata object
        will be given. Generated through an existing dataset file which contains at least Metadata values for RA and DEC.

        Parameters
        ----------
            dataset_filename : str
                The full path filename of the dataset CSV file to be used for the Zooniverse_Dataset object.
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
        with open(dataset_filename, newline='') as targetList:
            reader = csv.DictReader(targetList)
            for row in reader:
                RA = row['RA']
                DEC = row['DEC']

                row_metadata = []
                metadata_field_names = []
                for key in row.keys():
                    metadata_field_names.append(key)
                for key in row:
                    row_metadata.append(row[key])
                metadata_list.append(Metadata(metadata_field_names, row_metadata))

                # set WV parameters to RA and DEC
                wise_view_parameters = wv.custom_params(RA=RA, DEC=DEC)

                # Save all images for parameter set, add grid if toggled for that image
                flist = wv.png_set(wise_view_parameters, "pngs")

                data_field_names = []
                for i in range(len(flist)):
                    data_field_names.append("f" + str(i+1))
                data_list.append(Data(data_field_names, flist))
        super(Zooniverse_Dataset, self).__init__(data_list, metadata_list)


class CN_Dataset(Zooniverse_Dataset):
    def __init__(self, dataset_filename):
        """
        Initializes a CN_Dataset object (child Class of Zooniverse_Dataset), a container which holds a list of Data
        objects and a list of Metadata objects. When accessing, per index a dictionary containing the corresponding Data
        object and Metadata object will be given. Generated through an existing dataset file which contains at least
        Metadata values for RA, DEC, and !GRID.

        Parameters
        ----------
            dataset_filename : str
                The full path filename of the dataset CSV file to be used for the CN_Dataset object.
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
        with open(dataset_filename, newline='') as targetList:
            reader = csv.DictReader(targetList)
            for row in reader:
                RA = float(row['RA'])
                DEC = float(row['DEC'])
                GRID = int(row['!GRID'])

                # parse GRID into boolean values, only accept 1 as True, otherwise GRID is False.
                if (GRID == 1):
                    GRID = True
                else:
                    GRID = False

                row_metadata = []
                metadata_field_names = []
                for key in row.keys():
                    metadata_field_names.append(key)
                for key in row:
                    row_metadata.append(row[key])
                metadata_list.append(Metadata(metadata_field_names, row_metadata))

                # set WV parameters to RA and DEC
                wise_view_parameters = wv.custom_params(RA=RA, DEC=DEC)
                # Save all images for parameter set, add grid if toggled for that image
                flist = wv.png_set(wise_view_parameters, "pngs", scale_factor=2, addGrid=GRID)

                data_field_names = []
                for i in range(len(flist)):
                    data_field_names.append("f" + str(i + 1))
                data_list.append(Data(data_field_names, flist))
        super(Zooniverse_Dataset, self).__init__(data_list, metadata_list)

