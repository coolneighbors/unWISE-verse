from Data import Metadata

class Discriminator:
    def __init__(self, metadata_list):
        self.metadata_list = metadata_list

    def findValidMetadata(self, field_name, functional_condition):
        valid_metadata_list = []
        for metadata in self.metadata_list:
            if self.isValid(metadata, field_name, functional_condition):
                valid_metadata_list.append(metadata)
        return valid_metadata_list

    def isValid(self, metadata, functional_condition, *field_names):
        for field_name in field_names:
            if not metadata.hasField(field_name):
                return False

        field_name_value_list = []
        for field_name in field_names:
            field_name_value = metadata.getFieldValue(field_name)
            field_name_value_list.append(field_name_value)
        field_name_value_tuple = tuple(field_name_value_list)
        # Keep in mind that when writing the functional_condition, the input values will all be strings.
        # You will need to convert them to the appropriate data type within the functional condition
        # if desirable to do so.
        result = functional_condition(*field_name_value_tuple)
        if(result is None):
            raise Exception("The functional condition returned None. This is not allowed.")
        return result

class SubjectDiscriminator(Discriminator):
    def __init__(self, subject_set):
        self.subject_list = []
        for subject in subject_set.subjects:
            self.subject_list.append(subject)
        self.metadata_list = []
        for index, subject in enumerate(self.subject_list):
            subject_metadata = self.getSubjectMetadata(subject)
            subject_metadata.addField("index", index)
            self.metadata_list.append(subject_metadata)
        super().__init__(self.metadata_list)

    def getSubjectMetadata(self, subject):
        metadata = Metadata.createFromDictionary(subject.metadata)
        return metadata

    def findValidSubjects(self, functional_condition, *field_names):
        valid_subject_list = []
        for metadata in self.metadata_list:
            if self.isValid(metadata, functional_condition, *field_names):
                valid_subject_list.append(self.subject_list[metadata.getFieldValue("index")])
        return valid_subject_list
