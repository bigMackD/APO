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
        self.editedImageData = []  # Edited image [path, editable_tada, list(PIL_DATA)]
        self.saveHelperImageData = []  # When saving edited image to file, image from this variable is used
        self.cvImage = None  # image as cv2 object, required for some operations
        self.histogramData = None  # Data used for creating histograms

        self.pilImageData = None  # Image data in Image format
        self.allOpenImagesData = {}  # keys: names of open windows, value: image objects.
        self.imageHelper = ImageHelper()
        self.window = None;


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
            helper_index = 0
            while title in parent.allOpenImagesData.keys():
                helper_index += 1
                title = f"Obraz pierwotny ({str(helper_index)}) - {os.path.basename(imagePath)}"
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
            parent.editedImageData = [parent.loadedImageData[0], parent.loadedImageData[1]]
            parent.allOpenImagesData[title] = Image.open(imagePath)
            picture_label = tk.Label(window)
            picture_label.configure(image=render)
            picture_label.pack()
            window.mainloop()

            def on_closing():
                del parent.allOpenImagesData[title]  # remove image from list of open images
                window.destroy()

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
        plt.ion()

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

        # get each channel
        red_channel = [i[0] for i in img[1]]
        green_channel = [i[1] for i in img[1]]
        blue_channel = [i[2] for i in img[1]]

        # get each value
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
        """

        if parent.loadedImageType == 'gs3ch':
            # gets values of only first channel of greyscale 3 channel type image
            img = [parent.histogramData[1][i][0] for i in range(len(parent.histogramData[1]))]
        else:
            img = parent.histogramData[1]  # list containing image luminence values

        # List with pixel occurrences of each luminance value
        values_count = [0 for i in range(256)]
        for value in img:
            values_count[int(value)] += 1
        x_axis = list([i for i in range(256)])
        y_axis = values_count

        plt.title(f"Histogram - {parent.histogramData[0]}")
        plt.bar(x_axis, y_axis)
        plt.show()


class Lab2MenuDropdown(tk.Menu):
    def __init__(self):
        tk.Menu.__init__(self, tearoff=False)

    def stretchHistogram(self, parent):
        """
        Stretches the histogram to max range (to 0-255)
        """
        self.stretchHistogramCalculations(parent, 0, 255)

    def stretchHistogramCalculations(self, parent, l_min, l_max):
        values_count = [0 for i in range(256)]
        for value in parent.loadedImageData[1]:
            values_count[value] += 1

        for index, number in enumerate(values_count):
            if number:
                first_nonzero_index = index
                break
        for index, number in enumerate(values_count[::-1]):
            if number:
                first_nonzero_index_reverse = 255 - index
                break

        for index in range(len(parent.edited_image_data[1])):
            if parent.editedImageData[1][index] < l_min:
                parent.editedImageData[1][index] = l_min
            if parent.editedImageData[1][index] > l_max:
                parent.editedImageData[1][index] = l_max
            else:
                parent.editedImageData[1][index] = \
                    ((parent.editedImageData[1][index] - first_nonzero_index) * l_max) / \
                    (first_nonzero_index_reverse - first_nonzero_index)
        parent.saveHelperImageData = Image.new(parent.loadedImageMode,
                                               parent.loadedImageData[2].size)

        parent.editedImageData = list(parent.editedImageData)
        parent.saveHelperImageData.putdata(tuple(parent.editedImageData[1]))
        self.histogram_stretch_result_window(parent)

    def histogram_stretch_result_window(self, parent):
        stretch_result_window = tk.Toplevel(parent)
        img_title = "Obraz wynikowy - rozciąganie"

        helper_index = 0
        while img_title in parent.all_open_image_data.keys():
            helper_index += 1
            img_title = "Obraz wynikowy - rozciąganie " + f"({str(helper_index)})"
        stretch_result_window.title(img_title)

        def on_closing():
            del parent.all_open_image_data[img_title]
            stretch_result_window.destroy()

        stretch_result_window.protocol("WM_DELETE_WINDOW", on_closing)

        parent.pil_image_data = Image.new(parent.loaded_image_mode,
                                          parent.loaded_image_data[2].size)
        parent.pil_image_data.putdata(parent.edited_image_data[1])
        parent.all_open_image_data[img_title] = parent.pil_image_data
        picture_label = tk.Label(stretch_result_window)
        picture_label.pack()

        parent.histogram_image_data = ["Stretched", parent.pil_image_data.getdata()]
        selected_picture = ImageTk.PhotoImage(parent.pil_image_data)
        picture_label.configure(image=selected_picture)
        stretch_result_window.mainloop()

    def stretchHistogramFromTo(self, parent):
        # creating UI
        self.strechHistogramInputWindow = tk.Toplevel(parent)
        self.strechHistogramInputWindow.resizable(False, False)
        self.strechHistogramInputWindow.title("Rozciąganie histogramu")
        self.strechHistogramInputWindow.focus_set()

        stretchSettingsBox = tk.Frame(self.strechHistogramInputWindow, width=150, height=150)

        fromMinLabel = tk.Label(stretchSettingsBox, text="Od - Min", padx=10)
        fromMaxLabel = tk.Label(stretchSettingsBox, text="Od - Max", padx=10)

        fromMinInput = tk.Entry(stretchSettingsBox, width=10)
        fromMaxInput = tk.Entry(stretchSettingsBox, width=10)

        toMinLabel = tk.Label(stretchSettingsBox, text="Do - Min", padx=10)
        toMaxLabel = tk.Label(stretchSettingsBox, text="Do - Max", padx=10)
        toMinInput = tk.Entry(stretchSettingsBox, width=10)
        toMaxInput = tk.Entry(stretchSettingsBox, width=10)

        button_area = tk.Frame(self.strechHistogramInputWindow, width=100, pady=10)
        button = tk.Button(button_area, text="Wykonaj", width=10,
                           command=lambda: self.calculateHistogramStretchFromTo(parent,
                                                                                fromMinInput.get(),
                                                                                fromMaxInput.get(),
                                                                                toMinInput.get(),
                                                                                toMaxInput.get()))

        button.pack()
        stretchSettingsBox.grid(column=0, row=0)
        fromMinLabel.grid(column=0, row=0, padx=(25, 5))
        fromMaxLabel.grid(column=1, row=0, padx=(5, 15))
        toMinLabel.grid(column=3, row=0, padx=(15, 5))
        toMaxLabel.grid(column=4, row=0, padx=(5, 20))

        fromMinInput.grid(column=0, row=1, padx=(20, 5))
        fromMaxInput.grid(column=1, row=1, padx=(5, 15))
        toMinInput.grid(column=3, row=1, padx=(15, 5))
        toMaxInput.grid(column=4, row=1, padx=(5, 20))
        button_area.grid(column=0, row=1)

    def calculateHistogramStretchFromTo(self, parent, from_min, from_max, to_min, to_max):
        try:
            int(from_min)
            int(from_max)
            int(to_min)
            int(to_max)
        except ValueError:
            print("Wpisana wartosc musi by numerem.")
            return
        for value in [from_min, from_max, to_min, to_max]:
            if not 0 < int(value) < 255:
                print("Wartosc poza zakresem 0-255")
                return
        from_min = int(from_min)
        from_max = int(from_max)
        to_min = int(to_min)
        to_max = int(to_max)
        values_count = [0 for i in range(256)]

        # iterate over each pixel and apply cdf
        for value in parent.loadedImageData[1]:
            values_count[int(value)] += 1
        for index in range(len(parent.editedImageData[1])):
            if parent.editedImageData[1][index] < from_min:
                parent.editedImageData[1][index] = from_min
            if parent.editedImageData[1][index] > from_max:
                parent.editedImageData[1][index] = from_max
            else:
                parent.editedImageData[1][index] = \
                    (((parent.editedImageData[1][index] - from_min) * (to_max - to_min)) /
                     (from_max - from_min)) + to_min
        parent.saveHelperImageData = Image.new(parent.loadedImageMode,
                                               parent.loadedImageData[2].size)
        parent.saveHelperImageData.putdata(parent.editedImageData[1])
        self.histogramStrechFromToResultWindow(parent)

    def histogramStrechFromToResultWindow(self, parent):
        self.strechHistogramInputWindow.destroy()
        stretchResultWindow = tk.Toplevel()
        img_title = "Obraz wynikowy - rozciąganie od zakresu do zakresu"

        helper_index = 0
        while img_title in parent.allOpenImagesData.keys():
            helper_index += 1
            img_title = f"Obraz wynikowy - rozciąganie od zakresu do zakresu({str(helper_index)})"
        stretchResultWindow.title(img_title)

        def on_closing():
            del parent.allOpenImagesData[img_title]
            stretchResultWindow.destroy()

        stretchResultWindow.protocol("WM_DELETE_WINDOW", on_closing)
        parent.allOpenImagesData[img_title] = list(parent.editedImageData[1])
        parent.pilImageData = Image.new(parent.loadedImageMode,
                                        parent.loadedImageData[2].size)
        parent.pilImageData.putdata(parent.editedImageData[1])
        picture_label = tk.Label(stretchResultWindow)
        picture_label.pack()

        parent.histogram_image_data = ["Stretched", parent.pilImageData.getdata()]
        selected_picture = ImageTk.PhotoImage(parent.pilImageData)
        parent.histogramData = ["Rozciaganie histogramu - ", parent.pilImageData.getdata()]
        picture_label.configure(image=selected_picture)
        stretchResultWindow.mainloop()

    def equalizeImage(self, parent):
        # get cdf
        def calculateCumulativeDistribution(image_list):
            cumulativeDistribution = {}
            image_list_sorted = sorted(image_list)
            for number in image_list:
                if number in cumulativeDistribution.keys():
                    continue
                cumulativeDistribution[number] = countSmallerNumbers(number, image_list_sorted)
            return cumulativeDistribution

        def countSmallerNumbers(number, inp_list):
            count = 0
            for i in inp_list:
                if i <= number:
                    count += 1
                else:
                    return count
            return count

        cumulativeDistribution = calculateCumulativeDistribution(parent.loadedImageData[1])

        # Lowest value from cumulative distribution other than 0
        minCumulativeDistribution = min(list(filter(lambda x: x != 0, cumulativeDistribution.values())))

        m = parent.loadedImageData[2].size[0]
        n = parent.loadedImageData[2].size[1]

        def calculateEqualizedValue(value):
            return round(((cumulativeDistribution[value] - minCumulativeDistribution) / (
                        (m * n) - minCumulativeDistribution)) * 255)

        # appends cdf to each pixel
        def createEqualizedImage(original):
            result = []
            for pixel in original:
                result.append(calculateEqualizedValue(pixel))
            return result

        equalizedImage = createEqualizedImage(parent.loadedImageData[1])

        equalizeResultWindow = tk.Toplevel(parent)
        imgageTitle = "Obraz wynikowy - equalizacja"

        helper_index = 0
        while imgageTitle in parent.allOpenImagesData.keys():
            helper_index += 1
            imgageTitle = "Obraz wynikowy - equalizacja " + f"({str(helper_index)})"
        equalizeResultWindow.title(imgageTitle)

        def on_closing():
            del parent.allOpenImagesData[imgageTitle]
            equalizeResultWindow.destroy()

        equalizeResultWindow.protocol("WM_DELETE_WINDOW", on_closing)

        picture_label = tk.Label(equalizeResultWindow)
        picture_label.pack()

        parent.pilImageData = Image.new(parent.loadedImageMode,
                                        parent.loadedImageData[2].size)
        parent.pilImageData.putdata(equalizedImage)
        parent.allOpenImagesData[imgageTitle] = parent.pilImageData

        parent.saveHelperImageData = Image.new(parent.loadedImageMode,
                                               parent.loadedImageData[2].size)
        parent.saveHelperImageData.putdata(equalizedImage)
        parent.histogramData = ["Equalizacja - ", parent.pilImageData.getdata()]
        selectedPicture = ImageTk.PhotoImage(parent.pilImageData)
        picture_label.configure(image=selectedPicture)
        equalizeResultWindow.mainloop()

    def negateImage(self, parent):
        """ Negate image"""
        minPixelValue = parent.loadedImageData[1][0]
        maxPixelValue = parent.loadedImageData[1][0]
        imageNegated = list(parent.loadedImageData[1])

        # Get min and max pixel values
        for pixel in parent.loadedImageData[1]:
            if pixel > maxPixelValue:
                maxPixelValue = pixel
            if pixel < minPixelValue:
                minPixelValue = pixel

        # Iterate and negate each pixel
        for index in range(len(parent.loadedImageData[1])):
            imageNegated[index] = maxPixelValue - parent.loadedImageData[1][index]

        negateResultWindow = tk.Toplevel(parent)
        imageTitle = "Obraz wynikowy - negacja"

        index = 0
        while imageTitle in parent.allOpenImagesData.keys():
            index += 1
            imageTitle = f"Obraz wynikowy - negacja({str(index)})"
        negateResultWindow.title(imageTitle)

        def on_closing():
            del parent.allOpenImagesData[imageTitle]
            negateResultWindow.destroy()

        negateResultWindow.protocol("WM_DELETE_WINDOW", on_closing)

        pictureLabel = tk.Label(negateResultWindow)
        pictureLabel.pack()
        parent.pilImageData = Image.new(parent.loadedImageMode,
                                        parent.loadedImageData[2].size)
        parent.pilImageData.putdata(imageNegated)
        parent.allOpenImagesData[imageTitle] = parent.pilImageData
        parent.saveHelperImageData = Image.new(parent.loadedImageMode,
                                               parent.loadedImageData[2].size)
        parent.saveHelperImageData.putdata(imageNegated)
        parent.histogramData = ["Negacja - ", parent.pilImageData.getdata()]
        selectedPicture = ImageTk.PhotoImage(parent.pilImageData)
        pictureLabel.configure(image=selectedPicture)
        negateResultWindow.mainloop()

    def thresholdImage(self, parent):
        self.thresholdImageSettings = tk.Toplevel(parent)
        self.thresholdImageSettings.title("Ustawienia progowania")
        self.thresholdImageSettings.resizable(False, False)
        self.thresholdImageSettings.geometry("300x80")
        self.thresholdImageSettings.focus_set()

        label = tk.Label(self.thresholdImageSettings, text="Próg (od 1 do 255)", justify=tk.LEFT, anchor='w')

        entry = tk.Entry(self.thresholdImageSettings, width=10)
        entry.insert(0, "1")
        button = tk.Button(self.thresholdImageSettings, text="Wykonaj", width=10,
                           )

        label.pack()
        entry.pack()
        button.pack()

    def stretchHistogram(self, parent):
        """
        Stretches the histogram to max range (to 0-255)
        """
        self.histogramStretchCalculations(parent, 0, 255)

    def histogramStretchCalculations(self, parent, l_min, l_max):
        values_count = [0 for i in range(256)]
        for value in parent.loadedImageData[1]:
            values_count[value] += 1

        for index, number in enumerate(values_count):
            if number:
                first_nonzero_index = index
                break
        for index, number in enumerate(values_count[::-1]):
            if number:
                first_nonzero_index_reverse = 255 - index
                break

        for index in range(len(parent.editedImageData[1])):
            if parent.editedImageData[1][index] < l_min:
                parent.editedImageData[1][index] = l_min
            if parent.editedImageData[1][index] > l_max:
                parent.editedImageData[1][index] = l_max
            else:
                parent.editedImageData[1][index] = \
                    ((parent.editedImageData[1][index] - first_nonzero_index) * l_max) / \
                    (first_nonzero_index_reverse - first_nonzero_index)
        parent.saveHelperImageData = Image.new(parent.loadedImageMode,
                                                  parent.loadedImageData[2].size)

        parent.editedImageData = list(parent.editedImageData)
        parent.saveHelperImageData.putdata(tuple(parent.editedImageData[1]))
        self.histogramStretchResultWindow(parent)

    def histogramStretchResultWindow(self, parent):
        stretchResultsWindow = tk.Toplevel(parent)
        imageTitle = "Obraz wynikowy - rozciąganie"

        helper_index = 0
        while imageTitle in parent.allOpenImagesData.keys():
            helper_index += 1
            imageTitle = "Obraz wynikowy - rozciąganie " + f"({str(helper_index)})"
        stretchResultsWindow.title(imageTitle)

        def on_closing():
            del parent.allOpenImagesData[imageTitle]
            stretchResultsWindow.destroy()

        stretchResultsWindow.protocol("WM_DELETE_WINDOW", on_closing)

        parent.pilImageData = Image.new(parent.loadedImageMode,
                                          parent.loadedImageData[2].size)
        parent.pilImageData.putdata(parent.editedImageData[1])
        parent.allOpenImagesData[imageTitle] = parent.pilImageData
        pictureLabel = tk.Label(stretchResultsWindow)
        pictureLabel.pack()

        parent.histogram_image_data = ["Stretched", parent.pilImageData.getdata()]
        selectedPicture = ImageTk.PhotoImage(parent.pilImageData)
        parent.histogramData = ["Rozciaganie - ", parent.pilImageData.getdata()]
        pictureLabel.configure(image=selectedPicture)
        stretchResultsWindow.mainloop()


class Lab3MenuDropdown(tk.Menu):
    def __init__(self):
        tk.Menu.__init__(self, tearoff=False)

    def addImages(self, parent):
        """
        Add the two images
        """
        for key, value in parent.allOpenImagesData.items():
            test = value.getData();
            bk = 1;


class Scaling(tk.Menu):
    def __init__(self):
        tk.Menu.__init__(self, tearoff=False)

    def resize(self, parent, fx, fy):
        """
        Resize the image and opens in a new window
        """
        imagePath = parent.loadedImageData[2].filename;
        title = f"Obraz skalowany - {os.path.basename(imagePath)}"
        imgScaled = cv2.resize(parent.cvImage, (0, 0), fx=fx, fy=fy)
        cv2.imshow(title, imgScaled)


class MenuTopBar(tk.Menu):
    def __init__(self, parent: Program):
        tk.Menu.__init__(self, parent, tearoff=False)

        self.menu = tk.Menu(self, tearoff=0)
        self.lab1menu = tk.Menu(self, tearoff=0)
        self.lab2menu = tk.Menu(self, tearoff=0)
        self.lab3menu = tk.Menu(self, tearoff=0)
        self.scalingMenu = tk.Menu(self, tearoff=0)
        self.fill(parent)

        self.fileMenuDropdown = FileMenuDropdown()
        self.lab1MenuDropdown = Lab1MenuDropdown()
        self.lab2MenuDropdown = Lab2MenuDropdown()
        self.lab3MenuDropdown = Lab3MenuDropdown()
        self.resizeDropdown = Scaling()

    def fill(self, parent: Program):
        self.add_cascade(label="Plik", menu=self.menu)
        self.menu.add_command(label="Otwórz", command=lambda: self.fileMenuDropdown.loadImage(parent))
        self.menu.add_command(label="Zapisz", command=lambda: self.fileMenuDropdown.saveImage(parent))
        self.menu.add_command(label="Duplikuj", command=lambda: self.fileMenuDropdown.duplicateImage(parent))

        self.add_cascade(label="Lab1", menu=self.lab1menu)
        self.lab1menu.add_command(label="Histogram", command=lambda: self.lab1MenuDropdown.showHistogram(parent))

        self.add_cascade(label="Lab2", menu=self.lab2menu)
        self.lab2menu.add_command(label="Rozciaganie histogramu",
                                  command=lambda: self.lab2MenuDropdown.stretchHistogram(parent))
        self.lab2menu.add_command(label="Rozciaganie histogramu w zakresie",
                                  command=lambda: self.lab2MenuDropdown.stretchHistogramFromTo(parent))
        self.lab2menu.add_command(label="Wyrownywanie przez eq histogramu",
                                  command=lambda: self.lab2MenuDropdown.equalizeImage(parent))
        self.lab2menu.add_command(label="Negacja obrazu",
                                  command=lambda: self.lab2MenuDropdown.negateImage(parent))
        self.lab2menu.add_command(label="Progowanie obrazu",
                                  command=lambda: self.lab2MenuDropdown.thresholdImage(parent))

        self.add_cascade(label="Lab3", menu=self.lab3menu)
        self.lab3menu.add_command(label="Dodawanie obrazów z wysyceniem",
                                  command=lambda: self.lab3MenuDropdown.addImages(parent)
                                  )

        self.add_cascade(label="Skalowanie", menu=self.scalingMenu)
        self.scalingMenu.add_command(label="200%", command=lambda: self.resizeDropdown.resize(parent, 4, 4))
        self.scalingMenu.add_command(label="150%", command=lambda: self.resizeDropdown.resize(parent, 2.5, 2.5))
        self.scalingMenu.add_command(label="100%", command=lambda: self.resizeDropdown.resize(parent, 2, 2))
        self.scalingMenu.add_command(label="50%", command=lambda: self.resizeDropdown.resize(parent, 0.5, 0.5))
        self.scalingMenu.add_command(label="25%", command=lambda: self.resizeDropdown.resize(parent, 0.25, 0.25))
        self.scalingMenu.add_command(label="20%", command=lambda: self.resizeDropdown.resize(parent, 0.2, 0.2))
        self.scalingMenu.add_command(label="10%", command=lambda: self.resizeDropdown.resize(parent, 0.1, 0.1))


if __name__ == "__main__":
    app = Program()
    app.mainloop()
