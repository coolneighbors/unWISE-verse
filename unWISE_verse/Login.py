"""
Created on Friday, June 7th

@authors: Austin Humphreys
"""

from copy import copy
import os

class Login:
    def __init__(self, username='', password=''):
        """
        Construct a Login object, a simple way to store a Zooniverse user's username and password.

        Parameters
        ----------
            username : str
                A string representing the username of a user on Zooniverse
                Defaults to empty
            password : str
                A string representing the password of the same user on Zooniverse
                Defaults to empty
        Notes
        -----
            This object and the login process probably could be made more secure, but this doesn't seem very necessary
            if the login is done locally and for our own purposes
        """
        
        self.username = copy(username)
        self.password = copy(password)

    def save(self, filename='login.pickle'):
        """
        Save the Login object as a pickle file.

        Parameters
        ----------
            filename : str
                A string representing the name of the file to save the Login object as
                Defaults to 'login.pickle'
        """

        import pickle
        with open(filename, 'wb') as file:
            pickle.dump(self, file)

    @staticmethod
    def load(filename='login.pickle'):
        """
        Load a Login object from a pickle file.

        Parameters
        ----------
            filename : str
                A string representing the name of the file to load the Login object from
                Defaults to 'login.pickle'
        """

        import pickle
        with open(filename, 'rb') as file:
            login = pickle.load(file)
            return login

    @staticmethod
    def loginExists(filename='login.pickle'):
        """
        Check if a Login object exists in a pickle file.

        Parameters
        ----------
            filename : str
                A string representing the name of the file to load the Login object from
                Defaults to 'login.pickle'
        """

        return os.path.isfile(filename)