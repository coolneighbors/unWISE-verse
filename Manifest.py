import csv
import os

import wv
from Header import Header
from Dataset import Dataset

# Errors
class InvalidHeaderError(Exception):
    def __init__(self):
        super(InvalidHeaderError, self).__init__("The header defined by the provided data and metadata does not match the master header file.")

class InvalidManifestFileError(Exception):
    def __init__(self):
        super(InvalidManifestFileError, self).__init__("The provided manifest filename is not a .csv or .fits file.")

class Manifest:
    def __init__(self, dataset, manifest_filename = "manifest.csv", overwrite_automatically = None, use_master_header = False, delimiter = " "):
        self.header = Header(dataset.data_field_names,dataset.metadata_field_names)
        if (use_master_header):
            master_header = Header.create_header_from_text_file("master_header.txt", delimiter)
            if (master_header != self.header):
                raise InvalidHeaderError

        self.information_table = []
        for i in range(len(dataset)):
            dataset_dict = dataset[i]
            data = dataset_dict["data"]
            metadata = dataset_dict["metadata"]
            self.information_table.append([*metadata.values, *data.values])

        self.createManifestFile(manifest_filename=manifest_filename, overwrite_automatically=overwrite_automatically)

    def __str__(self):
        return "Header: " + str(self.header) + "\n" + "Information Table: " + str(self.information_table)

    def createManifestFile(self, manifest_filename = "manifest.csv", filetype = ".csv", overwrite_automatically = None):
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
                        print("Warning: manifest file being overridden at: " + str(manifest_filename))
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
                raise InvalidManifestFileError
        else:
            print("Existing Manifest Preserved")


class Defined_Manifest(Manifest):
    def __init__(self, dataset, manifest_filename = "manifest.csv", auto_generate_manifest = True, use_master_header = True, delimiter = " "):
        super(Defined_Manifest, self).__init__(dataset,manifest_filename, auto_generate_manifest, use_master_header, delimiter)





