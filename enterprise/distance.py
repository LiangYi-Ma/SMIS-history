"""
@file_intro:
@creation_date:
@update_date:
@author:Yaqi Meng
"""
import torch
from scipy.spatial import distance
import numpy


class Distance:

    def __init__(self):
        self.mat = None
        self.var = None
        self.lenth = None
        self.dimension = None
        self.indexes = None

    def take_key(self, l):
        return l[1]

    def compute_var(self, arr):
        var = round(numpy.var(arr), 3)
        if var == 0:
            return 0.001
        else:
            return var

    def compute_vars(self):
        self.lenth = len(self.mat)
        self.dimension = len(self.mat[0])
        vars = []
        for i in range(self.dimension):
            vars.append(self.compute_var(self.mat[:, i]))
        self.var = numpy.array(vars)

    def compute_standard_euclidean(self):
        self.compute_vars()
        distance_set = []
        for i, idx in zip(range(self.lenth), self.indexes):
            distance_set.append([idx, distance.seuclidean(self.mat[0], self.mat[i], self.var)])
        distance_set.sort(reverse=False, key=self.take_key)
        return distance_set

