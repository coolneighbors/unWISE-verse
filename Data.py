# Errors
class FieldAndValueMismatchError(Exception):
    def __init__(self, field_names, values):
        super(FieldAndValueMismatchError, self).__init__("The field names and the values are not the same length: " + str(len(field_names)) + ", " + str(len(values)))

class NonExistentFieldError(Exception):
    def __init__(self, field_name):
        super(NonExistentFieldError, self).__init__("The field name trying to be removed is not a field: " + str(field_name))

class NonExistentPrivateFieldError(Exception):
    def __init__(self, field_name):
        super(NonExistentPrivateFieldError, self).__init__("The field name trying to be removed was given as private but is not private: " + str(field_name))

class NonUniqueFieldsError(Exception):
    def __init__(self, field_names):
        super(NonUniqueFieldsError, self).__init__("The field names are not unique for at least one field name: " + str(field_names))

class InvalidMetadataRequestError(Exception):
    def __init__(self, field_name):
        super(InvalidMetadataRequestError, self).__init__("The requested metadata " + "\"" + field_name +  "\"" + " could not be found.")

class ImproperDataComparisonError(Exception):
    def __init__(self, object, other):
        super(ImproperDataComparisonError, self).__init__("The objects you are trying to compare are not comparable: " + str(type(object)) + " and " + str(type(other)))

class ImproperMetadataComparisonError(Exception):
    def __init__(self, object, other):
        super(ImproperMetadataComparisonError, self).__init__("The objects you are trying to compare are not comparable: " + str(type(object)) + " and " + str(type(other)))

class PrivateMetadataFieldMismatchError(Exception):
    def __init__(self, object, other):
        super(PrivateMetadataFieldMismatchError, self).__init__("The metadata objects you are trying to compare have a mismatch in which fields are private: " + str(object) + " and " + str(other))

class InvalidFieldNameError(Exception):
    def __init__(self, field_name):
        super(InvalidFieldNameError, self).__init__("The provided field name has a privatization character (\"!\") after the first privatization character: " + str(field_name))



class Data:
    def __init__(self,field_names = [],data_values = []):

        """
        Constructs a Data object, a container object which resembles a python dictionary except that it is a pair of
        ordered lists rather than directly linked via keys. Additionally, it will only accept unique field names.

        Parameters
        ----------
            project_identifier : str or int
                A generalized identifier for both string-based slugs, defined in the panoptes_client API, or an
                integer ID number associated with a project (can be found on Zooniverse)
            login : Login object
                A login object which holds the login details of the user trying to access Zooniverse. Consists of
                a username and a password.

        Notes
        -----
            The slug identifier only can work if the owner of the project is the one who is logging in
            since the owner's name is a part of the slug.


            A Zooniverse slug is of the form: "owner_username/project-name-with-dashes-for-spaces"

            Change the master manifest header to add new metadata or if you want to increase the total maximum of frames
            Frames are recognized as frames if they start with f and the rest is an integer. Slots them in the the order they appear
            in the master header from left to right
        """

        # Check if the field names are in a 1-1 correspondence with values
        if(len(field_names) != len(data_values)):
            raise FieldAndValueMismatchError(field_names,data_values)
        # Check if the field names are unique
        elif(len(set(field_names)) != len(field_names)):
            raise NonUniqueFieldsError(field_names)
        else:
            self.field_names = field_names
            self.values = data_values

    def __eq__(self, other):
        if (isinstance(other, Data)):
            return (self.field_names == other.field_names and self.values == other.values)
        else:
            raise ImproperDataComparisonError(self, other)

    def have_equal_fields(self,other):
        if (isinstance(other, Data)):
            return (self.field_names == other.field_names)
        else:
            raise ImproperDataComparisonError(self, other)

    def have_equal_values(self,other):
        if (isinstance(other, Data)):
            return (self.values == other.values)
        else:
            raise ImproperDataComparisonError(self, other)

    def __str__(self):
        return "Field Names: " + str(self.field_names) + "\n" + "Values: " + str(self.values)

    def __len__(self):
        return len(self.field_names)

    def addField(self, field_name, value, index = -1):
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
        if (field_name in self.field_names):
            index_to_be_removed = self.field_names.index(field_name)
            self.field_names.pop(index_to_be_removed)
            self.values.pop(index_to_be_removed)
        else:
            raise NonExistentFieldError(field_name)

class Metadata(Data):
    def __init__(self, field_names = [], metadata_values = []):

        # Checking if any field names are private upon initialization and if they are unique
        self.private_fields = [False] * len(field_names)
        for i in range(len(field_names)):
            field_name = field_names[i]
            if(field_name[0] == "!"):
                field_names[i] = field_name[1:]
                check_field_name = field_name[1:]
                if("!" in check_field_name):
                    raise InvalidFieldNameError(field_name)
                self.private_fields[i] = True

        super(Metadata, self).__init__(field_names,metadata_values)

    def setFieldAsPrivate(self, field_name):
        if (field_name in self.field_names):
            field_name_index = self.field_names.index(field_name)
            if(not self.private_fields[field_name_index]):
                self.private_fields[field_name_index] = True
            else:
                print("Field name " + str(field_name) + " is already private.")
            return
        else:
            raise NonExistentFieldError(field_name)

    def isPrivateField(self,field_name):
        if (field_name[0] == "!" and (field_name[1:] in self.field_names)):
            index_of_field_name = self.field_names.index(field_name[1:])
            return self.private_fields[index_of_field_name]
        elif(field_name in self.field_names):
            index_of_field_name = self.field_names.index(field_name)
            return self.private_fields[index_of_field_name]
        else:
            raise NonExistentFieldError(field_name)

    def isPublicField(self,field_name):
        return not self.isPrivateField(field_name)

    def addField(self, field_name, value, index = -1, make_private = False):
        if (index == -1):
            self.private_fields.append(False)
        elif (index >= 0 and index < len(self.field_names)):
            self.private_fields.insert(index, False)

        if (field_name[0] == "!"):
            field_name = field_name[1:]
            make_private = True

        super().addField(field_name, value, index)

        if(make_private):
            self.setFieldAsPrivate(field_name)

    def removeField(self, field_name):
        if(field_name[0] == "!" and (field_name[1:] in self.field_names)):
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

    def have_equal_fields(self,other):
        if (isinstance(other, Metadata)):
            if(self.private_fields != other.private_fields):
                raise PrivateMetadataFieldMismatchError(self, other)
            return (self.field_names == other.field_names and self.private_fields == other.private_fields)
        else:
            raise ImproperMetadataComparisonError(self, other)

    def getAdjustedFieldNames(self):
        field_names_with_private_symbol = []
        for i in range(len(self.field_names)):
            if (self.private_fields[i]):
                field_names_with_private_symbol.append("!" + self.field_names[i])
            else:
                field_names_with_private_symbol.append(self.field_names[i])
        return field_names_with_private_symbol
    def __str__(self):
        field_names_with_private_symbol = self.getAdjustedFieldNames()
        return "Field Names: " + str(field_names_with_private_symbol) + "\n" + "Values: " + str(self.values)
