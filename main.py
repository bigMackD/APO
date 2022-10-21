import os
from math import floor
from time import sleep

from tkinter import ttk
import tkinter as tk
import tkinter.filedialog

import cv2
import matplotlib.pyplot as plt
from PIL import Image, ImageTk
from comtypes.safearray import numpy


class Program(tk.Tk):

    def __init__(self, *args, **kwargs):
        print("hello")

        tk.Tk.__init__(self, *args, **kwargs)

        self.title("ImageProcessor")
        self.geometry("700x100")  # Size of main window
        #
        self.menuTopBar = MenuTopBar(self)
        self.config(menu=self.menuTopBar)  # Adds menu bar to the main window

        self.resize_width = 500
        self.resize_height = 500

        # self.loaded_image_mode = None  # Can be RGB for colour images or L for greyscale
        #
        self.loadedImageData = []  # Original image(from load_image method) [path, editable_tada, tuple(PIL_DATA)
        self.loadedImageType = None  # Can be b, gs, gs3ch, c; binary, greyscale, greyscale 3 channels, colour
        self.loadedImageMode = None  # Can be RGB for colour images or L for greyscale

        self.imageHelper = None
        # self.edited_image_data = []  # Edited image [path, editable_tada, list(PIL_DATA)]
        self.saveHelperImageData = []  # When saving edited image to file, image from this variable is used
        self.cvImage = None  # image as cv2 object, required for some operations
        self.histogramData = None  # Data used for creating histograms

        self.pil_image_data = None  # Image data in Image format
        self.all_open_image_data = {}  # keys: names of open windows, value: image objects.
        self.imageHelper = ImageHelper()

class ImageHelper(tk.Menu):
    def __init__(self):
        tk.Menu.__init__(self, tearoff=False)

    def getColourType(self, parent):
        """
        Checks colour typeo f image
        :param parent:
        :return: string for color type: c, gs, gs3ch, b; colour, greyscale, greyscale 3 channels, binary
        """
        channel_amount = 0
        try:
            test1, test2, test3 = cv2.split(parent.cvImage)  # split channels content into 3 variables
            channel_amount = 3
        except ValueError:
            channel_amount = 1

        if channel_amount == 3:
            ch1, ch2, ch3 = cv2.split(parent.cvImage)  # Split image into 3 images for each channel
            # difference between 2 channels in greyscale 3 channel image results in fully black image
            if (not numpy.any(cv2.subtract(ch1, ch2))) and (not numpy.any(cv2.subtract(ch2, ch3))):
                parent.loadedImageMode = "L"
                return 'gs3ch'
            parent.loadedImageMode = "RGB"
            return "c"
        elif channel_amount == 1:
            for value in parent.loadedImageData[1]:
                binary_values = [0, 255]
                parent.loadedImageMode = "L"
                if isinstance(value, tuple):
                    return 'gs3ch'
                if value not in binary_values:
                    return "gs"  # GreyScale
            return "b"  # Binary


class FileMenuDropdown(tk.Menu):
    def __init__(self):
        tk.Menu.__init__(self, tearoff=False)

    def loadImage(self, parent):
        """
        Opens selected image in separate window
        """
        # Opens menu allowing to select path to picture
        imagePath = tk.filedialog.askopenfilename(initialdir=os.getcwd())

        # Assigns picture to variable
        if imagePath:
            window = tk.Toplevel(parent)  # create window
            title = f"Obraz pierwotny - {os.path.basename(imagePath)}"
            window.title(title)
            parent.cvImage = cv2.imread(imagePath, cv2.IMREAD_UNCHANGED)
            load = Image.open(imagePath)
            load.convert("L")

            if isinstance(list(Image.fromarray(parent.cvImage).getdata())[0], tuple):
                helper = list(Image.fromarray(parent.cvImage).getdata())
                content = [helper[i][0] for i in range(len(helper))]
                parent.loadedImageData = [os.path.basename(imagePath), content, load]
            else:
                parent.loadedImageData = [os.path.basename(imagePath),
                                            list(Image.fromarray(parent.cvImage).getdata()),
                                            load]

            render = ImageTk.PhotoImage(load)
            parent.loadedImageType = parent.imageHelper.getColourType(parent)
            parent.histogramData = [os.path.basename(imagePath), list(load.getdata()), load]
            picture_label = tk.Label(window)
            picture_label.configure(image=render)
            picture_label.pack()
            window.mainloop()

    def saveImage(self, parent):
        """
        Image saving
        """

        img_type = tk.StringVar()
        path = tk.filedialog.asksaveasfilename(filetypes=(('BMP', '.bmp'),
                                                          ('PNG', '.png'),
                                                          ('JPEG', '.jpg')),
                                               typevariable=img_type)
        if path:
            try:
                file_type = img_type.get()
                parent.saveHelperImageData.save(path + "." + file_type.lower(), format=file_type)
            except AttributeError:  # parent.save_helper_image_data is empty
                print("Najpierw edytuj obraz!")

    def duplicateImage(self, parent):
        """
        Image duplicating
        """
        imagePath = parent.loadedImageData[2].filename;
        if imagePath:
            window = tk.Toplevel(parent)
            title = f"Obraz pierwotny - {os.path.basename(imagePath)}"
            window.title(title)
            parent.cvImage = cv2.imread(imagePath, cv2.IMREAD_UNCHANGED)
            load = Image.open(imagePath)
            load.convert("L")

            if isinstance(list(Image.fromarray(parent.cvImage).getdata())[0], tuple):
                helper = list(Image.fromarray(parent.cvImage).getdata())
                content = [helper[i][0] for i in range(len(helper))]
                parent.loadedImageData = [os.path.basename(imagePath), content, load]
            else:
                parent.loadedImageData = [os.path.basename(imagePath),
                                          list(Image.fromarray(parent.cvImage).getdata()),
                                          load]

            render = ImageTk.PhotoImage(load)

            picture_label = tk.Label(window)
            picture_label.configure(image=render)
            picture_label.pack()
            window.mainloop()


class Lab1MenuDropdown(tk.Menu):
    def __init__(self):
        tk.Menu.__init__(self, tearoff=False)

    def showHistogram(self, parent):
        if parent.loadedImageType == 'gs' or \
                parent.loadedImageType == 'b' or \
                parent.loadedImageType == 'gs3ch':
            self.createGreyscaleHistogram(parent)
        else:
            self.createColorHistogram(parent)

    def createColorHistogram(self, parent):
        """
        Splits color image into separate channels and
        displays histogram for each
        """
        if parent.loadedImageType == "gs" or \
                parent.loadedImageType == 'b' or \
                parent.loadedImageType == 'gs3ch':
            return self.createGreyscaleHistogram(parent)
        img = parent.histogramData
        y_axis = [0 for i in range(256)]
        x_axis = [i for i in range(256)]
        red_channel = [i[0] for i in img[1]]
        green_channel = [i[1] for i in img[1]]
        blue_channel = [i[2] for i in img[1]]

        def compute_values_count(channel_name):
            for value in channel_name:
                luminence_value = int(value)
                y_axis[luminence_value] += 1

        compute_values_count(red_channel)

        plt.figure()
        plt.bar(x_axis, y_axis)
        plt.title(f'Histogram - kanał czerwony - {img[0]}')  # Red channel

        y_axis = [0 for i in range(256)]
        compute_values_count(green_channel)
        plt.figure()
        plt.bar(x_axis, y_axis)
        plt.title(f'Histogram - kanał zielony - {img[0]}')  # Green channel

        y_axis = [0 for i in range(256)]
        compute_values_count(blue_channel)
        plt.figure()
        plt.bar(x_axis, y_axis)
        plt.title(f'Histogram - kanał niebieski - {img[0]}')  # Blue channel

        plt.show()

    def createGreyscaleHistogram(self, parent, img=None):
        """
        Displays histogram for greyscale image.
        img=None parameter allows to prevent certain issue
        """
        if parent.loadedImageType == 'gs3ch':
            # gets values of only first channel of greyscale 3 channel type image
            img = [parent.loadedImageData[1][i][0] for i in range(len(parent.loadedImageData[1]))]
        else:
            img = parent.loadedImageData[1]  # list containing image luminence avlues

        # List with occurrences of each luminance value
        values_count = [0 for i in range(256)]
        for value in img:
            values_count[value] += 1

        x_axis = list([i for i in range(256)])
        y_axis = values_count
        plt.title(f"Histogram - {parent.loadedImageData[0]}")
        plt.bar(x_axis, y_axis)
        plt.show()


class Lab2MenuDropdown(tk.Menu):
    def __init__(self):
        tk.Menu.__init__(self, tearoff=False)



class MenuTopBar(tk.Menu):
    def __init__(self, parent: Program):
        tk.Menu.__init__(self, parent, tearoff=False)

        self.menu = tk.Menu(self, tearoff=0)
        self.lab1menu = tk.Menu(self, tearoff=0)
        self.lab2menu = tk.Menu(self, tearoff=0)
        self.fill(parent)

        self.fileMenuDropdown = FileMenuDropdown()
        self.lab1MenuDropdown = Lab1MenuDropdown()
        self.lab2MenuDropdown = Lab2MenuDropdown()

    def fill(self, parent: Program):
        self.add_cascade(label="Plik", menu=self.menu)
        self.menu.add_command(label="Otwórz", command=lambda: self.fileMenuDropdown.loadImage(parent))
        self.menu.add_command(label="Zapisz", command=lambda: self.fileMenuDropdown.saveImage(parent))
        self.menu.add_command(label="Duplikuj", command=lambda: self.fileMenuDropdown.duplicateImage(parent))

        self.add_cascade(label="Lab1", menu=self.lab1menu)
        self.lab1menu.add_command(label="Histogram", command=lambda: self.lab1MenuDropdown.showHistogram(parent))

        self.add_cascade(label="Lab2", menu=self.lab2menu)
        self.lab2menu.add_command(label="Rozciaganie histogramu")
        self.lab2menu.add_command(label="Wyrownywanie przez eq histogramu")


if __name__ == "__main__":
    app = Program()
    app.mainloop()
