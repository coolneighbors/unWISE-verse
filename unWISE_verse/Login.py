"""
Created on Friday, June 7th

@authors: Austin Humphreys
"""

from copy import copy
import os

import uuid

# Get the MAC address
device_mac_address = hex(uuid.getnode()).replace('0x', '').upper()

# Format the MAC address
device_mac_address = ':'.join(device_mac_address[i:i+2] for i in range(0, 12, 2))

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
            The Login object encrypts the username and password using the device's MAC address as a key. This means that
            the username and password are not stored in plain text in memory or in a file. If you try to use the Login object
            from a different device, the username and password will not be decrypted correctly. Keep this in mind.
        """

        self.filename = None

        self.__username, self.__password = self.encryptCredentials(copy(username), copy(password))

    @staticmethod
    def encryptCredentials(username, password):
        """
        Encrypt a username and password pair using the device's MAC address as a key.

        Parameters
        ----------
            username : str
                A string representing the username of a user on Zooniverse
            password : str
                A string representing the password of the same user on Zooniverse
        """

        encrypted_username = ""
        encrypted_password = ""

        for i in range(len(username)):
            encrypted_username += chr(ord(username[i]) ^ ord(device_mac_address[i % len(device_mac_address)]))

        for i in range(len(password)):
            encrypted_password += chr(ord(password[i]) ^ ord(device_mac_address[i % len(device_mac_address)]))

        return encrypted_username, encrypted_password

    @staticmethod
    def decryptCredentials(encrypted_username, encrypted_password):
        """
        Decrypt a username and password pair using the device's MAC address as a key.

        Parameters
        ----------
            encrypted_username : str
                A string representing the encrypted username of a user on Zooniverse
            encrypted_password : str
                A string representing the encrypted password of the same user on Zooniverse
        """

        username = ""
        password = ""

        for i in range(len(encrypted_username)):
            username += chr(ord(encrypted_username[i]) ^ ord(device_mac_address[i % len(device_mac_address)]))

        for i in range(len(encrypted_password)):
            password += chr(ord(encrypted_password[i]) ^ ord(device_mac_address[i % len(device_mac_address)]))

        return username, password

    def save(self, filename='login.pickle'):
        """
        Save the Login object as a pickle file.

        Parameters
        ----------
            filename : str
                A string representing the name of the file to save the Login object as
                Defaults to 'login.pickle'
        """

        self.filename = filename

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

    def deleteLoginSave(self):
        """
        Delete the file that the Login object is saved in.
        """

        if(self.filename is not None):
            if(os.path.isfile(self.filename)):
                os.remove(self.filename)

    @property
    def username(self):

        decrypted_username, _ = self.decryptCredentials(self.__username, self.__password)

        return decrypted_username

    @property
    def password(self):

        _, decrypted_password = self.decryptCredentials(self.__username, self.__password)

        return decrypted_password

    @property
    def credentials(self):
        decrypted_username, decrypted_password = self.decryptCredentials(self.__username, self.__password)
        return decrypted_username, decrypted_password