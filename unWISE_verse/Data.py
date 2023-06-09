"""
Created on Thursday, June 9th

@author: Austin Humphreys
"""

from copy import copy

# Errors
class FieldAndValueMismatchError(Exception):
    def __init__(self, field_names, values):
        super(FieldAndValueMismatchError, self).__init__(f"The field names and the values are not the same length: {len(field_names)} , {len(values)}")

class NonExistentFieldError(Exception):
    def __init__(self, field_name):
        super(NonExistentFieldError, self).__init__(f"The field name trying to be accessed is not a field: {field_name}")

class NonExistentPrivateFieldError(Exception):
    def __init__(self, field_name):
        super(NonExistentPrivateFieldError, self).__init__(f"The field name trying to be removed was given as private but is not private: {field_name}")

class NonUniqueFieldsError(Exception):
    def __init__(self, field_names):
        seen_field_names = set()
        duplicate_list = []
        for field_name in field_names:
            if field_name in seen_field_names:
                duplicate_list.append(field_name)
            else:
                seen_field_names.add(field_name)
        if(len(duplicate_list) == 1):
            super(NonUniqueFieldsError, self).__init__(f"The following field name is not unique: {duplicate_list[0]}")
        else:
            super(NonUniqueFieldsError, self).__init__(f"The following field names are not unique: {duplicate_list}")

class ImproperDataComparisonError(Exception):
    def __init__(self, object, other):
        super(ImproperDataComparisonError, self).__init__(f"The objects you are trying to compare are not comparable: {type(object)} and {type(other)}")

class ImproperMetadataComparisonError(Exception):
    def __init__(self, object, other):
        super(ImproperMetadataComparisonError, self).__init__(f"The objects you are trying to compare are not comparable: {type(object)} and  {type(other)}")

class PrivateMetadataFieldMismatchError(Exception):
    def __init__(self, object, other):
        super(PrivateMetadataFieldMismatchError, self).__init__(f"The metadata objects you are trying to compare have a mismatch in which fields are private: {object} and {other}")

class InvalidFieldNameError(Exception):
    def __init__(self, field_name):
        super(InvalidFieldNameError, self).__init__(f"The provided field name has the privatization symbol (\"{Metadata.privatization_symbol}\") after the first privatization symbol: {field_name}")

class FieldNameIndexedIncorrectlyError(Exception):
    def __init__(self, field_name):
        super(FieldNameIndexedIncorrectlyError, self).__init__(f"The field name, {field_name} (or another field at this index), is not correctly indexed compared to the other Data or Metadata.")

class Data:
    def __init__(self,field_names = [],data_values = []):
        """
        Initializes a Data object, an object which resembles a dictionary except that it is a pair of
        ordered lists rather than directly linked via keys. Additionally, it will only accept unique field names.

        Parameters
        ----------
            field_names : List of str
                A list of strings representing the field names of different data fields in the Data object. All field
                names must be unique strings, otherwise it will throw an error.
            data_values : List of Any
                A list of values representing the field values associated, in order, to the different field names in
                the Data object. Must have the same length as field_names, otherwise it will throw an error.

        Notes
        -----
            The container structure of the data object could have been easily replicated with a dictionary, but I
            wanted extra functionality associated with it, so I made it its own class. I didn't create a
            dictionary inside of the data object to make sure that the names and values could be easily accessed and in
            a particular order.
        """

        # Check if the field names are in a 1-1 correspondence with values
        if(len(field_names) != len(data_values)):
            raise FieldAndValueMismatchError(field_names,data_values)
        # Check if the field names are unique
        elif(len(set(field_names)) != len(field_names)):
            raise NonUniqueFieldsError(field_names)
        else:
            self.field_names = copy(field_names)
            self.values = copy(data_values)

    def __eq__(self, other):
        """
        Overloads the == operator for the Data object such that two Data objects are equal, if and only if both their
        field_names and their field_values are equal.

        Parameters
        ----------
            other : Data object
                A Data object which is being equated to the current Data object.

        Returns
        -------
        True/False : boolean
            A boolean value based on whether both the field_names and the field_values are equal.

        Notes
        -----

        """

        if (isinstance(other, Data)):
            return (self.field_names == other.field_names and self.values == other.values)
        else:
            raise ImproperDataComparisonError(self, other)

    def have_equal_fields(self,other):
        """
        Determines if the field names of two data objects are equal.

        Parameters
        ----------
            other : Data object
                A Data object which is being equated to the current Data object's field names.

        Returns
        -------
        True/False : boolean
            A boolean value based on whether both the field_names are equal.

        Notes
        -----

        """

        if (isinstance(other, Data)):
            return (self.field_names == other.field_names)
        else:
            raise ImproperDataComparisonError(self, other)

    def resolve_missing_fields(self, other):
        """
        Fixes the missing fields between these data objects

        Parameters
        ----------
            other : Data object
                A Data object to compare against

        Notes
        -----

        """

        if (isinstance(other, Data)):

            first_bool_list = []
            for i in range(len(self)):
                self_field_name = self[i]["name"]
                name_found = False
                for j in range(len(other)):
                    other_field_name = other[j]["name"]
                    if (self_field_name == other_field_name and i == j):
                        first_bool_list.append(True)
                        name_found = True
                if (not name_found):
                    first_bool_list.append(False)

            second_bool_list = []
            for i in range(len(other)):
                self_field_name = other[i]["name"]
                name_found = False
                for j in range(len(self)):
                    other_field_name = self[j]["name"]
                    if (self_field_name == other_field_name and i == j):
                        second_bool_list.append(True)
                        name_found = True
                if (not name_found):
                    second_bool_list.append(False)

            first_mismatched_indices = [i for i, x in enumerate(first_bool_list) if not x]
            first_mismatched_names = []
            for index in first_mismatched_indices:
                first_mismatched_names.append(self[index]["name"])

            second_mismatched_indices = [i for i, x in enumerate(second_bool_list) if not x]
            second_mismatched_names = []
            for index in second_mismatched_indices:
                second_mismatched_names.append(other[index]["name"])

            for name in first_mismatched_names:
                if(not name in other.field_names):
                    other.addField(name,None)
                else:
                    raise FieldNameIndexedIncorrectlyError(name)
            for name in second_mismatched_names:
                if (not name in self.field_names):
                    self.addField(name, None)
                else:
                    raise FieldNameIndexedIncorrectlyError(name)
        else:
            raise ImproperDataComparisonError(self, other)

    def have_equal_values(self,other):
        """
        Determines if the field values of two data objects are equal.

        Parameters
        ----------
            other : Data object
                A Data object which is being equated to the current Data object's field values.

        Returns
        -------
        True/False : boolean
            A boolean value based on whether both the field_values are equal.

        Notes
        -----

        """

        if (isinstance(other, Data)):
            return (self.values == other.values)
        else:
            raise ImproperDataComparisonError(self, other)

    def __len__(self):
        """
        Overloads the len() function for the Data object such that the length is the number of field names
        (which should be equal to the number of field values, otherwise the data object could not have been initialized).

        Returns
        -------
        len(self.field_names) : int
            An integer value based on the the number of field names.

        Notes
        -----

        """

        return len(self.field_names)

    def __getitem__(self, index):
        """
        Overloads the [] operator for the Data object such that each index corresponds to a dictionary of a field name
        and a value corresponding to that index.

        Returns
        -------
        data_dict : dict
            A dictionary of the form, {"name" : str, "value" : Any}
            An index of the Data object, from 0 to len(Data object)-1.
        Notes
        -----

        """
        data_dict = {"name": self.field_names[index], "value": self.values[index]}
        return data_dict

    def __str__(self):
        """
        Overloads the str() function for the Data object such that a string of the field names and the field values
        is provided.

        Returns
        -------
        string : str
            Provides a string of the form, f"Field Names: {self.field_names} , Values: {self.values}".

        Notes
        -----

        """

        return f"Field Names: {self.field_names} , Values: {self.values}"

    @classmethod
    def createFromDictionary(cls,data_dict):
        data_field_names = list(data_dict.keys())
        data_values = list(data_dict.values())
        return Data(data_field_names,data_values)

    def toDictionary(self):
        """
        Converts the Data object into a dictionary with the field names as keys and the values as the corresponding
        values.

        Returns
        -------
        dictionary : dict
            Provides a dictionary of the form, {self.field_names[i]: self.values[i]}

        Notes
        -----

        """

        return {self.field_names[i]: self.values[i] for i in range(len(self.field_names))}

    def addField(self, field_name, value, index = -1):
        """
        Adds a field at a specific index to the existing Data object, consisting of a unique field name and any
        field value.

        Parameters
        ----------
            field_name : str
                A string representing the field name being added. Must be a unique field name and not already in the
                Data object.
            value : Any
                A data value being associated to the field name being added to the Data object. Does not need to be a unique value,
                unlike the field name.
            index : int, optional
                The index in the Data object where the new field_name and value will be placed. By default, the index
                is -1 and appends the field name and value to the end of the Data object. Must be an integer in-between
                0 and len(Data object)-1 (or -1).

        Notes
        -----

        """

        if (not(field_name in self.field_names)):
            if (index == -1):
                self.field_names.append(field_name)
                self.values.append(value)
            elif (index >= 0 and index < len(self.field_names)):
                self.field_names.insert(index, field_name)
                self.values.insert(index, value)
            else:
                raise IndexError
        else:
            raise NonUniqueFieldsError

    def removeField(self, field_name):
        """
        Removes a field from the existing Data object, which removes both the field name and the associated value.

        Parameters
        ----------
            field_name : str
                A string representing the field name being removed.

        Notes
        -----

        """

        if (field_name in self.field_names):
            index_to_be_removed = self.field_names.index(field_name)
            self.field_names.pop(index_to_be_removed)
            self.values.pop(index_to_be_removed)
        else:
            raise NonExistentFieldError(field_name)

    def getFieldValue(self, field_name):
        """
        Gets the value of the field name if it exists in the Data object.

        Returns
        -------
        field_value: Any
            The value of the field name in the Data object.

        """

        if(field_name in self.field_names):
            index = self.field_names.index(field_name)
            return self.values[index]
        else:
            raise NonExistentFieldError(field_name)

    def hasField(self, field_name):
        """
        Checks if the Data object has a field name.

        Parameters
        ----------
            field_name : str
                A string representing the field name being checked.

        Returns
        -------
        has_field : bool
            A boolean representing whether or not the Data object has the field name.

        Notes
        -----

        """

        return field_name in self.field_names

class Metadata(Data):

    privatization_symbol = "#"

    def __init__(self, field_names = [], metadata_values = []):
        """
        Initializes a Metadata object, a child class of a Data object, an object which resembles a dictionary except
        that it is a pair of ordered lists rather than directly linked via keys. Additionally, it will only accept
        unique field names. Fields of a Metadata object also have the ability to be private or public.

        Parameters
        ----------
            field_names : List of str
                A list of strings representing the field names of different data fields in the Data object. All field
                names must be unique strings, otherwise it will throw an error. Field names in the list which start with
                the privatization symbol will be made private automatically.
            metadata_values : List of Any
                A list of values representing the field values associated, in order, to the different field names in
                the Metadata object. Must have the same length as field_names, otherwise it will throw an error.

        Notes
        -----
            Field names given to a metadata object can be make private by placing the privatization symbol at the start of the name or can
            be made private after-the-fact via the setFieldAsPrivate function.
        """

        # Checking if any field names are private upon initialization and if they are unique
        self.private_fields = [False] * len(field_names)
        adjusted_field_names = copy(field_names)
        for i in range(len(field_names)):
            adjusted_field_name = adjusted_field_names[i]
            if(adjusted_field_name[0] == Metadata.privatization_symbol):
                adjusted_field_names[i] = adjusted_field_name[1:]
                check_field_name = adjusted_field_name[1:]
                if(Metadata.privatization_symbol in check_field_name):
                    raise InvalidFieldNameError(adjusted_field_name)
                self.private_fields[i] = True

        super(Metadata, self).__init__(adjusted_field_names,metadata_values)

    def __getitem__(self, index):
        """
        Overloads the [] operator for the Metadata object such that each index corresponds to a dictionary of a field
        name and a value corresponding to that index.

        Returns
        -------
        metadata_dict : dict
            A dictionary of the form, {"name" : str, "value" : Any}
            An index of the Metadata object, from 0 to len(Metadata object)-1.
        Notes
        -----

        """

        field_names_with_private_symbol = self.getAdjustedFieldNames()
        metadata_dict = {"name": field_names_with_private_symbol[index], "value": self.values[index]}
        return metadata_dict

    def getFieldValue(self, field_name):
        """
        Gets the value of the field name if it exists in the Metadata object.

        Returns
        -------
        metadata_dict : dict
            A dictionary of the form, {"name" : str, "value" : Any}
            An index of the Metadata object, from 0 to len(Metadata object)-1.
        Notes
        -----

        """

        if(field_name in self.field_names):
            index = self.field_names.index(field_name)
            return self.values[index]
        elif(Metadata.privatization_symbol + field_name in self.field_names):
            index = self.field_names.index(Metadata.privatization_symbol + field_name)
            return self.values[index]
        else:
            raise NonExistentFieldError(field_name)


    def __str__(self):
        """
        Overloads the str() function for the Metadata object such that a string of the adjusted field names and the
        field values is provided.

        Returns
        -------
        string : str
            Provides a string of the form, f"Field Names: {field_names_with_private_symbol} , Values: {self.values}".

        Notes
        -----

        """

        field_names_with_private_symbol = self.getAdjustedFieldNames()
        return f"Field Names: {field_names_with_private_symbol} , Values: {self.values}"

    def toDictionary(self):
        """
        Converts the Metadata object into a dictionary with the adjusted field names as keys and the values as the corresponding
        values.

        Returns
        -------
        dictionary : dict
            Provides a dictionary of the form, {field_names_with_private_symbol[i]: self.values[i]}

        Notes
        -----

        """

        field_names_with_private_symbol = self.getAdjustedFieldNames()
        return {field_names_with_private_symbol[i]: self.values[i] for i in range(len(self.field_names))}

    def setFieldAsPrivate(self, field_name):
        """
        Sets an existing field as private, which updates the private_fields boolean list.

        Parameters
        ----------
            field_name : str
                A string representing the field name being made private.

        Notes
        -----

        """

        if (field_name in self.field_names):
            field_name_index = self.field_names.index(field_name)
            if(not self.private_fields[field_name_index]):
                self.private_fields[field_name_index] = True
            else:
                print(f"{field_name} is already private.")
        else:
            raise NonExistentFieldError(field_name)

    def setFieldAsPublic(self, field_name):
        """
        Sets an existing field as public, which updates the private_fields boolean list.

        Parameters
        ----------
            field_name : str
                A string representing the field name being made public.

        Notes
        -----

        """

        if (field_name in self.field_names):
            field_name_index = self.field_names.index(field_name)
            if(self.private_fields[field_name_index]):
                self.private_fields[field_name_index] = False
            else:
                print(f"{field_name} is already public.")
        else:
            raise NonExistentFieldError(field_name)

    def isPrivateField(self,field_name):
        """
        Determines if an existing field is private.

        Parameters
        ----------
            field_name : str
                A string representing the field name being determined if it is private.

        Returns
        -------
        self.private_fields[index_of_field_name] : bool
            Provides the boolean value of the private_fields list for the provided field name.

        Notes
        -----

        """

        if (field_name[0] == Metadata.privatization_symbol and (field_name[1:] in self.field_names)):
            index_of_field_name = self.field_names.index(field_name[1:])
            return self.private_fields[index_of_field_name]
        elif(field_name in self.field_names):
            index_of_field_name = self.field_names.index(field_name)
            return self.private_fields[index_of_field_name]
        else:
            raise NonExistentFieldError(field_name)

    def isPublicField(self,field_name):
        """
        Determines if an existing field is public.

        Parameters
        ----------
            field_name : str
                A string representing the field name being determined if it is public.

        Returns
        -------
        not self.isPrivateField(field_name) : bool
            Provides the negated value from the isPrivateField function.

        Notes
        -----

        """

        return not self.isPrivateField(field_name)

    def addField(self, field_name, value, index = -1, make_private = False):
        """
        Adds a field at a specific index to the existing Metadata object, consisting of a unique field name and any
        field value. There is an additional parameter to set the added field as private.

        Parameters
        ----------
            field_name : str
                A string representing the field name being added. Must be a unique field name and not already in the
                Metadata object.
            value : Any
                A metadata value being associated to the field name being added to the Metadata object. Does not need
                to be a unique value, unlike the field name.
            index : int, optional
                The index in the Metadata object where the new field_name and value will be placed. By default, the index
                is -1 and appends the field name and value to the end of the Data object. Must be an integer in-between
                0 and len(Metadata object)-1 (or -1).
            make_private : bool
                A boolean which sets the newly added field as private (True) or public (False). By default it is set to
                False.

        Notes
        -----

        """

        if (index == -1):
            self.private_fields.append(False)
        elif (index >= 0 and index < len(self.field_names)):
            self.private_fields.insert(index, False)

        if (field_name[0] == Metadata.privatization_symbol):
            field_name = field_name[1:]
            make_private = True

        super().addField(field_name, value, index)

        if(make_private):
            self.setFieldAsPrivate(field_name)

    def removeField(self, field_name):
        """
        Removes a field from the existing Metadata object, which removes both the field name, the associated value,
        and the associated boolean for whether it is a private field.

        Parameters
        ----------
            field_name : str
                A string representing the field name being removed.

        Notes
        -----

        """

        if(field_name[0] == Metadata.privatization_symbol and (field_name[1:] in self.field_names)):
            index_of_field_name = self.field_names.index(field_name[1:])
            if(self.private_fields[index_of_field_name]):
                field_name = field_name[1:]
            else:
                raise NonExistentPrivateFieldError(field_name)
        if (field_name in self.field_names):
            index_to_be_removed = self.field_names.index(field_name)
            self.field_names.pop(index_to_be_removed)
            self.values.pop(index_to_be_removed)
            self.private_fields.pop(index_to_be_removed)
        else:
            raise NonExistentFieldError(field_name)

    def __eq__(self, other):
        """
        Overloads the == operator for the Metadata object such that two Metadata objects are equal, if and only if both their
        field_names, their field_values, and their private_fields are equal.

        Parameters
        ----------
            other : Metadata object
                A Metadata object which is being equated to the current Metadata object.

        Returns
        -------
        True/False : boolean
            A boolean value based on whether both the field_names, the field_values, and the private_fields
            are equal.

        Notes
        -----

        """

        if (isinstance(other, Metadata)):
            return (self.field_names == other.field_names and self.values == other.values and self.private_fields == other.private_fields)
        else:
            raise ImproperDataComparisonError(self, other)

    def have_equal_fields(self,other):
        """
        Determines if the field names and private fields of two Metadata objects are equal.

        Parameters
        ----------
            other : Metadata object
                A Metadata object which is being equated to the current Metadata object's field names and private fields

        Returns
        -------
        True/False : boolean
            A boolean value based on whether both the field_names and private_fields are equal.

        Notes
        -----

        """

        if (isinstance(other, Metadata)):
            if(self.private_fields != other.private_fields and len(self.private_fields) == len(other.private_fields)):
                raise PrivateMetadataFieldMismatchError(self, other)
            return (self.field_names == other.field_names and self.private_fields == other.private_fields)
        else:
            raise ImproperMetadataComparisonError(self, other)

    def getAdjustedFieldNames(self):
        """
        Provides the field names of the current Metadata object with the privatization symbol in the first
        index of the name string if it is a private field.


        Returns
        -------
        field_names_with_private_symbol : List of str
            A list of strings representing the field names but with a privatization symbol at the front of the name if the field is
            private

        Notes
        -----

        """

        field_names_with_private_symbol = []
        for i in range(len(self.field_names)):
            if (self.private_fields[i]):
                field_names_with_private_symbol.append(Metadata.privatization_symbol + self.field_names[i])
            else:
                field_names_with_private_symbol.append(self.field_names[i])
        return field_names_with_private_symbol

    @classmethod
    def createFromDictionary(cls, data_dict):
        data_field_names = list(data_dict.keys())
        data_values = list(data_dict.values())
        return Metadata(data_field_names, data_values)
