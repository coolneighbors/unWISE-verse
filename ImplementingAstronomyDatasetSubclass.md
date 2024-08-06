# Implementing a new AstronomyDataset subclass

To implement a new subclass of AstronomyDataset, append a subclass declaration to the existing Dataset.py file. The structure of the subclass should be as follows:

```
class SubclassNameDataset(AstronomyDataset):
    dataset_name = "Subclass Name"
    required_target_columns = [] # List of required columns in the target CSV file. Columns take the form of: "column_name" (lowercase, snakecase).
    required_private_columns = [] # List of columns which, if present, should be hidden from Zooniverse users.
    mutable_columns_dict = {} # Dictionary of columns which can be modified by the user. Key-value pairs are of the form {"column_name":  InputField.Entry/OptionMenu/... (see available InputField subclasses)}
    mutable_columns_keys_dict = {} # Dictionary of columns and their associated header names in the resulting manifest file. Key-value pairs are of the form {"column_name": "header_name"}
    def __init__(self, target_filename, manifest_filename, ignore_incomplete_data=False, termination_event=None, log_queue=None):
  
        uniform_data = True # Boolean indicating whether all data objects should have the same data fields.
        uniform_metadata = True # Boolean indicating whether all data objects should have the same metadata fields.

        # Adjustable parameters for the chunker.
        chunk_size = 1000 # Number of rows to process in a single chunk.
        subchunk_size = 100 # Number of rows to process in a single subchunk.

        # Adjustable parameters for the query process.
        max_query_queue_size = 50 # Maximum number of queries to be collected before processing.

        super().__init__(target_filename, manifest_filename, self.dataset_name, ignore_incomplete_data, uniform_data, uniform_metadata, termination_event, log_queue, chunk_size, subchunk_size, max_query_queue_size)

    def generateData(self, row, query=None, log_queue=None):
        data = {} # Dictionary of data fields for the current data object.
        metadata = {} # Dictionary of metadata fields for the current data object.
        
        # Retrieve values from the current row of the target CSV file.
        COLUMN_NAME = self.retrieveValue("column_name", row)
        PNG_DIRECTORY = self.retrieveValue("png_directory", row) # Retrieve the directory for storing the PNG images.
        
        # Set the metadata fields for the current data object, as well as any additional metadata generated from the values in the target CSV file.
        metadata[self.getColumnKey("column_name")] = COLUMN_NAME 

        # Add any other metadata not found directly from the CSV file or query.
        metadata['Other'] = "Lorem ipsum dolor sit amet, consectetur adipiscing elit..."
        
        # Use the query object to retrieve the image data for the current data object. 
        flist = [] # List of filepaths for the image data.
        size_list = [] # List of image sizes for the image data. (This is optional, and can be omitted if not needed for your dataset implementation.)
        if(self.chunker is None):
                image_directory = PNG_DIRECTORY
                image, image_size = query.getImage(image_directory) # Retrieve the image data (and image size) from the query object. This will clearly depend on the specifics of the query object and the data source.
         
                flist.append(image)
                size_list.append(image_size)
        else:
            chunk_directory = self.chunker.getChunkDirectory()

            image, image_size = query.getImage(chunk_directory)

            flist.append(image)
            size_list.append(image_size)
        
        # Perhaps establish safeguards for incomplete data or missing data.
        
        has_empty_image = False
        is_partial_cutout = False

        for image_filepath in flist:
            if(image_filepath is None):
                has_empty_image = True
                break

        if(not has_empty_image):
            for size in size_list:
                width, height = size
                metadata["Width"] = width
                metadata["Height"] = height
                if (width != height):
                    is_partial_cutout = True
                    break

        if((is_partial_cutout or has_empty_image) and self.ignore_incomplete_data):
            self.log(f"This is a partial cutout or an empty image and is being ignored.", log_queue) # Log the fact that the current data object is being ignored due to incomplete data.

        data_field_names = [] # List of data field names for the current data object.
        for i in range(len(flist)):
            data_field_names.append("f" + str(i + 1)) # Generate the data field names for the current data object.

        data = {data_field_name: flist[i] for i, data_field_name in enumerate(data_field_names)} # Populate the data dictionary with the image data for the current data object.

        # Add unaccounted for metadata to the metadata dictionary (if desired).
        for key in row:
            if key not in metadata:
                metadata[key] = row[key]

        # If the image is a partial cutout, then return (None, Data(data, metadata)). (This will send this row to an ignored manifest file.)
        if((is_partial_cutout or has_empty_image) and self.ignore_incomplete_data):
            return (None, Data(data, metadata))

        return Data(data, metadata) # Return the data object for the current row of the target CSV file.

    def requestQuery(self, row):
        RA = self.retrieveValue("ra", row)
        DEC = self.retrieveValue("dec", row)
        ...

        query = SubclassNameQuery(RA=RA, DEC=DEC, ...)
        return (row, query)
```

Once the subclass has been implemented, the subclass is automatically available for use in the unWISE-verse pipeline. The subclass can be selected from the session selection screen, and the user can interact with the subclass through the Dataset dropdown menu.
The only other requirement is to create corresponding variables in the UserInterface.py file to allow the user to interact with the mutable columns of the subclass using the user interface.
For instance, a mutable column "fov" in the subclass would require the following variable in the UserInterface.py file:
self.fov = tk.StringVar(value="120") (For an InputField.Entry mutable column, but you would use other types for other InputField types) (The default value for the field is "120" in this case).
If multiple of the same mutable column are present across different subclasses, the variable will be shared across all of them and modifications to the variable will be reflected in all subclasses that use it.
The values associated with mutable columns are automatically saved in the saved_session.pickle file and are loaded when the program is run again. To start fresh, delete the saved_session.pickle file.

```