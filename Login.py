"""
Created on Friday, June 7th

@authors: Austin Humphreys
"""

from copy import copy

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