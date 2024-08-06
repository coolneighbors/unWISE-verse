"""
Created on June 9th 2021
Completely refactored on December 21st 2023
@author: Austin Humphreys
"""
import re


class Data:
    privatization_symbol = "#"
    def __init__(self, data, metadata=None):
        """
        Initializes a Data object, an object which holds the data and metadata of a single object.

        Parameters
        ----------
            data : Iterable of strings as the data field names or a dictionary of data field names and data values
                The data field names or the data field names and values of the data object.
            metadata : Iterable of strings as the metadata field names or a dictionary of metadata field names and metadata values, optional
                The metadata field names or the metadata field names and values of the data object. By default, it is None.
        """

        self.data = {}
        self.data_types = {}
        self.metadata = {}
        self.metadata_types = {}
        self.private_metadata_fields_dictionary = {}

        if(isinstance(data, dict)):
            self.setData(data)
        else:
            for d in data:
                if(not isinstance(d, str)):
                    raise TypeError(f"The provided data field name, {d}, is not a string.")
            self.initializeDataFields(data)

        if(metadata is not None):
            if(isinstance(metadata, dict)):
                self.setMetadata(metadata)
            else:
                for m in metadata:
                    if(not isinstance(m, str)):
                        raise TypeError(f"The provided metadata field name, {m}, is not a string.")
                self.initializeMetadataFields(metadata)

    def initializeFields(self, data_field_names, metadata_field_names=()):
        """
        Initializes the fields of a Data object.

        Parameters
        ----------
            data_field_names : Iterable of str
                The names of the data fields to initialize.
            metadata_field_names : Iterable of str, optional
                The names of the metadata fields to initialize.
        """

        self.initializeDataFields(data_field_names)
        self.initializeMetadataFields(metadata_field_names)

    def initializeDataFields(self, data_field_names):
        """
        Initializes the data fields of a Data object.

        Parameters
        ----------
            data_field_names : Iterable of str
                The names of the data fields to initialize.
        """

        data_field_names = list(data_field_names)

        if(len(data_field_names) != len(set(data_field_names))):
            repeated_fields = []
            for field_name in data_field_names:
                if (data_field_names.count(field_name) > 1):
                    repeated_fields.append(field_name)
            raise ValueError("Data field names cannot be repeated: " + str(repeated_fields))

        for field_name in data_field_names:
            if (not isinstance(field_name, str)):
                raise TypeError("Data field names must be strings, not " + str(type(field_name)))

            if (not self.isReducedFieldName(field_name)):
                raise ValueError("Data field names cannot start with the privatization symbol: " + self.privatization_symbol)

            self.data[field_name] = None
            self.data_types[field_name] = None

    def initializeMetadataFields(self, metadata_field_names):
        """
        Initializes the metadata fields of a Data object.

        Parameters
        ----------
            metadata_field_names : Iterable of str
                The names of the metadata fields to initialize.
        """

        metadata_field_names = list(metadata_field_names)

        reduced_metadata_field_names = self.reduceFieldNames(metadata_field_names)
        if (len(reduced_metadata_field_names) != len(set(reduced_metadata_field_names))):
            repeated_fields = []
            for field_name in reduced_metadata_field_names:
                if (reduced_metadata_field_names.count(field_name) > 1):
                    repeated_fields.append(field_name)
            raise ValueError("Metadata fields must be unique, but the following repeated fields were found: " + str(list(set(repeated_fields))))

        if (len(metadata_field_names) > 0):
            for field_name in metadata_field_names:
                if (not isinstance(field_name, str)):
                    raise TypeError("Metadata field names must be strings, not " + str(type(field_name)))

                if (not self.isReducedFieldName(field_name)):
                    reduced_field_name = self.reduceFieldName(field_name)
                    self.metadata[reduced_field_name] = None
                    self.metadata_types[reduced_field_name] = None
                    self.private_metadata_fields_dictionary[reduced_field_name] = True
                else:
                    self.metadata[field_name] = None
                    self.metadata_types[field_name] = None
                    self.private_metadata_fields_dictionary[field_name] = False

    def reduceFieldName(self, field_name):
        """
        Reduces a field name to its reduced form, removing the privatization symbol if it exists.

        Parameters
        ----------
            field_name : str
                The field name to reduce.

        Returns
        -------
            str
                The reduced field name.
        """

        if (field_name[0] == self.privatization_symbol):
            return field_name[1:]
        else:
            return field_name

    def reduceFieldNames(self, field_names):
        """
        Reduces a list of field names to their reduced forms, removing the privatization symbol if it exists.
        Parameters
        ----------
        field_names
            The field names to reduce.

        Returns
        -------
        list of str
            The reduced field names.

        """

        return [self.reduceFieldName(field_name) for field_name in field_names]

    def isReducedFieldName(self, field_name):
        """
        Returns whether a field name is reduced.

        Parameters
        ----------
            field_name : str
                The field name to check.

        Returns
        -------
            bool
                Whether the field name is reduced.
        """

        return (field_name[0] != self.privatization_symbol)

    def areReducedFieldNames(self, field_names):
        """
        Returns whether a list of field names are reduced.

        Parameters
        ----------
            field_names : Iterable of str
                The field names to check.

        Returns
        -------
            bool
                Whether the field names are reduced.
        """

        return all([self.isReducedFieldName(field_name) for field_name in field_names])

    def __str__(self):
        """
        Returns a string representation of the Data object.

        Returns
        -------
            str
                A string representation of the Data object.
        """

        return "Data: " + str(self.data) + ", Metadata: " + str(self.metadata)

    def __repr__(self):
        """
        Returns a string representation of the Data object.

        Returns
        -------
            str
                A string representation of the Data object.
        """

        return str(self)

    def __eq__(self, other):
        """
        Returns whether two Data objects are equal.

        Parameters
        ----------
            other : Data object
                The Data object to compare against.

        Returns
        -------
            bool
                Whether the two Data objects are equal.
        """

        return (self.data == other.data) and (self.metadata == other.metadata) and (self.data_types == other.data_types) and (self.metadata_types == other.metadata_types) and (self.private_metadata_fields_dictionary == other.private_metadata_fields_dictionary)

    def __ne__(self, other):
        """
        Returns whether two Data objects are not equal.

        Parameters
        ----------
            other : Data object
                The Data object to compare against.

        Returns
        -------
            bool
                Whether the two Data objects are not equal.
        """

        return not (self == other)

    def removeDataField(self, data_field_name):
        """
        Removes a data object from the data dictionary.

        Parameters
        ----------
            data_field_name : str
        """

        del self.data[data_field_name]
        del self.data_types[data_field_name]

    def removeMetadataField(self, metadata_field_name):
        """
        Removes a metadata object from the metadata dictionary.

        Parameters
        ----------
            metadata_field_name : str
        """

        del self.metadata[metadata_field_name]
        del self.metadata_types[metadata_field_name]

    def getFieldNames(self, reduced=True):
        """
        Returns the names of the data and metadata fields.

        Returns
        -------
            list
                The names of the data and metadata fields.
        """
        field_names = []

        field_names.extend(self.getMetadataFieldNames(reduced=reduced))
        field_names.extend(self.getDataFieldNames())

        return field_names

    def getDataFieldNames(self):
        """
        Returns the names of the data fields.

        Returns
        -------
            list
                The names of the data fields.
        """

        return list(self.data.keys())

    def getMetadataFieldNames(self, reduced=True):
        """
        Returns the names of the metadata fields.

        Returns
        -------
            list
                The names of the metadata fields.
        """

        if(reduced):
            return list(self.metadata.keys())
        else:
            unreduced_metadata_field_names = []
            for key in self.metadata.keys():
                if(self.private_metadata_fields_dictionary[key]):
                    unreduced_metadata_field_names.append(self.privatization_symbol + key)
                else:
                    unreduced_metadata_field_names.append(key)
            return unreduced_metadata_field_names

    def hasField(self, field_name):
        """
        Returns whether the Data object has a field with the given name.

        Parameters
        ----------
            field_name : str
                The name of the field.

        Returns
        -------
            bool
                Whether the Data object has a field with the given name.
        """

        reduced_field_name = self.reduceFieldName(field_name)

        return (reduced_field_name in self.data) or (reduced_field_name in self.metadata)

    def hasDataField(self, data_field_name):
        """
        Returns whether the Data object has a data field with the given name.

        Parameters
        ----------
            data_field_name : str
                The name of the data field.

        Returns
        -------
            bool
                Whether the Data object has a data field with the given name.
        """

        reduced_field_name = self.reduceFieldName(data_field_name)

        return reduced_field_name in self.data

    def hasMetadataField(self, metadata_field_name):
        """
        Returns whether the Data object has a metadata field with the given name.

        Parameters
        ----------
            metadata_field_name : str
                The name of the metadata field.

        Returns
        -------
            bool
                Whether the Data object has a metadata field with the given name.
        """

        reduced_field_name = self.reduceFieldName(metadata_field_name)

        return reduced_field_name in self.metadata

    def getData(self):
        """
        Returns the data dictionary.

        Returns
        -------
            dict
                The data dictionary.
        """

        return self.data

    def getMetadata(self):
        """
        Returns the metadata dictionary.

        Returns
        -------
            dict
                The metadata dictionary.
        """

        return self.metadata

    def setData(self, data_dictionary):
        """
        Sets the data dictionary.

        Parameters
        ----------
            data_dictionary : dict
                The data dictionary.
        """

        self.initializeDataFields(data_dictionary.keys())
        self.data = data_dictionary

        for key in data_dictionary.keys():
            self.data_types[key] = type(data_dictionary[key])

    def setMetadata(self, metadata_dictionary):
        """
        Sets the metadata dictionary.

        Parameters
        ----------
            metadata_dictionary : dict
                The metadata dictionary.
        """

        self.initializeMetadataFields(metadata_dictionary.keys())

        # Convert the metadata dictionary to its reduced form
        reduced_metadata_dictionary = {}
        for key in metadata_dictionary.keys():
            reduced_key = self.reduceFieldName(key)
            reduced_metadata_dictionary[reduced_key] = metadata_dictionary[key]
            self.metadata_types[reduced_key] = type(metadata_dictionary[key])

        self.metadata = reduced_metadata_dictionary

    def setMetadataFieldAsPrivate(self, metadata_field_name):
        """
        Sets a metadata field as private.

        Parameters
        ----------
            metadata_field_name : str
                The metadata field name.
        """
        reduced_field_name = self.reduceFieldName(metadata_field_name)

        if (reduced_field_name not in self.private_metadata_fields_dictionary):
            raise ValueError(f"'{metadata_field_name}' is not a metadata field.")

        self.private_metadata_fields_dictionary[reduced_field_name] = True

    def setMetadataFieldAsPublic(self, metadata_field_name):
        """
        Sets a metadata field as public.

        Parameters
        ----------
            metadata_field_name : str
                The metadata field name.
        """
        reduced_field_name = self.reduceFieldName(metadata_field_name)

        if (reduced_field_name not in self.private_metadata_fields_dictionary):
            raise ValueError(f"'{metadata_field_name}' is not a metadata field.")

        self.private_metadata_fields_dictionary[reduced_field_name] = False

    def __setitem__(self, key, value):
        """
        Sets the value of a key in the data or metadata dictionaries. Does not allow creation of new keys if they do not exist.

        Parameters
        ----------
            key : str
                The key of the value to be set.
            value : object
                The value to be set.
        """

        reduced_key = self.reduceFieldName(key)

        if (reduced_key in self.data):
            self.data[reduced_key] = value
            self.data_types[reduced_key] = type(value)
        elif (reduced_key in self.metadata):
            self.metadata[reduced_key] = value
            self.metadata_types[reduced_key] = type(value)
        else:
            raise KeyError(f"Key '{reduced_key}' does not exist in the data or metadata dictionaries.")

    def __getitem__(self, key):
        """
        Gets the value of a key in the data or metadata dictionaries.

        Parameters
        ----------
            key : str
                The key of the value to be retrieved.

        Returns
        -------
            object
                The value of the key.
        """

        reduced_key = self.reduceFieldName(key)

        if (reduced_key in self.data):
            return self.data[reduced_key]
        elif (reduced_key in self.metadata):
            return self.metadata[reduced_key]
        else:
            return None

    def getDictionary(self, reduced=True):
        """
        Returns the combined data and metadata dictionaries in a dictionary of the form {data: data_dictionary, metadata: metadata_dictionary}.

        Returns
        -------
            dict
                The combined data and metadata dictionaries.
        """

        if(reduced):
            return {"data": self.data, "metadata": self.metadata}
        else:
            unreduced_metadata_dictionary = {}
            for key in self.metadata.keys():
                if(self.private_metadata_fields_dictionary[key]):
                    unreduced_metadata_dictionary[self.privatization_symbol + key] = self.metadata[key]
                else:
                    unreduced_metadata_dictionary[key] = self.metadata[key]
            return {"data": self.data, "metadata": unreduced_metadata_dictionary}

    def getCombinedDictionary(self, reduced=True):
        """
        Returns the combined data and metadata dictionaries in a single dictionary.

        Parameters
        ----------
            reduced : bool
                Whether to return the reduced form of the metadata dictionary.

        Returns
        -------
            dict
                The combined data and metadata dictionaries.
        """
        combined_dictionary = {}
        metadata_field_names = self.getMetadataFieldNames(reduced=reduced)
        for metadata_field_name in metadata_field_names:
            combined_dictionary[metadata_field_name] = self[metadata_field_name]

        combined_dictionary.update(self.data)
        return combined_dictionary

    def convertToRecord(self):
        """
        Converts the data and metadata dictionaries to a record.

        Returns
        -------
            dict
                The record.

        Notes
        -----
        A record is a formatted version of the data and metadata dictionaries. It is used to store the data and metadata in a csv file and be able to retrieve it later with its original typing.
        """

        record = {}

        # Add the metadata fields to the record
        metadata_field_names = self.getMetadataFieldNames(reduced=False)
        for metadata_field_name in metadata_field_names:
            record_field = {}
            record_field["category"] = "metadata"
            record_field["value"] = self[metadata_field_name]
            record_field["type"] = self.metadata_types[self.reduceFieldName(metadata_field_name)]
            record[metadata_field_name] = record_field

        # Add the data fields to the record
        data_field_names = self.getDataFieldNames()
        for data_field_name in data_field_names:
            record_field = {}
            record_field["category"] = "data"
            record_field["value"] = self[data_field_name]
            record_field["type"] = self.data_types[data_field_name]
            record[data_field_name] = record_field

        return record

    @staticmethod
    def createFromRecord(record):
        """
        Creates a Data object from a record.

        Parameters
        ----------
            record : dict
                The record either as a dictionary from convertToRecord() or as a dictionary read from a row of a csv file.

        Notes
        -----
        A record is a formatted version of the data and metadata dictionaries. It is used to store the data and metadata in a csv file and be able to retrieve it later with its original typing.
        """

        data = {}
        metadata = {}

        for key in record.keys():
            record_field_dictionary = {}
            if(isinstance(record[key], str)):
                try:
                    # Check if a pattern of the form "<class '...'>" is present and replace it with the actual class
                    if(not re.search(r"<class '.*'>", record[key])):
                        record_field_dictionary = eval(record[key])
                    else:
                        class_strings = re.findall(r"<class '.*'>", record[key])
                        # Replace the class strings with the actual class names for evaluation. Do so for each found class string.
                        for class_string in class_strings:
                            class_name = class_string[8:-2]
                            record[key] = re.sub(class_string, class_name, record[key])
                        record_field_dictionary = eval(record[key])
                except Exception as e:
                    raise ValueError(f"Could not evaluate record field '{key}': {e}")
            elif(isinstance(record[key], dict)):
                record_field_dictionary = record[key]
            else:
                raise ValueError(f"Record field '{key}' is not a valid record field.")

            category = record_field_dictionary["category"]

            if (category == "data"):
                data_type = record_field_dictionary["type"]

                if(not isinstance(data_type, type)):
                    raise TypeError(f"Data type '{record_field_dictionary['type']}' is not a valid type.")

                data[key] = data_type(record_field_dictionary["value"])
            elif (category == "metadata"):
                metadata_type = record_field_dictionary["type"]

                if(not isinstance(metadata_type, type)):
                    raise TypeError(f"Metadata type '{record_field_dictionary['type']}' is not a valid type.")

                metadata[key] = metadata_type(record_field_dictionary["value"])
            else:
                raise ValueError(f"Category '{category}' is not a valid category.")

        return Data(data=data, metadata=metadata)

    def getTypeDictionary(self):
        """
        Returns the combined data and metadata type dictionaries in a dictionary of the form {data: data_types, metadata: metadata_types}.

        Returns
        -------
            dict
                The combined data and metadata type dictionaries.
        """

        return {"data": self.data_types, "metadata": self.metadata_types}
