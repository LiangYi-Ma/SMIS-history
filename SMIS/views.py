from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required

from django.http import HttpResponse, JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import datetime
import random

import cv2
import numpy as np
# import matplotlib.pyplot as plt
from sklearn.neighbors import NearestNeighbors
from copy import copy
import time
import pandas as pd


def compute_nearest_point(points_list, start_points_idx):
    points_list = np.array(points_list)
    nbrs = NearestNeighbors(n_neighbors=2, algorithm='ball_tree').fit(points_list)
    distances, indices = nbrs.kneighbors(points_list)
    index_near = indices[:, 1][start_points_idx]
    dis_near = distances[:, 1][start_points_idx]
    return index_near, dis_near


# 检测异常值，四分位点检测法
def detect_outliers2(df):
    epsilon = 5
    outlier_indices = []
    # 1st quartile (25%)
    Q1 = np.percentile(df, 25)
    # 3rd quartile (75%)
    Q3 = np.percentile(df, 75)
    # Interquartile range (IQR)
    IQR = Q3 - Q1
    # outlier step
    outlier_step = 1.5 * IQR + epsilon
    no = 0
    for nu in df:
        # if (nu < Q1 - outlier_step) | (nu > Q3 + outlier_step):
        if nu > Q3 + outlier_step:
            outlier_indices.append(1)
            no += 1
        else:
            outlier_indices.append(0)
    print("轮次的离群点判定距离为", Q3 + outlier_step, ";检测到离群点数量", no)
    return outlier_indices


# 画面右转
def turn_right(points_list, size):
    row = size[0]
    result = []
    for point in points_list:
        # print(point)
        temp = copy(point)
        x = temp[1]
        y = row - temp[0]
        result.append([x, y])
        # print([x, y])
    return result


def drawing_by_image(request):
    text = "好地方"
    return render(request, "drawingAI.html", locals())


def drawing_file(request, image_id):
    # image_name = "/static/img/drawing-proj/draw-" + str(image_id) + ".jpeg"
    image_name = "static/img/drawing-proj/draw_imgs/draw-0" + str(image_id) + ".jpeg"
    points_file = "static/img/drawing-proj/final_files/draw-0" + str(image_id) + ".txt"

    df_news = pd.read_table(points_file, header=None).values


    return render(request, "drawingAI-imageID.html", locals())
