"""
Created on Thursday, June 9th

@author: Austin Humphreys
"""

import csv
import os
from Header import Header

# Errors
class InvalidHeaderError(Exception):
    def __init__(self, header, master_header):
        super(InvalidHeaderError, self).__init__(f"The header defined by the provided data and metadata does not match the master header file: {header} , {master_header}")

class InvalidManifestFileError(Exception):
    def __init__(self, manifest_filename):
        super(InvalidManifestFileError, self).__init__(f"The provided manifest filename is not a .csv or .fits file: {manifest_filename}")

class Manifest:
    def __init__(self, dataset, manifest_filename = "manifest.csv", overwrite_automatically = None, use_master_header = False, delimiter = " "):
        """
        Initializes a Manifest object, an object which uses a dataset to create a formatted manifest CSV file.

        Parameters
        ----------
            dataset : Dataset object
                A dataset object which will be converted into the manifest file.
            manifest_filename : str, optional
                The full path filename of the manifest CSV file to be generated or overridden. By default it is
                "manifest.csv".
            overwrite_automatically : bool, optional
                Allows for any existing manifest file to be overwritten with a new one automatically if made True. If
                False, it will keep any existing manifest trying to be overridden. If None, it will prompt the user to
                decide. By default, it is None.
            use_master_header : bool, optional
                Allows for a master_header.txt file to be compared against the manifest trying to be generated. If
                they differ, it will raise an error. By default it is False.
            delimiter : str, optional
                The string used to separate fields in the master_header.txt file. By default it is " ", a single space.

        Notes
        -----

        """

        self.header = Header(dataset.data_field_names,dataset.metadata_field_names)
        if (use_master_header):
            master_header = Header.create_header_from_text_file("master_header.txt", delimiter)
            if (master_header != self.header):
                raise InvalidHeaderError(self.header, master_header)

        self.information_table = []
        for i in range(len(dataset)):
            dataset_dict = dataset[i]
            data = dataset_dict["data"]
            metadata = dataset_dict["metadata"]
            self.information_table.append([*metadata.values, *data.values])

        self.createManifestFile(manifest_filename=manifest_filename, overwrite_automatically=overwrite_automatically)

    def __str__(self):
        """
        Overloads the str() function for the Manifest object such that a string of the Header object and the information
        table (2D list of values) is provided.

        Returns
        -------
        string : str
            Provides a string of the form, f"Header: {self.header} \n Information Table: {self.information_table}".

        Notes
        -----

        """

        return f"Header: {self.header} \n Information Table: {self.information_table}"

    def createManifestFile(self, manifest_filename = "manifest.csv", filetype = ".csv", overwrite_automatically = None):
        """
        Creates the manifest file associated with this Manifest object.

        Parameters
        ----------
            manifest_filename : str, optional
                The full path filename of the manifest CSV file to be generated or overridden. By default it is
                "manifest.csv".
            filetype : str, optional
                A string representing the filetype of the manifest file to be generated or overridden. By default it is
                ".csv"
            overwrite_automatically : bool, optional
                Allows for any existing manifest file to be overwritten with a new one automatically if made True. If
                False, it will keep any existing manifest trying to be overridden. If None, it will prompt the user to
                decide. By default, it is None.

        Notes
        -----

        """

        if(not (".csv" in manifest_filename) and not(".fits" in manifest_filename)):
            manifest_filename = manifest_filename + filetype
        overwrite_manifest = None
        if (overwrite_automatically is None):
            if (os.path.exists(manifest_filename)):
                print("Manifest File: " + str(manifest_filename))
                response = input("This manifest already exists. Would you like to overwrite this manifest? (y/n) ")
                end_prompt = False
                while (not end_prompt):
                    if (response.lower() == "y"):
                        end_prompt = True
                        overwrite_manifest = True
                        print(f"Warning: manifest file being overridden at: {manifest_filename}")
                    elif (response.lower() == "n"):
                        end_prompt = True
                        overwrite_manifest = False
                    else:
                        response = input("Invalid response, please type a valid response (y/n): ")
            else:
                overwrite_manifest = True
        elif (overwrite_automatically):
            overwrite_manifest = True
        else:
            overwrite_manifest = False

        if (overwrite_manifest):
            if(".csv" in manifest_filename):
                f = open(manifest_filename, 'w', newline='')
                writer = csv.writer(f)
                writer.writerow([*self.header.metadata_fields,*self.header.data_fields])
                print('Header Created')
                for row in self.information_table:
                    writer.writerow(row)
                f.close()
                print('Manifest Generation Complete')
            elif(".fits" in manifest_filename):
                print("Currently no functionality for .fits files")
            else:
                raise InvalidManifestFileError(manifest_filename)
        else:
            print("Existing Manifest Preserved")


class Defined_Manifest(Manifest):
    def __init__(self, dataset, manifest_filename = "manifest.csv", auto_generate_manifest = True, delimiter = " "):
        """
        Initializes a Defined_Manifest object, an object which uses a dataset to create a formatted manifest CSV file and
        must be compared against a master_header.txt file.

        Parameters
        ----------
            dataset : Dataset object
                A dataset object which will be converted into the manifest file.
            manifest_filename : str, optional
                The full path filename of the manifest CSV file to be generated or overridden. By default it is
                "manifest.csv".
            overwrite_automatically : bool, optional
                Allows for any existing manifest file to be overwritten with a new one automatically if made True. If
                False, it will keep any existing manifest trying to be overridden. If None, it will prompt the user to
                decide. By default, it is None.
            delimiter : str, optional
                The string used to separate fields in the master_header.txt file. By default it is " ", a single space.

        Notes
        -----

        """

        super(Defined_Manifest, self).__init__(dataset,manifest_filename, auto_generate_manifest, True, delimiter)





