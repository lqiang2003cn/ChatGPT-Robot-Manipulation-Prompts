import IPython.display
import glob
from utils_demo import *
from sys import platform
import sys
from PIL import Image
import matplotlib.pyplot as plt
from tqdm import tqdm

import virtualhome
from virtualhome.simulation.unity_simulator.comm_unity import UnityCommunication
from virtualhome.simulation.unity_simulator import utils_viz

views = []
for scene_id in tqdm(range(10)):
    comm.reset(scene_id)

    # We will go over the line below later
    comm.remove_terrain()
    top_view = get_scene_cameras(comm, [-1])
    views += top_view

IPython.display.display(display_grid_img(views, nrows=2))