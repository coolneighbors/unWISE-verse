"""
Created on Thursday, June 9th

@author: Austin Humphreys
"""

import csv
import math
import os
import pickle
from copy import copy
from statistics import mean
import warnings
import platform
import time as clock

import astropy
from astropy import time
from astropy import units as u
from astropy.coordinates import SkyCoord
import multiprocessing as mp
from flipbooks import WiseViewQuery, unWISEQuery

from unWISE_verse.UserInterface import display

from unWISE_verse import MetadataPointers

from unWISE_verse import Data


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
            require_uniform_fields : A boolean determining whether to require all data objects to have the exact same
            field names and requires all metadata objects to have the exact same field names

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
                self.metadata_list.append(Data.Metadata([f"{Data.Metadata.privatization_symbol}no_metadata"], [""]))

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
                data_list.append(Data.Data.createFromDictionary(row))

        metadata_list = []
        with open(metadata_csv_filename, newline='') as metadata_file:
            reader = csv.DictReader(metadata_file)
            for row in reader:
                metadata_list.append(Data.Metadata.createFromDictionary(row))

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

        display("Dataset created.", display_printouts, UI)

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

                if (is_partial_cutout and ignore_partial_cutouts):
                    display(f"Row {count} out of {total_data_rows} in {dataset_filename} with (RA,DEC): ({RA}, {DEC}) is a partial cutout and has been ignored.", display_printouts, UI)
                else:
                    display(f"Row {count} out of {total_data_rows} has been downloaded.", display_printouts, UI)

                data_field_names = []
                for i in range(len(flist)):
                    data_field_names.append("f" + str(i + 1))

                if (not is_partial_cutout or not ignore_partial_cutouts):
                    data_list.append(Data.Data(data_field_names, flist))
                    metadata_list.append(Data.Metadata(metadata_field_names, row_metadata))
                else:
                    ignored_data_list.append(Data.Data(data_field_names, flist))
                    ignored_metadata_list.append(Data.Metadata(["Original Row: ", *metadata_field_names], [count, *row_metadata]))

        if (len(ignored_data_list) != 0):
            self.generateIgnoredTargetsCSV(ignored_data_list, ignored_metadata_list)
        elif (os.path.exists("ignored-targets.csv")):
            os.remove("ignored-targets.csv")

        return data_list, metadata_list

    def generateIgnoredTargetsCSV(self, filename, ignored_data_list, ignored_metadata_list):
        temp_dataset = Dataset(ignored_data_list,ignored_metadata_list,self.require_uniform_fields)
        with open(filename, "w", newline='') as ignored_targets_file:
            writer = csv.DictWriter(ignored_targets_file, [*temp_dataset.metadata_field_names,*temp_dataset.data_field_names])
            writer.writeheader()
            for dataset_dict in temp_dataset:
                writer.writerow(dataset_dict["metadata"].toDictionary() | dataset_dict["data"].toDictionary())

class CN_Dataset(Zooniverse_Dataset):

    def __init__(self, dataset_filename, ignore_partial_cutouts=False, require_uniform_fields=True, display_printouts=False, UI=None):
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
        super(CN_Dataset, self).__init__(dataset_filename, ignore_partial_cutouts, require_uniform_fields, display_printouts, UI)

    def generateRowWiseViewQuery(self, row):
        """
        Generates a WiseViewQuery object from a row of a dataset CSV file.

        Parameters
        ----------
        row : dict
            A dictionary containing the metadata for a single row of a dataset CSV file. Keys should be the field names.

        Returns
        -------
        wise_view_query : WiseViewQuery object
            A WiseViewQuery object generated from the row of the dataset CSV file.

        """


        RA = float(row['RA'])
        DEC = float(row['DEC'])
        FOV = float(row['FOV'])

        # Pixel side-length of the images
        SIZE = WiseViewQuery.WiseViewQuery.FOVToPixelSize(FOV)

        MINBRIGHT = None
        MAXBRIGHT = None

        if (row[f'{Data.Metadata.privatization_symbol}MINBRIGHT'] == "" or row[f'{Data.Metadata.privatization_symbol}MAXBRIGHT'] == ""):

            unWISE_query = unWISEQuery.unWISEQuery(ra=RA, dec=DEC, size=SIZE, bands=12)
            brightness_clip = unWISE_query.calculateBrightnessClip(mode="percentile", percentile=97.5)
            if (row[f'{Data.Metadata.privatization_symbol}MINBRIGHT'] == ""):
                MINBRIGHT = brightness_clip[0]
            else:
                MINBRIGHT = float(row[f'{Data.Metadata.privatization_symbol}MINBRIGHT'])
            if (row[f'{Data.Metadata.privatization_symbol}MAXBRIGHT'] == ""):
                MAXBRIGHT = brightness_clip[1]
            else:
                MAXBRIGHT = float(row[f'{Data.Metadata.privatization_symbol}MAXBRIGHT'])
        else:
            MINBRIGHT = int(row[f'{Data.Metadata.privatization_symbol}MINBRIGHT'])
            MAXBRIGHT = int(row[f'{Data.Metadata.privatization_symbol}MAXBRIGHT'])

        if (MAXBRIGHT < MINBRIGHT):
            raise ValueError(f"MAXBRIGHT ({MAXBRIGHT}) is less than MINBRIGHT ({MINBRIGHT})")

        # Set WiseView parameters
        wise_view_query = WiseViewQuery.WiseViewQuery(RA=RA, DEC=DEC, size=SIZE, minbright=MINBRIGHT, maxbright=MAXBRIGHT, window=1.5)

        return wise_view_query

    def generateDataAndMetadata(self, row, index, png_count, sub_directory_path, wise_view_queries):
        # Get metadata
        RA = float(row['RA'])
        DEC = float(row['DEC'])
        PNG_DIRECTORY = row[f'{Data.Metadata.privatization_symbol}PNG_DIRECTORY']
        ADDGRID = int(row[f'{Data.Metadata.privatization_symbol}ADDGRID'])
        GRIDCOUNT = int(row[f'{Data.Metadata.privatization_symbol}GRIDCOUNT'])
        SCALE = int(row[f'{Data.Metadata.privatization_symbol}SCALE'])
        FOV = float(row['FOV'])

        GRIDTYPE = row[f'{Data.Metadata.privatization_symbol}GRIDTYPE']
        RGB_list = []
        for s in row[f'{Data.Metadata.privatization_symbol}GRIDCOLOR'][1:][:-1].split(","):
            RGB_list.append(int(s))
        GRIDCOLOR = tuple(RGB_list)

        # Access the WiseViewQuery object for this row
        wise_view_query = wise_view_queries[index]

        # Assign the metadata values to the row
        row[f'{Data.Metadata.privatization_symbol}MINBRIGHT'] = wise_view_query.wise_view_parameters["minbright"]
        row[f'{Data.Metadata.privatization_symbol}MAXBRIGHT'] = wise_view_query.wise_view_parameters["maxbright"]
        row['Data Source'] = f"[unWISE](+tab+http://unwise.me/)"
        row['unWISE Pixel Scale'] = f"~{WiseViewQuery.unWISE_pixel_scale} arcseconds per pixel"

        # Get the modified Julian dates for each frame
        modified_julian_date_pairs = wise_view_query.requestMetadata("mjds")
        date_str = ""
        for i in range(len(modified_julian_date_pairs)):
            for j in range(len(modified_julian_date_pairs[i])):
                if (j == 0):
                    time_start = time.Time(modified_julian_date_pairs[i][j], format="mjd").to_value("decimalyear")
                if (j == len(modified_julian_date_pairs[i]) - 1):
                    time_end = time.Time(modified_julian_date_pairs[i][j], format="mjd").to_value("decimalyear")
            if (time_start == time_end):
                if (i != len(modified_julian_date_pairs) - 1):
                    date_str = date_str + f"Frame {i + 1}: {round(time_start, 2)}, "
                else:
                    date_str = date_str + f"Frame {i + 1}: {round(time_start, 2)}"
            else:
                if (i != len(modified_julian_date_pairs) - 1):
                    date_str = date_str + f"Frame {i + 1}: {round(mean([time_start, time_end]), 2)}, "
                else:
                    date_str = date_str + f"Frame {i + 1}: {round(mean([time_start, time_end]), 2)}"

        # Assign the generated modified Julian dates string to the row
        row["Decimal Year Epochs"] = date_str

        # Determine the galactic and ecliptic coordinates of the image and assign them to the row
        ICRS_coordinates = SkyCoord(ra=RA * u.degree, dec=DEC * u.degree, frame='icrs')

        galactic_coordinates = ICRS_coordinates.transform_to(frame="galactic")
        row['Galactic Coordinates'] = galactic_coordinates.to_string("decimal")

        ecliptic_coordinates = ICRS_coordinates.transform_to(frame=astropy.coordinates.GeocentricMeanEcliptic)
        row[f'{Data.Metadata.privatization_symbol}Ecliptic Coordinates'] = ecliptic_coordinates.to_string("decimal")

        # Assign the associated WISEVIEW url to the row
        row['WISEVIEW'] = f"[WiseView](+tab+{wise_view_query.generateWiseViewURL()})"

        # Radius is the smallest circle radius which encloses the square image.
        # This is done to ensure the entire image frame is searched.
        radius = (math.sqrt(2) / 2) * FOV

        VizieR_FOV = 15

        # Assign the associated SIMBAD, Legacy Surveys, VizieR, and IRSA urls to the row
        row['SIMBAD'] = f"[SIMBAD](+tab+{MetadataPointers.generate_SIMBAD_url(RA, DEC, radius)})"
        row['Legacy Surveys'] = f"[Legacy Surveys](+tab+{MetadataPointers.generate_legacy_survey_url(RA, DEC)})"
        row['VizieR'] = f"[VizieR](+tab+{MetadataPointers.generate_VizieR_url(RA, DEC, VizieR_FOV)})"
        row['IRSA'] = f"[IRSA](+tab+{MetadataPointers.generate_IRSA_url(RA, DEC)})"

        # Save all images for parameter set, add grid if toggled for that image
        flist, size_list = wise_view_query.downloadWiseViewData(os.path.join(PNG_DIRECTORY, sub_directory_path),
                                                                scale_factor=SCALE, addGrid=ADDGRID,
                                                                gridCount=GRIDCOUNT, gridType=GRIDTYPE,
                                                                gridColor=GRIDCOLOR)
        png_count += len(flist)
        is_partial_cutout = False
        for size in size_list:
            width, height = size
            row["unWISE Pixel Width"] = int(width/SCALE)
            row["unWISE Pixel Height"] = int(height/SCALE)
            row['FOV'] = f"{round(wise_view_query.PixelSizeToFOV(int(width/SCALE)),2)} x {round(wise_view_query.PixelSizeToFOV(int(height/SCALE)),2)} arcseconds"
            if (width != height):
                is_partial_cutout = True
                break

        row_metadata = list(row.values())
        metadata_field_names = list(row.keys())

        data_field_names = []
        for i in range(len(flist)):
            data_field_names.append("f" + str(i + 1))

        data = Data.Data(data_field_names, flist)
        metadata = Data.Metadata(metadata_field_names, row_metadata)

        return data, metadata, png_count, is_partial_cutout


    def saveState(self, dataset_filename, data_list, metadata_list, png_count, sub_directory, time_per_row, wise_view_queries_time, wise_view_queries):
        # Create the save state file name based on the dataset filename
        save_state_filename = os.path.splitext(os.path.basename(dataset_filename))[0] + "_save_state.pkl"

        # Save the data and metadata lists to a pickle file
        with open(save_state_filename, 'wb') as save_state_file:
            pickle.dump([data_list, metadata_list, png_count, sub_directory, time_per_row, wise_view_queries_time, wise_view_queries], save_state_file)

    def loadState(self, dataset_filename):
        # Create the save state file name based on the dataset filename
        save_state_filename = os.path.splitext(os.path.basename(dataset_filename))[0] + "_save_state.pkl"

        # Load the data and metadata lists from a pickle file
        with open(save_state_filename, 'rb') as save_state_file:
            data_list, metadata_list, png_count, sub_directory, time_per_row, wise_view_queries_time, wise_view_queries = pickle.load(save_state_file)

        return data_list, metadata_list, png_count, sub_directory, time_per_row, wise_view_queries_time, wise_view_queries

    def deleteState(self, dataset_filename):
        # Create a save state file name based on the dataset filename
        save_state_filename = os.path.splitext(os.path.basename(dataset_filename))[0] + "_save_state.pkl"

        # Delete the save state file
        os.remove(save_state_filename)

    def stateExists(self, dataset_filename):
        # Create a save state file name based on the dataset filename
        save_state_filename = os.path.splitext(os.path.basename(dataset_filename))[0] + "_save_state.pkl"

        # Return whether the save state file exists
        return os.path.exists(save_state_filename)

    def getNextSubDirectory(self, directories, sub_directory_limit, UI=None):
        sub_directory_values = []

        for sub_directory_name in directories:
            try:
                sub_directory_values.append(int(sub_directory_name))
            except ValueError:
                sub_directory_name_form = ""
                for c in str(sub_directory_limit):
                    sub_directory_name_form += "0"
                if (not self.given_directory_warning):
                    display(f"Warning: Sub-directory name {sub_directory_name} is not of the form: {sub_directory_name_form}", True, UI)
                    self.given_directory_warning = True

        max_value = max(sub_directory_values, default=-1)
        max_value = max_value + 1
        if (max_value > sub_directory_limit):
            raise OverflowError(f"Subdirectories with indexes greater than the sub directory limit ({sub_directory_limit}) are trying to be created.")
        sub_directory = str(max_value)
        for i in range(len(str(sub_directory_limit)) - len(sub_directory)):
            if (len(sub_directory) < len(str(sub_directory_limit))):
                sub_directory = "0" + sub_directory

        return sub_directory

    def handleSubDirectoryOverflow(self, png_count, sub_directory, sub_directory_threshold, sub_directory_limit):
        if (png_count >= sub_directory_threshold):
            sub_directory = str(int(sub_directory) + 1)
            if (int(sub_directory) + 1 > sub_directory_limit):
                raise OverflowError(f"Subdirectories with indexes greater than the sub directory limit ({sub_directory_limit}) are trying to be created.")
            for i in range(len(str(sub_directory_limit)) - len(sub_directory)):
                if (len(sub_directory) < len(str(sub_directory_limit))):
                    sub_directory = "0" + sub_directory
            png_count = 0

        return png_count, sub_directory

    def generateDataAndMetadataLists(self, dataset_filename, ignore_partial_cutouts = False, display_printouts=False, UI=None):

        # Initialize the data and metadata lists
        data_list = []
        metadata_list = []

        # Initialize the ignored data and metadata lists
        ignored_data_list = []
        ignored_metadata_list = []

        # Initialize the sub-directory values
        sub_directory_limit = 9999
        sub_directory_threshold = 1000

        # Initialize the png count
        png_count = 0

        # Initialize the size of chunks to be processed
        chunk_size = 1000

        # Initialize whether partial cutouts are to be ignored in the dataset
        if(UI is not None):
            ignore_partial_cutouts = UI.ignorePartialCutouts.get()

        # Initialize the wise view queries list
        wise_view_queries = []

        # Get the total number of rows in the dataset for determining the progress
        total_data_rows = 0
        with open(dataset_filename, newline='') as dataset_file:
            total_data_rows = len(list(dataset_file)) - 1

        # Begin processing the dataset file
        with open(dataset_filename, newline='') as dataset_file:
            # Create a csv reader for the dataset file and get all its rows
            reader = csv.DictReader(dataset_file)
            all_rows = [row for row in reader]

            # Get the number of chunks to be processed
            total_chunks = math.ceil(len(all_rows) / chunk_size)

            time_per_row = 0

            # Iterate through the chunks
            for chunk_index in range(total_chunks):
                # Initialize the sub-directory value to 0
                sub_directory = 0

                # Initialize the warning booleans
                self.given_file_warning = False
                self.given_directory_warning = False

                # Get the rows associated with the current chunk
                chunk_rows = all_rows[chunk_index * chunk_size:(chunk_index + 1) * chunk_size]

                # Check if a save state exists for the dataset and if it does, load it.
                if (self.stateExists(dataset_filename)):
                    data_list, metadata_list, png_count, sub_directory, time_per_row, wise_view_queries_time, wise_view_queries = self.loadState(dataset_filename)
                    current_row_index = len(data_list) - 1
                    current_chunk_index = math.floor(current_row_index / chunk_size)
                    if(current_chunk_index > chunk_index):
                        continue

                # Display that the chunk is being processed
                display(f"Downloading chunk {chunk_index}: ", display_printouts, UI)


                # Get the overall row index of the first row in the chunk
                chunk_first_row_index = chunk_index * chunk_size

                # If there are more wise view queries than the chunk's first row index, then the wise view queries are already generated for this chunk
                if (chunk_first_row_index - len(wise_view_queries) >= 0):
                    # Set the bunch size for processing the wise view queries
                    bunch_size = 25

                    # Create a process pool to generate the wise view queries
                    # Initialize the start time
                    wise_view_queries_start_time = clock.time()
                    for i in range(0, len(chunk_rows), bunch_size):
                        try:
                            if (UI.exitRequested):
                                return [Data.Data()], [Data.Metadata()]
                        except:
                            pass
                        if (i + bunch_size > len(chunk_rows)):
                            bunch_size = len(chunk_rows) - i
                        display(f"Generating WiseViewQueries for rows {chunk_first_row_index + i + 1} to {chunk_first_row_index + i + bunch_size}", display_printouts, UI)

                        # Get the bunch of rows to be processed
                        bunch = chunk_rows[i:i + bunch_size]

                        # Define an error callback for the wise view query creation threads
                        def error_callback(e):
                            print(f"Error in WiseViewQuery creation thread: {e}")

                        # Create a process pool to generate the wise view queries
                        pool = mp.Pool()

                        # Create a list of processes to generate the wise view queries
                        processes = [pool.apply_async(self.generateRowWiseViewQuery, args=(row,), error_callback=error_callback) for row in bunch]

                        # Close the process pool
                        pool.close()

                        # Wait for the processes to finish
                        pool.join()

                        # Get the wise view queries from the processes
                        bunch_wise_view_queries = [p.get() for p in processes]

                        # Add the wise view queries to the overall wise view queries list
                        wise_view_queries.extend(bunch_wise_view_queries)

                    wise_view_queries_end_time = clock.time()
                    wise_view_queries_time = wise_view_queries_end_time - wise_view_queries_start_time

                    # Save the state
                    self.saveState(dataset_filename, data_list, metadata_list, png_count, sub_directory, time_per_row, wise_view_queries_time, wise_view_queries)

                    # Display that the image downloads are beginning for the chunk
                    display(f"Beginning image downloads for chunk {chunk_index}.", display_printouts, UI)


                # Iterate through the rows in the chunk
                for chunk_row_index, row in enumerate(chunk_rows):
                    try:
                        if (UI.exitRequested):
                            return [Data.Data()], [Data.Metadata()]
                    except:
                        pass

                    # Get the row index of the current row being processed
                    row_index = chunk_index * chunk_size + chunk_row_index

                    # Check if a save state exists for the dataset and if it does, load it.
                    if (self.stateExists(dataset_filename)):
                        data_list, metadata_list, png_count, sub_directory, time_per_row, wise_view_queries_time, wise_view_queries = self.loadState(dataset_filename)
                        loaded_row_index = len(data_list) - 1
                        if(row_index <= loaded_row_index):
                            continue

                    row_time_start = clock.time()
                    # Get the PNG_DIRECTORY from the row
                    PNG_DIRECTORY = row[f'{Data.Metadata.privatization_symbol}PNG_DIRECTORY']


                    # Check if the current index is the first index of the chunk
                    if(chunk_row_index == 0):

                        # Check if the current chunk is the first chunk
                        if(chunk_index == 0):
                            # Loop through each chunk index to create the chunk directories
                            for n in range(total_chunks):

                                # If the chunk directory doesn't exist, create it
                                if (not os.path.exists(os.path.join(PNG_DIRECTORY, f"Chunk_{n}"))):
                                    os.mkdir(os.path.join(PNG_DIRECTORY, f"Chunk_{n}"))
                                else:
                                    # If the chunk directory already exists, display a warning
                                    display(f"The Chunk_{n} directory already exists in {PNG_DIRECTORY}. This may cause issues.", display_printouts, UI)

                        # Create the filepath for the current chunk directory
                        chunk_directory = os.path.join(PNG_DIRECTORY, f"Chunk_{chunk_index}")

                        # Get the directories in the chunk directory
                        directories = [name for name in os.listdir(chunk_directory) if os.path.isdir(os.path.join(chunk_directory, name))]

                        # Increment the sub_directory value to the next sub_directory
                        if(len(directories) == 0):
                            sub_directory = self.getNextSubDirectory(directories, sub_directory_limit, UI)

                        # Save the state
                        self.saveState(dataset_filename, data_list, metadata_list, png_count, sub_directory, time_per_row, wise_view_queries_time, wise_view_queries)

                        # If a non-png directory is found, display a warning. Unless the user has already been warned.
                        if (not self.given_file_warning):

                            # Get all of the directories/files in the chunk_directory which are not known png directories
                            file_list = [x for x in os.listdir(chunk_directory) if x not in directories]
                            # Remove .DS_Store from the list if it is present (MAC-OS file)
                            if (platform.system() == "Darwin" and ".DS_Store" in file_list):
                                file_list.remove(".DS_Store")
                            if (len(file_list) != 0):
                                if (len(file_list) == 1):
                                    display(f"The following file (or directory) was found in {chunk_directory} and does not belong: {', '.join(file_list)}", display_printouts, UI)
                                else:
                                    display(f"The following files (or directories) were found in {chunk_directory} and do not belong: {', '.join(file_list)}", display_printouts, UI)
                                self.given_file_warning = True

                    # Check if the current sub_directory has reached the sub_directory_threshold, and if it has update sub_directory and png_count
                    png_count, sub_directory = self.handleSubDirectoryOverflow(png_count, sub_directory, sub_directory_threshold, sub_directory_limit)
                    # Save the state
                    self.saveState(dataset_filename, data_list, metadata_list, png_count, sub_directory, time_per_row, wise_view_queries_time, wise_view_queries)

                    # Begin to generate the data and metadata for the current row and disable the ability to safely quit
                    UI.canSafelyQuit = False

                    # Generate the data and metadata for the current row
                    data, metadata, png_count, is_partial_cutout = self.generateDataAndMetadata(row, row_index, png_count, os.path.join(f"Chunk_{chunk_index}", sub_directory), wise_view_queries)

                    # Display that the current row has been ignored if it is a partial cutout and ignore_partial_cutouts is True
                    if (is_partial_cutout and ignore_partial_cutouts):
                        RA = float(row['RA'])
                        DEC = float(row['DEC'])
                        display(f"Row {row_index + 1} out of {total_data_rows} in {dataset_filename} with (RA,DEC): ({RA}, {DEC}) is a partial cutout and has been ignored.", display_printouts, UI)
                    else:
                        display(f"Row {row_index + 1} out of {total_data_rows} has been downloaded.",display_printouts, UI)

                    # Check if the current row is a partial cutout and if ignore_partial_cutouts is True
                    if (not is_partial_cutout or not ignore_partial_cutouts):
                        # Add the data and metadata to the lists
                        data_list.append(data)
                        metadata_list.append(metadata)

                        # Save the state
                        self.saveState(dataset_filename, data_list, metadata_list, png_count, sub_directory, time_per_row, wise_view_queries_time, wise_view_queries)
                    else:
                        # Add the data and metadata to the ignored lists if the row is a partial cutout and ignore_partial_cutouts is True
                        ignored_data_list.append(data)
                        ignored_metadata_list.append(metadata)

                    row_time_end = clock.time()
                    row_time = row_time_end - row_time_start

                    row_time = row_time + (wise_view_queries_time / chunk_size)

                    if (time_per_row == 0):
                        time_per_row = row_time
                    else:
                        time_per_row = (time_per_row + row_time) / 2

                    # Save the state
                    self.saveState(dataset_filename, data_list, metadata_list, png_count, sub_directory, time_per_row, wise_view_queries_time, wise_view_queries)

                    # Enable the ability to safely quit
                    UI.canSafelyQuit = True

                # Save the state
                self.saveState(dataset_filename, data_list, metadata_list, png_count, sub_directory, time_per_row, wise_view_queries_time, wise_view_queries)

                # Estimate the time remaining for the remaining rows
                remaining_rows = total_data_rows - (row_index + 1)
                time_remaining = remaining_rows * time_per_row

                # Depending on how many seconds are remaining, display the time remaining in a different format
                def formatTimeRemaining(time_remaining):
                    MINUTE = 60
                    HOUR = 60 * MINUTE
                    DAY = 24 * HOUR
                    WEEK = 7 * DAY
                    MONTH = 30.44 * DAY
                    YEAR = 365.24 * DAY

                    time_units = [
                        (YEAR, 'year'),
                        (MONTH, 'month'),
                        (WEEK, 'week'),
                        (DAY, 'day'),
                        (HOUR, 'hour'),
                        (MINUTE, 'minute'),
                        (1, 'second')
                    ]

                    parts = []
                    for unit, unit_name in time_units:
                        if time_remaining >= unit:
                            num_units = int(time_remaining / unit)
                            time_remaining -= num_units * unit
                            parts.append(f"{num_units} {unit_name}{'' if num_units == 1 else 's'}")

                    return ', '.join(parts)

                # Display that the chunk has been completed and the estimated time remaining
                if(chunk_index != total_chunks - 1):
                    display(f"Chunk {chunk_index + 1} out of {total_chunks} has been completed. \nThe estimated time remaining: {formatTimeRemaining(time_remaining)}.", display_printouts, UI)

                # Reset the png_count
                png_count = 0

                # Save the state
                self.saveState(dataset_filename, data_list, metadata_list, png_count, sub_directory, time_per_row, wise_view_queries_time, wise_view_queries)

            # Generate the CSV files for the ignored data and metadata
            ignored_targets_csv_filename = f"ignored-targets_chunk_{chunk_index}.csv"
            if (len(ignored_data_list) != 0):
                self.generateIgnoredTargetsCSV(ignored_targets_csv_filename, ignored_data_list, ignored_metadata_list)
            elif(os.path.exists(ignored_targets_csv_filename)):
                os.remove(ignored_targets_csv_filename)
        # If the UI has requested an exit near the end of processing DO NOT delete the state, this is most likely an
        # accidental exit and the user will want to resume.
        try:
            if(not UI.exitRequested):
                # Delete the state
                self.deleteState(dataset_filename)
        except:
            # Delete the state
            self.deleteState(dataset_filename)

        # Return the data and metadata lists
        return data_list, metadata_list
