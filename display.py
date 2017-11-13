# Skeleton Tk interface example
# Written by Bruce Maxwell
# Modified by Stephanie Taylor
#
# CS 251
# Spring 2015

import Tkinter as tk
import tkFileDialog
import math
import random
import view
import numpy as np
import data
import analysis
from scipy import stats
import os
from PIL import Image
import datetime


# create a class to build and manage the display
class DisplayApp:

    def __init__(self, width, height):

        # create a tk object, which is the root window
        self.root = tk.Tk()

        # width and height of the window
        self.initDx = width
        self.initDy = height

        # set up the geometry for the window
        self.root.geometry("%dx%d+50+30" % (self.initDx, self.initDy))

        # set the title of the window
        self.root.title("A-lab GUI")

        # set the maximum size of the window for resizing
        self.root.maxsize(1600, 900)

        # set the shape, distribution choice and color, and density option and other fields
        self.distributionChoice = None
        self.colorOption = None
        self.shapeChoice = None
        self.densityOption = None
        self.columnsChoices = None
        self.pca_cols_choices = None
        self.linRegChoices = None
        self.cluster_header_choices = None

        self.scale_label = None
        self.lin_reg_label = None
        self.rotation_label = None
        self.x_label = None
        self.y_label = None
        self.z_label = None

        self.lin_reg_line = None

        self.canvas = None

        self.normalized_non_spatial = None
        # setup dx, the radius of the random points
        self.size = None

        # data objects for the program
        self.data_object = None
        self.data_to_plot = None
        self.pca_data_object = None
        self.pca_data_objects_list = []

        self.use_pca_data_object = False
        self.cluster_preselected_color_scheme = False
        self.cluster_mode = False
        self.pca_listbox = None
        self.cntlframewidth = None
        self.originalExtent = None

        # create view object
        self.view_object = view.View()

        # implement axes
        self.axes = np.matrix([[0, 0, 0, 1],
                               [1, 0, 0, 1],
                               [0, 0, 0, 1],
                               [0, 1, 0, 1],
                               [0, 0, 0, 1],
                               [0, 0, 1, 1]])

        # implement linear regression
        self.reg_line_objects = []
        self.reg_end_points = None

        # setup the menus
        self.buildMenus()

        # build the controls
        self.buildControls()

        # build the Canvas
        self.buildCanvas()

        # bring the window to the front
        self.root.lift()

        # - do idle events here to get actual canvas size
        self.root.update_idletasks()

        # now we can ask the size of the canvas
        print self.canvas.winfo_geometry()

        # set up the key bindings
        self.setBindings()

        # instatiate the axes
        self.x_axis = None
        self.y_axis = None
        self.z_axis = None
        self.graphics_lines = [self.x_axis, self.y_axis, self.z_axis]

        # build the axes
        self.buildAxes()

        # set up the application state
        self.objects = []  # list of data objects that will be drawn in the canvas
        self.data = None  # will hold the raw data someday.
        self.baseClick = None  # used to keep track of mouse movement for translation
        self.baseClick2 = None  # used to keep track of mouse movement for rotation
        self.baseClick3 = None  # used to keep track of mouse movement for scaling
        self.view_object_clone = None

        self.data_object = None  # to read and hold the file's data

    def buildAxes(self):

        # build the VTM
        vtm = self.view_object.build()

        # multiply the axis endpoints by the VTM
        axes_points = (vtm * self.axes.T).T
        self.x_axis = self.canvas.create_line(axes_points[0, 0], axes_points[0, 1],
                                              axes_points[1, 0], axes_points[1, 1], fill="purple")
        self.y_axis = self.canvas.create_line(axes_points[2, 0], axes_points[2, 1],
                                              axes_points[3, 0], axes_points[3, 1], fill="blue")
        self.z_axis = self.canvas.create_line(axes_points[4, 0], axes_points[4, 1],
                                              axes_points[5, 0], axes_points[5, 1], fill="brown")
        self.graphics_lines = [self.x_axis, self.y_axis, self.z_axis]

        # add labels to the axes
        self.x_label = self.canvas.create_text(axes_points[1, 0]+10, axes_points[1, 1]+10, text="x", fill="purple")
        self.y_label = self.canvas.create_text(axes_points[3, 0], axes_points[3, 1]-10, text="y", fill="blue")
        self.z_label = self.canvas.create_text(axes_points[5, 0]+5, axes_points[5, 1]+5, text="z", fill="brown")

        # return vtm

    def updateAxes(self):

        # build the VTM
        vtm = self.view_object.build()

        # multiply the axis endpoints by the VTM
        axes_points = (vtm * self.axes.T).T

        # update the coordinates of each line object

        self.canvas.coords(self.graphics_lines[0], axes_points[0, 0], axes_points[0, 1],
                           axes_points[1, 0], axes_points[1, 1])
        self.canvas.coords(self.graphics_lines[1], axes_points[2, 0], axes_points[2, 1],
                           axes_points[3, 0], axes_points[3, 1])
        self.canvas.coords(self.graphics_lines[2], axes_points[4, 0], axes_points[4, 1],
                           axes_points[5, 0], axes_points[5, 1])

        # update coordinates of the labels
        self.canvas.coords(self.x_label, axes_points[1, 0]+10, axes_points[1, 1])
        self.canvas.coords(self.y_label, axes_points[3, 0], axes_points[3, 1]-10)
        self.canvas.coords(self.z_label, axes_points[5, 0]+5, axes_points[5, 1]+5)

    def buildPoints(self, headers):
        print "building points"

        # delete the regression lines first
        if len(self.reg_line_objects) != 0:
            self.canvas.delete(self.reg_line_objects[0])
        self.reg_line_objects = []

        # keep reference to old data object
        old_data_object = self.data_object

        # handle plotting of pca data
        if self.pca_data_object is not None and self.use_pca_data_object:

            self.data_object = self.pca_data_object

            # allow for plotting eigenvalues and original numeric data
            # add missing columns
            for i in range(len(headers)-1):
                if headers[i] not in self.data_object.get_headers():
                    col = [headers[i], "numeric"]
                    items = old_data_object.get_data([headers[i]])
                    for k in range(items.shape[0]):
                        col.append(items[k, 0])
                    self.data_object.add_column(col)

        # handle plotting clustered data: create dictionary of colors if user wants preselected color scheme
        if self.cluster_mode:
            cluster_ids = self.data_object.get_data(["ids"])
            # get unique cluster ids
            unique_cluster_ids = list(set(cluster_ids[:, 0].flat))
            color_dict = {}
            color_options = ["blue", "red", "black", "orange", "green", "coral", "violet", "navy", "firebrick",
                             "DeepPink", "LightGray", "SlateGray", "PaleVioletRed", 'DarkGoldenrod',  'DarkGoldenrod1',  'DarkGoldenrod2',  'DarkGoldenrod3',  'DarkGoldenrod4',  'dark gray',  'DarkGray',  'dark green',  'DarkGreen',  'dark grey',  'DarkGrey',  'dark khaki',  'DarkKhaki',  'dark magenta',  'DarkMagenta',  'dark olive green',  'DarkOliveGreen',  'DarkOliveGreen1',  'DarkOliveGreen2',  'DarkOliveGreen3',  'DarkOliveGreen4',  'dark orange',  'DarkOrange',  'DarkOrange1',  'DarkOrange2',  'DarkOrange3',  'DarkOrange4',  'dark orchid',  'DarkOrchid',  'DarkOrchid1',  'DarkOrchid2',  'DarkOrchid3',  'DarkOrchid4',  'dark red',  'DarkRed',  'dark salmon',  'DarkSalmon',  'dark sea green',  'DarkSeaGreen',  'DarkSeaGreen1',  'DarkSeaGreen2',  'DarkSeaGreen3',  'DarkSeaGreen4',  'dark slate blue',  'DarkSlateBlue',  'dark slate gray',  'DarkSlateGray',  'DarkSlateGray1',  'DarkSlateGray2',  'DarkSlateGray3',  'DarkSlateGray4',  'dark slate grey',  'DarkSlateGrey',  'dark turquoise',  'DarkTurquoise',  'dark violet',  'DarkViolet',  'deep pink',  'DeepPink',  'DeepPink1',  'DeepPink2',  'DeepPink3',  'DeepPink4',  'deep sky blue',  'DeepSkyBlue',  'DeepSkyBlue1',  'DeepSkyBlue2',  'DeepSkyBlue3',  'DeepSkyBlue4',  'dim gray',  'DimGray',  'dim grey',  'DimGrey',  'dodger blue',  'DodgerBlue',  'DodgerBlue1',  'DodgerBlue2',  'DodgerBlue3',  'DodgerBlue4',  'firebrick',  'firebrick1',  'firebrick2',  'firebrick3',  'firebrick4',   'forest green',  'ForestGreen',  'gainsboro',  'gold',  'gold1',  'gold2',  'gold3',  'gold4',  'goldenrod',  'goldenrod1',  'goldenrod2',  'goldenrod3',  'goldenrod4',  'gray',  'gray0',  'gray1',  'gray10',  'gray100',  'gray11',  'gray12',  'gray13',  'gray14',  'gray15',  'gray16',  'gray17',  'gray18',  'gray19',  'gray2',  'gray20',  'gray21',  'gray22',  'gray23',  'gray24',  'gray25',  'gray26',  'gray27',  'gray28',  'gray29',  'gray3',  'gray30',  'gray31',  'gray32',  'gray33',  'gray34',  'gray35',  'gray36',  'gray37',  'gray38',  'gray39',  'gray4',  'gray40',  'gray41',  'gray42',  'gray43',  'gray44',  'gray45',  'gray46',  'gray47',  'gray48',  'gray49',  'gray5',  'gray50',  'gray51',  'gray52',  'gray53',  'gray54',  'gray55',  'gray56',  'gray57',  'gray58',  'gray59',  'gray6',  'gray60',  'gray61',  'gray62',  'gray63',  'gray64',  'gray65',  'gray66',  'gray67',  'gray68',  'gray69',  'gray7',  'gray70',  'gray71',  'gray72',  'gray73',  'gray74',  'gray75',  'gray76',  'gray77',  'gray78',  'gray79',  'gray8',  'gray80',  'gray81',  'gray82',  'gray83',  'gray84',  'gray85',  'gray86',  'gray87',  'gray88',  'gray89',  'gray9',  'gray90',  'gray91',  'gray92',  'gray93',  'gray94',  'gray95',  'gray96',  'gray97',  'gray98',  'gray99',  'green',  'green1',  'green2',  'green3',  'green4',  'green yellow',  'GreenYellow',  'grey',  'grey0',  'grey1',  'grey10',  'grey100',  'grey11',  'grey12',  'grey13',  'grey14',  'grey15',  'grey16',  'grey17',  'grey18',  'grey19',  'grey2',  'grey20',  'grey21',  'grey22',  'grey23',  'grey24',  'grey25',  'grey26',  'grey27',  'grey28',  'grey29',  'grey3',  'grey30',  'grey31',  'grey32',  'grey33',  'grey34',  'grey35',  'grey36',  'grey37',  'grey38',  'grey39',  'grey4',  'grey40',  'grey41',  'grey42',  'grey43',  'grey44',  'grey45',  'grey46',  'grey47',  'grey48',  'grey49',  'grey5',  'grey50',  'grey51',  'grey52',  'grey53',  'grey54',  'grey55',  'grey56',  'grey57',  'grey58',  'grey59',  'grey6',  'grey60',  'grey61',  'grey62',  'grey63',  'grey64',  'grey65',  'grey66',  'grey67',  'grey68',  'grey69',  'grey7',  'grey70',  'grey71',  'grey72',  'grey73',  'grey74',  'grey75',  'grey76',  'grey77',  'grey78',  'grey79',  'grey8',  'grey80',  'grey81',  'grey82',  'grey83',  'grey84',  'grey85',  'grey86',  'grey87',  'grey88',  'grey89',  'grey9',  'grey90',  'grey91',  'grey92',  'grey93',  'grey94',  'grey95',  'grey96',  'grey97',  'grey98',  'grey99',  'honeydew',  'honeydew1',  'honeydew2',  'honeydew3',  'honeydew4',  'hot pink',  'HotPink',  'HotPink1',  'HotPink2',  'HotPink3',  'HotPink4',  'indian red',  'IndianRed',  'IndianRed1',  'IndianRed2',  'IndianRed3',  'IndianRed4',  'ivory',  'ivory1',  'ivory2',  'ivory3',  'ivory4',  'khaki',  'khaki1',  'khaki2',  'khaki3',  'khaki4',  'lavender',  'lavender blush',  'LavenderBlush',  'LavenderBlush1',  'LavenderBlush2',  'LavenderBlush3',  'LavenderBlush4',  'lawn green',  'LawnGreen',  'lemon chiffon',  'LemonChiffon',  'LemonChiffon1',  'LemonChiffon2',  'LemonChiffon3',  'LemonChiffon4',  'light blue',  'LightBlue',  'LightBlue1',  'LightBlue2',  'LightBlue3',  'LightBlue4',  'light coral',  'LightCoral',  'light cyan',  'LightCyan',  'LightCyan1',  'LightCyan2',  'LightCyan3',  'LightCyan4',  'light goldenrod',  'LightGoldenrod',  'LightGoldenrod1',  'LightGoldenrod2',  'LightGoldenrod3',  'LightGoldenrod4',  'light goldenrod yellow',  'LightGoldenrodYellow',  'light gray',  'LightGray',  'light green',  'LightGreen',  'light grey',  'LightGrey',  'light pink',  'LightPink',  'LightPink1',  'LightPink2',  'LightPink3',  'LightPink4',  'light salmon',  'LightSalmon',  'LightSalmon1',  'LightSalmon2',  'LightSalmon3',  'LightSalmon4',  'light sea green',  'LightSeaGreen',  'light sky blue',  'LightSkyBlue',  'LightSkyBlue1',  'LightSkyBlue2',  'LightSkyBlue3',  'LightSkyBlue4',  'light slate blue',  'LightSlateBlue',  'light slate gray',  'LightSlateGray',  'light slate grey',  'LightSlateGrey',  'light steel blue',  'LightSteelBlue',  'LightSteelBlue1',  'LightSteelBlue2',  'LightSteelBlue3',  'LightSteelBlue4',  'light yellow',  'LightYellow',  'LightYellow1',  'LightYellow2',  'LightYellow3',  'LightYellow4',  'lime green',  'LimeGreen',  'linen',  'magenta',  'magenta1',  'magenta2',  'magenta3',  'magenta4',  'maroon',  'maroon1',  'maroon2',  'maroon3',  'maroon4',  'medium aquamarine',  'MediumAquamarine',  'medium blue',  'MediumBlue',  'medium orchid',  'MediumOrchid',  'MediumOrchid1',  'MediumOrchid2',  'MediumOrchid3',  'MediumOrchid4',  'medium purple',  'MediumPurple',  'MediumPurple1',  'MediumPurple2',  'MediumPurple3',  'MediumPurple4',  'medium sea green',  'MediumSeaGreen',  'medium slate blue',  'MediumSlateBlue',  'medium spring green',  'MediumSpringGreen',  'medium turquoise',  'MediumTurquoise',  'medium violet red',  'MediumVioletRed',  'midnight blue',  'MidnightBlue',  'mint cream',  'MintCream',  'misty rose',  'MistyRose',  'MistyRose1',  'MistyRose2',  'MistyRose3',  'MistyRose4',  'moccasin', 'navy',  'navy blue',  'NavyBlue',  'old lace',  'OldLace',  'olive drab',  'OliveDrab',  'OliveDrab1',  'OliveDrab2',  'OliveDrab3',  'OliveDrab4',  'orange',  'orange1',  'orange2',  'orange3',  'orange4',  'orange red',  'OrangeRed',  'OrangeRed1',  'OrangeRed2',  'OrangeRed3',  'OrangeRed4',  'orchid',  'orchid1',  'orchid2',  'orchid3',  'orchid4',  'pale goldenrod',  'PaleGoldenrod',  'pale green',  'PaleGreen',  'PaleGreen1',  'PaleGreen2',  'PaleGreen3',  'PaleGreen4',  'pale turquoise',  'PaleTurquoise',  'PaleTurquoise1',  'PaleTurquoise2',  'PaleTurquoise3',  'PaleTurquoise4',  'pale violet red',  'PaleVioletRed',  'PaleVioletRed1',  'PaleVioletRed2',  'PaleVioletRed3',  'PaleVioletRed4',  'papaya whip',  'PapayaWhip',  'peach puff',  'PeachPuff',  'PeachPuff1',  'PeachPuff2',  'PeachPuff3',  'PeachPuff4',  'peru',  'pink',  'pink1',  'pink2',  'pink3',  'pink4',  'plum',  'plum1',  'plum2',  'plum3',  'plum4',  'powder blue',  'PowderBlue',  'purple',  'purple1',  'purple2',  'purple3',  'purple4',  'red',  'red1',  'red2',  'red3',  'red4',  'rosy brown',  'RosyBrown',  'RosyBrown1',  'RosyBrown2',  'RosyBrown3',  'RosyBrown4',  'royal blue',  'RoyalBlue',  'RoyalBlue1',  'RoyalBlue2',  'RoyalBlue3',  'RoyalBlue4',  'saddle brown',  'SaddleBrown',  'salmon',  'salmon1',  'salmon2',  'salmon3',  'salmon4',  'sandy brown',  'SandyBrown',  'sea green',  'SeaGreen',  'SeaGreen1',  'SeaGreen2',  'SeaGreen3',  'SeaGreen4',  'seashell',  'seashell1',  'seashell2',  'seashell3',  'seashell4',  'sienna',  'sienna1',  'sienna2',  'sienna3',  'sienna4',  'sky blue',  'SkyBlue',  'SkyBlue1',  'SkyBlue2',  'SkyBlue3',  'SkyBlue4',  'slate blue',  'SlateBlue',  'SlateBlue1',  'SlateBlue2',  'SlateBlue3',  'SlateBlue4' ,  'snow',  'snow1',  'snow2',  'snow3',  'snow4',  'spring green',  'SpringGreen',  'SpringGreen1',  'SpringGreen2',  'SpringGreen3',  'SpringGreen4',  'steel blue',  'SteelBlue',  'SteelBlue1',  'SteelBlue2',  'SteelBlue3',  'SteelBlue4',  'tan',  'tan1',  'tan2',  'tan3',  'tan4',  'thistle',  'thistle1',  'thistle2',  'thistle3',  'thistle4',  'tomato',  'tomato1',  'tomato2',  'tomato3',  'tomato4',  'turquoise',  'turquoise1',  'turquoise2',  'turquoise3',  'turquoise4',  'violet',  'violet red',  'VioletRed',  'VioletRed1',  'VioletRed2',  'VioletRed3',  'VioletRed4',  'wheat',  'wheat1',  'wheat2',  'wheat3',  'wheat4', 'yellow',  'yellow1',  'yellow2',  'yellow3',  'yellow4',  'yellow green',  'YellowGreen', "blue", "red", "black", "orange", "green", "coral", "violet", "navy", "firebrick",
                             "DeepPink", "LightGray", "SlateGray", "PaleVioletRed", 'DarkGoldenrod',  'DarkGoldenrod1',  'DarkGoldenrod2',  'DarkGoldenrod3',  'DarkGoldenrod4',  'dark gray',  'DarkGray', "blue", "red", "black", "orange", "green", "coral", "violet", "navy", "firebrick",
                             "DeepPink", "LightGray", "SlateGray", "PaleVioletRed",
                             'DarkGoldenrod',  'DarkGoldenrod1',  'DarkGoldenrod2',  'DarkGoldenrod3',  'DarkGoldenrod4',  'dark gray',  'DarkGray',  'dark green',  'DarkGreen',  'dark grey',  'DarkGrey',  'dark khaki',  'DarkKhaki',  'dark magenta',  'DarkMagenta',  'dark olive green',  'DarkOliveGreen',  'DarkOliveGreen1',  'DarkOliveGreen2',  'DarkOliveGreen3',  'DarkOliveGreen4',  'dark orange',  'DarkOrange',  'DarkOrange1',  'DarkOrange2',  'DarkOrange3',  'DarkOrange4',  'dark orchid',  'DarkOrchid',  'DarkOrchid1',  'DarkOrchid2',  'DarkOrchid3',  'DarkOrchid4',  'dark red',  'DarkRed',  'dark salmon',  'DarkSalmon',  'dark sea green',  'DarkSeaGreen',  'DarkSeaGreen1',  'DarkSeaGreen2',  'DarkSeaGreen3',  'DarkSeaGreen4',  'dark slate blue',  'DarkSlateBlue',  'dark slate gray',  'DarkSlateGray',  'DarkSlateGray1',  'DarkSlateGray2',  'DarkSlateGray3',  'DarkSlateGray4',  'dark slate grey',  'DarkSlateGrey',  'dark turquoise',  'DarkTurquoise',  'dark violet',  'DarkViolet',  'deep pink',  'DeepPink',  'DeepPink1',  'DeepPink2',  'DeepPink3',  'DeepPink4',  'deep sky blue',  'DeepSkyBlue',  'DeepSkyBlue1',  'DeepSkyBlue2',  'DeepSkyBlue3',  'DeepSkyBlue4',  'dim gray',  'DimGray',  'dim grey',  'DimGrey',  'dodger blue',  'DodgerBlue',  'DodgerBlue1',  'DodgerBlue2',  'DodgerBlue3',  'DodgerBlue4',  'firebrick',  'firebrick1',  'firebrick2',  'firebrick3',  'firebrick4',   'forest green',  'ForestGreen',  'gainsboro',  'gold',  'gold1',  'gold2',  'gold3',  'gold4',  'goldenrod',  'goldenrod1',  'goldenrod2',  'goldenrod3',  'goldenrod4',  'gray',  'gray0',  'gray1',  'gray10',  'gray100',  'gray11',  'gray12',  'gray13',  'gray14',  'gray15',  'gray16',  'gray17',  'gray18',  'gray19',  'gray2',  'gray20',  'gray21',  'gray22',  'gray23',  'gray24',  'gray25',  'gray26',  'gray27',  'gray28',  'gray29',  'gray3',  'gray30',  'gray31',  'gray32',  'gray33',  'gray34',  'gray35',  'gray36',  'gray37',  'gray38',  'gray39',  'gray4',  'gray40',  'gray41',  'gray42',  'gray43',  'gray44',  'gray45',  'gray46',  'gray47',  'gray48',  'gray49',  'gray5',  'gray50',  'gray51',  'gray52',  'gray53',  'gray54',  'gray55',  'gray56',  'gray57',  'gray58',  'gray59',  'gray6',  'gray60',  'gray61',  'gray62',  'gray63',  'gray64',  'gray65',  'gray66',  'gray67',  'gray68',  'gray69',  'gray7',  'gray70',  'gray71',  'gray72',  'gray73',  'gray74',  'gray75',  'gray76',  'gray77',  'gray78',  'gray79',  'gray8',  'gray80',  'gray81',  'gray82',  'gray83',  'gray84',  'gray85',  'gray86',  'gray87',  'gray88',  'gray89',  'gray9',  'gray90',  'gray91',  'gray92',  'gray93',  'gray94',  'gray95',  'gray96',  'gray97',  'gray98',  'gray99',  'green',  'green1',  'green2',  'green3',  'green4',  'green yellow',  'GreenYellow',  'grey',  'grey0',  'grey1',  'grey10',  'grey100',  'grey11',  'grey12',  'grey13',  'grey14',  'grey15',  'grey16',  'grey17',  'grey18',  'grey19',  'grey2',  'grey20',  'grey21',  'grey22',  'grey23',  'grey24',  'grey25',  'grey26',  'grey27',  'grey28',  'grey29',  'grey3',  'grey30',  'grey31',  'grey32',  'grey33',  'grey34',  'grey35',  'grey36',  'grey37',  'grey38',  'grey39',  'grey4',  'grey40',  'grey41',  'grey42',  'grey43',  'grey44',  'grey45',  'grey46',  'grey47',  'grey48',  'grey49',  'grey5',  'grey50',  'grey51',  'grey52',  'grey53',  'grey54',  'grey55',  'grey56',  'grey57',  'grey58',  'grey59',  'grey6',  'grey60',  'grey61',  'grey62',  'grey63',  'grey64',  'grey65',  'grey66',  'grey67',  'grey68',  'grey69',  'grey7',  'grey70',  'grey71',  'grey72',  'grey73',  'grey74',  'grey75',  'grey76',  'grey77',  'grey78',  'grey79',  'grey8',  'grey80',  'grey81',  'grey82',  'grey83',  'grey84',  'grey85',  'grey86',  'grey87',  'grey88',  'grey89',  'grey9',  'grey90',  'grey91',  'grey92',  'grey93',  'grey94',  'grey95',  'grey96',  'grey97',  'grey98',  'grey99',  'honeydew',  'honeydew1',  'honeydew2',  'honeydew3',  'honeydew4',  'hot pink',  'HotPink',  'HotPink1',  'HotPink2',  'HotPink3',  'HotPink4',  'indian red',  'IndianRed',  'IndianRed1',  'IndianRed2',  'IndianRed3',  'IndianRed4',  'ivory',  'ivory1',  'ivory2',  'ivory3',  'ivory4',  'khaki',  'khaki1',  'khaki2',  'khaki3',  'khaki4',  'lavender',  'lavender blush',  'LavenderBlush',  'LavenderBlush1',  'LavenderBlush2',  'LavenderBlush3',  'LavenderBlush4',  'lawn green',  'LawnGreen',  'lemon chiffon',  'LemonChiffon',  'LemonChiffon1',  'LemonChiffon2',  'LemonChiffon3',  'LemonChiffon4',  'light blue',  'LightBlue',  'LightBlue1',  'LightBlue2',  'LightBlue3',  'LightBlue4',  'light coral',  'LightCoral',  'light cyan',  'LightCyan',  'LightCyan1',  'LightCyan2',  'LightCyan3',  'LightCyan4',  'light goldenrod',  'LightGoldenrod',  'LightGoldenrod1',  'LightGoldenrod2',  'LightGoldenrod3',  'LightGoldenrod4',  'light goldenrod yellow',  'LightGoldenrodYellow',  'light gray',  'LightGray',  'light green',  'LightGreen',  'light grey',  'LightGrey',  'light pink',  'LightPink',  'LightPink1',  'LightPink2',  'LightPink3',  'LightPink4',  'light salmon',  'LightSalmon',  'LightSalmon1',  'LightSalmon2',  'LightSalmon3',  'LightSalmon4',  'light sea green',  'LightSeaGreen',  'light sky blue',  'LightSkyBlue',  'LightSkyBlue1',  'LightSkyBlue2',  'LightSkyBlue3',  'LightSkyBlue4',  'light slate blue',  'LightSlateBlue',  'light slate gray',  'LightSlateGray',  'light slate grey',  'LightSlateGrey',  'light steel blue',  'LightSteelBlue',  'LightSteelBlue1',  'LightSteelBlue2',  'LightSteelBlue3',  'LightSteelBlue4',  'light yellow',  'LightYellow',  'LightYellow1',  'LightYellow2',  'LightYellow3',  'LightYellow4',  'lime green',  'LimeGreen',  'linen',  'magenta',  'magenta1',  'magenta2',  'magenta3',  'magenta4',  'maroon',  'maroon1',  'maroon2',  'maroon3',  'maroon4',  'medium aquamarine',  'MediumAquamarine',  'medium blue',  'MediumBlue',  'medium orchid',  'MediumOrchid',  'MediumOrchid1',  'MediumOrchid2',  'MediumOrchid3',  'MediumOrchid4',  'medium purple',  'MediumPurple',  'MediumPurple1',  'MediumPurple2',  'MediumPurple3',  'MediumPurple4',  'medium sea green',  'MediumSeaGreen',  'medium slate blue',  'MediumSlateBlue',  'medium spring green',  'MediumSpringGreen',  'medium turquoise',  'MediumTurquoise',  'medium violet red',  'MediumVioletRed',  'midnight blue',  'MidnightBlue',  'mint cream',  'MintCream',  'misty rose',  'MistyRose',  'MistyRose1',  'MistyRose2',  'MistyRose3',  'MistyRose4',  'moccasin', 'navy',  'navy blue',  'NavyBlue',  'old lace',  'OldLace',  'olive drab',  'OliveDrab',  'OliveDrab1',  'OliveDrab2',  'OliveDrab3',  'OliveDrab4',  'orange',  'orange1',  'orange2',  'orange3',  'orange4',  'orange red',  'OrangeRed',  'OrangeRed1',  'OrangeRed2',  'OrangeRed3',  'OrangeRed4',  'orchid',  'orchid1',  'orchid2',  'orchid3',  'orchid4',  'pale goldenrod',  'PaleGoldenrod',  'pale green',  'PaleGreen',  'PaleGreen1',  'PaleGreen2',  'PaleGreen3',  'PaleGreen4',  'pale turquoise',  'PaleTurquoise',  'PaleTurquoise1',  'PaleTurquoise2',  'PaleTurquoise3',  'PaleTurquoise4',  'pale violet red',  'PaleVioletRed',  'PaleVioletRed1',  'PaleVioletRed2',  'PaleVioletRed3',  'PaleVioletRed4',  'papaya whip',  'PapayaWhip',  'peach puff',  'PeachPuff',  'PeachPuff1',  'PeachPuff2',  'PeachPuff3',  'PeachPuff4',  'peru',  'pink',  'pink1',  'pink2',  'pink3',  'pink4',  'plum',  'plum1',  'plum2',  'plum3',  'plum4',  'powder blue',  'PowderBlue',  'purple',  'purple1',  'purple2',  'purple3',  'purple4',  'red',  'red1',  'red2',  'red3',  'red4',  'rosy brown',  'RosyBrown',  'RosyBrown1',  'RosyBrown2',  'RosyBrown3',  'RosyBrown4',  'royal blue',  'RoyalBlue',  'RoyalBlue1',  'RoyalBlue2',  'RoyalBlue3',  'RoyalBlue4',  'saddle brown',  'SaddleBrown',  'salmon',  'salmon1',  'salmon2',  'salmon3',  'salmon4',  'sandy brown',  'SandyBrown',  'sea green',  'SeaGreen',  'SeaGreen1',  'SeaGreen2',  'SeaGreen3',  'SeaGreen4',  'seashell',  'seashell1',  'seashell2',  'seashell3',  'seashell4',  'sienna',  'sienna1',  'sienna2',  'sienna3',  'sienna4',  'sky blue',  'SkyBlue',  'SkyBlue1',  'SkyBlue2',  'SkyBlue3',  'SkyBlue4',  'slate blue',  'SlateBlue',  'SlateBlue1',  'SlateBlue2',  'SlateBlue3',  'SlateBlue4' ,  'snow',  'snow1',  'snow2',  'snow3',  'snow4',  'spring green',  'SpringGreen',  'SpringGreen1',  'SpringGreen2',  'SpringGreen3',  'SpringGreen4',  'steel blue',  'SteelBlue',  'SteelBlue1',  'SteelBlue2',  'SteelBlue3',  'SteelBlue4',  'tan',  'tan1',  'tan2',  'tan3',  'tan4',  'thistle',  'thistle1',  'thistle2',  'thistle3',  'thistle4',  'tomato',  'tomato1',  'tomato2',  'tomato3',  'tomato4',  'turquoise',  'turquoise1',  'turquoise2',  'turquoise3',  'turquoise4',  'violet',  'violet red',  'VioletRed',  'VioletRed1',  'VioletRed2',  'VioletRed3',  'VioletRed4',  'wheat',  'wheat1',  'wheat2',  'wheat3',  'wheat4', 'yellow',  'yellow1',  'yellow2',  'yellow3',  'yellow4',  'yellow green',  'YellowGreen', 'dark green',  'DarkGreen',  'dark grey',  'DarkGrey',  'dark khaki',  'DarkKhaki',   'dark magenta',  'DarkMagenta',  'dark olive green',  'DarkOliveGreen',  'DarkOliveGreen1',  'DarkOliveGreen2',  'DarkOliveGreen3',  'DarkOliveGreen4',  'dark orange',  'DarkOrange',  'DarkOrange1',  'DarkOrange2',  'DarkOrange3',  'DarkOrange4',  'dark orchid',  'DarkOrchid',  'DarkOrchid1',  'DarkOrchid2',  'DarkOrchid3',  'DarkOrchid4',  'dark red',  'DarkRed',  'dark salmon',  'DarkSalmon',  'dark sea green',  'DarkSeaGreen',  'DarkSeaGreen1',  'DarkSeaGreen2',  'DarkSeaGreen3',  'DarkSeaGreen4',  'dark slate blue',  'DarkSlateBlue',  'dark slate gray',  'DarkSlateGray',  'DarkSlateGray1',  'DarkSlateGray2',  'DarkSlateGray3',  'DarkSlateGray4',  'dark slate grey',  'DarkSlateGrey',  'dark turquoise',  'DarkTurquoise',  'dark violet',  'DarkViolet',  'deep pink',  'DeepPink',  'DeepPink1',  'DeepPink2',  'DeepPink3',  'DeepPink4',  'deep sky blue',  'DeepSkyBlue',  'DeepSkyBlue1',  'DeepSkyBlue2',  'DeepSkyBlue3',  'DeepSkyBlue4',  'dim gray',  'DimGray',  'dim grey',  'DimGrey',  'dodger blue',  'DodgerBlue',  'DodgerBlue1',  'DodgerBlue2',  'DodgerBlue3',  'DodgerBlue4',  'firebrick',  'firebrick1',  'firebrick2',  'firebrick3',  'firebrick4',   'forest green',  'ForestGreen',  'gainsboro',  'gold',  'gold1',  'gold2',  'gold3',  'gold4',  'goldenrod',  'goldenrod1',  'goldenrod2',  'goldenrod3',  'goldenrod4',  'gray',  'gray0',  'gray1',  'gray10',  'gray100',  'gray11',  'gray12',  'gray13',  'gray14',  'gray15',  'gray16',  'gray17',  'gray18',  'gray19',  'gray2',  'gray20',  'gray21',  'gray22',  'gray23',  'gray24',  'gray25',  'gray26',  'gray27',  'gray28',  'gray29',  'gray3',  'gray30',  'gray31',  'gray32',  'gray33',  'gray34',  'gray35',  'gray36',  'gray37',  'gray38',  'gray39',  'gray4',  'gray40',  'gray41',  'gray42',  'gray43',  'gray44',  'gray45',  'gray46',  'gray47',  'gray48',  'gray49',  'gray5',  'gray50',  'gray51',  'gray52',  'gray53',  'gray54',  'gray55',  'gray56',  'gray57',  'gray58',  'gray59',  'gray6',  'gray60',  'gray61',  'gray62',  'gray63',  'gray64',  'gray65',  'gray66',  'gray67',  'gray68',  'gray69',  'gray7',  'gray70',  'gray71',  'gray72',  'gray73',  'gray74',  'gray75',  'gray76',  'gray77',  'gray78',  'gray79',  'gray8',  'gray80',  'gray81',  'gray82',  'gray83',  'gray84',  'gray85',  'gray86',  'gray87',  'gray88',  'gray89',  'gray9',  'gray90',  'gray91',  'gray92',  'gray93',  'gray94',  'gray95',  'gray96',  'gray97',  'gray98',  'gray99',  'green',  'green1',  'green2',  'green3',  'green4',  'green yellow',  'GreenYellow',  'grey',  'grey0',  'grey1',  'grey10',  'grey100',  'grey11',  'grey12',  'grey13',  'grey14',  'grey15',  'grey16',  'grey17',  'grey18',  'grey19',  'grey2',  'grey20',  'grey21',  'grey22',  'grey23',  'grey24',  'grey25',  'grey26',  'grey27',  'grey28',  'grey29',  'grey3',  'grey30',  'grey31',  'grey32',  'grey33',  'grey34',  'grey35',  'grey36',  'grey37',  'grey38',  'grey39',  'grey4',  'grey40',  'grey41',  'grey42',  'grey43',  'grey44',  'grey45',  'grey46',  'grey47',  'grey48',  'grey49',  'grey5',  'grey50',  'grey51',  'grey52',  'grey53',  'grey54',  'grey55',  'grey56',  'grey57',  'grey58',  'grey59',  'grey6',  'grey60',  'grey61',  'grey62',  'grey63',  'grey64',  'grey65',  'grey66',  'grey67',  'grey68',  'grey69',  'grey7',  'grey70',  'grey71',  'grey72',  'grey73',  'grey74',  'grey75',  'grey76',  'grey77',  'grey78',  'grey79',  'grey8',  'grey80',  'grey81',  'grey82',  'grey83',  'grey84',  'grey85',  'grey86',  'grey87',  'grey88',  'grey89',  'grey9',  'grey90',  'grey91',  'grey92',  'grey93',  'grey94',  'grey95',  'grey96',  'grey97',  'grey98',  'grey99',  'honeydew',  'honeydew1',  'honeydew2',  'honeydew3',  'honeydew4',  'hot pink',  'HotPink',  'HotPink1',  'HotPink2',  'HotPink3',  'HotPink4',  'indian red',  'IndianRed',  'IndianRed1',  'IndianRed2',  'IndianRed3',  'IndianRed4',  'ivory',  'ivory1',  'ivory2',  'ivory3',  'ivory4',  'khaki',  'khaki1',  'khaki2',  'khaki3',  'khaki4',  'lavender',  'lavender blush',  'LavenderBlush',  'LavenderBlush1',  'LavenderBlush2',  'LavenderBlush3',  'LavenderBlush4',  'lawn green',  'LawnGreen',  'lemon chiffon',  'LemonChiffon',  'LemonChiffon1',  'LemonChiffon2',  'LemonChiffon3',  'LemonChiffon4',  'light blue',  'LightBlue',  'LightBlue1',  'LightBlue2',  'LightBlue3',  'LightBlue4',  'light coral',  'LightCoral',  'light cyan',  'LightCyan',  'LightCyan1',  'LightCyan2',  'LightCyan3',  'LightCyan4',  'light goldenrod',  'LightGoldenrod',  'LightGoldenrod1',  'LightGoldenrod2',  'LightGoldenrod3',  'LightGoldenrod4',  'light goldenrod yellow',  'LightGoldenrodYellow',  'light gray',  'LightGray',  'light green',  'LightGreen',  'light grey',  'LightGrey',  'light pink',  'LightPink',  'LightPink1',  'LightPink2',  'LightPink3',  'LightPink4',  'light salmon',  'LightSalmon',  'LightSalmon1',  'LightSalmon2',  'LightSalmon3',  'LightSalmon4',  'light sea green',  'LightSeaGreen',  'light sky blue',  'LightSkyBlue',  'LightSkyBlue1',  'LightSkyBlue2',  'LightSkyBlue3',  'LightSkyBlue4',  'light slate blue',  'LightSlateBlue',  'light slate gray',  'LightSlateGray',  'light slate grey',  'LightSlateGrey',  'light steel blue',  'LightSteelBlue',  'LightSteelBlue1',  'LightSteelBlue2',  'LightSteelBlue3',  'LightSteelBlue4',  'light yellow',  'LightYellow',  'LightYellow1',  'LightYellow2',  'LightYellow3',  'LightYellow4',  'lime green',  'LimeGreen',  'linen',  'magenta',  'magenta1',  'magenta2',  'magenta3',  'magenta4',  'maroon',  'maroon1',  'maroon2',  'maroon3',  'maroon4',  'medium aquamarine',  'MediumAquamarine',  'medium blue',  'MediumBlue',  'medium orchid',  'MediumOrchid',  'MediumOrchid1',  'MediumOrchid2',  'MediumOrchid3',  'MediumOrchid4',  'medium purple',  'MediumPurple',  'MediumPurple1',  'MediumPurple2',  'MediumPurple3',  'MediumPurple4',  'medium sea green',  'MediumSeaGreen',  'medium slate blue',  'MediumSlateBlue',  'medium spring green',  'MediumSpringGreen',  'medium turquoise',  'MediumTurquoise',  'medium violet red',  'MediumVioletRed',  'midnight blue',  'MidnightBlue',  'mint cream',  'MintCream',  'misty rose',  'MistyRose',  'MistyRose1',  'MistyRose2',  'MistyRose3',  'MistyRose4',  'moccasin', 'navy',  'navy blue',  'NavyBlue',  'old lace',  'OldLace',  'olive drab',  'OliveDrab',  'OliveDrab1',  'OliveDrab2',  'OliveDrab3',  'OliveDrab4',  'orange',  'orange1',  'orange2',  'orange3',  'orange4',  'orange red',  'OrangeRed',  'OrangeRed1',  'OrangeRed2',  'OrangeRed3',  'OrangeRed4',  'orchid',  'orchid1',  'orchid2',  'orchid3',  'orchid4',  'pale goldenrod',  'PaleGoldenrod',  'pale green',  'PaleGreen',  'PaleGreen1',  'PaleGreen2',  'PaleGreen3',  'PaleGreen4',  'pale turquoise',  'PaleTurquoise',  'PaleTurquoise1',  'PaleTurquoise2',  'PaleTurquoise3',  'PaleTurquoise4',  'pale violet red',  'PaleVioletRed',  'PaleVioletRed1',  'PaleVioletRed2',  'PaleVioletRed3',  'PaleVioletRed4',  'papaya whip',  'PapayaWhip',  'peach puff',  'PeachPuff',  'PeachPuff1',  'PeachPuff2',  'PeachPuff3',  'PeachPuff4',  'peru',  'pink',  'pink1',  'pink2',  'pink3',  'pink4',  'plum',  'plum1',  'plum2',  'plum3',  'plum4',  'powder blue',  'PowderBlue',  'purple',  'purple1',  'purple2',  'purple3',  'purple4',  'red',  'red1',  'red2',  'red3',  'red4',  'rosy brown',  'RosyBrown',  'RosyBrown1',  'RosyBrown2',  'RosyBrown3',  'RosyBrown4',  'royal blue',  'RoyalBlue',  'RoyalBlue1',  'RoyalBlue2',  'RoyalBlue3',  'RoyalBlue4',  'saddle brown',  'SaddleBrown',  'salmon',  'salmon1',  'salmon2',  'salmon3',  'salmon4',  'sandy brown',  'SandyBrown',  'sea green',  'SeaGreen',  'SeaGreen1',  'SeaGreen2',  'SeaGreen3',  'SeaGreen4',  'seashell',  'seashell1',  'seashell2',  'seashell3',  'seashell4',  'sienna',  'sienna1',  'sienna2',  'sienna3',  'sienna4',  'sky blue',  'SkyBlue',  'SkyBlue1',  'SkyBlue2',  'SkyBlue3',  'SkyBlue4',  'slate blue',  'SlateBlue',  'SlateBlue1',  'SlateBlue2',  'SlateBlue3',  'SlateBlue4' ,  'snow',  'snow1',  'snow2',  'snow3',  'snow4',  'spring green',  'SpringGreen',  'SpringGreen1',  'SpringGreen2',  'SpringGreen3',  'SpringGreen4',  'steel blue',  'SteelBlue',  'SteelBlue1',  'SteelBlue2',  'SteelBlue3',  'SteelBlue4',  'tan',  'tan1',  'tan2',  'tan3',  'tan4',  'thistle',  'thistle1',  'thistle2',  'thistle3',  'thistle4',  'tomato',  'tomato1',  'tomato2',  'tomato3',  'tomato4',  'turquoise',  'turquoise1',  'turquoise2',  'turquoise3',  'turquoise4',  'violet',  'violet red',  'VioletRed',  'VioletRed1',  'VioletRed2',  'VioletRed3',  'VioletRed4',  'wheat',  'wheat1',  'wheat2',  'wheat3',  'wheat4', 'yellow',  'yellow1',  'yellow2',  'yellow3',  'yellow4',  'yellow green',  'YellowGreen']
            print len(unique_cluster_ids)
            print len(color_options)
            print
            for i in range(len(unique_cluster_ids)):
                color_dict[unique_cluster_ids[i]] = color_options[i]

        # handle the non spatial axes
        if len(headers) > 3:
            # handle plotting clustered data
            if self.cluster_mode:
                self.shapeChoice = "point"
                non_spatial_columns = [headers[4], "ids"]

            else:
                non_spatial_columns = headers[3:5]

            headers = headers[:3]
            self.normalized_non_spatial = analysis.normalize_columns_separately(non_spatial_columns, self.data_object)

        # get columns to plot
        self.data_to_plot = self.data_object.get_data(headers)

        # add zeros and/or ones to data to plot or throw an error if the user selects less than one column
        if len(headers) < 2:
            print "Select at least two columns to plot"
            self.root.destroy()
        if headers.__len__() == 2:
            self.data_to_plot = np.c_[self.data_to_plot, np.zeros(self.data_object.get_raw_num_rows()),
                                      np.ones(self.data_object.get_raw_num_rows())]
        if headers.__len__() == 3:
            self.data_to_plot = np.c_[self.data_to_plot, np.ones(self.data_object.get_raw_num_rows())]

        # normalize the data
        normalized_data = analysis.normalize_columns_separately(headers, self.data_object)

        # copy normalized data back to data to plot
        self.data_to_plot.T[:headers.__len__(), :] = normalized_data[:, :].T

        # Calculate the VTM using the current view object.
        # Transform the data using the VTM (the following assumes each data point is a row).
        vtm = self.view_object.build()
        pts = (vtm * self.data_to_plot.T).T

        # Delete any existing canvas objects used for plotting data.
        for obj in self.objects:
            self.canvas.delete(obj)
        self.objects = []

        for i in range(pts.shape[0]):

            # handle the color and size axes
            if self.normalized_non_spatial is not None:
                if self.cluster_mode:
                    if self.cluster_preselected_color_scheme:
                        color = color_dict[cluster_ids[i, 0]]
                    else:
                        alpha = self.normalized_non_spatial[i, 1] * 255
                        color = "#%02x%02x%02x" % (int(255-alpha), int(255-alpha), int(alpha))
                    size = 3
                else:
                    alpha = self.normalized_non_spatial[i, 1] * 255
                    color = "#%02x%02x%02x" % (int(255-alpha), int(255-alpha), int(alpha))
                    size = self.normalized_non_spatial[i, 0] * 5

            else:
                if self.cluster_mode:
                    if self.cluster_preselected_color_scheme:
                        color = color_dict[cluster_ids[i, 0]]
                    else:
                        alpha = self.normalized_non_spatial[i, 1] * 255
                        color = "#%02x%02x%02x" % (int(255-alpha), int(255-alpha), int(alpha))
                else:
                    color = "black"
                size = 3
                self.shapeChoice = "point"

            # draw the data points
            if self.shapeChoice == "square":
                pt = self.canvas.create_rectangle(pts[i, 0]-size, pts[i, 1]-size, pts[i, 0]+size,
                                                  pts[i, 1]+size, fill=color, outline='')
            elif self.shapeChoice == "point":
                pt = self.canvas.create_oval(pts[i, 0]-size, pts[i, 1]-size, pts[i, 0]+size,
                                             pts[i, 1]+size, fill=color, outline='')
            else:  # open circle
                pt = self.canvas.create_oval(pts[i, 0]-size, pts[i, 1]-size, pts[i, 0]+size,
                                             pts[i, 1]+size, outline=color)
            self.objects.append(pt)

        # restore the original data object for normal program functionality
        self.data_object = old_data_object
        self.use_pca_data_object = False
        self.cluster_mode = False
        self.cluster_preselected_color_scheme = False

    def updatePoints(self):

        # build the VTM
        vtm = self.view_object.build()

        # multiply the axis endpoints by the VTM
        pts = (vtm * self.data_to_plot.T).T

        # update the coordinates of each object
        if len(self.objects) != 0:
            for i in range(pts.shape[0]):
                if self.normalized_non_spatial is not None:
                    size = self.normalized_non_spatial[i, 0] * 5
                else:
                    size = 3
                self.canvas.coords(self.objects[i], pts[i, 0]-size, pts[i, 1]-size, pts[i, 0]+size, pts[i, 1]+size)

    def buildLinearRegression(self):
        print "building linear regression line"

        # extraction of chosen columns: x independent, y dependent
        data_to_plot = self.data_object.get_data(self.linRegChoices[:2])

        # add zeros and ones to data to plot
        data_to_plot = np.c_[data_to_plot, np.zeros(self.data_object.get_raw_num_rows()),
                             np.ones(self.data_object.get_raw_num_rows())]

        # normalize the data and copy the results back
        normalized_data = analysis.normalize_columns_separately(self.linRegChoices[:2], self.data_object)

        # copy normalized data back to data to plot
        data_to_plot.T[:len(self.linRegChoices[:2]), :] = normalized_data[:, :].T

        # make these copy the ones to plot
        self.data_to_plot = data_to_plot
        # Calculate the VTM using the current view object.
        # Transform the data using the VTM (the following assumes each data point is a row).
        vtm = self.view_object.build()
        pts = (vtm * self.data_to_plot.T).T

        # Delete any existing canvas objects and regression line used for plotting data.
        for obj in self.objects:
            self.canvas.delete(obj)
        if len(self.reg_line_objects) != 0:
            self.canvas.delete(self.reg_line_objects[0])

        self.reg_line_objects = []
        self.objects = []

        color = "black"
        size = 3
        for i in range(pts.shape[0]):
            pt = self.canvas.create_oval(pts[i, 0]-size, pts[i, 1]-size, pts[i, 0]+size,
                                         pts[i, 1]+size, fill=color, outline='')
            self.objects.append(pt)

        slope, intercept, r_value, p_value, std_err = stats.linregress(self.data_object.get_data(self.linRegChoices[:2]))

        # range of the independent (x) and dependent (y) variables
        range_data = analysis.data_range(self.linRegChoices[:2], self.data_object)

        # endpoints of the linear regression line fit
        # ((xmin * m + b) - ymin)/(ymax - ymin)
        # ((xmax * m + b) - ymin)/(ymax - ymin)
        self.reg_end_points = np.matrix([[0.0, ((range_data[0, 0]*slope + intercept) - range_data[1, 0]) /
                                          (range_data[1, 1]-range_data[1, 0]), 0, 1],
                                         [1.0, ((range_data[0, 1]*slope + intercept) - range_data[1, 0]) /
                                          (range_data[1, 1]-range_data[1, 0]), 0, 1]])
        reg_end_points = (vtm * self.reg_end_points.T).T

        self.lin_reg_line = self.canvas.create_line(reg_end_points[0, 0], reg_end_points[0, 1],
                                                    reg_end_points[1, 0], reg_end_points[1, 1], fill="red")
        self.reg_line_objects.append(self.lin_reg_line)

        # update the lin reg label and axes labels
        self.lin_reg_label.config(text="slope : " + str("%.3f" % slope) + " \nintercept : " +
                                       str("%.3f" % intercept) + " \nR^2-value : " + str("%.3f" % r_value**2))
        self.canvas.itemconfigure(self.x_label, text="x: "+str(self.linRegChoices[0]))
        self.canvas.itemconfigure(self.y_label, text="y: "+str(self.linRegChoices[1]))

    def updateFits(self):

        # build the VTM
        vtm = self.view_object.build()

        # multiply the reg line endpoints by the VTM
        reg_end_points = (vtm * self.reg_end_points.T).T

        # update the coordinates of the reg line object
        if len(self.reg_line_objects) != 0:
            self.canvas.coords(self.reg_line_objects[0], reg_end_points[0, 0], reg_end_points[0, 1],
                               reg_end_points[1, 0], reg_end_points[1, 1])

    def buildMenus(self):
        
        # create a new menu
        menu = tk.Menu(self.root)

        # set the root menu to our new menu
        self.root.config(menu=menu)

        # create a variable to hold the individual menus
        menulist = []

        # create a file menu
        filemenu = tk.Menu(menu)
        menu.add_cascade(label="File", menu=filemenu)
        menulist.append(filemenu)

        # create another menu for kicks
        cmdmenu = tk.Menu(menu)
        menu.add_cascade(label="Options", menu=cmdmenu)
        menulist.append(cmdmenu)

        # menu text for the elements
        # the first sublist is the set of items for the file menu
        # the second sublist is the set of items for the options menu
        menutext = [['New \xE2\x8C\x98N', 'Open \xE2\x8C\x98O', 'Plot \xE2\x8C\x98P', 'Reset \xE2\x8C\x98R', 'Save \xE2\x8C\x98S',
                     'Quit  \xE2\x8C\x98Q'],
                    ['Linear reg \xE2\x8C\x98L', 'PCA analysis \xE2\x8C\x98A', 'Cluster \xE2\x8C\x98C',
                     'Command 1', '-', '-']]

        # menu callback functions (note that some are left blank,
        # so that you can add functions there if you want).
        # the first sublist is the set of callback functions for the file menu
        # the second sublist is the set of callback functions for the option menu
        menu_commands = [[self.clearData, self.handleOpen, self.handlePlotData, self.reset, self.handleSave,
                          self.handleQuit],
                         [self.handleLinearRegression, self.handlePCAanalysis, self.handleCluster, self.handleMenuCmd1,
                          None, None]]
        
        # build the menu elements and callbacks
        for i in range(len(menulist)):
            for j in range(len(menutext[i])):
                if menutext[i][j] != '-':
                    menulist[i].add_command(label=menutext[i][j], command=menu_commands[i][j])
                else:
                    menulist[i].add_separator()

    # create the canvas object
    def buildCanvas(self):

        self.canvas = tk.Canvas(self.root, width=self.initDx, height=self.initDy)
        self.canvas.pack(expand=tk.YES, fill=tk.BOTH)

        return

    # build a frame and put controls in it
    def buildControls(self):

        # ## Control ###
        # make a control frame on the right
        rightcntlframe = tk.Frame(self.root)
        rightcntlframe.pack(side=tk.RIGHT, padx=2, pady=2, fill=tk.Y)
        self.cntlframewidth = rightcntlframe.winfo_screenmmwidth()-200

        # make a separator frame
        sep = tk.Frame(self.root, height=self.initDy, width=2, bd=1, relief=tk.SUNKEN)
        sep.pack(side=tk.RIGHT, padx=2, pady=2, fill=tk.Y)

        # use a label to set the size of the right panel
        label = tk.Label(rightcntlframe, text="Data Analyses", width=20)
        label.pack(side=tk.TOP, pady=10)

        # make a menu button that begins the process of plotting data
        # call the handlePlotData method when it is pressed.
        button = tk.Button(rightcntlframe, text="Plot Data", command=self.handlePlotData)
        button.pack(side=tk.TOP)

        button = tk.Button(rightcntlframe, text="Regression", command=self.handleLinearRegression)
        button.pack(side=tk.TOP)

        button = tk.Button(rightcntlframe, text="Cluster", command=self.handleCluster)
        button.pack(side=tk.TOP)

        button = tk.Button(rightcntlframe, text="New PCA", command=self.handlePCAanalysis)
        button.pack(side=tk.TOP)

        self.pca_listbox = tk.Listbox(rightcntlframe, selectmode=tk.SINGLE, exportselection=0)
        self.pca_listbox.pack(side=tk.TOP)

        button = tk.Button(rightcntlframe, text="View", command=self.handlePCAChoice)
        button.pack(side=tk.TOP)

        button = tk.Button(rightcntlframe, text="Delete", command=self.deletePCAChoice)
        button.pack(side=tk.TOP)

        # make labels to give user visual clues
        self.scale_label = tk.Label(rightcntlframe, text="Scaled by: " + str(1), width=20)

        self.rotation_label = tk.Label(rightcntlframe, text="Rotated by :" + str(0) + " rad in x\n and "
                                                            + str(0) + " rad in y", width=30)

        self.lin_reg_label = tk.Label(rightcntlframe, text="slope : " + str(0) + " \nintercept : " +
                                                           str(0) + " \nR^2-value : " + str(0), width=30)
        self.lin_reg_label.pack(side=tk.TOP)

        return

    def setBindings(self):

        # bind mouse motions to the canvas
        self.canvas.bind('<Button-1>', self.handleMouseButton1)
        self.canvas.bind('<B1-Motion>', self.handleMouseButton1Motion)
        self.canvas.bind('<Button-2>', self.handleMouseButton2)
        self.canvas.bind('<Control-Button-1>', self.handleMouseButton2)
        self.canvas.bind('<B2-Motion>', self.handleMouseButton2Motion)
        self.canvas.bind('<Control-B1-Motion>', self.handleMouseButton2Motion)
        self.canvas.bind('<Button-3>', self.handleMouseButton3)
        self.canvas.bind('<Control-Shift-Button-1>', self.handleMouseButton3)
        self.canvas.bind('<B3-Motion>', self.handleMouseButton3Motion)
        self.canvas.bind('<Control-Shift-B1-Motion>', self.handleMouseButton3Motion)

        # bind to resizing window
        self.canvas.bind('<Configure>', self.handleResize)

        # bind command sequences to the root window
        self.root.bind('<Command-q>', self.handleQuit)
        self.root.bind('<Command-n>', self.clearData)
        self.root.bind('<Command-r>', self.reset)
        self.root.bind('<Command-o>', self.handleOpen)
        self.root.bind('<Command-p>', self.handlePlotData)
        self.root.bind('<Command-l>', self.handleLinearRegression)
        self.root.bind('<Command-s>', self.handleSave)
        self.root.bind('<Command-a>', self.handlePCAanalysis)
        self.root.bind('<Command-c>', self.handleCluster)

    def handleQuit(self, event=None):
        print 'Terminating'
        self.root.destroy()

    def handleSave(self, event=None):
        print "saving data"
        name = tkFileDialog.asksaveasfilename(parent=self.root, title='Type name', initialdir='.',
                                              defaultextension='.png')
        pic = self.canvas.postscript(file=name, colormode='color')

        image = Image.open(name)
        image.save(name, "png")

    def handleResize(self, event=None):
        # calculate the ratio of old width/height to new width/height of window
        width_scale = (float(event.width)+self.cntlframewidth)/self.initDx
        height_scale = float(event.height)/self.initDy
        self.initDx = event.width+self.cntlframewidth
        self.initDy = event.height
        # resize the canvas
        self.canvas.config(width=event.width, height=event.width)
        # rescale all the objects tagged with the "all" tag
        self.canvas.scale("all", 0, 0, width_scale, height_scale)

    def handleOpen(self, event=None):
        filename = tkFileDialog.askopenfilename(parent=self.root, title='Choose a data file', initialdir='.')

        # split to get just the file name
        self.data_object = data.Data(filename=os.path.split(filename)[1])

        # self.data_object = data.Data(filename="data-simple.csv")

    def handleCluster(self, event=None):
        print "handling clustering"

        # self.data_object = data.Data(filename="AustraliaCoast.csv")

        # cater for when someone tries to build linear regression without selecting a file
        if self.data_object is None:
            self.handleOpen(event=None)

        self.createClusterDialog()

        # cater for when user wants to use preselected colors
        if self.cluster_header_choices[-1] == 1:
            self.cluster_preselected_color_scheme = True

        # toggle cluster mode on
        self.cluster_mode = True

        # cater for when the user wants to run pca first and cluster on the first 3 dimensions in the data
        if self.cluster_header_choices[-4] == 1:
            self.handlePCAanalysis(event=None, cluster=True)
            cluster_headers = self.pca_data_objects_list[-1].get_headers()[:3]

        else:
            cluster_headers = self.cluster_header_choices[:-4]

            # cluster the data depending on the metric specified
            # ["l1-norm aka manhattan", "l2 norm aka euclidean", "l-infinity aka maximum"]
        if self.cluster_header_choices[-3] == "l1-norm aka manhattan":
            codebook, codes, errors = analysis.kmeans(self.data_object, cluster_headers,
                                                      self.cluster_header_choices[-2], manhattan=True)

        elif self.cluster_header_choices[-3] == "l-infinity aka maximum":
            codebook, codes, errors = analysis.kmeans(self.data_object, cluster_headers,
                                                      self.cluster_header_choices[-2], l_infinity_norm=True)

        else:  # use euclidean distance
            codebook, codes, errors = analysis.kmeans(self.data_object, cluster_headers,
                                                      self.cluster_header_choices[-2])

        cluster_ids = ["ids", "numeric"] + list(codes.flat)

        # to plot pca data on first 3 dimensions
        if self.cluster_header_choices[-4] == 1:
            self.pca_data_object = self.pca_data_objects_list[-1]

            # add the ids to the data object
            self.pca_data_object.add_column(cluster_ids)

            # flag to alert handlePlot to use pcadata object
            self.use_pca_data_object = True
            cluster_headers = self.pca_data_object.get_headers()[:5]
            self.buildPoints(cluster_headers)

        # to plot normally clustered data
        else:
            # add the ids to the data object
            self.data_object.add_column(cluster_ids)

            # plot the data using the first 3 columns
            print self.cluster_header_choices
            self.buildPoints(self.cluster_header_choices[:5])

    def handlePCAanalysis(self, event=None, cluster=False):
        print "handling PCA analysis"

        # self.data_object = data.Data(filename="AustraliaCoast.csv")
        # cater for when someone tries to build linear regression without selecting a file
        if self.data_object is None:
            self.handleOpen(event=None)

        # if the pca analysis is being called by the cluster handler
        if cluster:
            headers = ["premin", "premax", "salmin", "salmax", "minairtemp", "maxairtemp", "minsst",
                       "maxsst", "minsoilmoist", "maxsoilmoist", "runoffnew"]
            # headers = self.data_object.get_headers()
            pcadata = analysis.pca(headers, self.data_object)
            name = "analysis"

        else:
            self.createPCADialog()
            pcadata = analysis.pca(self.pca_cols_choices, self.data_object)
            # dialog to ask to name the analysis
            name = tkFileDialog.asksaveasfilename(parent=self.root, title='name analysis', initialfile="analysis")

        self.pca_data_objects_list.append(pcadata)

        # result should appear as an option
        self.pca_listbox.insert(tk.END, os.path.split(name)[1] + " " + str(datetime.datetime.now().time()))

    def handlePCAChoice(self):
        index = int(self.pca_listbox.curselection()[0])
        self.pca_data_object = self.pca_data_objects_list[index]
        self.createEigenDialog(event=None)  # show the eigenvectors and values

        # flag to alert handlePlot to use pcadata object
        self.use_pca_data_object = True
        self.handlePlotData(event=None)

    # # delete the selected analysis
    def deletePCAChoice(self):
        index = int(self.pca_listbox.curselection()[0])
        self.pca_data_objects_list.pop(index)
        self.pca_listbox.delete(tk.ANCHOR)

    def handleLinearRegression(self, event=None):
        print "handling linear regression"

        # cater for when someone tries to build linear regression without selecting a file
        if self.data_object is None:
            self.handleOpen(event=None)

        # self.data_object = data.Data(filename="data-simple.csv")
        self.createLinRegDialog()
        self.buildLinearRegression()

    def handlePlotData(self, event=None):
        print "handling plot data"

        # cater for when someone tries to build linear regression without selecting a file
        if self.data_object is None:
            self.handleOpen(event=None)

        self.createColumnsDialog()  # create the columns dialog box here
        headers = self.handleChooseAxes()
        self.shapeChoice = headers[-1]
        headers = headers[:-1]
        self.buildPoints(headers)

    def handleChooseAxes(self):
        selected_headers = []
        for item in self.columnsChoices:
            selected_headers.append(item)

        return selected_headers

    def updateColor(self):
        for obj in self.objects:
            self.canvas.itemconfig(obj, fill=self.colorOption.get())

    def handleMenuCmd1(self):
        print 'handling menu command 1'

    def handleMouseButton1(self, event):
        self.baseClick = (event.x, event.y)

    def handleMouseButton2(self, event):
        self.baseClick2 = (event.x, event.y)
        self.view_object_clone = self.view_object.clone()

    def handleMouseButton3(self, event):
        self.baseClick3 = (event.x, event.y)
        self.originalExtent = self.view_object.clone().extent

    # This is called if the first mouse button is being moved. it translates the axes
    def handleMouseButton1Motion(self, event):
        # Calculate the differential motion since the last time the function was called and then
        # Divide the differential motion (dx, dy) by the screen size (view X, view Y)
        dx = float(event.x - self.baseClick[0]) / self.view_object.screen[0]
        dy = float(event.y - self.baseClick[1]) / self.view_object.screen[1]

        # Multiply the horizontal and vertical motion by the horizontal and vertical extents.
        # Put the result in delta0 and delta1
        delta0 = dx * self.view_object.extent[0]
        delta1 = dy * self.view_object.extent[1]

        # The VRP should be updated by delta0 * U + delta1 * VUP (this is a vector equation)

        self.view_object.vrp += 0.5*delta0 * self.view_object.u + 0.5*delta1 * self.view_object.vup
        self.updateAxes()
        self.updatePoints()
        if self.reg_end_points is not None:
            self.updateFits()

        # update the base click
        self.baseClick = (event.x, event.y)

    # This will be called if the second button of a real mouse has been pressed and the mouse is moving.
    # Or if the control key is held down while a person moves their finger on the track pad.
    # it rotates the axes
    def handleMouseButton2Motion(self, event):
        constant = 0.5*min(self.view_object.screen)  # use the minimum one of screen dimensions
        delta0 = float((event.x - self.baseClick2[0])) / constant * math.pi
        delta1 = float((event.y - self.baseClick2[1])) / constant * math.pi

        self.view_object = self.view_object_clone.clone()
        self.view_object.rotateVRC(-delta0, delta1)

        self.updateAxes()
        self.updatePoints()
        if self.reg_end_points is not None:
            self.updateFits()

        # update the orientation label
        self.rotation_label.config(text="Rotated by :" + str("%.3f" % delta0) + " rad in x\n and " +
                                        str("%.3f" % -delta1) + " rad in y")

    # This will be called if the middle button of a real mouse has been pressed and the mouse is moving.
    # Or if the control and shift key are held down while a person moves their finger on the track pad.
    # it scales the axes
    def handleMouseButton3Motion(self, event):
        delta1 = event.y - self.baseClick3[1]

        # k is a factor to control speed of scaling
        k = 1.0 / self.canvas.winfo_height()

        # f is the multiplication factor
        f = 1.0 + k * delta1

        # bound the factor between 0.1 and 3.0
        f = max(min(f, 3.0), 0.1)

        # update the view extent
        self.view_object.extent[0] = self.originalExtent[0] * f
        self.view_object.extent[1] = self.originalExtent[1] * f

        self.updateAxes()
        self.updatePoints()
        if self.reg_end_points is not None:
            self.updateFits()

        # update the scale label
        self.scale_label.config(text="Scaled by: " + str("%.3f" % (2-f)))

    # creates random ovals whose x coordinate is randomly selected between 0 and the canvas width, and y between 0 and
    # the canvas height
    def createRandomDataPoints(self, event=None):
        # for i in range(100):
        for i in range(self.densityOption.get()):
            dx = self.size.get()
            # handle distribution choice
            if self.distributionChoice == "gaussian":
                x = random.gauss(self.initDx/2, 100)
                y = random.gauss(self.initDy/2, 100)
            else:  # uniform
                x = random.randint(0, self.initDx)
                y = random.randint(0, self.initDy)

            # handle shape choice
            if self.shapeChoice == "square":
                pt = self.canvas.create_rectangle(x-dx, y-dx, x+dx, y+dx, fill=self.colorOption.get(), outline='')
            else:  # ovals
                pt = self.canvas.create_oval(x-dx, y-dx, x+dx, y+dx, fill=self.colorOption.get(), outline='')
            # update objects list
            self.objects.append(pt)

    # clears all the data points
    def clearData(self, event=None):
        self.objects = []
        self.canvas.delete("all")

    # reset everything to default in two clicks
    def reset(self, event=None):
        self.canvas.delete("all")
        self.initDx = 800
        self.initDy = 500
        self.root.geometry("%dx%d+50+30" % (self.initDx, self.initDy))
        self.canvas.config(width=self.initDx, height=self.initDy)
        self.graphics_lines = []
        self.view_object.reset()
        self.rotation_label.config(text="Rotated by :" + str(0) + " rad in x\n and " + str(0) + " rad in y")
        self.scale_label.config(text="Scaled by: " + str(1))
        self.lin_reg_label.config(text="slope : " + str(0) + " \nintercept : " +
                                       str(0) + " \nR^2-value : " + str(0))
        self.buildAxes()

        self.buildPoints(self.handleChooseAxes())
        print "resetting axes"

    # create dialog boxes
    def createEigenDialog(self, event=None):
        eigen_dialog_box = EigenDialog(self.root, "Eigenvectors and Eigenvalues table")

    def createDistributionDialog(self, event=None):
        # make the Dialog that allows the user to specify which random distribution
        distribution_dialog_box = DistributionDialog(self.root, "Choose distribution")
        self.distributionChoice = distribution_dialog_box.result

    def createColumnsDialog(self, event=None):
        # make the Dialog that allows the user to specify which columns to plot
        columns_dialog_box = ColumnsDialog(self.root, "Choose columns")
        self.columnsChoices = columns_dialog_box.result

    def createLinRegDialog(self, event=None):
        lin_reg_dialog_box = LinRegDialog(self.root, "Choose lin reg variables")
        self.linRegChoices = lin_reg_dialog_box.result

    def createPCADialog(self, event=None):
        pca_dialog = PCADialog(self.root, "Choose Columns")
        self.pca_cols_choices = pca_dialog.result

    def createClusterDialog(self, event=None):
        cluster_dialog = ClusterDialog(self.root, "Choose headers")
        self.cluster_header_choices = cluster_dialog.result

    def createShapeDialog(self, event=None):
        shape_dialog = ShapeDialog(self.root, "Choose shape")
        self.shapeChoice = shape_dialog.result

    def main(self):
        print 'Entering main loop'
        self.root.mainloop()


class Dialog(tk.Toplevel):

    def __init__(self, parent, title=None):

        tk.Toplevel.__init__(self, parent)
        self.transient(parent)

        if title:
            self.title(title)

        self.parent = parent

        self.result = None

        body = tk.Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)

        self.buttonbox()

        self.grab_set()

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry("+%d+%d" % (parent.winfo_rootx()+400, parent.winfo_rooty()+200))

        self.initial_focus.focus_set()

        self.wait_window(self)

    # construction hooks

    def body(self, master):
        # create dialog body.  return widget that should have
        # initial focus.  this method should be overridden
        pass

    def buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons

        box = tk.Frame(self)

        w = tk.Button(box, text="OK", width=10, command=self.ok, default=tk.ACTIVE)
        w.pack(side=tk.LEFT, padx=5, pady=5)
        w = tk.Button(box, text="Cancel", width=10, command=self.cancelButton)
        w.pack(side=tk.LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancelButton)

        box.pack()

    # standard button semantics

    def ok(self, event=None):

        if not self.validate():
            self.initial_focus.focus_set()  # put focus back
            return

        self.apply(event=None)

        self.withdraw()
        self.update_idletasks()

        self.cancel()

    def cancel(self, event=None):

        # put focus back to the parent window
        self.parent.focus_set()
        self.destroy()

    def cancelButton(self, event=None):
        # destroy the result
        self.result = None

        # put focus back to the parent window
        self.parent.focus_set()
        self.destroy()

    # command hooks

    def validate(self):
        return 1  # override

    def apply(self, event):
        pass  # override


class EigenDialog(Dialog):
    def body(self, master):
        # available header options

        header_options = dapp.pca_data_object.get_data_headers()
        eigen_raw_headers = dapp.pca_data_object.get_raw_headers()
        eigenvalues = dapp.pca_data_object.get_eigenvalues()
        eigenvectors = dapp.pca_data_object.get_eigenvectors()

        tk.Label(master, text="Eigenvectors", bg="DodgerBlue2").grid(row=0, column=0, sticky=tk.E+tk.W)
        tk.Label(master, text="Eigenvalues", bg="DodgerBlue2").grid(row=0, column=1, sticky=tk.E+tk.W)
        tk.Label(master, text="Cumulative", bg="DodgerBlue2").grid(row=0, column=2, sticky=tk.E+tk.W)
        for i in range(len(header_options)):
            tk.Label(master, text=header_options[i], bg="DodgerBlue2").grid(row=0, column=3+i, sticky=tk.E+tk.W)

        # sum of eigen values
        eigen_sum = 0.0
        for i in range(eigenvalues.shape[1]):
            eigen_sum += eigenvalues[0, i]
        cumulative = 0.0
        for i in range(len(eigen_raw_headers)):
            cumulative += float(eigenvalues[0, i])/eigen_sum

            tk.Label(master, text=eigen_raw_headers[i], bg="turquoise1").grid(row=1+i, column=0, sticky=tk.E+tk.W)
            tk.Label(master, text=str("%.4f" % eigenvalues[0, i]),
                     bg="turquoise1").grid(row=1+i, column=1, sticky=tk.E+tk.W)
            tk.Label(master, text=str("%.4f" % cumulative),
                     bg="turquoise1").grid(row=1+i, column=2, sticky=tk.E+tk.W)

        for i in range(eigenvectors.shape[0]):
            for j in range(eigenvectors.shape[1]):
                tk.Label(master, text=str("%.4f" % eigenvectors[i, j]),
                         bg="turquoise1").grid(row=1+i, column=3+j, sticky=tk.E+tk.W)


class ColumnsDialog(Dialog):
    def body(self, master):

        # add old data headers to header options list
        if dapp.pca_data_object is not None and dapp.use_pca_data_object is True:
            header_options = dapp.pca_data_object.get_headers() + dapp.data_object.get_headers()

        else:
            # available header options
            header_options = dapp.data_object.get_headers()

        tk.Label(master, text="X axis").grid(row=0, column=0, sticky=tk.W, rowspan=2)
        tk.Label(master, text="Y axis").grid(row=0, column=1, sticky=tk.W, rowspan=2)
        tk.Label(master, text="Z axis").grid(row=0, column=2, sticky=tk.W, rowspan=2)
        tk.Label(master, text="Color").grid(row=0, column=3, sticky=tk.W, rowspan=2)
        tk.Label(master, text="Size").grid(row=0, column=4, sticky=tk.W, rowspan=2)
        tk.Label(master, text="Shape").grid(row=0, column=5, sticky=tk.W, rowspan=2)

        self.XOption = tk.StringVar(master)
        self.YOption = tk.StringVar(master)
        self.ZOption = tk.StringVar(master)
        self.colorOption = tk.StringVar(master)
        self.sizeOption = tk.StringVar(master)
        self.shapeOption = tk.StringVar(master)

        # for any file
        self.XOption.set(header_options[0])
        self.YOption.set(header_options[1])
        self.XOption.set("Choose")
        self.YOption.set("Choose")
        self.ZOption.set("Optional")
        self.colorOption.set("Optional")
        self.sizeOption.set("Optional")
        self.shapeOption.set("Optional")

        # to plot first five eigen vectors

        # self.XOption.set(header_options[0])
        # self.YOption.set(header_options[1])
        # self.ZOption.set(header_options[2])
        # self.colorOption.set(header_options[3])
        # self.sizeOption.set(header_options[4])
        # self.shapeOption.set("point")

        # add commands to the menus
        XMenu = tk.OptionMenu(master, self.XOption, *header_options, command=self.apply)
        YMenu = tk.OptionMenu(master, self.YOption, *header_options, command=self.apply)
        ZMenu = tk.OptionMenu(master, self.ZOption, *header_options, command=self.apply)
        colorMenu = tk.OptionMenu(master, self.colorOption, *header_options, command=self.apply)
        sizeMenu = tk.OptionMenu(master, self.sizeOption, *header_options, command=self.apply)
        shapeMenu = tk.OptionMenu(master, self.shapeOption, "point", "square", "circle", command=self.apply)

        # place them appropriately
        XMenu.grid(row=2, column=0)
        YMenu.grid(row=2, column=1)
        ZMenu.grid(row=2, column=2)
        colorMenu.grid(row=2, column=3)
        sizeMenu.grid(row=2, column=4)
        shapeMenu.grid(row=2, column=5)

        self.apply(event=None)

    def apply(self, event):
        self.result = []
        if self.XOption.get() != "Choose":
            self.result.append(self.XOption.get())
        if self.YOption.get() != "Choose":
            self.result.append(self.YOption.get())
        if self.ZOption.get() != "Optional":
            self.result.append(self.ZOption.get())
        if self.colorOption.get() != "Optional":
            self.result.append(self.colorOption.get())
        if self.sizeOption.get() != "Optional":
            self.result.append(self.sizeOption.get())
        if self.shapeOption.get() != "Optional":
            self.result.append(self.shapeOption.get())
        else:
            self.result.append("point")


class LinRegDialog(Dialog):

    def body(self, master):

        # available header options
        header_options = dapp.data_object.get_headers()

        tk.Label(master, text="X axis").grid(row=0, column=0, sticky=tk.W, rowspan=2)
        tk.Label(master, text="Y axis").grid(row=0, column=1, sticky=tk.W, rowspan=2)
        tk.Label(master, text="Color").grid(row=0, column=2, sticky=tk.W, rowspan=2)
        tk.Label(master, text="Size").grid(row=0, column=3, sticky=tk.W, rowspan=2)

        self.XOption = tk.StringVar(master)
        self.YOption = tk.StringVar(master)
        self.colorOption = tk.StringVar(master)
        self.sizeOption = tk.StringVar(master)

        self.XOption.set(header_options[0])
        self.YOption.set(header_options[1])

        # self.XOption.set("independent var")
        # self.YOption.set("dependent var")
        self.colorOption.set("Optional")
        self.sizeOption.set("Optional")

        # add commands to the menus
        XMenu = tk.OptionMenu(master, self.XOption, *header_options, command=self.apply)
        YMenu = tk.OptionMenu(master, self.YOption, *header_options, command=self.apply)
        colorMenu = tk.OptionMenu(master, self.colorOption, *header_options, command=self.apply)
        sizeMenu = tk.OptionMenu(master, self.sizeOption, *header_options, command=self.apply)

        # place them appropriately
        XMenu.grid(row=2, column=0)
        YMenu.grid(row=2, column=1)
        colorMenu.grid(row=2, column=2)
        sizeMenu.grid(row=2, column=3)

        self.apply(event=None)

    def apply(self, event):
        self.result = []
        if self.XOption.get() != "independent var":
            self.result.append(self.XOption.get())
        if self.YOption.get() != "dependent var":
            self.result.append(self.YOption.get())
        if self.colorOption.get() != "Optional":
            self.result.append(self.colorOption.get())
        if self.sizeOption.get() != "Optional":
            self.result.append(self.sizeOption.get())


class DistributionDialog(Dialog):

    def body(self, master):
        # a list box to diplay the list of options for the random distributions
        listbox = tk.Listbox(master, selectmode=tk.SINGLE, exportselection=0)
        # add options
        for item in ["uniform", "gaussian"]:
            listbox.insert(tk.END, item)
        listbox.pack()
        listbox.bind('<<ListboxSelect>>', self.apply1)

    def apply1(self, event):
        w = event.widget
        index = int(w.curselection()[0])
        self.result = w.get(index)


class ClusterDialog(Dialog):
    def body(self, master):
        # listbox to select which headers to cluster
        header_options = dapp.data_object.get_headers()
        tk.Label(master, text="Headers to cluster").grid(row=0, column=0, sticky=tk.N)
        listbox = tk.Listbox(master, selectmode=tk.EXTENDED, exportselection=0)
        # add options
        for item in header_options:
            listbox.insert(tk.END, item)
        listbox.grid(row=1, column=0, sticky=tk.W, rowspan=2)
        listbox.bind('<<ListboxSelect>>', self.apply1)

        # entry widget to select number of clusters to make (default value ten clusters)
        tk.Label(master, text="No. of clusters").grid(row=0, column=1, sticky=tk.N)
        self.clusters_number = tk.IntVar()
        self.number_clusters_number = tk.Entry(master, textvariable=self.clusters_number)
        self.clusters_number.set(10)
        self.number_clusters_number.grid(row=1, column=1, sticky=tk.N)

        # checkbutton to decide whether to use preselected or smooth color scheme
        self.color = tk.IntVar()
        tk.Checkbutton(master, text="Use preselected colors", variable=self.color).grid(row=2, column=1, sticky=tk.N)

        # checkbutton to decide whether to run pca analysis first or not
        self.pca = tk.IntVar()
        tk.Checkbutton(master, text="Run pca anaysis first", variable=self.pca).grid(row=2, column=2, sticky=tk.N)

        # menu to choose distance metric
        tk.Label(master, text="Choose distance metric").grid(row=0, column=2, sticky=tk.N)
        self.metric_option = tk.StringVar(master)
        metric_options = ["l1-norm aka manhattan", "l2 norm aka euclidean", "l-infinity aka maximum"]
        self.metric_option.set(metric_options[1])
        metric_menu = tk.OptionMenu(master, self.metric_option, *metric_options)
        metric_menu.grid(row=1, column=2, sticky=tk.N)

    def apply1(self, event):
        self.result = []
        w = event.widget
        selected = w.curselection()
        for i in selected:
            self.result.append(w.get(i))

    def apply(self, event):

        # metric chosen number of clusters selected and color scheme selection
        self.result.append(self.pca.get())  # 1 for when run pca first is selected, 0 for when not
        self.result.append(self.metric_option.get())
        self.result.append(self.clusters_number.get())
        self.result.append(self.color.get())  # 1 for when preselected colors are chosen, 0 for when not


class PCADialog(Dialog):
    def body(self, master):

        # available column options
        column_options = dapp.data_object.get_headers()

        # a list box to diplay the list of columns options
        listbox = tk.Listbox(master, selectmode=tk.EXTENDED, exportselection=0)
        # add options
        for item in column_options:
            listbox.insert(tk.END, item)
        listbox.pack()
        listbox.bind('<<ListboxSelect>>', self.apply1)

    def apply1(self, event):
        self.result = []
        w = event.widget
        selected = w.curselection()
        for i in selected:
            self.result.append(w.get(i))


class ShapeDialog(Dialog):

    def body(self, master):
        # a list box to diplay the list of options for the random distributions
        listbox = tk.Listbox(master, selectmode=tk.SINGLE, exportselection=0)
        # add options
        for item in ["circle", "square"]:
            listbox.insert(tk.END, item)
        listbox.pack()
        listbox.bind('<<ListboxSelect>>', self.apply1)

    def apply1(self, event):
        w = event.widget
        index = int(w.curselection()[0])
        self.result = w.get(index)


if __name__ == "__main__":
    dapp = DisplayApp(800, 500)
    dapp.main()
