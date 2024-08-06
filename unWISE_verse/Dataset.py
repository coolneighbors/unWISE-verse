import atexit
import csv
import hashlib
import logging
import math
import tkinter
from datetime import datetime
from logging.handlers import QueueListener, QueueHandler
import multiprocessing
import os
import pickle
import random
import re
import signal
import time

import astropy
from astropy import time as astropy_time
from astropy.coordinates import SkyCoord
from astropy import units as u
from flipbooks import unWISEQuery, WiseViewQuery
from statistics import mean

from flipbooks.LegacySurveyQuery import LegacySurveyQuery
from tqdm import tqdm

from Data import Data
from unWISE_verse import MetadataLinks, ImageCrafter
from unWISE_verse.Chunker import Chunker, PreexistingChunkerError, NonEmptyChunkingDirectoryError
from unWISE_verse.Logger import Logger
from typing import List, Union, Callable

from unWISE_verse import InputField
import tkinter as tk

def empty_progress_callback(text):
    pass

# TODO: Implement a way to allow some metadata values to be empty or conditionally empty.

class Dataset:
    def __init__(self, data_list: Union[List[Data], List[dict]], uniform_data = False, uniform_metadata = False, progress_callback: Callable = None):
        """
        Initializes a Dataset object, an object which stores a list of data and metadata dictionaries.

        Parameters
        ----------
            data_list : list
                A list of data objects or dictionaries, where each dictionary has a "data" and "metadata" key which map to dictionaries of data and metadata field names and values.
            uniform_data : bool, optional
                Used to determine whether the data field names are uniform across all data objects. By default, it is False.
            uniform_metadata : bool, optional
                Used to determine whether the metadata field names are uniform across all data objects. By default, it is False.
            progress_callback : function, optional
                A function which takes in a string and displays it to the user for progress updates. By default, it is None.

        Notes
        -----
            The data_list should be a list of Data objects, but it can also be a list of dictionaries with "data" and "metadata" keys.
        """

        if(progress_callback is None):
            self.progress_callback = empty_progress_callback
        else:
            self.progress_callback = progress_callback
            self.progress_callback(f"Initializing {self.__class__.__name__}...")

        formatted_data_list = []

        for data in data_list:
            if (isinstance(data, dict)):
                if ("data" not in data):
                    raise KeyError("The data dictionary provided does not have a 'data' key.")
                if ("metadata" not in data):
                    raise KeyError("The data dictionary provided does not have a 'metadata' key.")
                if (not isinstance(data["data"], dict)):
                    raise TypeError("The data dictionary provided does not have a dictionary as the 'data' value.")
                if (not isinstance(data["metadata"], dict)):
                    raise TypeError("The data dictionary provided does not have a dictionary as the 'metadata' value.")
                formatted_data_list.append(Data(data["data"], data["metadata"]))
            elif (not isinstance(data, Data)):
                raise TypeError(f"The provided element, {data}, is not a Data object or a dictionary.")
            else:
                formatted_data_list.append(data)

        self.data_list = formatted_data_list

        self.uniform_data = uniform_data
        self.uniform_metadata = uniform_metadata

        if(len(self.data_list) > 0):
            if (uniform_data):
                data_field_names = self.data_list[0].getDataFieldNames()
                for data in self.data_list:
                    mismatched_field_names = []
                    if (data.getDataFieldNames() != data_field_names):
                        for field_name in data.getDataFieldNames():
                            if (field_name not in data_field_names):
                                mismatched_field_names.append(field_name)
                        raise ValueError("The data field names are not uniform across all data objects with the following mismatched field names: " + str(mismatched_field_names))

            if (uniform_metadata):
                metadata_field_names = self.data_list[0].getMetadataFieldNames()
                for data in self.data_list:
                    if (data.getMetadataFieldNames() != metadata_field_names):
                        mismatched_field_names = []
                        for field_name in data.getMetadataFieldNames():
                            if (field_name not in metadata_field_names):
                                mismatched_field_names.append(field_name)
                        raise ValueError("The metadata field names are not uniform across all data objects with the following mismatched field names: " + str(mismatched_field_names))

    def __len__(self):
        """
        Overloads the len() function for the Dataset object.
        """
        return len(self.data_list)

    def __getitem__(self, index):
        """
        Overloads the [] operator for the Dataset object.
        """

        return self.data_list[index]

    def __str__(self):
        """
        Overloads the str() function for the Dataset object.
        """

        if(self.uniform_data and self.uniform_metadata):
            return "Dataset with " + str(len(self.data_list)) + " data objects with uniform data and metadata fields: " + str(self.data_list[0].getDataFieldNames()) + " and " + str(self.data_list[0].getMetadataFieldNames()) + ", respectively."
        elif(self.uniform_data):
            return "Dataset with " + str(len(self.data_list)) + " data objects with uniform data fields: " + str(self.data_list[0].getDataFieldNames()) + "."
        elif(self.uniform_metadata):
            return "Dataset with " + str(len(self.data_list)) + " data objects with uniform metadata fields: " + str(self.data_list[0].getMetadataFieldNames()) + "."
        else:
            return "Dataset with " + str(len(self.data_list)) + " data objects."

    def __repr__(self):
        """
        Overloads the repr() function for the Dataset object such that a string of the data list is provided.
        """
        return repr(self.data_list)

    def getDictionaries(self):
        """
        Returns a list of dictionaries from the data objects in the dataset.
        """

        return [data.getDictionary(reduced=False) for data in self.data_list]

class ZooniverseDataset(Dataset):
    def __init__(self, manifest_filename, uniform_data = False, uniform_metadata = False, progress_callback = None):
        """
        Initializes a ZooniverseDataset object, an object which stores a list of data objects meant to be used for Zooniverse projects.

        Parameters
        ----------
            manifest_filename : str
                The manifest filename of the CSV file containing the Zooniverse subject data and metadata.
            uniform_data : bool, optional
                Used to determine whether the data field names are uniform across all data objects. By default, it is False.
            uniform_metadata : bool, optional
                Used to determine whether the metadata field names are uniform across all data objects. By default, it is False.
            progress_callback : function, optional
                A function which takes in a string and displays it to the user for progress updates. By default, it is None.
        """
        self.manifest_filename = manifest_filename

        data_list = self.loadDataFromManifest(manifest_filename)

        super().__init__(data_list, uniform_data, uniform_metadata, progress_callback)

    def loadDataFromManifest(self, filename):
        """
        Loads the data from the manifest CSV file into a list of data objects.

        Parameters
        ----------
            filename : str
                The manifest filename of the Zooniverse subject data and metadata CSV file.
        """

        data_list = []

        # If the file doesn't exist return an empty list
        if (not os.path.exists(filename)):
            return data_list

        with open(filename, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:

                # Find all fields with are of the form "fn" where n is an integer.
                # These fields are the data fields and the rest are the metadata fields.
                data_field_names = []
                metadata_field_names = []
                for field_name in row.keys():
                    if (re.match(r"^f\d+$", field_name)):
                        data_field_names.append(field_name)
                    else:
                        metadata_field_names.append(field_name)

                data = {}
                metadata = {}

                for data_field_name in data_field_names:
                    data[data_field_name] = row[data_field_name]

                for metadata_field_name in metadata_field_names:
                    metadata[metadata_field_name] = row[metadata_field_name]

                data_list.append(Data(data, metadata))

        return data_list

    @classmethod
    def generateManifest(cls, manifest_filename, data_list):
        """
        Generates a manifest CSV file from a list of data objects.

        Parameters
        ----------
            manifest_filename : str
                The manifest filename of the CSV file containing the Zooniverse subject data and metadata.
            data_list : list
                A list of data objects.
        """

        data_field_names = []
        metadata_field_names = []

        if(isinstance(data_list[0], Data)):
            data_field_names = data_list[0].getDataFieldNames()
            metadata_field_names = data_list[0].getMetadataFieldNames(reduced=False)
        elif(isinstance(data_list[0], tuple)):
            flag, data = data_list[0]
            data_field_names = data.getDataFieldNames()
            metadata_field_names = data.getMetadataFieldNames(reduced=False)
        else:
            raise TypeError("The data list must contain either Data objects or tuples of the form (flag, data).")

        ignored_data = []
        valid_data = []
        # Go through the data list and add any new metadata field names to the metadata field names list.
        for data in data_list:
            if(isinstance(data, Data)):
                for metadata_field_name in data.getMetadataFieldNames(reduced=False):
                    if (metadata_field_name not in metadata_field_names):
                        metadata_field_names.append(metadata_field_name)

                for data_field_name in data.getDataFieldNames():
                    if (data_field_name not in data_field_names):
                        data_field_names.append(data_field_name)

                valid_data.append(data)
            else:
                if(isinstance(data, tuple)):
                    flag, data = data
                    if(flag is None):
                        ignored_data.append(data)
                    else:
                        raise NotImplementedError("Only a flag of None is currently supported.")
                else:
                    raise TypeError("The data list must only contain Data objects or tuples of the form (flag, Data).")

        with open(manifest_filename, "w", newline='') as file:
            writer = csv.DictWriter(file, fieldnames=metadata_field_names + data_field_names)
            writer.writeheader()
            for data in valid_data:
                if(data is not None):
                    row = {}
                    for data_field_name in data_field_names:
                        row[data_field_name] = data[data_field_name]
                    for metadata_field_name in metadata_field_names:
                        row[metadata_field_name] = data[metadata_field_name]
                    writer.writerow(row)

        # Generate the ignored manifest file.
        ignored_manifest_filename = manifest_filename.split(".csv")[0] + "_ignored.csv"
        if (len(ignored_data) > 0):
            with open(ignored_manifest_filename, "w", newline='') as file:
                writer = csv.DictWriter(file, fieldnames=metadata_field_names + data_field_names)
                writer.writeheader()
                for data in ignored_data:
                    if (data is not None):
                        row = {}
                        for data_field_name in data_field_names:
                            row[data_field_name] = data[data_field_name]
                        for metadata_field_name in metadata_field_names:
                            row[metadata_field_name] = data[metadata_field_name]
                        writer.writerow(row)

class AstronomyDataset(ZooniverseDataset):
    required_target_columns = []
    required_private_columns = []
    mutable_columns_dict = {}
    mutable_columns_keys_dict = {}

    def __init__(self, target_filename, manifest_filename, dataset_name, ignore_incomplete_data = False, uniform_data = False, uniform_metadata = False, termination_event = None, log_queue = None, chunk_size = 1000, subchunk_size = 100, max_query_queue_size = 50, query_batch_number = 25):
        """
        Initializes a AstronomyDataset object, an object which stores a list of data objects meant to be used for an Astronomy-based Zooniverse project.

        Parameters
        ----------
            target_filename : str
                The target filename of the CSV file containing the target list, consisting of at least RA, DEC, and TARGET ID as columns.
            manifest_filename : str
                The manifest filename of the generated CSV file containing the Zooniverse subject data and metadata.
            dataset_name : str
                The associated name of the dataset.
            ignore_incomplete_data : bool, optional
                Used to determine whether to ignore incomplete data objects. By default, it is False.
            uniform_data : bool, optional
                Used to determine whether the field names should be uniform across all data objects. By default, it is False.
            uniform_metadata : bool, optional
                Used to determine whether the metadata field names should be uniform across all data objects. By default, it is False.
            termination_event : multiprocessing.Event, optional
                A multiprocessing.Event object which can be used to terminate the process early. By default, it is None.
            log_queue : multiprocessing.Queue
                A multiprocessing.Queue object which can be used to log messages to the main process.
            chunk_size : int, optional
                The size of the chunks to split the data into. By default, it is 1000.
            subchunk_size : int, optional
                The size of the subchunks to split the data into. By default, it is 100.
            max_query_queue_size : int, optional
                The maximum size of the query queue. By default, it is 50.
            query_batch_number : int, optional
                The number of queries to request in a batch. By default, it is 25.

        Notes
        -----
            Whether a data object is complete or incomplete is determined by the user's implementation of the generateData method.
            Usually a target file is be a CSV file with at least the following columns: RA, DEC, TARGET ID.
            The target file may contain additional columns, which will be added to the metadata of the data objects.
            The manifest file must be a CSV file.
            Astronomy Datasets load the data and metadata from the target file with save states, such that progress will
            not be lost if the process was stopped early.
        """

        self.dataset_name = dataset_name

        self.max_query_queue_size = max_query_queue_size
        self.query_batch_number = query_batch_number

        self.column_dictionary = {}
        self.column_names = []
        self.column_keys = []

        # Verify that the these attributes are implemented by the subclass.
        if(not hasattr(self, "required_target_columns")):
            raise NotImplementedError("The required_target_columns attribute must be implemented by the subclass.")
        if(not hasattr(self, "required_private_columns")):
            raise NotImplementedError("The required_private_columns attribute must be implemented by the subclass.")
        if(not hasattr(self, "mutable_columns_dict")):
            raise NotImplementedError("The mutable_columns_dict attribute must be implemented by the subclass.")
        if(not hasattr(self, "mutable_columns_keys_dict")):
            raise NotImplementedError("The mutable_columns_keys_dict attribute must be implemented by the subclass.")

        self.setColumnKeys(target_filename)

        self.ignore_incomplete_data = ignore_incomplete_data

        if(log_queue is None):
            progress_callback = lambda x: print(x)
        else:
            progress_callback = None

        # Verify that the target file exists.
        if(not os.path.isfile(target_filename)):
            raise FileNotFoundError("The target file " + target_filename + " does not exist.")
        
        # Verify that the target file is a CSV file.
        if(not target_filename.endswith(".csv")):
            raise ValueError("The target file " + target_filename + " is not a CSV file.")
        
        # Verify that the manifest file is a CSV file.
        if(not manifest_filename.endswith(".csv")):
            raise ValueError("The manifest file " + manifest_filename + " is not a CSV file.")

        # Verify that the target file has at least the required target keys as columns up to variation of case, spacing, and privatization.
        missing_required_keys = False
        for key in self.required_target_columns:
            if(key not in self.column_keys):
                self.log(f"The target file does not contain the required key: {key}", log_queue)
                missing_required_keys = True

        if(missing_required_keys):
            self.log("Halting process.", log_queue)
            termination_event.set()
            return

        # Verify that the target file has at least the required private keys as columns up to variation of case, spacing, and privatization.
        missing_private_keys = False
        if(len(self.required_private_columns) != 0):
            for key in self.required_private_columns:
                if(key in self.column_keys):
                    first_character = self.column_dictionary[key][0]
                    if(first_character != Data.privatization_symbol):
                        self.log(f"The target file does not contain the required private key: {Data.privatization_symbol}{self.column_dictionary[key]}", log_queue)
                        missing_private_keys = True

        if(missing_private_keys):
            self.log("Halting process.", log_queue)
            termination_event.set()
            return

        # Save a file which will be the save state for the dataset being processed.
        combined_keys = "".join(sorted(self.column_keys))
        dataset_type_name = str(self.__class__.__name__)
        unique_hash_id = hashlib.sha256((target_filename + combined_keys + dataset_type_name).encode("utf-8")).hexdigest()
        self.save_state_filename = str(unique_hash_id) + ".save_state"

        png_directory_key = self.getColumnKey("png_directory")

        try:
            if (png_directory_key is not None):
                # Open the target file and read the PNG directory key.
                with open(target_filename, "r") as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        png_directory = row[png_directory_key]
                        break

                if(Chunker.exists(id=unique_hash_id)):
                    self.chunker = Chunker.load(id=unique_hash_id)
                else:
                    self.chunker = Chunker(png_directory, id=unique_hash_id, chunk_size=chunk_size, subchunk_size=subchunk_size)
            else:
                # Create a local pngs directory for the chunker if the png_directory_key is not provided.
                if not os.path.exists("pngs"):
                    os.makedirs("pngs")

                png_directory = "pngs"
                self.chunker = Chunker(png_directory, id=unique_hash_id, chunk_size=chunk_size, subchunk_size=subchunk_size)
        except (PreexistingChunkerError, NonEmptyChunkingDirectoryError) as e:
            if(type(e) == PreexistingChunkerError):
                self.log(f"Chunker file with ID '{unique_hash_id}' shares a directory with the current chunker, this means that there may previous chunking in '{png_directory}' that has not completed. Please delete the chunker file and clear the directory before continuing.", log_queue)
            elif(type(e) == NonEmptyChunkingDirectoryError):
                self.log(f"Directory '{png_directory}' is not empty, please clear the directory before continuing.", log_queue)
            termination_event.set()
            return

        # If the save state file exists, then load the save state from the file.
        starting_index = 0
        manager = multiprocessing.Manager()
        data_list = manager.list()

        # Find the total number of rows in the target file.
        self.total_rows = 0
        with open(target_filename, "r") as file:
            reader = csv.reader(file)
            self.total_rows = sum(1 for row in reader) - 1

        if(os.path.isfile(self.save_state_filename)):
            self.log("Loading saved state...", log_queue=log_queue)
            data_list.extend(self.retrieveSaveState())
            starting_index = len(data_list)

            if (self.chunker.total_count != len(data_list)):
                if (self.chunker.total_count > len(data_list)):
                    self.chunker.unchunk(self.chunker.total_count - len(data_list))
                elif (self.chunker.total_count < len(data_list)):
                    print(self.chunker.total_count, "<", len(data_list))
                    raise ValueError("The chunker total count is less than the length of the data list.")
                self.chunker.save()

        if(starting_index != 0):
            self.log("Loaded saved state. Resuming from row " + str(starting_index+1) + "...", log_queue=log_queue)

        # Collect the data from the target file.

        collection_process = multiprocessing.Process(target=self.collectDataFromTargetList, args=(target_filename, starting_index, termination_event, data_list, log_queue), name="Collection Process")
        collection_process.start()


        # Wait for the collection process to finish.
        collection_process.join()

        collection_process_exitcode = collection_process.exitcode

        if(collection_process_exitcode != 0):
            self.log(f"Collection process has failed with exit code {collection_process_exitcode}", log_queue=log_queue)
            termination_event.set()

        if(self.chunker is not None):
            if(termination_event is not None and termination_event.is_set()):
                pass
            else:
                self.chunker.terminate()

        # Generate the manifest file.
        if(termination_event is None or not termination_event.is_set()):

            self.log("Collection process has finished.", log_queue=log_queue)

            self.log("Generating manifest file...", log_queue=log_queue)

            self.generateManifest(manifest_filename, data_list)

            self.log("Manifest file has been generated.", log_queue=log_queue)
        else:
            self.log("The process has been terminated early.", log_queue=log_queue)

        # Delete the save state file.
        if(os.path.isfile(self.save_state_filename) and not termination_event.is_set()):
            os.remove(self.save_state_filename)

        super().__init__(manifest_filename, uniform_data, uniform_metadata, progress_callback)

    def retrieveSaveState(self):
        """
        Retrieves the save state of the dataset.

        Returns
        -------
        data_list : list
            The list of data objects to retrieve the save state of.
        """

        # Load the data list from the save state file using pickle.
        with open(self.save_state_filename, "rb") as file:
            data_list = pickle.load(file)

        return data_list

    def periodicSaving(self, timeout = 10.0, termination_event = None, result_list = None):
        """
        Periodically saves the save state of the dataset.

        Parameters
        ----------
        timeout : float
            The timeout in seconds between each save.
        termination_event : multiprocessing.Event
            The event which signals the termination of the collection process.
        result_list : multiprocessing.Manager.ListProxy
            The list of data objects to save the save state of.
        """

        # TODO: Verify that this won't break if the save time is larger than the timeout for larger files (is this even possible?)

        if(termination_event is not None and result_list is not None):
            while (not termination_event.is_set()):
                time.sleep(timeout)
                self.saveSaveState(list(result_list))

    def saveSaveState(self, data_list: List[Data]):
        """
        Saves the save state of the dataset.

        Parameters
        ----------
            data_list : list
                The list of data objects to save the save state of.
        """

        data_list = list(data_list)

        # Save the data list to the save state file using pickle.
        with open(self.save_state_filename, "wb") as file:
            pickle.dump(data_list, file)

    def collectDataFromTargetList(self, target_filename, starting_index = 0, termination_event = None, result_list = None, log_queue = None):
        """
        Collects the data from the target list CSV file into a list of data objects.

        Parameters
        ----------
            target_filename : str
                The target filename of the CSV file containing the target list, consisting of at least RA, DEC, and TARGET ID as columns.
            starting_index : int, optional
                The starting index for loading the data objects. By default, it is 0.
            termination_event : multiprocessing.Event, optional
                A multiprocessing.Event object which can be used to terminate the process early. By default, it is None.
            result_list : multiprocessing.managers.ListProxy, optional
                A multiprocessing.managers.ListProxy object which will be used to store the data objects. By default, it is None.
            log_queue : multiprocessing.Queue, optional
                A multiprocessing.Queue object which will be used to log messages. By default, it is None.
        """

        if (result_list is None):
            result_list = []

        data_manager = multiprocessing.Manager()
        query_queue = data_manager.Queue(maxsize=self.max_query_queue_size)

        # Start a process which will send query requests to the database.

        query_process = multiprocessing.Process(target=self.requestQueries, args=(target_filename, starting_index, self.query_batch_number, query_queue, termination_event, log_queue), name="Query Process")
        query_process.start()

        # Start a process which will generate the data objects from the rows.
        data_process = multiprocessing.Process(target=self.generateDataList, args=(query_queue, termination_event, result_list, log_queue), name="Data Process")
        data_process.start()

        # Wait for the data process to finish.
        data_process.join()

        # Wait for the query process to finish.
        query_process.join()

        return list(result_list)

    def requestQuery(self, row):
        """
        Requests a query from the database.

        Parameters
        ----------
            row : dict
                The row dictionary of the CSV file to request the query for.

        Returns
        -------
        (row, query) : tuple
            The tuple containing the row dictionary and the query requested from the database.
        """

        raise NotImplementedError("This method must be implemented by the subclass for the specific dataset's needs.")

    def requestQueryBatch(self, rows, query_queue=None, log_queue=None):
        """
        Requests a query batch from the database.

        Parameters
        ----------
            rows : list of dict
                The list of rows of the CSV file to request the query for.
            query_queue : multiprocessing.Queue, optional
                The multiprocessing.Queue object to store the queries in.
            log_queue : multiprocessing.Queue, optional
                The multiprocessing.Queue object to log messages to.

        Returns
        -------
        queries : list
            The list of queries requested from the database.
        """

        queries = []

        def error_callback(e):
            self.log(f"{type(e)} in query thread: {e}", log_queue=log_queue)

        # Create a process pool to generate the queries
        pool = multiprocessing.Pool()

        # Create a list of processes to generate the queries
        processes = [pool.apply_async(self.requestQuery, args=(row,), error_callback=error_callback) for row in rows]

        # Close the process pool
        pool.close()

        # Wait for the processes to finish
        pool.join()

        # Get the queries from the processes
        result_tuples = [p.get() for p in processes]

        for result_tuple in result_tuples:
            if (query_queue is not None):
                query_queue.put(result_tuple, block=True, timeout=None)
            queries.append(result_tuple[1])

        return queries

    def requestQueries(self, target_filename, starting_index, batch_number=1, query_queue=None, termination_event=None, log_queue=None):
        """
        Requests all the queries in batches from the database.

        Parameters
        ----------
            target_filename : str
                The target filename of the CSV file containing the target list, consisting of at least RA, DEC, and TARGET ID as columns.
            starting_index : int
                The starting index for loading the data objects.
            batch_number : int
                The batch number to request the queries in increments of.
            query_queue : multiprocessing.Queue
                The multiprocessing.Queue object to store the queries in.
            termination_event : multiprocessing.Event, optional
                A multiprocessing.Event object which can be used to terminate the process early. By default, it is None.
            log_queue : multiprocessing.Queue, optional
                A multiprocessing.Queue object which will be used to log messages. By default, it is None.
        """

        max_index = None
        with open(target_filename, "r") as file:
            reader = csv.DictReader(file)

            max_index = sum(1 for row in reader) - starting_index

        row_batch = []
        with open(target_filename, "r") as file:
            reader = csv.DictReader(file)

            # Skip the first starting_index rows.
            for i in range(starting_index):
                next(reader)
                # Iterate through the rows of the CSV file.

            # Iterate through the rows of the CSV file and request the queries to fill the queue.
            for index, row in enumerate(reader):
                row_batch.append(row)
                if(termination_event is not None and termination_event.is_set()):
                    self.log("Terminating query requests...", log_queue)
                    break

                if ((index + 1) % batch_number == 0 or index == max_index - 1):
                    self.requestQueryBatch(rows=row_batch, query_queue=query_queue, log_queue=log_queue)
                    self.log(f"Received queries for rows {(index + starting_index) - len(row_batch) + 2} to {(index + starting_index) + 1}...", log_queue)
                    row_batch = []

        if(termination_event is not None and not termination_event.is_set()):
            self.log("Finished requesting queries.", log_queue)

    def generateDataList(self, query_queue, termination_event=None, result_list=None, log_queue=None):
        """
        Generates the data objects from the query queue.
        Parameters
        ----------
        query_queue : multiprocessing.Queue
            The multiprocessing.Queue object to retrieve the queries from.
        termination_event : multiprocessing.Event
            A multiprocessing.Event object which can be used to terminate the process early.
        result_list : multiprocessing.managers.ListProxy
            A multiprocessing.managers.ListProxy object which will be used to store the data objects.
        log_queue : multiprocessing.Queue
            A multiprocessing.Queue object which will be used to log the progress of the data generation process.

        Returns
        -------
        result_list : list
            The list of data objects generated from the query queue.
        """

        # Waiting for the query queue to have at least one query in it.
        while(query_queue.empty()):
            pass

        # Initially save the save state of the dataset.
        self.saveSaveState(list(result_list))

        # Create a process which will save the save state of the dataset every 10 seconds.
        saving_termination_event = multiprocessing.Event()
        save_timeout = 10
        save_state_process = multiprocessing.Process(target=self.periodicSaving, args=(save_timeout, saving_termination_event, result_list), name="Periodic Saving")
        save_state_process.start()

        # Generate the data objects from the query queue and store them in the result list.
        self.completed = False

        def data_function(row, query, log_queue):
            result = self.generateData(row, query=query, log_queue=log_queue)
            if (self.chunker is not None):
                self.chunker.chunk(1)
            return result

        while(not self.completed):
            row, query = query_queue.get(block=True)

            # Applying multiprocessing to the generateData function is not currently possible with the current logging scheme.
            try:
                result_list.append(data_function(row, query, log_queue))
            except Exception as e:
                self.log(f"{type(e)} in generating data: {e}", log_queue)
                termination_event.set()


            if(len(result_list) == self.total_rows):
                self.completed = True

            if(len(result_list) != 0):
                self.log(f"Row {len(result_list)} out of {self.total_rows} has been downloaded.", log_queue)
                self.log(f"Generate Manifest:{len(result_list)}/{self.total_rows}", log_queue, level=logging.DEBUG)

            if (termination_event is not None and termination_event.is_set()):
                self.completed = True
                saving_termination_event.set()
                self.saveSaveState(list(result_list))
                while (not query_queue.empty()):
                    query_queue.get()
                break

        if (termination_event is not None and not termination_event.is_set()):
            self.log("Finished downloading all rows.", log_queue)

        if(not saving_termination_event.is_set()):
            saving_termination_event.set()

        save_state_process.join()

        return list(result_list)

    def generateData(self, row, query=None, log_queue=None):
        """
        Generates the data object using the row of the CSV file and its corresponding query.

        Parameters
        ----------
            row : dict
                The row of the CSV file to generate the data object from.
            query : object, optional
                The query-like object used to get the data from the database associated with the row. By default, it is None.
            log_queue : multiprocessing.Queue, optional
                A multiprocessing.Queue object which will be used to log messages. By default, it is None.

        Returns
        -------
        data : Data object, or tuple (flag, Data)
            The data object generated from the row of the CSV file or a tuple containing a flag and the data object.
            Currently, the only supported flag is None to indicate that the data object is incomplete.
        """

        raise NotImplementedError("This method must be implemented by the subclass for the specific dataset's needs.")

    def log(self, message, log_queue, include_timestamps=False, level=logging.INFO):
        """
        Formats and adds the message to the log queue.

        Parameters
        ----------
            message : str
                The message to log to the console.
            log_queue : multiprocessing.Queue
                The multiprocessing.Queue object to store the log messages in.
            include_timestamps : bool, optional
                Whether to include timestamps in the log messages. By default, it is False.
            level : int, optional
                The level of the log message. By default, it is logging.INFO.
        """

        if(log_queue is not None and isinstance(log_queue, type(multiprocessing.Queue()))):
            logger = logging.getLogger()
            logger.handlers = []
            logger.setLevel(level=level)

            handler = QueueHandler(log_queue)
            logger.addHandler(handler)

            level_functions = {
                logging.DEBUG: logger.debug,
                logging.INFO: logger.info,
                logging.WARNING: logger.warning,
                logging.ERROR: logger.error,
                logging.CRITICAL: logger.critical,
                logging.FATAL: logger.fatal
            }

            level_names = {
                logging.DEBUG: "DEBUG",
                logging.INFO: "INFO",
                logging.WARNING: "WARNING",
                logging.ERROR: "ERROR",
                logging.CRITICAL: "CRITICAL",
                logging.FATAL: "FATAL"
            }

            if (include_timestamps):
                message = str(level_names[logger.level]) + " " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " " + message
            else:
                message = str(level_names[logger.level]) + " " + message

            level_functions[logger.level](message)

            logger.removeHandler(handler)
        else:
            print(message)

    @staticmethod
    def generateKeyVariations(key):
        """
        Generates the variations of the key which are permitted to be used.

        Parameters
        ----------
            key : str
                The key to generate the variations of.

        Returns
        -------
        variations : list
            The list of possible variations of the key.
        """
        key = key.strip()

        # If the first character is the privatization symbol, then we can remove it.

        if(len(key) > 1 and key[0] == Data.privatization_symbol):
            key = key[1:]

        variations = []

        space_delimiters = [" ", "_", "-", "."]

        # If the key has spaces in it, then it is likely a multi-word key, so we can split it into its words and capitalize each word.
        if(any(delimiter in key for delimiter in space_delimiters)):
            titled_key = key.title()
            variations.append(titled_key)

            normalized_variations = []
            for delimiter in space_delimiters:
                if(delimiter in key):
                    normalized_variations.append(titled_key.replace(delimiter, " "))

            for variation in normalized_variations:
                variations.append(variation)
                variations.append(variation.replace(" ", "_"))
                variations.append(variation.replace(" ", "-"))
                variations.append(variation.replace(" ", "."))
                variations.append(variation.replace(" ", ""))

            # For each variation, we can also add the key in all lowercase.
            lowercase_variations = [variation.lower() for variation in variations]
            variations.extend(lowercase_variations)

            # We can also add the key in all uppercase.
            uppercase_variations = [variation.upper() for variation in variations]
            variations.extend(uppercase_variations)

            # Add the variations where one word is capitalized and the rest are lowercase.
            new_variations = []
            for variation in variations:
                space_delimiter = None
                uniform_variation = None
                if("_" in variation):
                    uniform_variation = variation.replace("_", " ")
                    space_delimiter = "_"
                elif("-" in variation):
                    uniform_variation = variation.replace("-", " ")
                    space_delimiter = "-"
                elif("." in variation):
                    uniform_variation = variation.replace(".", " ")
                    space_delimiter = "."
                elif(" " in variation):
                    uniform_variation = variation
                    space_delimiter = " "

                if(space_delimiter is not None):
                    words = uniform_variation.split(" ")
                    for index, word in enumerate(words):
                        for j in range(2):
                            modified_words = words.copy()
                            if(j == 0):
                                for i, word in enumerate(modified_words):
                                    if(i == index):
                                        modified_words[index] = modified_words[index].upper()
                                    else:
                                        modified_words[index] = modified_words[index].lower()
                            elif(j == 1):
                                for i, word in enumerate(modified_words):
                                    if(i == index):
                                        modified_words[index] = modified_words[index].capitalize()
                                    else:
                                        modified_words[index] = modified_words[index].lower()
                            new_variations.append(" ".join(modified_words).replace(" ", space_delimiter))
            variations.extend(new_variations)
        else:
            variations.append(key.lower())

            variations.append(key.upper())

            variations.append(key.capitalize())

        # For each variation, we can also add the privatization symbol to the beginning of the key.
        new_variations = []
        for variation in variations:
            new_variations.append(f"{Data.privatization_symbol}{variation}")

        variations.extend(new_variations)

        # Convert the variations to a dictionary for easy lookup.
        variations = {variation: variation for variation in variations}

        return variations

    @staticmethod
    def verifyKey(key, template_key):
        """
        Verifies whether the key is allowed to be used.

        Parameters
        ----------
            key : str
                The key to verify.
            template_key : str
                The template key to use to verify the key by generating the variations of the template key.

        Returns
        -------
        is_allowed : bool
            Whether the key is allowed to be used.
        """

        allowed_variations_dictionary = AstronomyDataset.generateKeyVariations(template_key)

        return key in allowed_variations_dictionary

    def retrieveValue(self, column_name, row):
        """
        Retrieves the value of the key from the row.

        Parameters
        ----------
            column_name : str
                The column_name to retrieve the value of.
            row : dict
                The row to retrieve the value from.

        Returns
        -------
        value : object
            The formatted value of the key from the row.
        """

        if(column_name is None):
            return None

        if(not isinstance(column_name, str)):
            raise TypeError("The column_name must be a string.")

        if(column_name not in self.column_names):
            raise KeyError(f"The column_name '{column_name}' is not a valid column name.")

        key = self.column_dictionary[column_name]

        value = None

        if(AstronomyDataset.verifyKey(key, key) and key in row):
            value = row[key]
        else:
            raise KeyError(f"The key '{key}' could not be found in the row or is not allowed to be used.")

        if(value is None):
            return None

        if(isinstance(value, str)):
            value = value.strip()

            if(value == ""):
                return value

            try:
                value = float(value)

                if(value.is_integer()):
                    value = int(value)

                return value
            except ValueError:
                pass
        elif(isinstance(value, int) or isinstance(value, float)):
            return value

        return value

    def setValue(self, value, column_name, row):
        """
        Sets the value of the key from the row.

        Parameters
        ----------
            column_name : str
                The key to retrieve the value of.
            row : dict
                The row to retrieve the value from.

        Returns
        -------
        None
        """

        if(column_name is None):
            return None

        if(not isinstance(column_name, str)):
            raise TypeError("The column_name must be a string.")

        if(column_name not in self.column_names):
            raise KeyError(f"The column_name '{column_name}' is not a valid column name.")

        key = self.column_dictionary[column_name]

        if(AstronomyDataset.verifyKey(key, key) and key in row):
            row[key] = value
        else:
            raise KeyError(f"The key '{key}' could not be found in the row or is not allowed to be used.")

    def setColumnKeys(self, target_filename):
        """
        Sets the column keys from the target file.

        Parameters
        ----------
            target_filename : str
                The target filename of the CSV file containing the target list, usually consisting of at least RA, DEC, and TARGET ID as columns.
        """

        keys = []
        if(target_filename is not None):
            with open(target_filename, "r") as target_file:
                reader = csv.DictReader(target_file)
                keys = reader.fieldnames

        for key in keys:
            attribute_name = None

            key_variations = AstronomyDataset.generateKeyVariations(key)

            # Find the key variation that is all lowercase, no privatization symbol, and underscores instead of spaces.
            has_spaces = False
            for key_variation in key_variations:
                if (" " in key_variation):
                    has_spaces = True
                    break

            for key_variation in key_variations:
                if(has_spaces):
                    if(key_variation == key_variation.lower() and Data.privatization_symbol not in key_variation and "_" in key_variation):
                        attribute_name = key_variation
                else:
                    if(key_variation == key_variation.lower() and Data.privatization_symbol not in key_variation):
                        attribute_name = key_variation

                if(attribute_name is not None):
                    break

            if(not AstronomyDataset.verifyKey(key.lower(), key)):
                raise KeyError(f"The key '{key}' is not allowed to be used.")

            self.column_names.append(attribute_name)
            self.column_keys.append(attribute_name)
            self.column_dictionary[attribute_name] = key

    def getColumnKey(self, column_name):
        """
        Retrieves the column key from the column name.

        Parameters
        ----------
            column_name : str
                The column name to retrieve the column key of.

        Returns
        -------
        column_key : str
            The column key of the column name.
        """

        if(column_name is None):
            return None

        if(not isinstance(column_name, str)):
            raise TypeError("The column_name must be a string.")

        if(column_name in self.column_names):
            return self.column_dictionary[column_name]
        else:
            raise KeyError(f"The column name '{column_name}' is not a valid column name.")


class CoolNeighborsDataset(AstronomyDataset):
    dataset_name = "Cool Neighbors"
    required_target_columns = ["ra", "dec", "target_id", "bitmask", "addgrid", "scale", "fov", "png_directory", "minbright", "maxbright", "gridcount", "gridtype", "gridcolor", "ignore_partial_cutouts"]
    required_private_columns = ["bitmask", "addgrid", "scale", "png_directory", "minbright", "maxbright", "gridcount", "gridtype", "gridcolor", "ignore_partial_cutouts"]
    mutable_columns_dict = {"scale": InputField.Entry("Scale Factor", float),
                            "fov": InputField.Entry("FOV (arcseconds)", float),
                            "minbright": InputField.Entry("Minbright (Vega nmags)", float),
                            "maxbright": InputField.Entry("Maxbright (Vega nmags)", float),
                            "addgrid": InputField.Checkbutton("Add grid"),
                            "gridcount": InputField.Entry("Grid count", int),
                            "gridtype": InputField.OptionMenu("Grid type", str, ["Solid", "Intersection", "Dashed"]),
                            "gridcolor": InputField.ColorSelector("Grid color", "Select a grid color"),
                            "ignore_partial_cutouts": InputField.Checkbutton("Ignore partial cutouts")}
    mutable_columns_keys_dict = {"scale": "SCALE", "fov": "FOV", "minbright": "MINBRIGHT", "maxbright": "MAXBRIGHT", "addgrid": "ADDGRID", "gridcount": "GRIDCOUNT", "gridtype": "GRIDTYPE", "gridcolor": "GRIDCOLOR", "ignore_partial_cutouts": "IGNORE_PARTIAL_CUTOUTS"}
    def __init__(self, target_filename, manifest_filename, ignore_incomplete_data=False, termination_event=None, log_queue=None):
        """
        Initializes a CoolNeighborsDataset object, an object which stores a list of data objects meant to be used for the Cool Neighbors Zooniverse project.

        Parameters
        ----------
            target_filename : str
                The target filename of the CSV file containing the target list, consisting of at least RA, DEC, and TARGET ID as columns.
            manifest_filename : str
                The manifest filename of the generated CSV file containing the Zooniverse subject data and metadata.
            ignore_incomplete_data : bool, optional
                Whether to ignore partial cutouts. By default, it is False.
            termination_event : multiprocessing.Event, optional
                A multiprocessing.Event object which can be used to terminate the process early. By default, it is None.
            log_queue : multiprocessing.Queue, optional
                A multiprocessing.Queue object which will be used to log the progress of the data generation process. By default, it is None.

        Notes
        -----
            A partial cutout is a query which returns images which are not square.
        """

        uniform_data = True
        uniform_metadata = True

        # Adjustable parameters for the chunker.
        chunk_size = 1000
        subchunk_size = 100

        # Adjustable parameters for the query process.
        max_query_queue_size = 50 # Only increase this if the server/dataset you are querying can handle it.
        query_batch_number = 25 # Only increase this if the server/dataset you are querying can handle it.

        super().__init__(target_filename, manifest_filename, self.dataset_name, ignore_incomplete_data, uniform_data, uniform_metadata, termination_event, log_queue, chunk_size, subchunk_size, max_query_queue_size, query_batch_number)

    def generateData(self, row, query:WiseViewQuery = None, log_queue=None):
        """
        Generates the data object using the row of the CSV file and its corresponding query.

        Parameters
        ----------
            row : dict
                The row of the CSV file to generate the data object from.
            query : object, optional
                The query-like object used to get the data from the database associated with the row. By default, it is None.
            log_queue : multiprocessing.Queue, optional
                A multiprocessing.Queue object which will be used to log messages. By default, it is None.

        Returns
        -------
        data : Data object
            The data object generated from the row of the CSV file.
        """

        data = {}
        metadata = {}
        wise_view_query = query

        TARGET_ID = self.retrieveValue("target_id", row)
        RA = self.retrieveValue("ra", row)
        DEC = self.retrieveValue("dec", row)
        BITMASK = self.retrieveValue("bitmask", row)
        ADDGRID = self.retrieveValue("addgrid", row)
        SCALE = self.retrieveValue("scale", row)
        FOV = self.retrieveValue("fov", row)
        PNG_DIRECTORY = self.retrieveValue("png_directory", row)
        MINBRIGHT = self.retrieveValue("minbright", row)
        MAXBRIGHT = self.retrieveValue("maxbright", row)
        GRIDCOUNT = self.retrieveValue("gridcount", row)
        GRIDTYPE = self.retrieveValue("gridtype", row)
        RGB_list = []
        for s in self.retrieveValue("gridcolor", row)[1:][:-1].split(","):
            RGB_list.append(int(s))
        GRIDCOLOR = tuple(RGB_list)

        metadata[self.getColumnKey("target_id")] = TARGET_ID
        metadata[self.getColumnKey("ra")] = RA
        metadata[self.getColumnKey("dec")] = DEC
        metadata[self.getColumnKey("bitmask")] = BITMASK
        metadata[self.getColumnKey("addgrid")] = ADDGRID
        metadata[self.getColumnKey("scale")] = SCALE
        metadata[self.getColumnKey("fov")] = FOV
        metadata[self.getColumnKey("png_directory")] = PNG_DIRECTORY
        metadata[self.getColumnKey("minbright")] = MINBRIGHT
        metadata[self.getColumnKey("maxbright")] = MAXBRIGHT
        metadata[self.getColumnKey("gridcount")] = GRIDCOUNT
        metadata[self.getColumnKey("gridtype")] = GRIDTYPE
        metadata[self.getColumnKey("gridcolor")] = GRIDCOLOR

        # Add extra metadata not found directly from the CSV file.
        metadata['Data Source'] = "[unWISE](+tab+http://unwise.me/)"
        metadata['unWISE Pixel Scale'] = f"~{WiseViewQuery.unWISE_pixel_scale} arcseconds per pixel"

        def generateDecimalYearEpochs(wise_view_query):
            """
            Generates the decimal year epochs for the data object.

            Returns
            -------
            decimal_year_epochs_str : str
                The string containing the decimal year epochs for the data object.
            """

            modified_julian_date_pairs = wise_view_query.requestMetadata("mjds")

            date_str = ""
            for i in range(len(modified_julian_date_pairs)):
                for j in range(len(modified_julian_date_pairs[i])):
                    if (j == 0):
                        time_start = astropy_time.Time(modified_julian_date_pairs[i][j], format="mjd").to_value("decimalyear")
                    if (j == len(modified_julian_date_pairs[i]) - 1):
                        time_end = astropy_time.Time(modified_julian_date_pairs[i][j], format="mjd").to_value("decimalyear")
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

            return date_str

        metadata["Decimal Year Epochs"] = generateDecimalYearEpochs(wise_view_query)

        ICRS_coordinates = SkyCoord(ra=RA * u.degree, dec=DEC * u.degree, frame='icrs')

        galactic_coordinates = ICRS_coordinates.transform_to(frame="galactic")
        metadata['Galactic Coordinates'] = galactic_coordinates.to_string("decimal")

        ecliptic_coordinates = ICRS_coordinates.transform_to(frame=astropy.coordinates.GeocentricMeanEcliptic)
        metadata[f'{Data.privatization_symbol}Ecliptic Coordinates'] = ecliptic_coordinates.to_string("decimal")

        metadata['WISEVIEW'] = f"[WiseView](+tab+{wise_view_query.generateWiseViewURL()})"

        # Radius is the smallest circle radius which encloses the square image.
        # This is done to ensure the entire image frame is searched.
        radius = (math.sqrt(2) / 2) * FOV

        # Assign the associated SIMBAD, Legacy Surveys, VizieR, and IRSA urls to the row
        metadata['SIMBAD'] = f"[SIMBAD](+tab+{MetadataLinks.generate_SIMBAD_url(RA, DEC, radius)})"
        metadata['Legacy Surveys'] = f"[Legacy Surveys](+tab+{MetadataLinks.generate_legacy_survey_url(RA, DEC)})"
        VizieR_FOV = 15
        metadata['VizieR'] = f"[VizieR](+tab+{MetadataLinks.generate_VizieR_url(RA, DEC, VizieR_FOV)})"
        metadata['IRSA'] = f"[IRSA](+tab+{MetadataLinks.generate_IRSA_url(RA, DEC)})"

        # Save all images for parameter set, add grid if toggled for that image
        flist = []
        size_list = []
        if(self.chunker is None):
            flist, size_list = wise_view_query.downloadModifiedWiseViewData(PNG_DIRECTORY, scale_factor=SCALE, addGrid=ADDGRID, gridCount=GRIDCOUNT, gridType=GRIDTYPE, gridColor=GRIDCOLOR)
        else:
            chunk_directory = self.chunker.getChunkDirectory()
            flist, size_list = wise_view_query.downloadModifiedWiseViewData(chunk_directory, scale_factor=SCALE, addGrid=ADDGRID, gridCount=GRIDCOUNT, gridType=GRIDTYPE, gridColor=GRIDCOLOR)

        is_partial_cutout = False
        for size in size_list:
            width, height = size
            metadata["unWISE Pixel Width"] = int(width / SCALE)
            metadata["unWISE Pixel Height"] = int(height / SCALE)
            metadata['FOV'] = f"{round(wise_view_query.PixelSizeToFOV(int(width / SCALE)), 2)} x {round(wise_view_query.PixelSizeToFOV(int(height / SCALE)), 2)} arcseconds"
            if (width != height):
                is_partial_cutout = True
                break

        if(is_partial_cutout and self.ignore_incomplete_data):
            self.log(f"This is a partial cutout and is being ignored.", log_queue)

        data_field_names = []
        for i in range(len(flist)):
            data_field_names.append("f" + str(i + 1))

        data = {data_field_name : flist[i] for i, data_field_name in enumerate(data_field_names)}

        # Add unaccounted for metadata to the metadata dictionary.
        for key in row:
            if key not in metadata:
                metadata[key] = row[key]

        # If the image is a partial cutout, then return  (None, Data(data, metadata)).
        if(is_partial_cutout and self.ignore_incomplete_data):
            return (None, Data(data, metadata))

        return Data(data, metadata)

    def requestQuery(self, row):
        """
        Requests a query from the database.

        Parameters
        ----------
            row : dict
                The row of the CSV file to request the query for.

        Returns
        -------
        (row, query) : tuple
            The tuple containing the row and the query requested from the database.
        """

        RA = self.retrieveValue("ra", row)
        DEC = self.retrieveValue("dec", row)
        FOV = self.retrieveValue("fov", row)
        MINBRIGHT = self.retrieveValue("minbright", row)
        MAXBRIGHT = self.retrieveValue("maxbright", row)

        # Pixel side-length of the images
        SIZE = WiseViewQuery.WiseViewQuery.FOVToPixelSize(FOV)

        MINBRIGHT, MAXBRIGHT = calculate_min_and_max_brightness(MINBRIGHT, MAXBRIGHT, RA, DEC, SIZE)

        self.setValue(MINBRIGHT, "minbright", row)
        self.setValue(MAXBRIGHT, "maxbright", row)

        # Set WiseView parameters and return the query
        query = WiseViewQuery.WiseViewQuery(RA=RA, DEC=DEC, size=SIZE, minbright=MINBRIGHT, maxbright=MAXBRIGHT, window=1.5)
        return (row, query)


class ExoasteroidsDataset(AstronomyDataset):
    dataset_name = "Exoasteroids"
    required_target_columns = ["ra", "dec", "target_id", "bitmask", "addgrid", "scale", "fov", "png_directory", "minbright", "maxbright", "gridcount", "gridtype", "gridcolor", "ignore_partial_cutouts", "image_type"]
    required_private_columns = ["bitmask", "addgrid", "scale", "png_directory", "minbright", "maxbright", "gridcount", "gridtype", "gridcolor", "ignore_partial_cutouts", "image_type"]
    mutable_columns_dict = {"scale": InputField.Entry("Scale Factor", float),
                            "fov": InputField.Entry("FOV (arcseconds)", float),
                            "minbright": InputField.Entry("Minbright (Vega nmags)", float),
                            "maxbright": InputField.Entry("Maxbright (Vega nmags)", float),
                            "addgrid": InputField.Checkbutton("Add grid"),
                            "gridcount": InputField.Entry("Grid count", int),
                            "gridtype": InputField.OptionMenu("Grid type", str, ["Solid", "Intersection", "Dashed"]),
                            "gridcolor": InputField.ColorSelector("Grid color", "Select a grid color"),
                            "ignore_partial_cutouts": InputField.Checkbutton("Ignore partial cutouts"),
                            "image_type": InputField.OptionMenu("Select image type", str, ["Regular Image", "Difference Image", "Both"])}
    mutable_columns_keys_dict = {"scale": "SCALE", "fov": "FOV", "minbright": "MINBRIGHT", "maxbright": "MAXBRIGHT", "addgrid": "ADDGRID", "gridcount": "GRIDCOUNT", "gridtype": "GRIDTYPE", "gridcolor": "GRIDCOLOR", "ignore_partial_cutouts": "IGNORE_PARTIAL_CUTOUTS", "image_type": "IMAGE_TYPE"}

    def __init__(self, target_filename, manifest_filename, ignore_incomplete_data=False, termination_event=None, log_queue=None):
        """
        Initializes an ExoasteroidsDataset object, an object which stores a list of data objects meant to be used for the Exoasteroids Zooniverse project.

        Parameters
        ----------
            target_filename : str
                The target filename of the CSV file containing the target list, consisting of at least RA, DEC, and TARGET ID as columns.
            manifest_filename : str
                The manifest filename of the generated CSV file containing the Zooniverse subject data and metadata.
            ignore_incomplete_data : bool, optional
                Whether to ignore partial cutouts. By default, it is False.
            termination_event : multiprocessing.Event, optional
                A multiprocessing.Event object which can be used to terminate the process early. By default, it is None.
            log_queue : multiprocessing.Queue, optional
                A multiprocessing.Queue object which will be used to log the progress of the data generation process. By default, it is None.

        Notes
        -----

        """

        uniform_data = True
        uniform_metadata = True

        # Adjustable parameters for the chunker.
        chunk_size = 1000
        subchunk_size = 100

        # Adjustable parameters for the query process.
        max_query_queue_size = 50 # Only increase this if the server/dataset you are querying can handle it.
        query_batch_number = 25 # Only increase this if the server/dataset you are querying can handle it.

        super().__init__(target_filename, manifest_filename, self.dataset_name, ignore_incomplete_data, uniform_data, uniform_metadata, termination_event, log_queue, chunk_size, subchunk_size, max_query_queue_size, query_batch_number)

    def generateData(self, row, query=None, log_queue=None):
        """
        Generates the data object using the row of the CSV file and its corresponding query.

        Parameters
        ----------
            row : dict
                The row of the CSV file to generate the data object from.
            query : object, optional
                The query-like object used to get the data from the database associated with the row. By default, it is None.
            log_queue : multiprocessing.Queue, optional
                A multiprocessing.Queue object which will be used to log messages. By default, it is None.

        Returns
        -------

        data : Data object
            The data object generated from the row of the CSV file.
        """

        data = {}
        metadata = {}

        IMAGE_TYPE = self.retrieveValue("image_type", row)
        wise_view_query = None
        diff_wise_view_query = None
        query_tuple = None

        if(IMAGE_TYPE == "Regular Image"):
            wise_view_query = query
        elif(IMAGE_TYPE == "Difference Image"):
            wise_view_query = query
        elif(IMAGE_TYPE == "Both"):
            query_tuple = query
            wise_view_query = query_tuple[0]
            diff_wise_view_query = query_tuple[1]


        TARGET_ID = self.retrieveValue("target_id", row)
        RA = self.retrieveValue("ra", row)
        DEC = self.retrieveValue("dec", row)
        ADDGRID = self.retrieveValue("addgrid", row)
        SCALE = self.retrieveValue("scale", row)
        FOV = self.retrieveValue("fov", row)
        PNG_DIRECTORY = self.retrieveValue("png_directory", row)
        MINBRIGHT = self.retrieveValue("minbright", row)
        MAXBRIGHT = self.retrieveValue("maxbright", row)
        GRIDCOUNT = self.retrieveValue("gridcount", row)
        GRIDTYPE = self.retrieveValue("gridtype", row)
        RGB_list = []
        for s in self.retrieveValue("gridcolor", row)[1:][:-1].split(","):
            RGB_list.append(int(s))
        GRIDCOLOR = tuple(RGB_list)

        metadata[self.getColumnKey("target_id")] = TARGET_ID
        metadata[self.getColumnKey("ra")] = RA
        metadata[self.getColumnKey("dec")] = DEC
        metadata[self.getColumnKey("addgrid")] = ADDGRID
        metadata[self.getColumnKey("scale")] = SCALE
        metadata[self.getColumnKey("fov")] = FOV
        metadata[self.getColumnKey("png_directory")] = PNG_DIRECTORY
        metadata[self.getColumnKey("minbright")] = MINBRIGHT
        metadata[self.getColumnKey("maxbright")] = MAXBRIGHT
        metadata[self.getColumnKey("gridcount")] = GRIDCOUNT
        metadata[self.getColumnKey("gridtype")] = GRIDTYPE
        metadata[self.getColumnKey("gridcolor")] = GRIDCOLOR

        # Add extra metadata not found directly from the CSV file.
        metadata['Data Source'] = "[unWISE](+tab+http://unwise.me/)"
        metadata['unWISE Pixel Scale'] = f"~{WiseViewQuery.unWISE_pixel_scale} arcseconds per pixel"

        def generateDecimalYearEpochs(wise_view_query):
            """
            Generates the decimal year epochs for the data object.

            Returns
            -------
            decimal_year_epochs_str : str
                The string containing the decimal year epochs for the data object.
            """

            modified_julian_date_pairs = wise_view_query.requestMetadata("mjds")

            date_str = ""
            for i in range(len(modified_julian_date_pairs)):
                for j in range(len(modified_julian_date_pairs[i])):
                    if (j == 0):
                        time_start = astropy_time.Time(modified_julian_date_pairs[i][j], format="mjd").to_value("decimalyear")
                    if (j == len(modified_julian_date_pairs[i]) - 1):
                        time_end = astropy_time.Time(modified_julian_date_pairs[i][j], format="mjd").to_value("decimalyear")
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

            return date_str

        metadata["Decimal Year Epochs"] = generateDecimalYearEpochs(wise_view_query)

        ICRS_coordinates = SkyCoord(ra=RA * u.degree, dec=DEC * u.degree, frame='icrs')

        galactic_coordinates = ICRS_coordinates.transform_to(frame="galactic")
        metadata['Galactic Coordinates'] = galactic_coordinates.to_string("decimal")

        ecliptic_coordinates = ICRS_coordinates.transform_to(frame=astropy.coordinates.GeocentricMeanEcliptic)
        metadata[f'{Data.privatization_symbol}Ecliptic Coordinates'] = ecliptic_coordinates.to_string("decimal")

        metadata['WISEVIEW'] = f"[WiseView](+tab+{wise_view_query.generateWiseViewURL()})"

        # Radius is the smallest circle radius which encloses the square image.
        # This is done to ensure the entire image frame is searched.
        radius = (math.sqrt(2) / 2) * FOV

        # Assign the associated SIMBAD, Legacy Surveys, VizieR, and IRSA urls to the row
        metadata['SIMBAD'] = f"[SIMBAD](+tab+{MetadataLinks.generate_SIMBAD_url(RA, DEC, radius)})"
        metadata['Legacy Surveys'] = f"[Legacy Surveys](+tab+{MetadataLinks.generate_legacy_survey_url(RA, DEC)})"
        VizieR_FOV = 15
        metadata['VizieR'] = f"[VizieR](+tab+{MetadataLinks.generate_VizieR_url(RA, DEC, VizieR_FOV)})"
        metadata['IRSA'] = f"[IRSA](+tab+{MetadataLinks.generate_IRSA_url(RA, DEC)})"

        # Save all images for parameter set, add grid if toggled for that image
        flist = []
        size_list = []

        def getImageInformation(directory):
            flist = []
            size_list = []
            if(query_tuple is not None):

                reg_flist, reg_size_list = wise_view_query.downloadModifiedWiseViewData(directory, scale_factor=SCALE, addGrid=ADDGRID, gridCount=GRIDCOUNT, gridType=GRIDTYPE, gridColor=GRIDCOLOR)
                diff_flist, diff_size_list = diff_wise_view_query.downloadModifiedWiseViewData(directory, scale_factor=SCALE, addGrid=ADDGRID, gridCount=GRIDCOUNT, gridType=GRIDTYPE, gridColor=GRIDCOLOR)

                size_list = reg_size_list

                image_crafter = ImageCrafter.ImageCrafter()
                for reg_f, diff_f in zip(reg_flist, diff_flist):
                    combined_filename = str(os.path.basename(reg_f).replace("DIFF_0", "COMBINED_1"))
                    destination_filepath = str(os.path.join(directory, combined_filename))
                    flist.append(image_crafter.splice(reg_f, diff_f, destination_filepath, orientation="horizontal"))

                    # Delete the regular and difference images
                    os.remove(reg_f)
                    os.remove(diff_f)
            else:
                flist, size_list = wise_view_query.downloadModifiedWiseViewData(directory, scale_factor=SCALE, addGrid=ADDGRID, gridCount=GRIDCOUNT, gridType=GRIDTYPE, gridColor=GRIDCOLOR)

            return flist, size_list

        if(self.chunker is None):
            flist, size_list = getImageInformation(PNG_DIRECTORY)
        else:
            chunk_directory = self.chunker.getChunkDirectory()
            flist, size_list = getImageInformation(chunk_directory)

        is_partial_cutout = False
        for size in size_list:
            width, height = size
            metadata["unWISE Pixel Width"] = int(width / SCALE)
            metadata["unWISE Pixel Height"] = int(height / SCALE)
            metadata['FOV'] = f"{round(wise_view_query.PixelSizeToFOV(int(width / SCALE)), 2)} x {round(wise_view_query.PixelSizeToFOV(int(height / SCALE)), 2)} arcseconds"
            if (width != height):
                is_partial_cutout = True
                break

        if(is_partial_cutout and self.ignore_incomplete_data):
            self.log(f"This is a partial cutout and is being ignored.", log_queue)

        data_field_names = []
        for i in range(len(flist)):
            data_field_names.append("f" + str(i + 1))

        data = {data_field_name : flist[i] for i, data_field_name in enumerate(data_field_names)}

        # Add unaccounted for metadata to the metadata dictionary.
        for key in row:
            if key not in metadata:
                metadata[key] = row[key]

        # If the image is a partial cutout, then return  (None, Data(data, metadata)).
        if(is_partial_cutout and self.ignore_incomplete_data):
            return (None, Data(data, metadata))

        return Data(data, metadata)

    def requestQuery(self, row):
        """
        Requests a query from the database.

        Parameters
        ----------
            row : dict
                The row of the CSV file to request the query for.

        Returns
        -------
        (row, query) : tuple
            The tuple containing the row and the query requested from the database.
        """


        RA = self.retrieveValue("ra", row)
        DEC = self.retrieveValue("dec", row)
        FOV = self.retrieveValue("fov", row)
        MINBRIGHT = self.retrieveValue("minbright", row)
        MAXBRIGHT = self.retrieveValue("maxbright", row)

        # Pixel side-length of the images
        SIZE = WiseViewQuery.WiseViewQuery.FOVToPixelSize(FOV)

        MINBRIGHT, MAXBRIGHT = calculate_min_and_max_brightness(MINBRIGHT, MAXBRIGHT, RA, DEC, SIZE)

        self.setValue(MINBRIGHT, "minbright", row)
        self.setValue(MAXBRIGHT, "maxbright", row)

        IMAGE_TYPE = self.retrieveValue("image_type", row)

        if(IMAGE_TYPE == "Regular Image"):
            query = WiseViewQuery.WiseViewQuery(RA=RA, DEC=DEC, size=SIZE, minbright=MINBRIGHT, maxbright=MAXBRIGHT, window=1.5, diff=0)
            return (row, query)
        elif(IMAGE_TYPE == "Difference Image"):
            query = WiseViewQuery.WiseViewQuery(RA=RA, DEC=DEC, size=SIZE, minbright=MINBRIGHT, maxbright=MAXBRIGHT, window=1.5, diff=1)
            return (row, query)
        elif(IMAGE_TYPE == "Both"):
            regular_image_query = WiseViewQuery.WiseViewQuery(RA=RA, DEC=DEC, size=SIZE, minbright=MINBRIGHT, maxbright=MAXBRIGHT, window=1.5, diff=0)

            DIFF_MINBRIGHT, DIFF_MAXBRIGHT = calculate_diff_min_and_max_brightness(RA, DEC, SIZE)

            diff_image_query = WiseViewQuery.WiseViewQuery(RA=RA, DEC=DEC, size=SIZE, minbright=DIFF_MINBRIGHT, maxbright=DIFF_MAXBRIGHT, window=1.5, diff=1)
            return (row, [regular_image_query, diff_image_query])
        else:
            raise ValueError(f"Invalid image type '{IMAGE_TYPE}'.")


class LegacySurveyDataset(AstronomyDataset):
    dataset_name = "Legacy Survey"
    required_target_columns = ["ra", "dec", "target_id", "zoom", "fov", "png_directory", "layer", "blink", "ignore_partial_cutouts"]
    required_private_columns = ["zoom", "fov", "png_directory", "layer", "blink", "ignore_partial_cutouts"]
    mutable_columns_dict = {"zoom": InputField.Entry("Zoom", int),
                            "fov": InputField.Entry("FOV (arcseconds)", float),
                            "layer": InputField.Entry("Layer", str),
                            "blink": InputField.Entry("Blink", str),
                            "ignore_partial_cutouts": InputField.Checkbutton("Ignore partial cutouts")}
    mutable_columns_keys_dict = {"zoom": "ZOOM", "fov": "FOV", "layer": "LAYER", "blink": "BLINK", "ignore_partial_cutouts": "IGNORE_PARTIAL_CUTOUTS"}
    def __init__(self, target_filename, manifest_filename, ignore_incomplete_data=False, termination_event=None, log_queue=None):
        """
        Initializes a LegacySurveyDataset object, an object which stores a list of data objects meant to be used for the Legacy Surveys Zooniverse project.

        Parameters
        ----------
            target_filename : str
                The target filename of the CSV file containing the target list, consisting of at least RA, DEC, and TARGET ID as columns.
            manifest_filename : str
                The manifest filename of the generated CSV file containing the Zooniverse subject data and metadata.
            ignore_incomplete_data : bool, optional
                Whether to ignore partial cutouts. By default, it is False.
            termination_event : multiprocessing.Event, optional
                A multiprocessing.Event object which can be used to terminate the process early. By default, it is None.
            log_queue : multiprocessing.Queue, optional
                A multiprocessing.Queue object which will be used to log the progress of the data generation process. By default, it is None.
        """

        uniform_data = True
        uniform_metadata = True

        # Adjustable parameters for the chunker.
        chunk_size = 1000
        subchunk_size = 100

        # Adjustable parameters for the query process.
        max_query_queue_size = 50

        super().__init__(target_filename, manifest_filename, self.dataset_name, ignore_incomplete_data, uniform_data, uniform_metadata, termination_event, log_queue, chunk_size, subchunk_size, max_query_queue_size)

    def generateData(self, row, query=None, log_queue=None):
        """
        Generates the data object using the row of the CSV file and its corresponding query.

        Parameters
        ----------
            row : dict
                The row of the CSV file to generate the data object from.
            query : object, optional
                The query-like object used to get the data from the database associated with the row. By default, it is None.
            log_queue : multiprocessing.Queue, optional
                A multiprocessing.Queue object which will be used to log messages. By default, it is None.

        Returns
        -------
        data : Data object
            The data object generated from the row of the CSV file.
        """

        data = {}
        metadata = {}

        TARGET_ID = self.retrieveValue("target_id", row)
        RA = self.retrieveValue("ra", row)
        DEC = self.retrieveValue("dec", row)
        ZOOM = self.retrieveValue("zoom", row)
        PNG_DIRECTORY = self.retrieveValue("png_directory", row)

        metadata[self.getColumnKey("target_id")] = TARGET_ID
        metadata[self.getColumnKey("ra")] = RA
        metadata[self.getColumnKey("dec")] = DEC
        metadata[self.getColumnKey("zoom")] = ZOOM
        metadata[self.getColumnKey("png_directory")] = PNG_DIRECTORY

        legacy_survey_query = query

        # Add extra metadata not found directly from the CSV file.
        metadata['Data Source'] = "[Legacy Surveys](+tab+http://legacysurvey.org/viewer)"

        ICRS_coordinates = SkyCoord(ra=RA * u.degree, dec=DEC * u.degree, frame='icrs')

        galactic_coordinates = ICRS_coordinates.transform_to(frame="galactic")
        metadata['Galactic Coordinates'] = galactic_coordinates.to_string("decimal")

        ecliptic_coordinates = ICRS_coordinates.transform_to(frame=astropy.coordinates.GeocentricMeanEcliptic)
        metadata[f'{Data.privatization_symbol}Ecliptic Coordinates'] = ecliptic_coordinates.to_string("decimal")

        metadata['Legacy Survey Viewer'] = f"[Legacy Survey](+tab+{legacy_survey_query.getViewerURL()})"


        # Save all images for parameter set, add grid if toggled for that image
        flist = []
        size_list = []
        if(self.chunker is None):

            if (legacy_survey_query.legacy_survey_parameters.get("blink", None) is not None):
                flist, size_list = legacy_survey_query.getBlinkImages(PNG_DIRECTORY)
            else:
                image, image_size = legacy_survey_query.getImage(PNG_DIRECTORY)

                flist.append(image)
                size_list.append(image_size)
        else:
            chunk_directory = self.chunker.getChunkDirectory()

            if(legacy_survey_query.legacy_survey_parameters.get("blink", None) is not None):
                flist, size_list = legacy_survey_query.getBlinkImages(chunk_directory)
            else:
                image, image_size = legacy_survey_query.getImage(chunk_directory)

                flist.append(image)
                size_list.append(image_size)

        has_empty_image = False
        is_partial_cutout = False

        for image_filepath in flist:
            if(image_filepath is None):
                has_empty_image = True
                break

        if(not has_empty_image):
            for size in size_list:
                width, height = size
                metadata["Legacy Survey Pixel Width"] = width
                metadata["Legacy Survey Pixel Height"] = height
                if (width != height):
                    is_partial_cutout = True
                    break

        if((is_partial_cutout or has_empty_image) and self.ignore_incomplete_data):
            self.log(f"This is a partial cutout or an empty image and is being ignored.", log_queue)

        data_field_names = []
        for i in range(len(flist)):
            data_field_names.append("f" + str(i + 1))

        data = {data_field_name: flist[i] for i, data_field_name in enumerate(data_field_names)}

        # Add unaccounted for metadata to the metadata dictionary.
        for key in row:
            if key not in metadata:
                metadata[key] = row[key]

        # If the image is a partial cutout, then return  (None, Data(data, metadata)).
        if((is_partial_cutout or has_empty_image) and self.ignore_incomplete_data):
            return (None, Data(data, metadata))

        return Data(data, metadata)

    def requestQuery(self, row):
        """
        Requests a query from the database.

        Parameters
        ----------
            row : dict
                The row of the CSV file to request the query for.

        Returns
        -------
        (row, query) : tuple
            The tuple containing the row and the query requested from the database.
        """

        RA = self.retrieveValue("ra", row)
        DEC = self.retrieveValue("dec", row)
        ZOOM = self.retrieveValue("zoom", row)
        LAYER = self.retrieveValue("layer", row)
        BLINK = self.retrieveValue("blink", row)
        FOV = self.retrieveValue("fov", row)

        query = LegacySurveyQuery(RA=RA, DEC=DEC, zoom=ZOOM, layer=LAYER, blink=BLINK, fov=FOV, bands="grz")
        return (row, query)


# Helper functions for working with Datasets
def get_available_astronomy_datasets():
    # Find all the available subclasses of AstronomyDataset in the Dataset file

    # Get all the classes in the Dataset file
    dataset_classes = [cls for cls in AstronomyDataset.__subclasses__()]

    # Determine the classes that are subclasses of AstronomyDataset
    dataset_names = []

    # Get the names of the available datasets
    for dataset_class in dataset_classes:
        try:
            dataset_names.append(dataset_class.dataset_name)
        except AttributeError:
            dataset_names.append(dataset_class.__name__)
    dataset_dict = {dataset_name: dataset_class for dataset_name, dataset_class in zip(dataset_names, dataset_classes)}

    return dataset_dict

def calculate_min_and_max_brightness(MINBRIGHT, MAXBRIGHT, RA, DEC, SIZE):
    if (MINBRIGHT == "" or MAXBRIGHT == ""):
        unWISE_query = unWISEQuery.unWISEQuery(ra=RA, dec=DEC, size=SIZE, bands=12)
        percentile_brightness_clip = unWISE_query.calculateBrightnessClip(mode="percentile", percentile=97.5)

        MINBRIGHT, MAXBRIGHT = set_minimum_brightness_clip_width(percentile_brightness_clip)

    if (MAXBRIGHT < MINBRIGHT):
        raise ValueError(f"MAXBRIGHT ({MAXBRIGHT}) is less than MINBRIGHT ({MINBRIGHT})")

    return MINBRIGHT, MAXBRIGHT

def calculate_diff_min_and_max_brightness(RA, DEC, SIZE):
    unWISE_query = unWISEQuery.unWISEQuery(ra=RA, dec=DEC, size=SIZE, bands=12)

    percentile_brightness_clip = unWISE_query.calculateBrightnessClip(mode="percentile", percentile=97.5)
    median_brightness = unWISE_query.calculateBrightnessClip(mode="percentile", percentile=50)[0]

    DIFF_MINBRIGHT, DIFF_MAXBRIGHT = median_relative_brightness_clip(percentile_brightness_clip, median_brightness)

    if (DIFF_MAXBRIGHT < DIFF_MINBRIGHT):
        raise ValueError(f"DIFF_MAXBRIGHT ({DIFF_MAXBRIGHT}) is less than DIFF_MINBRIGHT ({DIFF_MINBRIGHT})")

    return DIFF_MINBRIGHT, DIFF_MAXBRIGHT

def set_minimum_brightness_clip_width(percentile_brightness_clip, minimum_brightness_width=100):
    """
    Increases the width of the brightness clip if the difference between the maximum and minimum brightness is less than the minimum brightness width.

    Parameters
    ----------
    percentile_brightness_clip : tuple
        The tuple containing the percentile brightness clip values.
    brightness_width : int, optional
        The width of the brightness clip. By default, it is 100.


    Returns
    -------
    MINBRIGHT : float
        The minimum brightness clip value.
    MAXBRIGHT : float
        The maximum brightness clip value.

    """

    MINBRIGHT = percentile_brightness_clip[0]
    MAXBRIGHT = percentile_brightness_clip[1]

    if(MAXBRIGHT - MINBRIGHT < minimum_brightness_width):
       brightness_difference = MAXBRIGHT - MINBRIGHT
       brightness_difference = minimum_brightness_width - brightness_difference
       MAXBRIGHT = MAXBRIGHT + brightness_difference/2
       MINBRIGHT = MINBRIGHT - brightness_difference/2

    return MINBRIGHT, MAXBRIGHT

def median_relative_brightness_clip(percentile_brightness_clip, median_brightness):
    """
    Offsets the percentile brightness clip values by the median brightness, so that the median brightness is at 0.

    Parameters
    ----------
    percentile_brightness_clip
    median_brightness

    Returns
    -------
    MINBRIGHT : float
        The minimum brightness clip value.
    MAXBRIGHT : float
        The maximum brightness clip value.

    """

    ABOVE_MEDIAN = percentile_brightness_clip[1] - median_brightness
    BELOW_MEDIAN = 1/4 * ABOVE_MEDIAN

    MINBRIGHT = -BELOW_MEDIAN
    MAXBRIGHT = ABOVE_MEDIAN

    MINBRIGHT, MAXBRIGHT = set_minimum_brightness_clip_width((MINBRIGHT, MAXBRIGHT))

    return MINBRIGHT, MAXBRIGHT