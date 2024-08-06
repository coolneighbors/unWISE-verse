import math
import os
import pickle
import re

# Create an error class

class ChunkerError(Exception):
    pass

class PreexistingChunkerError(ChunkerError):
    pass

class NonEmptyChunkingDirectoryError(ChunkerError):
    pass

class Chunker:
    def __init__(self, directory, id, chunk_size=1000, subchunk_size=0):
        """
        Coordinating class for chunking a large dataset into smaller chunks and subchunks.

        Parameters
        ----------
        directory : str
            The directory to create the chunk directories and provide file paths from.
        id : str
            The unique identifier for the chunker.
        chunk_size : int
            The number of subjects to include in each chunk.
        subchunk_size : int
            The number of subjects to include in each subchunk.
        """

        self.directory = directory
        self.id = id
        self.chunk_size = chunk_size
        self.subchunk_size = subchunk_size
        self.current_chunk_index = 0
        self.current_subchunk_index = 0
        self.chunk_count = 0
        self.subchunk_count = 0
        self.total_count = 0

        if(subchunk_size >= chunk_size):
            raise ValueError("Subchunk size must be less than chunk size.")

        # Use a pattern to check if there is a chunker file in the directory
        def find_chunker_files(directory=None):

            if(directory is None):
                directory = os.getcwd()

            # Regular expression pattern for matching the filename
            pattern = re.compile(r"Chunker_\w+\.pickle")

            # List to store the names of matching files
            matching_files = []

            # Iterate over the files in the directory
            for filename in os.listdir(directory):
                # Check if the filename matches the pattern
                if pattern.match(filename):
                    matching_files.append(filename)

            return matching_files

        # Get the names of all the chunker files in the directory
        chunker_files = find_chunker_files()

        if(len(chunker_files) > 0):
            # Iterate over the chunker files
            for chunker_file in chunker_files:
                # Get the id from the filename
                chunker_id = chunker_file.split("_")[1].split(".")[0]
                # Check if the id matches the current id
                if(str(chunker_id) != str(self.id)):
                    # Load the chunker file
                    other_chunker = Chunker.load(chunker_id)

                    if(self.directory == other_chunker.directory):
                        raise PreexistingChunkerError(f"Chunker file with ID '{chunker_id}' shares a directory with the current chunker, this means that there may previous chunking in '{self.directory}' that has not completed. Please delete the chunker file and clear the directory before continuing.")

        # Check if the directory exists and create it if it doesn't
        if (not os.path.exists(self.directory)):
            os.makedirs(self.directory)

        # Check if the directory is empty
        if(len(os.listdir(self.directory)) > 0):
            raise NonEmptyChunkingDirectoryError(f"Directory '{self.directory}' is not empty, please clear the directory before continuing.")

        if (not os.path.exists(self.getChunkDirectory())):
            os.makedirs(self.getChunkDirectory())

    def chunk(self, count):
        self.total_count += count
        self.chunk_count += count
        self.subchunk_count += count

        if(self.subchunk_size > 0):
            if(self.subchunk_count >= self.subchunk_size):
                self.subchunk_count = 0
                self.current_subchunk_index += 1

        if(self.chunk_count >= self.chunk_size):
            self.chunk_count = 0
            self.current_chunk_index += 1
            self.current_subchunk_index = 0

        self.getChunkDirectory()
        self.save()

    def unchunk(self, count):
        self.total_count -= count
        self.chunk_count -= count
        self.subchunk_count -= count

        if(self.subchunk_size > 0):
            if(self.subchunk_count < 0):
                self.subchunk_count = self.subchunk_size - abs(self.subchunk_count)
                self.current_subchunk_index -= math.ceil(count / self.subchunk_size)

        if(self.chunk_count < 0):
            self.chunk_count = self.chunk_size - abs(self.chunk_count)
            self.current_chunk_index -= math.ceil(count / self.chunk_size)
            self.current_subchunk_index = (self.chunk_count // self.subchunk_size)

        self.getChunkDirectory()
        self.save()

    def terminate(self):
        if(self.subchunk_size > 0):
            if(self.subchunk_count == 0):
                subchunk_directory = os.path.join(self.directory, f"Chunk_{self.current_chunk_index}", self.formatSubChunkIndex())
                if(len(os.listdir(subchunk_directory)) == 0):
                    os.rmdir(subchunk_directory)

            if(self.chunk_count == 0):
                chunk_directory = os.path.join(self.directory, f"Chunk_{self.current_chunk_index}")
                if(len(os.listdir(chunk_directory)) == 0):
                    os.rmdir(chunk_directory)
        else:
            if(self.chunk_count == 0):
                chunk_directory = os.path.join(self.directory, f"Chunk_{self.current_chunk_index}")
                if(len(os.listdir(chunk_directory)) == 0):
                    os.rmdir(chunk_directory)

        self.delete(self.id)

    def getChunkDirectory(self):
        if(self.subchunk_size > 0):
            os.makedirs(os.path.join(self.directory, f"Chunk_{self.current_chunk_index}", self.formatSubChunkIndex()), exist_ok=True)
            return os.path.join(self.directory, f"Chunk_{self.current_chunk_index}", self.formatSubChunkIndex())
        else:
            os.makedirs(os.path.join(self.directory, f"Chunk_{self.current_chunk_index}"), exist_ok=True)
            return os.path.join(self.directory, f"Chunk_{self.current_chunk_index}")

    def formatSubChunkIndex(self):
        subchunk_index_format_string = "{:0" + str(len(str(self.chunk_size // self.subchunk_size))) + "}"
        return subchunk_index_format_string.format(self.current_subchunk_index)

    def save(self, directory=None):

        if(directory is None):
            directory = os.getcwd()
        chunker_file_path = os.path.join(directory, f"Chunker_{self.id}.pickle")
        with open(chunker_file_path, "wb") as file:
            pickle.dump(self, file)

    @staticmethod
    def load(id, directory=None):

        if(directory is None):
            directory = os.getcwd()

        chunker_file_path = os.path.join(directory, f"Chunker_{id}.pickle")
        with open(chunker_file_path, "rb") as file:
            return pickle.load(file)

    @staticmethod
    def delete(id, directory=None):

        if(directory is None):
            directory = os.getcwd()

        chunker_file_path = os.path.join(directory, f"Chunker_{id}.pickle")
        os.remove(chunker_file_path)

    @staticmethod
    def exists(id, directory=None):

        if(directory is None):
            directory = os.getcwd()

        chunker_file_path = os.path.join(directory, f"Chunker_{id}.pickle")
        return os.path.exists(chunker_file_path)














