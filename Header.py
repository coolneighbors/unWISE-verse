# Errors
class InvalidTextHeaderError(Exception):
    def __init__(self, txt_header):
        super(InvalidTextHeaderError, self).__init__("The number of lines in the provided header: " + str(txt_header.name))

class ImproperHeaderComparisonError(Exception):
    def __init__(self, header, other):
        super(ImproperHeaderComparisonError, self).__init__("The objects you are trying to compare are not comparable: " + str(type(header)) + " and " + str(type(other)))

class Header:
    def __init__(self,data_fields,metadata_fields):
        self.data_fields = data_fields
        self.metadata_fields = metadata_fields

    def __eq__(self, other):
        if(isinstance(other,Header)):
            return (self.data_fields == other.data_fields and self.metadata_fields == other.metadata_fields)
        else:
            raise ImproperHeaderComparisonError(self,other)

    def __len__(self):
        return len(self.data_fields) + len(self.metadata_fields)

    def __getitem__(self, index):
        header_list = [*self.metadata_fields,*self.data_fields]
        return header_list[index]

    def __str__(self):
        return "Data Fields: " + str(self.data_fields) + ", " + "Metadata Fields: " + str(self.metadata_fields)

    @classmethod
    def create_header_from_text_file(cls, header_filename, delimiter= " "):
        data_fields = []
        metadata_fields = []
        with open(header_filename) as txt_header:
            line_count = 1;
            for line in txt_header:
                stripped_line = line.strip()
                if(line_count == 1):
                    data_fields = stripped_line.split(sep=delimiter)
                elif(line_count == 2):
                    metadata_fields = stripped_line.split(sep=delimiter)
                else:
                    raise InvalidTextHeaderError(txt_header)
                line_count = line_count + 1
        return Header(data_fields,metadata_fields)





