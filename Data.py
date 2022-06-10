# Errors
class FieldAndValueMismatchError(Exception):
    def __init__(self, field_names, values):
        super(FieldAndValueMismatchError, self).__init__("The field names and the values are not the same length: " + str(len(field_names)) + ", " + str(len(values)))

class NonUniqueFieldsError(Exception):
    def __init__(self, field_names):
        super(NonUniqueFieldsError, self).__init__("The field names are not unique for at least one field name: " + str(field_names))

class InvalidMetadataRequestError(Exception):
    def __init__(self, field_name):
        super(InvalidMetadataRequestError, self).__init__("The requested metadata " + "\"" + field_name +  "\"" + " could not be found.")

class ImproperDataComparisonError(Exception):
    def __init__(self, other):
        super(ImproperDataComparisonError, self).__init__("The objects you are trying to compare are not comparable: " + str(type(self)) + " and " + str(type(other)))

class Data:
    def __init__(self,field_names = [],data_values = []):

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
        if(index == -1):
            self.field_names.append(field_name)
            self.values.append(value)
        elif(index >= 0 and index < len(self.field_names)):
            self.field_names.insert(index,field_name)
            self.values.insert(index, field_name)
        else:
            raise IndexError

    def removeField(self, field_name, value):
        pass

class Metadata(Data):
    def __init__(self, field_names = [], metadata_values = []):
        # Checking if any field names are private upon initialization and if they are unique
        private_field_names = []
        for field_name in field_names:
            if(field_name[0] == "!"):
                private_field_names.append(field_name[1:])

        for private_field_name in private_field_names:
            for field_name in field_names:
                if(private_field_name == field_name):
                    raise NonUniqueFieldsError(field_names)

        super(Metadata, self).__init__(field_names,metadata_values)

    def setPrivateValue(self, field_name):
        for i in range(len(self.field_names)):
            name = self.field_names[i]
            if(name == field_name):
                self.field_names[i] = "!" + field_name
                return
            elif(name[0] == "!" and field_name == name[1:]):
                print("Field name " + str(name) + " is already private.")
                return
        raise InvalidMetadataRequestError(field_name)

    def addField(self, field_name, value, index = -1, private = False):
        super().addField(field_name,value,index)
        if(private):
            self.setPrivateValue(field_name)
