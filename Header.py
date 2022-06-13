"""
Created on Thursday, June 9th

@author: Austin Humphreys
"""

from copy import copy

# Errors
class InvalidTextHeaderError(Exception):
    def __init__(self, txt_header):
        super(InvalidTextHeaderError, self).__init__(f"The number of lines in the provided header: {txt_header.name}")

class ImproperHeaderComparisonError(Exception):
    def __init__(self, header, other):
        super(ImproperHeaderComparisonError, self).__init__(f"The objects you are trying to compare are not comparable: {type(header)} and {type(other)}")

class Header:

    def __init__(self,data_fields,metadata_fields):
        """
        Initializes the data fields and metadata fields for the Header object.

        Parameters
        ----------
            data_fields : List of str
                A list of strings representing the field names for the data of the header.
            metadata_fields : List of str
                A list of strings representing the field names for the metadata of the header.

        Notes
        -----

        """

        self.data_fields = copy(data_fields)
        self.metadata_fields = copy(metadata_fields)

    def __eq__(self, other):
        """
        Overloads the == operator for the Header object such that two Header objects are equal, if and only if both
        their data_fields and their metadata_fields are equal.

        Parameters
        ----------
            other : Header object
                A Header object which is being equated to the current Header object.

        Returns
        -------
        True/False : boolean
            A boolean value based on whether both the data_fields and the metadata_fields are equal.

        Notes
        -----

        """

        if(isinstance(other,Header)):
            return (self.data_fields == other.data_fields and self.metadata_fields == other.metadata_fields)
        else:
            raise ImproperHeaderComparisonError(self,other)

    def __len__(self):
        """
        Overloads the len() function for the Header object such that the length is the number of header elements.
        The number of header elements is the sum of the number of data fields and the number of metadata fields.

        Returns
        -------
        len(self.data_fields) + len(self.metadata_fields) : int
            An integer value based on the sum of the lengths of self.data_fields and self.metadata_fields.

        Notes
        -----

        """

        return len(self.data_fields) + len(self.metadata_fields)

    def __getitem__(self, index):
        """
        Overloads the [] operator for the Header object such that the element at an index is a corresponding field name
        of the Header object. The Header is ordered such that the metadata fields are first and then followed by the
        data fields for a total of len(Header) elements.

        Parameters
        ----------
            index : int
                An index of the Header object, from 0 to len(Header object)-1.

        Returns
        -------
        header_list[index] : str
            The field name of the corresponding metadata or data at the index.

        Notes
        -----

        """

        header_list = [*self.metadata_fields,*self.data_fields]
        return header_list[index]

    def __str__(self):
        """
        Overloads the str() function for the Header object such that a string of the metadata fields and the data fields
        is provided.

        Returns
        -------
        string : str
            Provides a string of the form, f"Metadata Fields: {self.metadata_fields}, Data Fields: {self.data_fields}".

        Notes
        -----

        """

        return f"Metadata Fields: {self.metadata_fields}, Data Fields: {self.data_fields}"

    @classmethod
    def create_header_from_text_file(cls, header_filename, delimiter= " "):
        """
        Creates a Header object from a text file in an established format (See Notes for format).

        Parameters
        ----------
            header_filename : str
                A string representing the full path filename of the header text file.
            delimiter : str, optional
                The string used to separate different elements in the header text file.
                Defaults to " ", a single space.

        Returns
        -------
        Header(data_fields,metadata_fields) : Header object
            A Header object constructed from the data and metadata provided in the header text file.

        Notes
        -----
            Header Text File Format: (Delimiter = " ")

            data1 data2 data3 ...
            metadata1 metadata2 metadata3 ...

            (Number of data and metadata field names does not need to be equal)
        """

        data_fields = []
        metadata_fields = []
        with open(header_filename) as txt_header:
            line_count = 1
            for line in txt_header:
                stripped_line = line.strip()
                if(line_count == 1):
                    data_fields = stripped_line.split(sep=delimiter)
                elif(line_count == 2):
                    metadata_fields = stripped_line.split(sep=delimiter)
                else:
                    raise InvalidTextHeaderError(txt_header)
                line_count += 1
        return Header(data_fields,metadata_fields)





