import os
from math import floor
from time import sleep

from tkinter import ttk
import tkinter as tk
import tkinter.filedialog

import cv2

from PIL import Image

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
        # self.loaded_image_type = None  # Can be b, gs, gs3ch, c; binary, greyscale, greyscale 3 channels, colour
        # self.loaded_image_mode = None  # Can be RGB for colour images or L for greyscale
        #
        self.imageData = []  # Original image(from load_image method) [path, editable_tada, tuple(PIL_DATA)]
        # self.edited_image_data = []  # Edited image [path, editable_tada, list(PIL_DATA)]
        # self.save_helper_image_data = []  # When saving edited image to file, image from this variable is used
        self.cvImage = None  # image as cv2 object, required for some operations
        # self.histogram_image_data = None  # Data used for creating histograms

        self.pil_image_data = None  # Image data in Image format
        self.all_open_image_data = {}  # keys: names of open windows, value: image objects.


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
            parent.cv2_image = cv2.imread(imagePath, cv2.IMREAD_UNCHANGED)
            image = Image.open(imagePath)
            image.convert("L")
            parent.loaded_image_data = [os.path.basename(img_path), content, image]


class MenuTopBar(tk.Menu):
    def __init__(self, parent: Program):
        tk.Menu.__init__(self, parent, tearoff=False)
        self.menu = tk.Menu(self, tearoff=0)
        self.fill(parent)

        self.fileMenuDropdown = FileMenuDropdown()

    def fill(self, parent: Program):
        """
        Handles adding elements executing specific functions, to the top menu, and submenus
        :param parent: reference to outermost window and its parameters
        """
        self.add_cascade(label="Plik", menu=self.menu)
        self.menu.add_command(label="Otwórz", command=lambda: self.fileMenuDropdown.loadImage(parent))
        # self.menu.add_command(label="Zapisz", command=lambda: self.menu_bar_file.save_image(parent))


if __name__ == "__main__":
    app = Program()
    app.mainloop()
