# Errors
class InvalidTextHeaderError(Exception):
    def __init__(self, header):
        super(InvalidTextHeaderError, self).__init__("The number of lines in the provided header: " + str(header.name))

class Header:
    def __init__(self,data_fields,metadata_fields):
        self.data_fields = data_fields
        self.metadata_fields = metadata_fields

    @classmethod
    def create_header_from_text_file(cls, header_filename, delimiter= " "):
        with open(header_filename) as header:
            line_count = 1;
            data_fields = []
            metadata_fields = []
            for line in header:
                if(line_count == 1):
                    data_fields = line.split(sep=delimiter)
                elif(line_count == 2):
                    metadata_fields = line.split(sep=delimiter)
                else:
                    raise InvalidTextHeaderError(header)
                print(data_fields)
                print(metadata_fields)
                line_count = line_count + 1





