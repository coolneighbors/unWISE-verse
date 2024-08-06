import os

from PIL import Image


class ImageCrafter:
    def __init__(self):
        pass

    def splice(self, image1_filepath, image2_filepath, destination_filepath, orientation='horizontal'):
        """
        Splices two images together into a single image with the specified orientation

        Parameters
        ----------
        image1_filepath : str
            The file path of the first image
        image2_filepath : str
            The file path of the second image
        destination_filepath : str
            The file path of the spliced image

        Returns
        -------
        file_path : str
            The file path of the spliced image

        Notes
        -----
        The orientation parameter can be set to "horizontal" or "h" to splice the images together horizontally, or "vertical" or "v" to splice the images together vertically
        Horizontal splicing will place the second image to the right of the first image
        Vertical splicing will place the second image below the first image

        """

        divider_color = (0, 0, 0)
        divider_width = 10

        # Connects two images together at the specified coordinates
        with Image.open(image1_filepath) as image1:
            with Image.open(image2_filepath) as image2:
                combined_image = None

                if(orientation.lower() == "horizontal" or orientation.lower() == "h"):
                    # Calculate the size of the combined image
                    total_width = image1.width + image2.width
                    total_height = max(image1.height, image2.height)

                    # Create a new image with the combined size
                    combined_image = Image.new('RGB', (total_width, total_height))

                    # Paste the first image at (0, 0)
                    combined_image.paste(image1, (0, 0))

                    # Paste the second image to the right of the first image
                    combined_image.paste(image2, (image1.width, 0))

                    # Add a divider line between the images with the specified color and divider width
                    for y in range(total_height):
                        for x in range(-divider_width//2, divider_width//2):
                            combined_image.putpixel((image1.width + x, y), divider_color)
                elif(orientation.lower() == "vertical" or orientation.lower() == "v"):
                    # Calculate the size of the combined image
                    total_width = max(image1.width, image2.width)
                    total_height = image1.height + image2.height

                    # Create a new image with the combined size
                    combined_image = Image.new('RGB', (total_width, total_height))

                    # Paste the first image at (0, 0)
                    combined_image.paste(image1, (0, 0))

                    # Paste the second image below the first image
                    combined_image.paste(image2, (0, image1.height))

                    # Add a divider line between the images
                    for x in range(total_width):
                        for y in range(-divider_width//2, divider_width//2):
                            combined_image.putpixel((x, image1.height + y), divider_color)
                else:
                    raise ValueError("Invalid orientation: " + orientation)

                if(combined_image is not None):
                    # Save the combined image to the destination file path
                    combined_image.save(destination_filepath)
                    return destination_filepath
