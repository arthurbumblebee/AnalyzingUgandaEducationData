# Data class
# Written by Arthur Makumbi
# CS251

import numpy as np


# create a class to manage the data
class Data:

    def __init__(self, filename=None):
        # create and initialize fields for the class
        self.raw_headers = []   # list of all headers

        self.headers = []  # list of headers with numeric data

        self.raw_types = []  # list of all types

        self.raw_data = []  # list of lists of all data. Each row is a list of strings

        self.header2raw = {}  # dictionary mapping header string to index of column in raw data

        self.matrix_data = np.matrix([])  # matrix of numeric data

        self.header2matrix = {}  # dictionary mapping header string to index of column in matrix data

        # if filename is not None
        if filename is not None:
            self.read(filename)

    def read(self, filename):
        temp = []  # temporary list for matrix
        our_file = open(filename, 'rU')
        raw_headers = our_file.readline().strip().split(",")
        # add to header list
        for i in range(raw_headers.__len__()):
            self.raw_headers.append(raw_headers[i].strip())
            self.header2raw[raw_headers[i].strip()] = i
        # add to types list
        types = our_file.readline().strip().split(",")
        for t in types:
            self.raw_types.append(t.strip())
        # add to raw data, and matrix data
        for line in our_file:
            numeric_data = []  # to store the numeric data
            raw_data = line.strip().split(",")
            # raw_data = line.strip("\n").split(",")
            self.raw_data.append(raw_data)  # add to raw data list
            count = 0
            # change all strings of numeric data to floats
            for i in range(raw_data.__len__()):
                if self.raw_types[i] == "numeric":
                    count += 1
                    numeric_data.append(float(raw_data[i]))
                    self.headers.append(self.raw_headers[i])

            temp.append(numeric_data)  # add to temporary list

            # build the headers to matrix dictionary
            self.headers = self.headers[:count]
            for i in range(count):
                self.header2matrix[self.headers[i]] = i

        # modify matrix data
        self.matrix_data = np.matrix(temp)

    # returns a list of all of the headers
    def get_raw_headers(self):
        return self.raw_headers

    # returns a list of all of the types.
    def get_raw_types(self):
        return self.raw_types

    # returns the number of columns in the raw data set
    def get_raw_num_columns(self):
        return self.raw_headers.__len__()

    #  returns the number of rows in the data set. This should be identical to the number of rows in the numeric data,
    #  so you can get away with writing just one function for this purpose.
    def get_raw_num_rows(self):

        return self.raw_data.__len__()

    def get_num_rows(self):
        return self.raw_data.__len__()

    # returns a row of data (the type is list) given a row index (int).
    def get_raw_row(self, index):
        return self.raw_data[index]

    # takes a row index (an int) and column header (a string) and returns the raw data at that location.
    #  (The return type will be a string)
    def get_raw_value(self, index, header):
        return self.raw_data[index][self.header2raw[header]]

    # list of headers of columns with numeric data
    def get_headers(self):
        return self.headers

    # returns the number of columns of numeric data
    def get_num_columns(self):
        return self.headers.__len__()

    # take a row index and returns a row of numeric data
    def get_row(self, index):
        return self.matrix_data[index]

    # takes a row index (int) and column header (string) and returns the data in the numeric matrix.
    def get_value(self, index, header):
        return self.matrix_data[index, self.header2matrix[header]]

    # At a minimum, this should take a list of columns headers and return a matrix with the data for all rows but
    # just the specified columns. It is optional to also allow the caller to specify a specific set of rows.
    def get_data(self, headers, rows=None):
        temp = []
        if rows is not None:  # if rows are specified
            for row in rows:
                numeric_data = []
                for header in headers:
                    numeric_data.append(self.matrix_data[row, self.header2matrix[header]])
                temp.append(numeric_data)
        else:  # if no row is specified
            for i in range(self.matrix_data.__len__()):
                numeric_data = []
                for header in headers:
                    numeric_data.append(self.matrix_data[i, self.header2matrix[header]])
                temp.append(numeric_data)
        return np.matrix(temp)

    # method add_column to add a column of data to the Data object.
    def add_column(self, column):
        temp = []  # to store the temporary column
        if column.__len__() < 1:
            # if column.__len__() < self.get_raw_num_rows():
            print "Usage: your input column does not have the correct number of points"
            print "  must have a header(string), a type(string), and %s points" % (self.get_raw_num_rows()-2)
            exit()
        else:
            self.raw_headers.append(column[0])
            self.header2raw[column[0]] = len(self.header2raw)
            self.raw_types.append(column[1])
            for i in range(2, len(column)):
                # self.raw_data.append(column[i])
                if column[1] == "numeric":
                    self.headers.append(column[0])
                    temp.append([float(column[i])])
                self.headers = self.headers[:self.get_num_columns()+1]
                self.header2matrix[column[0]] = len(self.header2matrix)-1

        self.matrix_data = np.append(self.matrix_data, temp, axis=1)

    # write out a selected set of headers to a specified file.
    # takes in a filename and an optional list of the headers of the columns to write to the file
    def write_to_file(self, filename, headers=[]):
        if len(headers) == 0:
            data_list = self.get_data(self.get_headers())
        else:
            data_list = self.get_data(headers)
        with open(filename, 'wb') as csvfile:
            np.savetxt(csvfile, data_list, delimiter=',', fmt='%.3f')

    # main method
    def main(self):
        # self.add_column(["age", "numeric", 30, 60, 10])
        # print "raw headers : ", self.get_raw_headers()
        # print "raw num cols : ", self.get_raw_num_columns()
        # print "raw types : ", self.get_raw_types()
        # print "raw row : ", self.get_raw_row(1)
        # print "headers to raw dict : ", self.header2raw
        # print "headers : ", self.get_headers()
        # print "matrix data : ", self.matrix_data
        # print " header2matrix : ", self.header2matrix
        # print self.raw_headers[1]
        # print self.matrix_data
        # print "raw value is : ", self.get_raw_value(1, "bad")
        # print "row is : ", self.get_row(1)
        # print "numeric value is : ", self.get_value(1, "bad")
        # print "the matrix is : ", self.get_data(["headers", "bad"])[0, 1]
        # print "the matrix is : ", self.get_data(["headers", "bad"], [0, 2])
        self.write_to_file("file.csv")


class PCAData(Data):
    def __init__(self, headers, pdata, evals, evecs, means):
        Data.__init__(self, filename=None)

        # super(PCAData, self).__init__()
        self.eigenvalues = evals
        self.eigenvectors = evecs  # matrix of eigenvectors
        self.mean_data_values = means  # matrix of mean_data_values
        self.original_headers = headers  # list of  headers of the original data columns used to create projected data

        # the existing numeric data field is used to hold the projected data (numpy matrix).
        self.matrix_data = pdata  # matrix of numeric data

        # populate fields of data object
        self.populate_fields(pdata, headers)

    # function that populates the old fields
    def populate_fields(self, pdata, headers):
        self.headers = headers
        raw_headers, raw_types = [], []
        for i in range(len(headers)):
            raw_headers.append("P0" + str(i))
            raw_types.append("numeric")
            self.header2matrix[self.headers[i]] = i

        self.raw_headers = raw_headers
        self.raw_types = raw_types
        self.raw_data = pdata

    # returns a copy of the eigenvalues as a single-row numpy matrix.
    def get_eigenvalues(self):
        return self.eigenvalues

    # returns a copy of the eigenvectors as a numpy matrix with the eigenvectors as rows.
    def get_eigenvectors(self):
        return self.eigenvectors

    # returns the means for each column in the original data as a single row numpy matrix.
    def get_data_means(self):
        return self.mean_data_values

    # returns a copy of the list of the headers from the original data used to generate the projected data.
    def get_data_headers(self):
        return self.original_headers


if __name__ == "__main__":
    # data = Data(filename="smallsample.csv")
    data = Data(filename="testdata3.csv")
    data.main()
