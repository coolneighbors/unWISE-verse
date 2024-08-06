from tkinter import ttk
import tkinter as tk
from tkinter.colorchooser import askcolor


class InputField:
    separator = "~"
    valid_input_types = [int, float, str, bool, list, tuple, dict]

    def __init__(self, label, type, input_type, additional_attributes):
        self.label = label
        self.type = type
        self.input_type = input_type
        self.additional_attributes = additional_attributes

        # Verify that none of these contain the separator character
        if(self.separator in str(self.label)):
            raise ValueError(f"Separator character {self.separator} is not allowed in the label attribute.")
        if(self.separator in str(self.type)):
            raise ValueError(f"Separator character {self.separator} is not allowed in the type attribute.")
        if(self.separator in str(self.input_type)):
            raise ValueError(f"Separator character {self.separator} is not allowed in the input_type attribute.")
        if(self.separator in str(self.additional_attributes)):
            raise ValueError(f"Separator character {self.separator} is not allowed in the additional_attributes attribute.")

    def __str__(self):
        # Return the formatted entry string based on the type, input type, additional attributes, and default values
        formatted_entry_string = f"{repr(self.label)}{self.separator}{repr(self.type)}{self.separator}{repr(self.input_type)}{self.separator}{repr(self.additional_attributes)}"
        return formatted_entry_string

    def __repr__(self):
        representation_string = f"InputField({repr(self.label)}, {repr(self.type)}, {repr(self.input_type)}, {repr(self.additional_attributes)})"
        return representation_string

    def create(self, window, variable, **kwargs):
        """
        Creates the input field in the master widget, depending on the type of input field. This method should be overridden by subclasses.

        Parameters
        ----------
        window : tk.Tk
            Window object to create the input field in
        variable : tk.Variable
            Variable to store the value of the input field
        kwargs : dict
            Additional keyword arguments to pass to the input field object

        Returns
        -------
        frame : ttk.Frame
            Frame object that contains the input field
        input_field : tk.Widget
            Input field object that was created

        """

        raise NotImplementedError("This method should be overridden by subclasses for the specific implementation of the input field.")

    @classmethod
    def createInputFieldString(cls, label, type, input_type, additional_attributes):

        # Verify that label is a string
        if(not isinstance(label, str)):
            raise ValueError(f"Label {label} must be a string.")

        # Verify that type is a tk.Widget
        if(not issubclass(type, tk.Widget)):
            raise ValueError(f"Type {type} must be a subclass of tk.Widget.")

        # Verify that input_type is a valid input type
        if(input_type not in cls.valid_input_types):
            raise ValueError(f"Input type {input_type} is not valid. Must be one of {cls.valid_input_types}")

        # Verify that additional_attributes is a dictionary
        if(not isinstance(additional_attributes, dict)):
            raise ValueError(f"Additional attributes {additional_attributes} must be a dictionary.")


        return f"{repr(label)}{cls.separator}{repr(type)}{cls.separator}{repr(input_type)}{cls.separator}{repr(additional_attributes)}"

    @classmethod
    def createInputFieldFromString(cls, input_field_string):
        return eval(input_field_string)

class Entry(InputField):
    valid_input_types = [int, float, str]
    def __init__(self, label, input_type, background_color_hex = "#FFF8E7", hide_text=False):

        if(input_type not in self.valid_input_types):
            raise ValueError(f"Input type {input_type} is not valid. Must be one of {self.valid_input_types}")
        if(input_type not in self.valid_input_types):
            raise ValueError(f"Input type {input_type} is not valid. Must be one of {self.valid_input_types}")

        super().__init__(label, tk.Entry, input_type, additional_attributes={"background_color_hex" : background_color_hex, "hide_text": hide_text})

    def create(self, window, variable, **kwargs):

        # Additional attributes
        background_color = self.additional_attributes["background_color_hex"]
        hide_text = self.additional_attributes["hide_text"]

        # Default value
        placeholder_text = ''

        # Set the style of the frame
        style = ttk.Style(window)
        style.configure("BW.TFrame", background=background_color)

        # Create the input frame
        frame = ttk.Frame(master=window, style="BW.TFrame")

        def on_focus_in(event):
            if entry.get() == placeholder_text:
                entry.delete(0, tk.END)
                entry.config(foreground='black')

        def on_focus_out(event):
            if entry.get() == '':
                entry.insert(0, placeholder_text)
                entry.config(foreground='grey')

        def on_map(event):
            if entry.get() == '':
                entry.insert(0, placeholder_text)
                entry.config(foreground='grey')

        # Create the entry field
        if (not hide_text):
            entry = ttk.Entry(master=frame, textvariable=variable, **kwargs)
        else:
            entry = ttk.Entry(master=frame, show='*', textvariable=variable, **kwargs)

        style.configure("BW.TLabel", background=background_color)

        if (self.label != ''):
            label_obj = ttk.Label(master=frame, text=self.label, style="BW.TLabel")
            label_obj.grid(row=0, column=0)
            entry.grid(row=1, column=0)
        else:
            entry.grid(row=0, column=0)

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
        entry.bind("<Map>", on_map)

        return frame, entry


class OptionMenu(InputField):
    valid_input_types = [int, float, str]
    def __init__(self, label, input_type, options_list, background_color_hex = "#FFF8E7"):

        if(input_type not in self.valid_input_types):
            raise ValueError(f"Input type {input_type} is not valid. Must be one of {self.valid_input_types}")

        # Verify that the type of the elements in the options list are the same as the input type
        if(not all(isinstance(option, input_type) for option in options_list)):
            raise ValueError(f"All elements in the options list must be of type {input_type}")

        # Convert the elements of options list to strings
        options_list = [str(option) for option in options_list]

        super().__init__(label, tk.OptionMenu, input_type=input_type, additional_attributes={"options_list": options_list, "background_color_hex": background_color_hex})

    def create(self, window, variable, **kwargs):

        # Additional attributes
        background_color_hex = self.additional_attributes["background_color_hex"]
        options_list = self.additional_attributes["options_list"]

        style = ttk.Style(window)

        style.configure("BW.TFrame", background=background_color_hex)
        frame = ttk.Frame(master=window, style="BW.TFrame")

        style.configure("BW.TMenubutton", background="white")

        default_value = variable.get()

        option_menu = ttk.OptionMenu(frame, variable, default_value, *options_list, **kwargs)
        option_menu.config(style="BW.TMenubutton")
        style.configure("BW.TLabel", background=background_color_hex)
        label = ttk.Label(master=frame, text=self.label, style="BW.TLabel")

        label.grid(row=0, column=0)
        option_menu.grid(row=1, column=0)

        return frame, option_menu

class Checkbutton(InputField):
    def __init__(self, label, background_color_hex = "#FFF8E7"):
        super().__init__(label, tk.Checkbutton, input_type=bool, additional_attributes={"background_color_hex": background_color_hex})

    def create(self, window, variable, **kwargs):
        # Additional attributes
        background_color_hex = self.additional_attributes["background_color_hex"]

        style = ttk.Style(window)

        style.configure("BW.TFrame", background=background_color_hex)
        frame = ttk.Frame(master=window, style="BW.TFrame")

        kwargs.update({"takefocus": 0})

        style.configure("BW.TCheckbutton", background=background_color_hex)
        checkbutton = ttk.Checkbutton(frame, text=self.label, variable=variable, onvalue=True, offvalue=False, style="BW.TCheckbutton", **kwargs)
        checkbutton.grid(row=0, column=0)

        return frame, checkbutton

class Scale(InputField):
    valid_input_types = [int, float]
    def __init__(self, label, input_type, min_value, max_value, background_color_hex = "#FFF8E7"):

        # Verify that the input type is int or float
        if(input_type not in self.valid_input_types):
            raise ValueError(f"Input type {input_type} is not valid. Must be one of {self.valid_input_types}")

        # Verify that the min and max values are the same type as the input type
        if(not isinstance(min_value, input_type)):
            raise ValueError(f"Min value {min_value} must be of type {input_type}")
        if(not isinstance(max_value, input_type)):
            raise ValueError(f"Max value {max_value} must be of type {input_type}")

        # Convert the min, max, and default values to strings
        min_value = str(min_value)
        max_value = str(max_value)

        super().__init__(label, tk.Scale, input_type, additional_attributes={"min_value": min_value, "max_value": max_value, "background_color_hex": background_color_hex})

    def create(self, window, variable, **kwargs):
        # Additional attributes
        min_value = self.additional_attributes["min_value"]
        max_value = self.additional_attributes["max_value"]
        background_color_hex = self.additional_attributes["background_color_hex"]

        style = ttk.Style(window)

        style.configure("BW.TFrame", background=background_color_hex)
        frame = ttk.Frame(master=window, style="BW.TFrame")

        style.configure("BW.TScale", background=background_color_hex)
        scale = ttk.Scale(frame, from_=min_value, to=max_value, variable=variable, orient=tk.HORIZONTAL, style="BW.TScale", **kwargs)
        scale.grid(row=0, column=0)

        return frame, scale

class ColorSelector(InputField):
    def __init__(self, label, selection_title, background_color_hex="#FFF8E7"):

        # Verify that the default value is a tuple of 3 integers
        super().__init__(label, tk.Button, input_type=tuple, additional_attributes={"selection_title": selection_title, "background_color_hex": background_color_hex})

    def create(self, window, variable, **kwargs):
        # Additional attributes
        selection_title = self.additional_attributes["selection_title"]
        background_color_hex = self.additional_attributes["background_color_hex"]

        # Default value

        style = ttk.Style(window)

        style.configure("BW.TFrame", background=background_color_hex)
        frame = ttk.Frame(master=window, style="BW.TFrame")

        kwargs.update({"takefocus": 0})

        def requestColor():
            color_representations = askcolor(title=selection_title, initialcolor=eval(variable.get()))
            if(color_representations == (None, None)):
                return
            else:
                RGB_color, hex_color = color_representations
                variable.set(str(RGB_color))

        button = ttk.Button(frame, text=self.label, command=requestColor, style="BW.TButton", **kwargs)
        button.grid(row=0, column=0)

        return frame, button
