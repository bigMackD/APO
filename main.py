import os
from math import floor
from time import sleep

from tkinter import ttk
import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox

import csv

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

    def loadImage(self, parent, type):
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
            parent.cvImage = cv2.imread(imagePath, type)
            load = Image.open(imagePath)
            helper = list(Image.fromarray(parent.cvImage).getdata())
            if isinstance(list(Image.fromarray(parent.cvImage).getdata())[0], tuple):
                content = [helper[i][0] for i in range(len(helper))]
                parent.loadedImageData = [os.path.basename(imagePath), content, load]
            else:
                parent.loadedImageData = [os.path.basename(imagePath),
                                          list(Image.fromarray(parent.cvImage).getdata()),
                                          load]

            render = ImageTk.PhotoImage(load)
            parent.loadedImageType = parent.imageHelper.getColourType(parent)
            parent.histogramData = [os.path.basename(imagePath), helper, load]
            parent.editedImageData = [parent.loadedImageData[0], parent.loadedImageData[1]]
            # parent.allOpenImagesData[title] = Image.open(imagePath)
            parent.allOpenImagesData[title] = cv2.imread(imagePath, type)
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

        # if parent.loadedImageType == 'gs3ch' or 'gs':
        #     # gets values of only first channel of greyscale 3 channel type image
        #     img = [parent.histogramData[1][i][0] for i in range(len(parent.histogramData[1]))]
        # else:
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
        # parent.saveHelperImageData = Image.new(parent.loadedImageMode,
        #                                        parent.loadedImageData[2].size)

        parent.editedImageData = list(parent.editedImageData)
        # parent.saveHelperImageData.putdata(tuple(parent.editedImageData[1]))
        self.histogram_stretch_result_window(parent)

    def histogram_stretch_result_window(self, parent):
        stretch_result_window = tk.Toplevel(parent)
        img_title = "Obraz wynikowy - rozciąganie"

        helper_index = 0
        while img_title in parent.allOpenImagesData.keys():
            helper_index += 1
            img_title = "Obraz wynikowy - rozciąganie " + f"({str(helper_index)})"
        stretch_result_window.title(img_title)

        def on_closing():
            del parent.allOpenImagesData[img_title]
            stretch_result_window.destroy()

        stretch_result_window.protocol("WM_DELETE_WINDOW", on_closing)

        parent.pilImageData = Image.new(parent.loadedImageMode,
                                        parent.loadedImageData[2].size)
        parent.pilImageData.putdata(parent.editedImageData[1])
        parent.allOpenImagesData[img_title] = parent.pilImageData
        picture_label = tk.Label(stretch_result_window)
        picture_label.pack()

        parent.histogram_image_data = ["Stretched", parent.pilImageData.getdata()]
        selected_picture = ImageTk.PhotoImage(parent.pilImageData)
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
                           command=lambda: self.imageThresholdCalculations(parent, entry.get()))

        label.pack()
        entry.pack()
        button.pack()

    def imageThresholdCalculations(self, parent, value):
        try:
            int(value)
        except ValueError:
            print("Wpisana wartosc musi byc liczba")
            return
        if not (0 < int(value) < 255):
            print("Wartosc poza zakresem 0-255")
            return
        value = int(value)
        imageThresholded = list(parent.loadedImageData[1])
        self.thresholdImageSettings.destroy()
        for index in range(len(parent.loadedImageData[1])):
            if parent.loadedImageData[1][index] > value:
                imageThresholded[index] = 255
            else:
                imageThresholded[index] = 0

        thresholdImageWindow = tk.Toplevel()
        imageTitle = "Obraz wynikowy - progowanie"

        helper_index = 0
        while imageTitle in parent.allOpenImagesData.keys():
            helper_index += 1
            imageTitle = f"Obraz wynikowy - progowanie({str(helper_index)})"
        thresholdImageWindow.title(imageTitle)

        def on_closing():
            del parent.allOpenImagesData[imageTitle]
            thresholdImageWindow.destroy()

        thresholdImageWindow.protocol("WM_DELETE_WINDOW", on_closing)

        imageLabel = tk.Label(thresholdImageWindow)
        imageLabel.pack()
        parent.pilImageData = Image.new(parent.loadedImageMode,
                                        parent.loadedImageData[2].size)
        parent.pilImageData.putdata(imageThresholded)
        parent.allOpenImagesData[imageTitle] = parent.pilImageData
        parent.saveHelperImageData = Image.new(parent.loadedImageMode,
                                               parent.loadedImageData[2].size)
        parent.saveHelperImageData.putdata(imageThresholded)

        selectedImage = ImageTk.PhotoImage(parent.pilImageData)
        imageLabel.configure(image=selectedImage)
        parent.histogramData = ["Progowanie - ", parent.pilImageData.getdata()]
        thresholdImageWindow.mainloop()

    def thresholdImageWithGreyscale(self, parent):
        self.thresholdGreyscaleImageSettings = tk.Toplevel(parent)
        self.thresholdGreyscaleImageSettings.title("Ustawienia progowania z zachowaniem progow szarosci")
        self.thresholdGreyscaleImageSettings.resizable(False, False)
        self.thresholdGreyscaleImageSettings.geometry("300x80")
        self.thresholdGreyscaleImageSettings.focus_set()

        label = tk.Label(self.thresholdGreyscaleImageSettings, text="Próg (od 1 do 255)", justify=tk.LEFT, anchor='w')

        entry = tk.Entry(self.thresholdGreyscaleImageSettings, width=10)
        entry.insert(0, "1")
        button = tk.Button(self.thresholdGreyscaleImageSettings, text="Wykonaj", width=10,
                           command=lambda: self.thresholdImageWithGreyscaleCalculations(parent, entry.get()))

        label.pack()
        entry.pack()
        button.pack()

    def thresholdImageWithGreyscaleCalculations(self, parent, value):
        try:
            int(value)
        except ValueError:
            print("Wpisana wartosc musi byc liczba")
            return
        if not (0 < int(value) < 255):
            print("Wartosc poza zakresem 0-255")
            return
        value = int(value)
        imageThresholdedWithGreyscale = list(parent.loadedImageData[1])
        self.thresholdGreyscaleImageSettings.destroy()
        for index in range(len(parent.loadedImageData[1])):
            if parent.loadedImageData[1][index] > value:
                imageThresholdedWithGreyscale[index] = imageThresholdedWithGreyscale[index]
            else:
                imageThresholdedWithGreyscale[index] = 0

        thresholdImageWithGreyscaleWindow = tk.Toplevel()
        imageTitle = "Obraz wynikowy - progowanie"

        helper_index = 0
        while imageTitle in parent.allOpenImagesData.keys():
            helper_index += 1
            imageTitle = f"Obraz wynikowy - progowanie z zachowaniem szarosci({str(helper_index)})"
        thresholdImageWithGreyscaleWindow.title(imageTitle)

        def on_closing():
            del parent.allOpenImagesData[imageTitle]
            thresholdImageWithGreyscaleWindow.destroy()

        thresholdImageWithGreyscaleWindow.protocol("WM_DELETE_WINDOW", on_closing)

        imageLabel = tk.Label(thresholdImageWithGreyscaleWindow)
        imageLabel.pack()
        parent.pilImageData = Image.new(parent.loadedImageMode,
                                        parent.loadedImageData[2].size)
        parent.pilImageData.putdata(imageThresholdedWithGreyscale)
        parent.allOpenImagesData[imageTitle] = parent.pilImageData
        parent.saveHelperImageData = Image.new(parent.loadedImageMode,
                                               parent.loadedImageData[2].size)
        parent.saveHelperImageData.putdata(imageThresholdedWithGreyscale)

        selectedImage = ImageTk.PhotoImage(parent.pilImageData)
        imageLabel.configure(image=selectedImage)
        parent.histogramData = ["Progowanie z zachowaniem poziomu szarosci- ", parent.pilImageData.getdata()]
        thresholdImageWithGreyscaleWindow.mainloop()

    def imageThresholdWithTwoValues(self, parent):
        # Set threshold level window
        self.thresholdWithLevelMenu = tk.Toplevel(parent)
        self.thresholdWithLevelMenu.resizable(False, False)
        self.thresholdWithLevelMenu.title("Thresholding settings")
        self.thresholdWithLevelMenu.focus_set()

        stretch_options_top = tk.Frame(self.thresholdWithLevelMenu, width=150, height=150)
        floorLevellabel = tk.Label(stretch_options_top, text="Próg dolny", padx=10, pady=10)
        cellingLevelLabel = tk.Label(stretch_options_top, text="Próg górny", padx=10, pady=10)
        floorLevelValue = tk.Entry(stretch_options_top, width=10)
        cellingLevelValue = tk.Entry(stretch_options_top, width=10)

        button_area = tk.Frame(self.thresholdWithLevelMenu, width=100, pady=10)
        button = tk.Button(button_area, text="Wykonaj", width=10,
                           command=lambda: self.imageThresholdWithTwoValuesCalculations(parent, floorLevelValue.get(),
                                                                                        cellingLevelValue.get()))
        button.pack()

        stretch_options_top.grid(column=1, row=0)
        floorLevellabel.grid(column=1, row=1, padx=(55, 5))
        cellingLevelLabel.grid(column=2, row=1, padx=(5, 55))
        floorLevelValue.grid(column=1, row=2, padx=(55, 5))
        cellingLevelValue.grid(column=2, row=2, padx=(5, 55))
        button_area.grid(column=1, row=1)

    def imageThresholdWithTwoValuesCalculations(self, parent, floorValue, cellingValue):
        try:
            int(floorValue)
            int(cellingValue)
        except ValueError:
            print("Wpisana wartosc musi by numerem.")
            return
        if not (0 < int(floorValue) < 255) or not (0 < int(cellingValue) < 255):
            print("Wartosc poza zakresem 0-255")
            return
        floorValue = int(floorValue)
        cellingValue = int(cellingValue)
        self.thresholdWithLevelMenu.destroy()
        image_thresholded = list(parent.loadedImageData[1])

        for index in range(len(parent.loadedImageData[1])):
            if parent.loadedImageData[1][index] >= cellingValue:
                image_thresholded[index] = 255
            elif parent.loadedImageData[1][index] <= floorValue:
                image_thresholded[index] = 0

        threshold_with_level_result_window = tk.Toplevel()
        img_title = "Obraz wynikowy - progowanie z zakresem"

        helper_index = 0
        while img_title in parent.allOpenImagesData.keys():
            helper_index += 1
            img_title = f"Obraz wynikowy - progowanie z zakresem({str(helper_index)})"
        threshold_with_level_result_window.title(img_title)

        def on_closing():
            del parent.allOpenImagesData[img_title]
            threshold_with_level_result_window.destroy()

        threshold_with_level_result_window.protocol("WM_DELETE_WINDOW", on_closing)

        picture_label = tk.Label(threshold_with_level_result_window)
        picture_label.pack()
        parent.pilImageData = Image.new(parent.loadedImageMode,
                                        parent.loadedImageData[2].size)
        parent.pilImageData.putdata(image_thresholded)
        parent.allOpenImagesData[img_title] = parent.pilImageData
        parent.saveHelperImageData = Image.new(parent.loadedImageMode,
                                               parent.loadedImageData[2].size)
        parent.saveHelperImageData.putdata(image_thresholded)
        parent.histogramData = ["Progowanie z dwoma progami - ", parent.pilImageData.getdata()]
        selected_picture = ImageTk.PhotoImage(parent.pilImageData)
        picture_label.configure(image=selected_picture)
        threshold_with_level_result_window.mainloop()

    def imageThresholdWithTwoValuesGreyscaleLevel(self, parent):
        # Set threshold level window
        self.thresholdWithLevelMenu = tk.Toplevel(parent)
        self.thresholdWithLevelMenu.resizable(False, False)
        self.thresholdWithLevelMenu.title("Thresholding settings")
        self.thresholdWithLevelMenu.focus_set()

        stretch_options_top = tk.Frame(self.thresholdWithLevelMenu, width=150, height=150)
        floorLevellabel = tk.Label(stretch_options_top, text="Próg dolny", padx=10, pady=10)
        cellingLevelLabel = tk.Label(stretch_options_top, text="Próg górny", padx=10, pady=10)
        floorLevelValue = tk.Entry(stretch_options_top, width=10)
        cellingLevelValue = tk.Entry(stretch_options_top, width=10)

        button_area = tk.Frame(self.thresholdWithLevelMenu, width=100, pady=10)
        button = tk.Button(button_area, text="Wykonaj", width=10,
                           command=lambda: self.imageThresholdWithTwoValuesGreyscaleLevelCalculations(parent,
                                                                                                      floorLevelValue.get(),
                                                                                                      cellingLevelValue.get()))
        button.pack()

        stretch_options_top.grid(column=1, row=0)
        floorLevellabel.grid(column=1, row=1, padx=(55, 5))
        cellingLevelLabel.grid(column=2, row=1, padx=(5, 55))
        floorLevelValue.grid(column=1, row=2, padx=(55, 5))
        cellingLevelValue.grid(column=2, row=2, padx=(5, 55))
        button_area.grid(column=1, row=1)

    def imageThresholdWithTwoValuesGreyscaleLevelCalculations(self, parent, floorValue, cellingValue):
        try:
            int(floorValue)
            int(cellingValue)
        except ValueError:
            print("Wpisana wartosc musi by numerem.")
            return
        if not (0 < int(floorValue) < 255) or not (0 < int(cellingValue) < 255):
            print("Wartosc poza zakresem 0-255")
            return
        floorValue = int(floorValue)
        cellingValue = int(cellingValue)
        self.thresholdWithLevelMenu.destroy()
        image_thresholded = list(parent.loadedImageData[1])

        for index in range(len(parent.loadedImageData[1])):
            if parent.loadedImageData[1][index] >= cellingValue:
                image_thresholded[index] = image_thresholded[index]
            elif parent.loadedImageData[1][index] <= floorValue:
                image_thresholded[index] = 0

        threshold_with_level_result_window = tk.Toplevel()
        img_title = "Obraz wynikowy - progowanie z zakresem z poziomem szarosci"

        helper_index = 0
        while img_title in parent.allOpenImagesData.keys():
            helper_index += 1
            img_title = f"Obraz wynikowy - progowanie z zakresem z poziomem szarosci({str(helper_index)})"
        threshold_with_level_result_window.title(img_title)

        def on_closing():
            del parent.allOpenImagesData[img_title]
            threshold_with_level_result_window.destroy()

        threshold_with_level_result_window.protocol("WM_DELETE_WINDOW", on_closing)

        picture_label = tk.Label(threshold_with_level_result_window)
        picture_label.pack()
        parent.pilImageData = Image.new(parent.loadedImageMode,
                                        parent.loadedImageData[2].size)
        parent.pilImageData.putdata(image_thresholded)
        parent.allOpenImagesData[img_title] = parent.pilImageData
        parent.saveHelperImageData = Image.new(parent.loadedImageMode,
                                               parent.loadedImageData[2].size)
        parent.saveHelperImageData.putdata(image_thresholded)
        parent.histogramData = ["Progowanie z dwoma progami - ", parent.pilImageData.getdata()]
        selected_picture = ImageTk.PhotoImage(parent.pilImageData)
        picture_label.configure(image=selected_picture)
        threshold_with_level_result_window.mainloop()

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
            test = value.getData()
            bk = 1

    def mathAdd(self, parent):
        """
        Add the two images
        """
        self.math_add_settings_window = tk.Toplevel(parent)
        self.math_add_settings_window.resizable(False, False)
        self.math_add_settings_window.title("Dodawanie - wybierz obrazy")
        self.math_add_settings_window.focus_set()

        mathAddSettings = tk.Frame(self.math_add_settings_window, width=150, height=150)
        openImages = [_ for _ in parent.allOpenImagesData.keys()]

        image1Label = tk.Label(mathAddSettings, text="Obraz 1", padx=10)
        image2Label = tk.Label(mathAddSettings, text="Obraz 2", padx=10)

        image1Dropdown = ttk.Combobox(mathAddSettings, state='readonly', width=45)
        image1Dropdown["values"] = openImages
        image2Dropdown = ttk.Combobox(mathAddSettings, state='readonly', width=45)
        image2Dropdown["values"] = openImages

        buttonArea = tk.Frame(self.math_add_settings_window, width=100, pady=10)
        button = tk.Button(buttonArea, text="Wykonaj", width=10,
                           command=lambda: self.mathAddCommand(
                               parent,
                               image1Dropdown.get(),
                               image2Dropdown.get()))

        button.pack()
        mathAddSettings.grid(column=0, row=0)
        image1Label.grid(column=0, row=0, padx=(25, 5))
        image2Label.grid(column=1, row=0, padx=(5, 15))
        image1Dropdown.grid(column=0, row=1, padx=(20, 5))
        image2Dropdown.grid(column=1, row=1, padx=(5, 15))
        buttonArea.grid(column=0, row=1)

    def mathAddCommand(self, parent, img_one, img_two):
        firstImage = numpy.array(parent.allOpenImagesData[img_one])
        secondImage = numpy.array(parent.allOpenImagesData[img_two])

        if (firstImage.shape[0] != secondImage.shape[0]) & (firstImage.shape[1] != secondImage.shape[1]):
            tkinter.messagebox.showerror("Error", "Obrazy musza miec taki sam rozmiar!")
        else:
            parent.editedImageData[1] = self.mathAddCalculations(parent, img_one, img_two)
            self.math_add_result_window(parent, img_one)

    def mathAddCalculations(self, parent, img_one, img_two):
        firstImage = numpy.array(parent.allOpenImagesData[img_one])
        secondImage = numpy.array(parent.allOpenImagesData[img_two])
        addedImagesData = firstImage
        for i in range(len(firstImage)):
            for j in range(len(firstImage[i])):
                firstImagePixel = firstImage[i, j]
                secondImagePixel = secondImage[i, j]
                addedImagesData[i][j] = (int(firstImagePixel) + int(secondImagePixel))
                #DOPISAC 255 WARUNEK

        # result = Image.fromarray(list(addedImagesData)).getdata()
        # parent.pilImageData = Image.new(parent.loadedImageMode,
        #                                 parent.loadedImageData[2].size)
        # parent.pilImageData.putdata(result, parent.loadedImageMode)
        return addedImagesData

    def math_add_result_window(self, parent, img_one):
        self.math_add_settings_window.destroy()
        img_title = "Obraz wynikowy - dodawanie"

        helper_index = 0
        while img_title in parent.allOpenImagesData.keys():
            helper_index += 1
            img_title = f"Obraz wynikowy - dodawanie({str(helper_index)})"

        def on_closing():
            del parent.allOpenImagesData[img_title]

        # picture_label = tk.Label(math_add_result_window)
        # picture_label.pack()
        #

        # parent.histogramData = ["Dodane", parent.pilImageData.getdata()]
        # selected_picture = ImageTk.PhotoImage(parent.pilImageData)
        # picture_label.configure(image=selected_picture)
        cv2.imshow("Obraz wynikowy - dodawanie", parent.editedImageData[1])
        # math_add_result_window.mainloop()

    def mathAnd(self, parent):
        """
        Add the two images
        """
        self.math_and_settings_window = tk.Toplevel(parent)
        self.math_and_settings_window.resizable(False, False)
        self.math_and_settings_window.title("And - wybierz obrazy")
        self.math_and_settings_window.focus_set()

        mathAndSettings = tk.Frame(self.math_and_settings_window, width=150, height=150)
        openImages = [_ for _ in parent.allOpenImagesData.keys()]

        image1Label = tk.Label(mathAndSettings, text="Obraz 1", padx=10)
        image2Label = tk.Label(mathAndSettings, text="Obraz 2", padx=10)

        image1Dropdown = ttk.Combobox(mathAndSettings, state='readonly', width=45)
        image1Dropdown["values"] = openImages
        image2Dropdown = ttk.Combobox(mathAndSettings, state='readonly', width=45)
        image2Dropdown["values"] = openImages

        buttonArea = tk.Frame(self.math_and_settings_window, width=100, pady=10)
        button = tk.Button(buttonArea, text="Wykonaj", width=10,
                           command=lambda: self.mathAndCommand(
                               parent,
                               image1Dropdown.get(),
                               image2Dropdown.get()))

        button.pack()
        mathAndSettings.grid(column=0, row=0)
        image1Label.grid(column=0, row=0, padx=(25, 5))
        image2Label.grid(column=1, row=0, padx=(5, 15))
        image1Dropdown.grid(column=0, row=1, padx=(20, 5))
        image2Dropdown.grid(column=1, row=1, padx=(5, 15))
        buttonArea.grid(column=0, row=1)

    def mathAndCommand(self, parent, img_one, img_two):
        firstImage = numpy.array(parent.allOpenImagesData[img_one])
        secondImage = numpy.array(parent.allOpenImagesData[img_two])

        if (firstImage.shape[0] != secondImage.shape[0]) & (firstImage.shape[1] != secondImage.shape[1]):
            tkinter.messagebox.showerror("Error", "Obrazy musza miec taki sam rozmiar!")
        else:
            parent.editedImageData[1] = self.mathAndCalculations(parent, img_one, img_two)
            self.math_and_result_window(parent, img_one)

    def mathAndCalculations(self, parent, img_one, img_two):
        firstImage = numpy.array(parent.allOpenImagesData[img_one])
        secondImage = numpy.array(parent.allOpenImagesData[img_two])
        andImagesData = firstImage
        for i in range(len(firstImage)):
            for j in range(len(firstImage[i])):
                firstImagePixel = firstImage[i, j]
                secondImagePixel = secondImage[i, j]
                andImagesData[i][j] = firstImagePixel & secondImagePixel

        # result = Image.fromarray(list(addedImagesData)).getdata()
        # parent.pilImageData = Image.new(parent.loadedImageMode,
        #                                 parent.loadedImageData[2].size)
        # parent.pilImageData.putdata(result, parent.loadedImageMode)
        return andImagesData

    def math_and_result_window(self, parent, img_one):
        self.math_and_settings_window.destroy()
        img_title = "Obraz wynikowy - and"

        helper_index = 0
        while img_title in parent.allOpenImagesData.keys():
            helper_index += 1
            img_title = f"Obraz wynikowy - and({str(helper_index)})"

        def on_closing():
            del parent.allOpenImagesData[img_title]

        # picture_label = tk.Label(math_add_result_window)
        # picture_label.pack()
        #

        # parent.histogramData = ["Dodane", parent.pilImageData.getdata()]
        # selected_picture = ImageTk.PhotoImage(parent.pilImageData)
        # picture_label.configure(image=selected_picture)
        cv2.imshow("Obraz wynikowy - and", parent.editedImageData[1])

        # math_add_result_window.mainloop()

    def mathOr(self, parent):
        """
        Add the two images
        """
        self.math_or_settings_window = tk.Toplevel(parent)
        self.math_or_settings_window.resizable(False, False)
        self.math_or_settings_window.title("Or - wybierz obrazy")
        self.math_or_settings_window.focus_set()

        mathOrSettings = tk.Frame(self.math_or_settings_window, width=150, height=150)
        openImages = [_ for _ in parent.allOpenImagesData.keys()]

        image1Label = tk.Label(mathOrSettings, text="Obraz 1", padx=10)
        image2Label = tk.Label(mathOrSettings, text="Obraz 2", padx=10)

        image1Dropdown = ttk.Combobox(mathOrSettings, state='readonly', width=45)
        image1Dropdown["values"] = openImages
        image2Dropdown = ttk.Combobox(mathOrSettings, state='readonly', width=45)
        image2Dropdown["values"] = openImages

        buttonArea = tk.Frame(self.math_or_settings_window, width=100, pady=10)
        button = tk.Button(buttonArea, text="Wykonaj", width=10,
                           command=lambda: self.mathOrCommand(
                               parent,
                               image1Dropdown.get(),
                               image2Dropdown.get()))

        button.pack()
        mathOrSettings.grid(column=0, row=0)
        image1Label.grid(column=0, row=0, padx=(25, 5))
        image2Label.grid(column=1, row=0, padx=(5, 15))
        image1Dropdown.grid(column=0, row=1, padx=(20, 5))
        image2Dropdown.grid(column=1, row=1, padx=(5, 15))
        buttonArea.grid(column=0, row=1)

    def mathOrCommand(self, parent, img_one, img_two):
        firstImage = numpy.array(parent.allOpenImagesData[img_one])
        secondImage = numpy.array(parent.allOpenImagesData[img_two])

        if (firstImage.shape[0] != secondImage.shape[0]) & (firstImage.shape[1] != secondImage.shape[1]):
            tkinter.messagebox.showerror("Error", "Obrazy musza miec taki sam rozmiar!")
        else:
            parent.editedImageData[1] = self.mathOrCalculations(parent, img_one, img_two)
            self.math_or_result_window(parent, img_one)

    def mathOrCalculations(self, parent, img_one, img_two):
        firstImage = numpy.array(parent.allOpenImagesData[img_one])
        secondImage = numpy.array(parent.allOpenImagesData[img_two])
        orImagesData = firstImage
        for i in range(len(firstImage)):
            for j in range(len(firstImage[i])):
                firstImagePixel = firstImage[i, j]
                secondImagePixel = secondImage[i, j]
                orImagesData[i][j] = firstImagePixel | secondImagePixel

        return orImagesData

    def math_or_result_window(self, parent, img_one):
        self.math_or_settings_window.destroy()
        img_title = "Obraz wynikowy - or"

        helper_index = 0
        while img_title in parent.allOpenImagesData.keys():
            helper_index += 1
            img_title = f"Obraz wynikowy - or({str(helper_index)})"

        def on_closing():
            del parent.allOpenImagesData[img_title]

        cv2.imshow("Obraz wynikowy - or", parent.editedImageData[1])


    def mathXor(self, parent):
        """
        Add the two images
        """
        self.math_xor_settings_window = tk.Toplevel(parent)
        self.math_xor_settings_window.resizable(False, False)
        self.math_xor_settings_window.title("Xor - wybierz obrazy")
        self.math_xor_settings_window.focus_set()

        mathXorSettings = tk.Frame(self.math_xor_settings_window, width=150, height=150)
        openImages = [_ for _ in parent.allOpenImagesData.keys()]

        image1Label = tk.Label(mathXorSettings, text="Obraz 1", padx=10)
        image2Label = tk.Label(mathXorSettings, text="Obraz 2", padx=10)

        image1Dropdown = ttk.Combobox(mathXorSettings, state='readonly', width=45)
        image1Dropdown["values"] = openImages
        image2Dropdown = ttk.Combobox(mathXorSettings, state='readonly', width=45)
        image2Dropdown["values"] = openImages

        buttonArea = tk.Frame(self.math_xor_settings_window, width=100, pady=10)
        button = tk.Button(buttonArea, text="Wykonaj", width=10,
                           command=lambda: self.mathXorCommand(
                               parent,
                               image1Dropdown.get(),
                               image2Dropdown.get()))

        button.pack()
        mathXorSettings.grid(column=0, row=0)
        image1Label.grid(column=0, row=0, padx=(25, 5))
        image2Label.grid(column=1, row=0, padx=(5, 15))
        image1Dropdown.grid(column=0, row=1, padx=(20, 5))
        image2Dropdown.grid(column=1, row=1, padx=(5, 15))
        buttonArea.grid(column=0, row=1)

    def mathXorCommand(self, parent, img_one, img_two):
        firstImage = numpy.array(parent.allOpenImagesData[img_one])
        secondImage = numpy.array(parent.allOpenImagesData[img_two])

        if (firstImage.shape[0] != secondImage.shape[0]) & (firstImage.shape[1] != secondImage.shape[1]):
            tkinter.messagebox.showerror("Error", "Obrazy musza miec taki sam rozmiar!")
        else:
            parent.editedImageData[1] = self.mathXorCalculations(parent, img_one, img_two)
            self.math_xor_result_window(parent, img_one)

    def mathXorCalculations(self, parent, img_one, img_two):
        firstImage = numpy.array(parent.allOpenImagesData[img_one])
        secondImage = numpy.array(parent.allOpenImagesData[img_two])
        xorImagesData = firstImage
        for i in range(len(firstImage)):
            for j in range(len(firstImage[i])):
                firstImagePixel = firstImage[i, j]
                secondImagePixel = secondImage[i, j]
                xorImagesData[i][j] = firstImagePixel ^ secondImagePixel

        return xorImagesData

    def math_xor_result_window(self, parent, img_one):
        self.math_xor_settings_window.destroy()
        img_title = "Obraz wynikowy - xor"

        helper_index = 0
        while img_title in parent.allOpenImagesData.keys():
            helper_index += 1
            img_title = f"Obraz wynikowy - xor({str(helper_index)})"

        def on_closing():
            del parent.allOpenImagesData[img_title]

        cv2.imshow("Obraz wynikowy - xor", parent.editedImageData[1])


    def mathNot(self, parent):
        """
        Add the two images
        """
        self.math_not_settings_window = tk.Toplevel(parent)
        self.math_not_settings_window.resizable(False, False)
        self.math_not_settings_window.title("Not - wybierz obrazy")
        self.math_not_settings_window.focus_set()

        mathXorSettings = tk.Frame(self.math_not_settings_window, width=150, height=150)
        openImages = [_ for _ in parent.allOpenImagesData.keys()]

        image1Label = tk.Label(mathXorSettings, text="Obraz 1", padx=10)
        image2Label = tk.Label(mathXorSettings, text="Obraz 2", padx=10)

        image1Dropdown = ttk.Combobox(mathXorSettings, state='readonly', width=45)
        image1Dropdown["values"] = openImages
        image2Dropdown = ttk.Combobox(mathXorSettings, state='readonly', width=45)
        image2Dropdown["values"] = openImages

        buttonArea = tk.Frame(self.math_not_settings_window, width=100, pady=10)
        button = tk.Button(buttonArea, text="Wykonaj", width=10,
                           command=lambda: self.mathNotCommand(
                               parent,
                               image1Dropdown.get(),
                               image2Dropdown.get()))

        button.pack()
        mathXorSettings.grid(column=0, row=0)
        image1Label.grid(column=0, row=0, padx=(25, 5))
        image2Label.grid(column=1, row=0, padx=(5, 15))
        image1Dropdown.grid(column=0, row=1, padx=(20, 5))
        image2Dropdown.grid(column=1, row=1, padx=(5, 15))
        buttonArea.grid(column=0, row=1)

    def mathNotCommand(self, parent, img_one, img_two):
        firstImage = numpy.array(parent.allOpenImagesData[img_one])
        secondImage = numpy.array(parent.allOpenImagesData[img_two])

        if (firstImage.shape[0] != secondImage.shape[0]) & (firstImage.shape[1] != secondImage.shape[1]):
            tkinter.messagebox.showerror("Error", "Obrazy musza miec taki sam rozmiar!")
        else:
            parent.editedImageData[1] = self.mathNotCalculations(parent, img_one, img_two)
            self.math_not_result_window(parent, img_one)

    def mathNotCalculations(self, parent, img_one, img_two):
        firstImage = numpy.array(parent.allOpenImagesData[img_one])
        secondImage = numpy.array(parent.allOpenImagesData[img_two])
        notImagesData = firstImage
        for i in range(len(firstImage)):
            for j in range(len(firstImage[i])):
                firstImagePixel = firstImage[i, j]
                secondImagePixel = secondImage[i, j]
                notImagesData[i][j] = firstImagePixel ^ secondImagePixel

        return notImagesData

    def math_not_result_window(self, parent, img_one):
        self.math_not_settings_window.destroy()
        img_title = "Obraz wynikowy - or"

        helper_index = 0
        while img_title in parent.allOpenImagesData.keys():
            helper_index += 1
            img_title = f"Obraz wynikowy - or({str(helper_index)})"

        def on_closing():
            del parent.allOpenImagesData[img_title]

        cv2.imshow("Obraz wynikowy - or", parent.editedImageData[1])


    def mathAddValue(self, parent):
        self.mathAddValueSettings = tk.Toplevel(parent)
        self.mathAddValueSettings.title("Dodawanie liczby do obrazu")
        self.mathAddValueSettings.resizable(False, False)
        self.mathAddValueSettings.geometry("300x80")
        self.mathAddValueSettings.focus_set()

        label = tk.Label(self.mathAddValueSettings, text="Liczba (od 1 do 255)", justify=tk.LEFT, anchor='w')

        entry = tk.Entry(self.mathAddValueSettings, width=10)
        button = tk.Button(self.mathAddValueSettings, text="Wykonaj", width=10,
                           command=lambda: self.mathAddValueCommand(parent, entry.get()))

        label.pack()
        entry.pack()
        button.pack()

    def mathAddValueCommand(self, parent, img_one):
        parent.editedImageData[1] = self.mathAddValueCalculations(parent, img_one)
        self.math_add_value_result_window(parent, img_one)

    def mathAddValueCalculations(self, parent, value):
        try:
            int(value)
        except ValueError:
            print("Wpisana wartosc musi byc liczba")
            return
        if not (0 < int(value) < 255):
            print("Wartosc poza zakresem 0-255")
            return
        value = int(value)

        image = list(parent.allOpenImagesData.values())[0]
        imageWithAddedNumber = numpy.array(image)
        self.mathAddValueSettings.destroy()
        for i in range(len(imageWithAddedNumber)):
            for j in range(len(imageWithAddedNumber[i])):
                pixel = imageWithAddedNumber[i, j]
                pixelSum = int(pixel) + int(value)
                if pixelSum > 255:
                    imageWithAddedNumber[i, j] = 255
                else:
                    imageWithAddedNumber[i, j] = pixelSum

        return imageWithAddedNumber

    def math_add_value_result_window(self, parent, img_one):
        self.mathAddValueSettings.destroy()
        img_title = "Obraz wynikowy - dodanie wartosci"

        helper_index = 0
        while img_title in parent.allOpenImagesData.keys():
            helper_index += 1
            img_title = f"Obraz wynikowy - dodanie wartosci ({str(helper_index)})"

        def on_closing():
            del parent.allOpenImagesData[img_title]

        cv2.imshow("Obraz wynikowy - dodanie wartosci", parent.editedImageData[1])

    def mathDivideValue(self, parent):
        self.mathDivideValueSettings = tk.Toplevel(parent)
        self.mathDivideValueSettings.title("Dzielenie przez liczbe")
        self.mathDivideValueSettings.resizable(False, False)
        self.mathDivideValueSettings.geometry("300x80")
        self.mathDivideValueSettings.focus_set()

        label = tk.Label(self.mathDivideValueSettings, text="Liczba", justify=tk.LEFT, anchor='w')

        entry = tk.Entry(self.mathDivideValueSettings, width=10)
        button = tk.Button(self.mathDivideValueSettings, text="Wykonaj", width=10,
                           command=lambda: self.mathDivideValueCommand(parent, entry.get()))

        label.pack()
        entry.pack()
        button.pack()

    def mathDivideValueCommand(self, parent, img_one):
        parent.editedImageData[1] = self.mathDivideCalculations(parent, img_one)
        self.math_divide_result_window(parent, img_one)

    def mathDivideCalculations(self, parent, value):
        try:
            int(value)
        except ValueError:
            print("Wpisana wartosc musi byc liczba")
            return
        value = int(value)

        image = list(parent.allOpenImagesData.values())[0]
        imageWithDividedNumber = numpy.array(image)
        self.mathDivideValueSettings.destroy()
        for i in range(len(imageWithDividedNumber)):
            for j in range(len(imageWithDividedNumber[i])):
                pixel = imageWithDividedNumber[i, j]
                pixelDivided = int(pixel) / int(value)
                imageWithDividedNumber[i, j] = pixelDivided

        return imageWithDividedNumber

    def math_divide_result_window(self, parent, img_one):
        self.mathDivideValueSettings.destroy()
        img_title = "Obraz wynikowy - podzielenie"

        helper_index = 0
        while img_title in parent.allOpenImagesData.keys():
            helper_index += 1
            img_title = f"Obraz wynikowy - podzielenie ({str(helper_index)})"

        def on_closing():
            del parent.allOpenImagesData[img_title]

        cv2.imshow("Obraz wynikowy - podzielenie", parent.editedImageData[1])

    def mathDivideValue(self, parent):
        self.mathDivideValueSettings = tk.Toplevel(parent)
        self.mathDivideValueSettings.title("Dzielenie przez liczbe")
        self.mathDivideValueSettings.resizable(False, False)
        self.mathDivideValueSettings.geometry("300x80")
        self.mathDivideValueSettings.focus_set()

        label = tk.Label(self.mathDivideValueSettings, text="Liczba", justify=tk.LEFT, anchor='w')

        entry = tk.Entry(self.mathDivideValueSettings, width=10)
        button = tk.Button(self.mathDivideValueSettings, text="Wykonaj", width=10,
                           command=lambda: self.mathDivideValueCommand(parent, entry.get()))

        label.pack()
        entry.pack()
        button.pack()

    def mathMultiplyValueCommand(self, parent, img_one):
        parent.editedImageData[1] = self.mathMultiplyCalculations(parent, img_one)
        self.math_multiply_result_window(parent, img_one)

    def mathMultiplyCalculations(self, parent, value):
        try:
            int(value)
        except ValueError:
            print("Wpisana wartosc musi byc liczba")
            return
        value = int(value)

        image = list(parent.allOpenImagesData.values())[0]
        imageMultiplyNumber = numpy.array(image)
        self.mathMultiplyValueSettings.destroy()
        for i in range(len(imageMultiplyNumber)):
            for j in range(len(imageMultiplyNumber[i])):
                pixel = imageMultiplyNumber[i, j]
                pixelMultiply = int(pixel) * int(value)
                imageMultiplyNumber[i, j] = pixelMultiply

        return imageMultiplyNumber

    def math_multiply_result_window(self, parent, img_one):
        self.mathMultiplyValueSettings.destroy()
        img_title = "Obraz wynikowy - mnozenie"

        helper_index = 0
        while img_title in parent.allOpenImagesData.keys():
            helper_index += 1
            img_title = f"Obraz wynikowy - mnozenie ({str(helper_index)})"

        def on_closing():
            del parent.allOpenImagesData[img_title]

        cv2.imshow("Obraz wynikowy - mnozenie", parent.editedImageData[1])

class Lab4MenuDropdown(tk.Menu):
    def __init__(self):
        smoothingAveragingMatrix = numpy.array([
            [1, 1, 1],
            [1, 1, 1],
            [1, 1, 1]
        ])
        smoothingAveragingWeightsMatrix = numpy.array([
            [1, 1, 1],
            [1, 8, 1],
            [1, 1, 1]
        ])
        smoothingGaussMatrix = numpy.array([
            [1, 2, 1],
            [2, 4, 2],
            [1, 2, 1]
        ])
        tk.Menu.__init__(self, tearoff=False)
        self.smoothingDropdownOptions = {"Usrednienie": smoothingAveragingMatrix,
                      "Usrednienie z wagami": smoothingAveragingWeightsMatrix,
                      "Filtr gaussowski": smoothingGaussMatrix}

    def linearSmoothing(self, parent):
        self.linearSmoothingWindow = tk.Toplevel(parent)
        self.linearSmoothingWindow.resizable(False, False)
        self.linearSmoothingWindow.title("Ustawienia")
        self.linearSmoothingWindow.focus_set()

        settingsFrame = tk.Frame(self.linearSmoothingWindow, width=150, height=150)
        label = tk.Label(settingsFrame, text="Ustawienia pikseli brzegowych", padx=10)
        combobox = ttk.Combobox(settingsFrame, state='readonly', width=45)
        combobox["values"] = list(self.smoothingDropdownOptions.keys())
        combobox.current(0)

        buttonArea = tk.Frame(self.linearSmoothingWindow, width=50, pady=10)
        button = tk.Button(buttonArea, text="Wykonaj", width=10,
                           command=lambda: self.linearSmoothingControler(
                               parent,
                               self.smoothingDropdownOptions[combobox.get()]))
        button.pack()
        settingsFrame.grid(column=0, row=0)
        label.grid(column=0, row=0, padx=(25, 5))
        combobox.grid(column=0, row=1, padx=(20, 5))
        buttonArea.grid(column=0, row=1, padx=(20, 5))

    def linearSmoothingControler(self, parent, border):
        parent.editedImageData[1] = self.linearSmoothingCalculate(parent, border)
        self.linearSmoothingResultWindow(parent)

    def linearSmoothingCalculate(self, parent, border):
        # result = cv2.blur(parent.cvImage, (5, 5), 0, borderType=border)
        # kernel = numpy.ones((5, 5), numpy.float32) / 25
        result = cv2.filter2D(parent.cvImage, -1, border)
        return result

    def linearSmoothingResultWindow(self, parent):
        img_title = "Obraz wynikowy - wygladzanie"
        helper_index = 0
        while img_title in parent.allOpenImagesData.keys():
            helper_index += 1
            img_title = f"Obraz wynikowy - wygladzanie({str(helper_index)})"

        def on_closing():
            del parent.allOpenImagesData[img_title]

        cv2.imshow(img_title, parent.editedImageData[1])

        # --------------------------------------------

    def linearSharpening(self, parent):

        mask_values = {"Maska 1 - [[0, -1, 0], [-1, 4, -1], [0, -1, 0]]": 0,
                       "Maska 2 - [[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]]": 1,
                       "Maska 3 - [[1, -2, 1], [-2, 4, -2], [1, -2, 1]]": 2}

        self.linearSharpeningWindow = tk.Toplevel(parent)
        self.linearSharpeningWindow.resizable(False, False)
        self.linearSharpeningWindow.title("Ustawienia")
        self.linearSharpeningWindow.focus_set()

        settingsFrame = tk.Frame(self.linearSharpeningWindow, width=150, height=150)
        label = tk.Label(settingsFrame, text="Ustawienia pikseli brzegowych", padx=10)
        combobox = ttk.Combobox(settingsFrame, state='readonly', width=45)
        combobox["values"] = list(mask_values.keys())
        combobox.current(0)

        buttonArea = tk.Frame(self.linearSharpeningWindow, width=50, pady=10)
        button = tk.Button(buttonArea, text="Wykonaj", width=10,
                           command=lambda: self.linearSharpeningControler(
                               parent,
                               mask_values[combobox.get()]))
        button.pack()
        settingsFrame.grid(column=0, row=0)
        label.grid(column=0, row=0, padx=(25, 5))
        combobox.grid(column=0, row=1, padx=(20, 5))
        buttonArea.grid(column=0, row=1, padx=(20, 5))

    def linearSharpeningControler(self, parent, selected):
        parent.editedImageData[1] = self.linearSharpeningCalculate(parent, selected)
        self.linearSmoothingResultWindow(parent)

    def linearSharpeningCalculate(self, parent, selected):
        mask_sharp = [numpy.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]]),
                      numpy.array([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]]),
                      numpy.array([[1, -2, 1], [-2, 4, -2], [1, -2, 1]])]

        result = cv2.filter2D(parent.cvImage, cv2.CV_64F, mask_sharp[selected], borderType=cv2.BORDER_DEFAULT)
        return result

    def linearSharpeningResultWindow(self, parent):
        img_title = "Obraz wynikowy - wyostrzanie"
        helper_index = 0
        while img_title in parent.allOpenImagesData.keys():
            helper_index += 1
            img_title = f"Obraz wynikowy - wyostrzanie({str(helper_index)})"

        def on_closing():
            del parent.allOpenImagesData[img_title]

        cv2.imshow(img_title, parent.editedImageData[1])

        # --------------------------------------------

    def sobelDirectional(self, parent):

        directions_values = {"Maska NW - [[+1, +1, 0], [+1, 0, -1], [0, -1, -1]]": 0,
                             "Maska N - [[+1, +1, +1], [0, 0, 0], [-1, -1, -1]]":  1,
                             "Maska NE - [[0, +1, +1], [-1, 0, +1], [-1, -1, 0]]": 2,
                             "Maska E - [[-1, 0, +1], [-1, 0, +1], [-1, 0, +1]]":  3,
                             "Maska SE - [[-1, -1, 0], [-1, 0, +1], [0, +1, +1]]": 4,
                             "Maska S - [[-1, -1, -1], [0, 0, 0], [+1, +1, +1]]":  5,
                             "Maska SW - [[0, -1, -1], [+1, 0, -1], [+1, +1, 0]]": 6,
                             "Maska W - [[+1, 0, -1], [+1, 0, -1], [+1, 0, -1]]":  7}

        self.sobelDirectionalWindow = tk.Toplevel(parent)
        self.sobelDirectionalWindow.resizable(False, False)
        self.sobelDirectionalWindow.title("Ustawienia")
        self.sobelDirectionalWindow.focus_set()

        settingsFrame = tk.Frame(self.sobelDirectionalWindow, width=150, height=150)
        label = tk.Label(settingsFrame, text="Ustawienia kierunku", padx=10)
        combobox = ttk.Combobox(settingsFrame, state='readonly', width=45)
        combobox["values"] = list(directions_values.keys())
        combobox.current(0)

        buttonArea = tk.Frame(self.sobelDirectionalWindow, width=50, pady=10)
        button = tk.Button(buttonArea, text="Wykonaj", width=10,
                           command=lambda: self.sobelDirectionalControler(
                               parent,
                               directions_values[combobox.get()]))
        button.pack()
        settingsFrame.grid(column=0, row=0)
        label.grid(column=0, row=0, padx=(25, 5))
        combobox.grid(column=0, row=1, padx=(20, 5))
        buttonArea.grid(column=0, row=1, padx=(20, 5))

    def sobelDirectionalControler(self, parent, selected):
        parent.editedImageData[1] = self.sobelDirectionalCalculate(parent, selected)
        self.sobelDirectionalResultWindow(parent)

    def sobelDirectionalCalculate(self, parent, selected):
        mask_values = [numpy.array([[+1, +1, 0], [+1, 0, -1], [0, -1, -1]]),
                       numpy.array([[+1, +1, +1], [0, 0, 0], [-1, -1, -1]]),
                       numpy.array([[0, +1, +1], [-1, 0, +1], [-1, -1, 0]]),
                       numpy.array([[-1, 0, +1], [-1, 0, +1], [-1, 0, +1]]),
                       numpy.array([[-1, -1, 0], [-1, 0, +1], [0, +1, +1]]),
                       numpy.array([[-1, -1, -1], [0, 0, 0], [+1, +1, +1]]),
                       numpy.array([[0, -1, -1], [+1, 0, -1], [+1, +1, 0]]),
                       numpy.array([[+1, 0, -1], [+1, 0, -1], [+1, 0, -1]])]

        result = cv2.filter2D(parent.cvImage, cv2.CV_64F, mask_values[selected], borderType=cv2.BORDER_DEFAULT)
        return result

    def sobelDirectionalResultWindow(self, parent):
        img_title = "Obraz wynikowy - sobel kierunkowy"
        helper_index = 0
        while img_title in parent.allOpenImagesData.keys():
            helper_index += 1
            img_title = f"Obraz wynikowy - sobel kierunkowy({str(helper_index)})"

        def on_closing():
            del parent.allOpenImagesData[img_title]

        cv2.imshow(img_title, parent.editedImageData[1])


class Lab5MenuDropdown(tk.Menu):
    def __init__(self):
        tk.Menu.__init__(self, tearoff=False)

        self.thresholdMethods = {"Zwykłe": cv2.THRESH_BINARY,
                                 "Otsu": cv2.THRESH_OTSU,
                                 "Adaptacyjne": 0}


    def imageSobelControler(self, parent):
        parent.editedImageData[1] = self.imageSobelCalculate(parent)
        self.imageSobelResultWindow(parent)

    def imageSobelCalculate(self, parent):
        img_gaussian = cv2.GaussianBlur(parent.cvImage, (3, 3), 0)
        sobelx = cv2.Sobel(img_gaussian, -1, 1, 0, ksize=3)
        sobely = cv2.Sobel(img_gaussian, -1, 0, 1, ksize=3)
        sobelSum = sobelx + sobely
        return sobelSum

    def imageSobelResultWindow(self, parent):
        img_title = "Obraz wynikowy - detekcja krawedzi met. sobel"
        helper_index = 0
        while img_title in parent.allOpenImagesData.keys():
            helper_index += 1
            img_title = f"Obraz wynikowy - detekcja krawedzi met. sobel({str(helper_index)})"

        def on_closing():
            del parent.allOpenImagesData[img_title]

        cv2.imshow(img_title, parent.editedImageData[1])

    def imagePrewittControler(self, parent):
        parent.editedImageData[1] = self.imagePrewittCalculate(parent)
        self.imagePrewittResultWindow(parent)

    def imagePrewittCalculate(self, parent):
        img_gaussian = cv2.GaussianBlur(parent.cvImage, (3, 3), 0)
        kernelx = numpy.array([[1, 1, 1], [0, 0, 0], [-1, -1, -1]])
        kernely = numpy.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]])
        img_prewittx = cv2.filter2D(img_gaussian, -1, kernelx)
        img_prewitty = cv2.filter2D(img_gaussian, -1, kernely)

        prewittSum = img_prewittx + img_prewitty
        return prewittSum

    def imagePrewittResultWindow(self, parent):
        img_title = "Obraz wynikowy - detekcja krawedzi met. prewitta"
        helper_index = 0
        while img_title in parent.allOpenImagesData.keys():
            helper_index += 1
            img_title = f"Obraz wynikowy - detekcja krawedzi met. prewitta({str(helper_index)})"
        def on_closing():
            del parent.allOpenImagesData[img_title]

        cv2.imshow(img_title, parent.editedImageData[1])

    def imageCannyControler(self, parent):
        parent.editedImageData[1] = self.imageCannyCalculate(parent)
        self.imageCannyResultWindow(parent)

    def imageCannyCalculate(self, parent):
        img_canny = cv2.Canny(parent.cvImage, 100, 200)
        return img_canny

    def imageCannyResultWindow(self, parent):
        img_title = "Obraz wynikowy - detekcja krawedzi met. canny"
        helper_index = 0
        while img_title in parent.allOpenImagesData.keys():
            helper_index += 1
            img_title = f"Obraz wynikowy - detekcja krawedzi met. canny({str(helper_index)})"

        def on_closing():
            del parent.allOpenImagesData[img_title]

        cv2.imshow(img_title, parent.editedImageData[1])

    def interactiveThreshold(self, parent):
        self.interactiveThresholdSettingsWindow = tk.Toplevel(parent)
        self.interactiveThresholdSettingsWindow.title("Ustawienia progowania")
        self.interactiveThresholdSettingsWindow.resizable(False, False)
        self.interactiveThresholdSettingsWindow.geometry("350x200")
        self.interactiveThresholdSettingsWindow.focus_set()

        topLabel = tk.Label(self.interactiveThresholdSettingsWindow, text="Sposób progowania", padx=10)
        thresholdTypeCombobox = ttk.Combobox(self.interactiveThresholdSettingsWindow, state='readonly', width=45)
        thresholdTypeCombobox["values"] = list(self.thresholdMethods.keys())
        thresholdTypeCombobox.current(0)

        bottomLabel = tk.Label(self.interactiveThresholdSettingsWindow, text="Próg", justify=tk.LEFT, anchor='w')
        self.scaleWiget = tk.Scale(self.interactiveThresholdSettingsWindow, from_=1, to=255,
                                     orient=tk.HORIZONTAL, length=320,
                                     command=lambda scaleValue: self.thresholdAdaptiveCalcRefresh(parent,
                                                                self.thresholdMethods[thresholdTypeCombobox.get()],
                                                                int(scaleValue)))
        closeButton = tk.Button(self.interactiveThresholdSettingsWindow, text="Zamknij", width=10,
                           command=lambda: self.interactiveThresholdSettingsWindow.destroy())

        topLabel.pack()
        thresholdTypeCombobox.pack()
        bottomLabel.pack()
        self.scaleWiget.pack()

    def thresholdAdaptiveCalcRefresh(self, parent, thresholdType, blockSize):
        """
        Refreshes and calculates displayed image every time scale widget is moved.
        :param parent:
        :param thresholdType:
        :param blockSize:
        :return:
        """
        # calculate thresholded img
        if not (blockSize % 2) or blockSize == 1:
            return
        new_picture = self.imageThresholdAdaptiveCalculations(parent, thresholdType,
                                                              blockSize)
        cv2.imshow("Progowanie", new_picture)


    def imageThresholdAdaptiveCalculations(self, parent, thresholdType, blockSize):
        imageThresholded = []
        if thresholdType == 0:
            imageThresholded = cv2.adaptiveThreshold(parent.cvImage, 255, cv2.THRESH_BINARY, thresholdType, blockSize, 5)
        else:
            imageThresholded = cv2.threshold(src=parent.cvImage, type=thresholdType, thresh=blockSize,
                                             maxval=255)[1]
        return imageThresholded


class Lab6MenuDropdown(tk.Menu):
    def __init__(self):
        tk.Menu.__init__(self, tearoff=False)

    def erode(self, parent):
        parent.editedImageData[1] = self.imageErodeCalculate(parent)
        self.imageErodeResultWindow(parent)

    def imageErodeCalculate(self, parent):
        kernel = numpy.ones((3, 3), numpy.uint8)
        image = cv2.erode(parent.cvImage, kernel)
        return image

    def imageErodeResultWindow(self, parent):
        img_title = "Obraz wynikowy - erozja"
        helper_index = 0
        while img_title in parent.allOpenImagesData.keys():
            helper_index += 1
            img_title = f"Obraz wynikowy - erozja({str(helper_index)})"
        cv2.imshow(img_title, parent.editedImageData[1])

    def dilate(self, parent):
        parent.editedImageData[1] = self.imageDilateCalculate(parent)
        self.imageErodeResultWindow(parent)

    def imageDilateCalculate(self, parent):
        kernel = numpy.ones((3, 3), numpy.uint8)
        image = cv2.dilate(parent.cvImage, kernel)
        return image

    def imageDilateResultWindow(self, parent):
        img_title = "Obraz wynikowy - dylacja"
        helper_index = 0
        while img_title in parent.allOpenImagesData.keys():
            helper_index += 1
            img_title = f"Obraz wynikowy - dylacja({str(helper_index)})"
        cv2.imshow(img_title, parent.editedImageData[1])

    def morphologyOpenClose(self, parent, morph_type):
        parent.editedImageData[1] = self.imagemorphologyOpenCloseCalculate(parent, morph_type)
        self.imageErodeResultWindow(parent)

    def imagemorphologyOpenCloseCalculate(self, parent, morph_type):
        kernel = numpy.ones((3, 3), numpy.uint8)
        image = cv2.morphologyEx(parent.cvImage, morph_type, kernel)
        return image

    def imagemorphologyOpenCloseResultWindow(self, parent):
        img_title = "Obraz wynikowy - open/close"
        helper_index = 0
        while img_title in parent.allOpenImagesData.keys():
            helper_index += 1
            img_title = f"Obraz wynikowy - open/close({str(helper_index)})"
        cv2.imshow(img_title, parent.editedImageData[1])

    def moments(self, parent):
        moments = self.imageMomentsCalculate(parent)
        print(moments)

    def imageMomentsCalculate(self, parent):
        moments = cv2.moments(parent.cvImage)
        return moments

    def getDataAndExport(self, parent):
        data = self.getAllData(parent)
        self.exportToCsv(data)

    def getAllData(self, parent):
        areaPerimeter = self.imageAreaPerimeterCalculate(parent)
        cnt = self.getContours(parent)
        aspectRatio = self.getAspectRatio(cnt)
        extent = self.getExtent(cnt)
        solidity = self.getSolidity(cnt)
        eqiDiameter = self.getEquivalentDiameter(cnt)
        result = [("Area and Perimeter", areaPerimeter),
                ("Aspect Ratio", aspectRatio),
                ("Extent", extent),
                ("Solidity", solidity),
                ("Equivalent Diameter", eqiDiameter)
                ]
        return result

    def exportToCsv(self, data):
        name = "Results.csv"
        with open(name, 'w', newline='') as csvfile:
            my_writer = csv.writer(csvfile, delimiter=';')

            for item in data:
                my_writer.writerow(item)

        print(f"Wyeksportowano do ./{name}")


    def areaPerimeter(self, parent):
        areaPerimeter = self.imageAreaPerimeterCalculate(parent)
        print(areaPerimeter)

    def imageAreaPerimeterCalculate(self, parent):
        cnt = self.getContours(parent)
        # compute the area and perimeter
        area = cv2.contourArea(cnt)
        perimeter = cv2.arcLength(cnt, True)
        perimeter = round(perimeter, 4)
        return [area, perimeter]

    def getContours(self, parent):
        # Find the contours using binary image
        contours, hierarchy = cv2.findContours(parent.cvImage, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        return contours[0]

    def getAspectRatio(self, cnt):
        x, y, w, h = cv2.boundingRect(cnt)
        aspect_ratio = float(w) / h
        return aspect_ratio

    def getExtent(self, cnt):
        area = cv2.contourArea(cnt)
        x, y, w, h = cv2.boundingRect(cnt)
        rect_area = w * h
        extent = float(area) / rect_area
        return extent

    def getSolidity(self, cnt):
        area = cv2.contourArea(cnt)
        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        solidity = float(area) / hull_area
        return solidity

    def getEquivalentDiameter(self, cnt):
        area = cv2.contourArea(cnt)
        equi_diameter = numpy.sqrt(4 * area / numpy.pi)
        return equi_diameter

class ProjectMenuDropdown(tk.Menu):
    def __init__(self):
        tk.Menu.__init__(self, tearoff=False)

    def equalize(self, parent):
        """
        HSV Equalize
        """
        hsvImg, hist_original, hist_equalized = self.equalize_hsv_histogram(parent.cvImage)
        cv2.imshow('Wyrownany HSV', hsvImg)

        helper = self.Helper
        helper.createHistogram(self, hsvImg, "Histogram HSV po wyrownaniu")
        helper.createHistogram(self, parent.cvImage, "Histogram oryginalny")
        plt.show()

    def equalize_hsv_histogram(self, image):

        # Konwersja z RGB do HSV przy użyciu cvtColor
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

        # Wyodrębnienie kanału V
        v = hsv[:, :, 2]

        # Tworzenie histogramu i obliczanie funkcji rozkładu prawdopodobieństwa
        v_hist, bins = numpy.histogram(v, bins=256, range=(0, 255))
        cumulativeDistribution = v_hist.cumsum()

        # Tworzenie nowego histogramu wyrównanego
        cumulativeDistributionMasked = numpy.ma.masked_equal(cumulativeDistribution, 0)
        cumulativeDistributionMasked = (cumulativeDistributionMasked - cumulativeDistributionMasked.min()) * 255 \
                                       / (cumulativeDistributionMasked.max() - cumulativeDistributionMasked.min())
        cumulativeDistribution = numpy.ma.filled(cumulativeDistributionMasked, 0).astype('uint8')


        # Przeprowadzenie transformacji odwrotnej na nowym histogramie V
        equalized = cumulativeDistribution[v]
        hsv[:, :, 2] = equalized

        # Konwersja z powrotem z HSV do RGB
        image_eq = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

        # Tworzenie histogramów
        hist_original = cv2.calcHist([v], [0], None, [256], [0, 256])

        hist_equalized = cv2.calcHist([equalized], [0], None, [256], [0, 256])

        return image_eq, hist_original, hist_equalized

    class Helper(tk.Menu):
        def __init__(self):
            tk.Menu.__init__(self, tearoff=False)

        def createHistogram(self, img, title):
            """
            Wyświetla histogram dla obrazu kolorowego
            """

            y_axis = [0 for i in range(256)]
            x_axis = [i for i in range(256)]

            # pobranie wartosci dla kazdego kanalu
            red_channel = [i[0] for i in img[1]]
            green_channel = [i[1] for i in img[1]]
            blue_channel = [i[2] for i in img[1]]

            # stworzenie tablicy
            def compute_values_count(channel_name):
                for value in channel_name:
                    luminence_value = int(value)
                    y_axis[luminence_value] += 1

            plt.style.use('bmh')
            plt.figure()

            compute_values_count(red_channel)
            plt.bar(x_axis, y_axis, color='red', alpha=0.8)

            y_axis = [0 for i in range(256)]
            compute_values_count(green_channel)
            plt.bar(x_axis, y_axis, color='green', alpha=0.8)

            y_axis = [0 for i in range(256)]
            compute_values_count(blue_channel)
            plt.bar(x_axis, y_axis, color='blue', alpha=0.8)
            plt.title(title)


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
        self.lab4menu = tk.Menu(self, tearoff=0)
        self.lab5menu = tk.Menu(self, tearoff=0)
        self.lab6menu = tk.Menu(self, tearoff=0)
        self.lab6menu = tk.Menu(self, tearoff=0)
        self.lab3menuMathCascade = tk.Menu(self.lab3menu, tearoff=0)
        self.projectMenu = tk.Menu(self.lab3menu, tearoff=0)
        self.scalingMenu = tk.Menu(self, tearoff=0)
        self.fill(parent)

        self.fileMenuDropdown = FileMenuDropdown()
        self.lab1MenuDropdown = Lab1MenuDropdown()
        self.lab2MenuDropdown = Lab2MenuDropdown()
        self.lab3MenuDropdown = Lab3MenuDropdown()
        self.lab4MenuDropdown = Lab4MenuDropdown()
        self.lab5MenuDropdown = Lab5MenuDropdown()
        self.lab6MenuDropdown = Lab6MenuDropdown()
        self.projectMenuDropdown = ProjectMenuDropdown()

        self.resizeDropdown = Scaling()

    def fill(self, parent: Program):
        self.add_cascade(label="Plik", menu=self.menu)
        self.menu.add_command(label="Otwórz", command=lambda: self.fileMenuDropdown.loadImage(parent, 0))
        self.menu.add_command(label="Otwórz kolorowy", command=lambda: self.fileMenuDropdown.loadImage(parent, -1))
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
        self.lab2menu.add_command(label="Progowanie obrazu z zachowaniem szarosci",
                                  command=lambda: self.lab2MenuDropdown.thresholdImageWithGreyscale(parent))
        self.lab2menu.add_command(label="Progowanie 2 progami",
                                  command=lambda: self.lab2MenuDropdown.imageThresholdWithTwoValues(parent))

        self.lab2menu.add_command(label="Progowanie 2 progami z zachowaniem szarosci",
                                  command=lambda: self.lab2MenuDropdown.imageThresholdWithTwoValuesGreyscaleLevel(
                                      parent))

        self.add_cascade(label="Lab3", menu=self.lab3menu)
        self.lab3menu.add_cascade(label="Operacje matematyczne", menu=self.lab3menuMathCascade)
        self.lab3menuMathCascade.add_command(label="Dodawanie",
                                             command=lambda: self.lab3MenuDropdown.mathAdd(parent))
        self.lab3menuMathCascade.add_command(label="Dodawanie z wysyceniem",
                                             command=lambda: self.lab3MenuDropdown.mathAdd(parent))
        self.lab3menuMathCascade.add_command(label="AND",
                                             command=lambda: self.lab3MenuDropdown.mathAnd(parent))
        self.lab3menuMathCascade.add_command(label="OR",
                                             command=lambda: self.lab3MenuDropdown.mathOr(parent))
        self.lab3menuMathCascade.add_command(label="NOT",
                                             command=lambda: self.lab3MenuDropdown.mathNot(parent))
        self.lab3menuMathCascade.add_command(label="XOR",
                                             command=lambda: self.lab3MenuDropdown.mathXor(parent))
        self.lab3menuMathCascade.add_command(label="Dodawanie liczby",
                                             command=lambda: self.lab3MenuDropdown.mathAddValue(parent))
        self.lab3menuMathCascade.add_command(label="Dzielenie przez liczbe",
                                             command=lambda: self.lab3MenuDropdown.mathDivideValue(parent))

        self.add_cascade(label="Lab4", menu=self.lab4menu)
        self.lab4menu.add_command(label="Wygladzanie liniowe",
                                  command=lambda: self.lab4MenuDropdown.linearSmoothing(parent))
        self.lab4menu.add_command(label="Wyostrzanie liniowe",
                                  command=lambda: self.lab4MenuDropdown.linearSharpening(parent))
        self.lab4menu.add_command(label="Sobel kierunkowy",
                                  command=lambda: self.lab4MenuDropdown.sobelDirectional(parent))

        self.add_cascade(label="Lab5", menu=self.lab5menu)
        self.lab5menu.add_command(label="Detekcja krawedzi sobela",
                                  command=lambda: self.lab5MenuDropdown.imageSobelControler(parent))
        self.lab5menu.add_command(label="Detekcja krawedzi prwitta",
                                  command=lambda: self.lab5MenuDropdown.imagePrewittControler(parent))
        self.lab5menu.add_command(label="Detekcja krawedzi canny",
                                  command=lambda: self.lab5MenuDropdown.imageCannyControler(parent))
        self.lab5menu.add_command(label="Progowanie interaktywne",
                                  command=lambda: self.lab5MenuDropdown.interactiveThreshold(parent))

        self.add_cascade(label="Lab6", menu=self.lab6menu)
        self.lab6menu.add_command(label="Erozja",
                                  command=lambda: self.lab6MenuDropdown.erode(parent))
        self.lab6menu.add_command(label="Dylacja",
                                  command=lambda: self.lab6MenuDropdown.dilate(parent))
        self.lab6menu.add_command(label="Morfologficzne otwarcie",
                                  command=lambda: self.lab6MenuDropdown.morphologyOpenClose(parent, cv2.MORPH_OPEN))
        self.lab6menu.add_command(label="Morfologficzne zamkniecie",
                                  command=lambda: self.lab6MenuDropdown.morphologyOpenClose(parent, cv2.MORPH_CLOSE))
        self.lab6menu.add_command(label="Momenty",
                                  command=lambda: self.lab6MenuDropdown.moments(parent))
        self.lab6menu.add_command(label="Pole powierzchni i obwod",
                                  command=lambda: self.lab6MenuDropdown.areaPerimeter(parent))
        self.lab6menu.add_command(label="Pobierz wszystkie dane",
                                  command=lambda: self.lab6MenuDropdown.getAllData(parent))
        self.lab6menu.add_command(label="Pobierz wszystkie dane i wyeksportuj",
                                  command=lambda: self.lab6MenuDropdown.getDataAndExport(parent))

        self.add_cascade(label="Projekt", menu=self.projectMenu)
        self.projectMenu.add_command(label="Equalizacja histogramu",
                                  command=lambda: self.projectMenuDropdown.equalize(parent))

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
