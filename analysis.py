# analysis.py to analyze data
# Written by Arthur Makumbi
# CS251

import numpy as np
import scipy.cluster.vq as vq
from scipy import stats
import scipy.spatial.distance as dist
import data
import random


# - Takes in a list of column headers and the Data object and returns a list of 2-element lists with the minimum
#  and maximum values for each column. The function is required to work only on numeric data types.
def data_range(headers, target):
    results = []
    data_list = target.get_data(headers)
    for i in range(headers.__len__()):
        maximum = 0
        minimum = data_list[0, i]
        for item in data_list:
            maximum = max(maximum, item[0, i])
            minimum = min(minimum, item[0, i])
        results.append([minimum, maximum])
    return np.matrix(results)


# - Takes in a list of column headers and the Data object and returns a list of the mean values for each column.
def mean(headers, target):
    results = []
    data_list = target.get_data(headers)
    for i in range(headers.__len__()):
        temp = []
        for item in data_list:
            temp.append(item[0, i])
        results.append(np.mean(temp))

    return np.matrix(results)


# - Takes in a list of column headers and the Data object and returns a list of the
# standard deviation for each specified column.
def stdev(headers, target):
    results = []
    data_list = target.get_data(headers)
    for i in range(headers.__len__()):
        temp = []
        for item in data_list:
            temp.append(item[0, i])
        results.append(np.std(temp, ddof=1))

    return np.matrix(results)


# - Takes in a list of column headers and the Data object and returns a list of the
# median for each specified column.
def median(headers, target):
    results = []
    data_list = target.get_data(headers)
    for i in range(headers.__len__()):
        temp = []
        for item in data_list:
            temp.append(item[0, i])
        results.append(np.median(temp))

    return np.matrix(results)


# - Takes in a list of column headers and the Data object and returns a matrix with each column normalized
#  so its minimum value is mapped to zero and its maximum value is mapped to 1.
def normalize_columns_separately(headers, target):
    data_list = target.get_data(headers)
    col_list = []
    ranges = data_range(headers, target)
    for i in range(headers.__len__()):
        diff = ranges[i, 1] - ranges[i, 0]
        temp = []
        for item in data_list:
            item = item - ranges[i, 0]
            temp.append(item[0, i]/diff)
        col_list.append(temp)

    return np.matrix(col_list).T


# - Takes in a list of column headers and the Data object and returns a matrix
#  with each entry normalized so that the minimum value (of all the data in this set of columns) is mapped
# to zero and its maximum value is mapped to 1.
def normalize_columns_together(headers, target):
    data_list = target.get_data(headers)
    col_list = []
    ranges = all_data_range(headers, target)
    diff = ranges[0, 1] - ranges[0, 0]
    for item in data_list:
        temp = []
        for i in item:
            i = i - ranges[0, 0]
            temp.append(i/diff)
        col_list.append(temp)
    return np.matrix(col_list).T


# helper function for normalize_columns_together function to compute the min and max of all the column entries
def all_data_range(headers, target):
    data_list = target.get_data(headers)
    maximum = 0
    minimum = 10000000000000000
    results = []
    for item in data_list:
        for i in range(item.shape[1]):
            maximum = max(maximum, item[0, i])
            minimum = min(minimum, item[0, i])
    results.append([minimum, maximum])
    return np.matrix(results)


# takes in the data set, a list of headers for
# the independent variables, and a single header (in a list) for the dependent variable. The function
# implements linear regression for one or more independent variables.
def linear_regression(headers, dependent, target):
    # y is the column of data for the dependent variable
    y = np.matrix(target.get_data([dependent]))
    # A is the columns of data for the independent variables
    # added a column of 1's to A to represent the constant term in the regression equation.  Remember, this is just
    # y = mx + b (even if m and x are vectors).
    A = np.matrix(np.c_[target.get_data(headers), np.ones(target.get_data(headers).shape[0])])

    # The matrix A.T * A is the covariance matrix of the independent data, and we will use it for computing
    # the standard error of the linear regression fit below.
    AAinv = np.linalg.inv(np.dot(A.T, A))

    # This solves the equation y = Ab, where A is a matrix of the independent data, b is the set of unknowns as a
    # column vector, and y is the dependent column of data.  The return value x contains the solution for b.
    x = np.linalg.lstsq(A, y)

    b = x[0]
    # This is the solution that provides the best fit regression

    # assign to N the number of data points (rows in y)
    N = y.shape[0]
    # assign to C the number of coefficients (rows in b)
    C = b.shape[0]
    # assign to df_e the value N-C,
    df_e = N-C
    # This is the number of degrees of freedom of the error

    # assign to df_r the value C-1
    df_r = C-1
    # This is the number of degrees of freedom of the model fit
    # It means if you have C-1 of the values of b you can find the last one.

    # assign to error, the error of the model prediction.  Do this by taking the difference between the value to be
    # predicted and the prediction. These are the vertical differences between the regression line and the data.
    error = y - np.dot(A, b)

    # assign to sse, the sum squared error, which is the sum of the squares of the errors computed in the prior step,
    # divided by the number of degrees of freedom of the error.  The result is a 1x1 matrix.
    sse = np.dot(error.T, error) / df_e

    # assign to stderr, the standard error, which is the square root of the diagonals of the sum-squared error
    # multiplied by the inverse covariance matrix of the data. This will be a Cx1 vector.
    stderr = np.sqrt(np.diagonal(sse[0, 0] * AAinv))

    # assign to t, the t-statistic for each independent variable by dividing each coefficient of the fit by the
    # standard error.
    t = b.T / stderr

    # assign to p, the probability of the coefficient indicating a random relationship (slope = 0). To do this we use
    # the cumulative distribution function of the student-t distribution. Multiply by 2 to get the 2-sided tail.
    p = 2*(1 - stats.t.cdf(abs(t), df_e))

    # assign to r2, the r^2 coefficient indicating the quality of the fit.
    r2 = 1 - error.var() / y.var()

    # Return the values of the fit (b), the sum-squared error, the R^2 fit quality, the t-statistic, and the probability
    # of a random relationship.
    return b, sse, r2, t, p


# return a PCAData object
# This version uses SVD to calculate the eigenvectors and eigenvalues: singular value decomposition on the original
# data matrix, or direct eigenvalue and eigenvector calculation using the covariance matrix of the data
def pca(headers, target, normalize=True):

    # assign to A the desired data.
    if normalize:
        A = normalize_columns_separately(headers, target)
    else:
        A = target.get_data(headers)

    # m the mean values of the columns of A
    m = A.mean(axis=0)

    # D the difference matrix A - m

    D = A - m

    # assign to U, S, V the result of running np.svd on D, with full_matrices=False
    U, S, V = np.linalg.svd(D, full_matrices=False)

    # the eigenvalues of cov(A) are the squares of the singular values (S matrix)
    #   divided by the degrees of freedom (N-1). The values are sorted.

    eigenvalues = np.matrix(np.zeros(S.shape))
    for i in range(S.shape[0]):
        eigenvalues[0, i] = S[i]**2/(A.shape[0] - 1.0)

    # project the data onto the eigenvectors. Treat V as a transformation
    #   matrix and right-multiply it by D transpose. The eigenvectors of A
    #   are the rows of V. The eigenvectors match the order of the eigenvalues.
    projected_data = V.dot(D.T).T
    eigenvectors = V

    return data.PCAData(headers, projected_data, eigenvalues, eigenvectors, m)


# This version calculates the eigenvectors of the covariance matrix
# def pca(d, headers, normalize=True):
# assign to A the desired data. Use either normalize_columns_separately
#   or get_data, depending on the value of the normalize argument.

# assign to C the covariance matrix of A, using np.cov with rowvar=False

# assign to W, V the result of calling np.eig

# sort the eigenvectors V and eigenvalues W to be in descending order. At
#   the end of this process, the eigenvectors should be a matrix V with
#   each eigenvector as a row of the matrix.

# assign to m the mean values of the columns of A

# assign to D the difference matrix A - m

# project the data onto the eigenvectors. Treat V as a transformation
#   matrix and right-multiply it by D transpose.

# create and return a PCA data object with the headers, projected data,
# eigenvectors, eigenvalues, and mean vector.


# def kmeans(target, headers, K, whiten = True, categories = ''):
def kmeans_numpy(target, headers, K, whiten = True):
    """ Takes in a Data object, a set of headers, and the number of clusters, K to create
    Computes and returns the codebook, codes, and representation error.
    """
    # assign to A the result of getting the data from your Data object
    A = target.get_data(headers)

    # assign to W the result of calling vq.whiten on A
    W = vq.whiten(A)

    # assign to codebook, bookerror the result of calling vq.kmeans with W and K
    codebook, bookerror = vq.kmeans(W, K)

    # assign to codes, error the result of calling vq.vq with W and the codebook
    codes, error = vq.vq(W, codebook)

    return codebook, codes, error


# def kmeans_numpy(target, headers, K, whiten=True, categories = ''):
def kmeans(target, headers, K, whiten=True, categories='', manhattan=False, l_infinity_norm=False):
    '''Takes in a Data object, a set of headers, and the number of clusters to create
    Computes and returns the codebook, codes and representation errors.
    If given an Nx1 matrix of categories, it uses the category labels
    to calculate the initial cluster means.
    '''

    A = target.get_data(headers)

    if whiten is True:
        W = vq.whiten(A)
    else:
        W = A

    # assign to codebook the result of calling kmeans_init with W, K, and categories
    codebook = kmeans_init(W, K, categories)

    # assign to codebook, codes, errors, the result of calling kmeans_algorithm with W and codebook
    codebook, codes, errors = kmeans_algorithm(W, codebook, manhattan, l_infinity_norm)

    return codebook, codes, errors


# The kmeans_init should take in the data, the number of clusters K, and an optional set of categories
# (cluster labels for each data point) and return a numpy matrix with K rows, each one repesenting a cluster mean.
# If no categories are given, a simple way to select the means is to randomly choose K data points
# (rows of the data matrix) to be the first K cluster means. You want to avoid have two of the initial means being
# the same.
# If you are given an Nx1 matrix of categories/labels, then compute the mean values of each category and
# return those as the initial set of means. You can assume the categories given in the data are zero-indexed and
# range from 0 to K-1.
def kmeans_init(data_matrix, K, categories=''):
    cluster_means = np.matrix(np.zeros((K, data_matrix.shape[1])))
    if len(categories) == 0:
        for i in range(K):
            cluster_means[i, :] = (data_matrix[random.randint(0, K-1), :])
    else:
        # data_matrix = np.c_[data_matrix, categories]
        unique, labels = np.unique(np.array(categories.tolist()), return_inverse=True)
        for i in range(len(unique)):
            cluster_means[i, :] = np.mean(data_matrix[labels == i, :], axis=0)
    return cluster_means


# The kmeans_classify should take in the data and cluster means and return a list or matrix (your choice)
# of ID values and distances. The IDs should be the index of the closest cluster mean to the data point.
# The default distance metric should be sum-squared distance to the nearest cluster mean.
def kmeans_classify(data_matrix, cluster_means, manhattan, l_infinity_norm):
    distances = np.matrix(np.zeros((data_matrix.shape[0], cluster_means.shape[0])))
    for i in range(cluster_means.shape[0]):
        # also manhattan distance or l1 norm
        if manhattan:
            distances[:, i] = np.sum(np.absolute(data_matrix - cluster_means[i, :]), axis=1)

        # also called maximum norm
        elif l_infinity_norm:
            distances[:, i] = np.amax(np.absolute(data_matrix - cluster_means[i, :]), axis=1)

        # euclidean distance. also called l2 norm
        else:
            distances[:, i] = np.sqrt(np.sum(np.square(data_matrix - cluster_means[i, :]), axis=1))

    ids = np.argmin(distances, axis=1)
    distance = np.matrix(np.zeros((distances.shape[0], 1)))
    for i in range(distance.shape[0]):
        distance[i, 0] = distances[i, ids[i, 0]]

    return ids, distance


# basic K-means algorithm is as follows:
# initialize a set of K mean vectors
# loop
#   identify the closest cluster mean for each data point
#   compute a new set of cluster means
#   calculate the error between the old and new cluster means
#   if the error is small enough, break
# identify the closest cluster mean for each data point
# return the new cluster means and the cluster IDs and distances for each data point
def kmeans_algorithm(A, means, manhattan=False, l_infinity_norm=False):
    # set up some useful constants
    MIN_CHANGE = 1e-7
    MAX_ITERATIONS = 100
    D = means.shape[1]
    K = means.shape[0]
    N = A.shape[0]

    # iterate no more than MAX_ITERATIONS
    for i in range(MAX_ITERATIONS):
        # calculate the codes
        codes, errors = kmeans_classify(A, means, manhattan, l_infinity_norm)

        # calculate the new means
        newmeans = np.zeros_like(means)
        counts = np.zeros((K, 1))
        for j in range(N):
            newmeans[codes[j, 0], :] += A[j, :]
            counts[codes[j, 0], 0] += 1.0

        # finish calculating the means, taking into account possible zero counts
        for j in range(K):
            if counts[j, 0] > 0.0:
                newmeans[j, :] /= counts[j, 0]
            else:
                newmeans[j, :] = A[random.randint(0, A.shape[0]-1), :]

        # test if the change is small enough
        diff = np.sum(np.square(means - newmeans))
        means = newmeans
        if diff < MIN_CHANGE:
            break

    # call classify with the final means
    codes, errors = kmeans_classify(A, means, manhattan, l_infinity_norm)

    # return the means, codes, and errors
    return means, codes, errors


# hw06 computations check using numpy
def proofCheck(pt1, pt2):
    print "cityblock", dist.cityblock(pt1[0, :], pt2[0, :])
    print "hamming", dist.hamming(pt1[0, :], pt2[0, :])
    print "correlation", dist.correlation(pt1[0, :], pt2[0, :])


# compute the manhattan/ cityblock distance between 2 points
def LNorm(pt1, pt2):
    distance = 0.0
    for i in range(pt1.shape[1]):
        distance += abs(pt1[0, i] - pt2[0, i])
    return distance


# compute the hamming between 2 points
def hamming(pt1, pt2):
    diff_bits = 0.0
    for i in range(pt1.shape[1]):
        if pt1[0, i] != pt2[0, i]:
            diff_bits += 1

    return diff_bits/pt1.shape[1]


# compute the correlation distance
def correlation(pt1, pt2):
    return 1 - np.corrcoef(pt1, pt2)


def hw06():
    # pt1 = np.matrix([[1.0,2.0,3.0]])
    # pt2 = np.matrix([[1.1,1.9,4.05]])

    pt1 = np.matrix([[1,1,1]])
    pt2 = np.matrix([[1,0,1]])
    proofCheck(pt1, pt2)
    print

    print "cityblock mine", LNorm(pt1, pt2)
    print "hamming mine", hamming(pt1, pt2)
    print "correlation mine", correlation(pt1, pt2)


# main function
def main():
    # create data object here
    # data_object = data.Data(filename="testdata3.csv")
    # headerlist = ["headers", "spaces", "bad", "places"]
    data_object = data.Data(filename="AustraliaCoast.csv")

    # header_list = data_object.get_headers()
    # header_list = ["salmax", "maxairtemp"]
    # headers_list = header_list[-3:-1]
    # lin_reg_data = linear_regression(header_list, "premax", data_object)
    # print "m0 = ", "%.3f" % lin_reg_data[0][0, 0]
    # print "m1 = ", "%.3f" % lin_reg_data[0][1, 0]
    # print "b = ", "%.3f" % lin_reg_data[0][2, 0]
    # print "sse = ", "%.3f" % lin_reg_data[1][0, 0]
    # print "R2 = ", "%.3f" % lin_reg_data[2]
    # print "t = ", lin_reg_data[3][0, :]
    # print "t = ", ["%.3f" % lin_reg_data[3][0, 0], "%.3f" % lin_reg_data[3][0, 1], "%.3f" % lin_reg_data[3][0, 2]]
    # print "p = ", lin_reg_data[4]
    # print "p = ", lin_reg_data[4][0]
    #
    # print "data range is : ", data_range(headerlist, data_object)
    # print "mean is : ", mean(headerlist, data_object)
    # print "standard deviation is : ", stdev(headerlist, data_object)
    # print "median is : ", median(headerlist, data_object)
    # print
    # print "normalize_columns_separately"
    # print normalize_columns_separately(headerlist, data_object)
    # print
    # print "range of all data ", all_data_range(headerlist, data_object)
    # print
    # print "normalize_columns_together"
    # print normalize_columns_together(headerlist, data_object)


if __name__ == "__main__":
    main()
