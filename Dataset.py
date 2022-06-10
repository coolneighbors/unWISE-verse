import csv
import wv
from Data import Data, Metadata

#initialize image manipulation variables
scaling = 2

# Errors
class NonUniformFieldsError(Exception):
    def __init__(self):
        super(NonUniformFieldsError, self).__init__("The field names are not uniform for all data and or metadata objects.")

class MismatchedDataAndMetadataError(Exception):
    def __init__(self):
        super(MismatchedDataAndMetadataError, self).__init__("The number of data objects does not match the number of metadata objects.")

class Dataset():
    def __init__(self, data_list, metadata_list):
        self.data_list = data_list
        self.metadata_list = metadata_list
        if(len(data_list) != len(metadata_list)):
            raise MismatchedDataAndMetadataError

        for data in data_list:
            for other_data in data_list:
                if(not data.have_equal_fields(other_data)):
                    raise NonUniformFieldsError
        self.data_field_names = self.data_list[0].field_names

        for metadata in metadata_list:
            for other_metadata in metadata_list:
                if (not metadata.have_equal_fields(other_metadata)):
                    raise NonUniformFieldsError
        self.metadata_field_names = self.metadata_list[0].field_names

    def __str__(self):
        return "Datalist: " + str(self.data_list) + ", " + "Metadata List: " + str(self.metadata_list)

    def __len__(self):
        return len(self.data_list)

    def __getitem__(self, index):
        data = self.data_list[index]
        metadata = self.metadata_list[index]
        dataset_dict = {"data": data,"metadata": metadata}
        return dataset_dict

class Zooniverse_Dataset(Dataset):
    def __init__(self, dataset_filename):
        data_list = []
        metadata_list = []

        # Currently is only able to use CSV files
        with open(dataset_filename, newline='') as targetList:
            reader = csv.DictReader(targetList)
            for row in reader:
                RA = row['RA']
                DEC = row['DEC']
                gridYN = row['GRID']
                
                #parse gridyn into integer values, only accept '1'
                if gridYN == '1':
                    gridYN = 1
                else:
                    gridYN = 0
                
                row_metadata = []
                metadata_field_names = []
                for key in row.keys():
                    metadata_field_names.append(key)
                for key in row:
                    row_metadata.append(row[key])
                metadata_list.append(Metadata(metadata_field_names, row_metadata))

                # set WV parameters to RA and DEC
                wv.custom_params(RA, DEC)

                # Save all images for parameter set, add grid if toggled for that image
                if (gridYN == 1):
                    flist = wv.png_set(RA, DEC, "pngs", scale_factor=scaling, addGrid=True)
                else:
                    flist = wv.png_set(RA, DEC, "pngs", scale_factor=scaling)
                    
                    
                
                data_field_names = []
                for i in range(len(flist)):
                    data_field_names.append("f" + str(i+1))
                data_list.append(Data(data_field_names, flist))
        super(Zooniverse_Dataset, self).__init__(data_list, metadata_list)
