#! /usr/bin/env python
"""
github: https://github.com/Sebastian1011/py_map.git
license: MIT
"""

import os
import sys
import math
import requests
from PIL import Image
from tqdm import trange
import configparser
import time
from datetime import datetime
from multiprocessing import Pool
from requests import Session
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util import Retry

URL = {
    "gaode": "http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=7&x={x}&y={y}&z={z}",
    "gaode.image": "http://webst02.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}",
    "tianditu": "http://t2.tianditu.cn/DataServer?T=vec_w&X={x}&Y={y}&L={z}",
    "googlesat": "http://khm0.googleapis.com/kh?v=203&hl=zh-CN&&x={x}&y={y}&z={z}",
    "tianditusat":"http://t2.tianditu.cn/DataServer?T=img_w&X={x}&Y={y}&L={z}",
    "esrisat":"http://server.arcgisonline.com/arcgis/rest/services/world_imagery/mapserver/tile/{z}/{y}/{x}",
    "gaode.road": "http://webst02.is.autonavi.com/appmaptile?x={x}&y={y}&z={z}&lang=zh_cn&size=1&scale=1&style=8",
    "default":"http://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
    "openstreet": "http://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
    "szbuilding":"http://61.144.226.124:9001/map/GISDATA/SZBUILDING/{z}/{y}/{x}.png",
    "szbase":"http://61.144.226.44:6080/arcgis/rest/services/basemap/szmap_basemap_201507_01/MapServer/tile/{z}/{y}/{x}"
}

def process_latlng(north, west, south, east, zoom, project='default', maptype="default", output='mosaic'):
    """
    download and mosaic by latlng

    Keyword arguments:
    north -- north latitude
    west  -- west longitude
    south -- south latitude
    east  -- east longitude
    zoom  -- map scale (0-18)
    output -- output file name default mosaic

    """
    print("Start to download zoom : {0}".format(zoom))
    north = float(north)
    west = float(west)
    south = float(south)
    east = float(east)
    zoom = int(zoom)
    assert(east>-180 and east<180)
    assert(west>-180 and west<180)
    assert(north>-90 and north<90)
    assert(south>-90 and south<90)
    assert(west<east)
    assert(north>south)

    left, top = latlng2tilenum(north, west, zoom)
    right, bottom = latlng2tilenum(south, east, zoom)
    process_tilenum(left, right, top, bottom, zoom, project, maptype, output)
    log = "Level {}, scope: ({},{})({},{}) download finished.".format(zoom, north, west, south, east)
    print(log)
    append_success_log(log, project)

def process_tilenum(left, right, top, bottom, zoom, project="default", maptype="default", output='mosaic'):
    """
    download and mosaic by tile number

    Keyword arguments:
    left   -- left tile number
    right  -- right tile number
    top    -- top tile number
    bottom -- bottom tile number
    zoom   -- map scale (0-18)
    output -- output file name default mosaic

    """
    left = int(left)
    right = int(right)
    top = int(top)
    bottom = int(bottom)
    zoom = int(zoom)
    assert(right>=left)
    assert(bottom>=top)

    download(left, right, top, bottom, zoom, project, maptype)
    _mosaic(left, right, top, bottom, zoom, output, project)

def download(left, right, top, bottom, zoom, project, maptype="default"):
    for x in trange(left, right + 1, desc="Zoom:{}, nw:({},{}),se:({},{})".format(zoom, left, top, right, bottom), leave=False):
        for y in trange(top, bottom + 1, desc="Zoom:{} sub job, nw:({},{}),se:({},{})".format(zoom, left, top, right, bottom), leave=False):
            path = './tiles/%s/%i/%i/%i.png' % (project, zoom, x, y)
            if not os.path.exists(path):
                _download(x, y, zoom, project,maptype)

def _download(x, y, z, project, maptype):
    url = URL.get(maptype, maptype)
    path = './tiles/%s/%i/%i' % (project, z, x)
    map_url = url.format(x=x, y=y, z=z)
    r = None
    for i in range(10):
        try:
            r = requests.get(map_url)
        except Exception as e:
            if i>=9:
                append_error_log(map_url, project)
            else:
                time.sleep(0.5)
        else:
            time.sleep(0.1)
            break

    if not os.path.isdir(path):
        os.makedirs(path)
    with open('%s/%i.png' % (path, y), 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
                f.flush()

# this function used to append failed image download
def append_error_log(log, project_name):
    log_file_name = "error_log_" + project_name + ".txt";
    with open(log_file_name, "a") as log_file:
        log_file.write(log+"\n")

def append_success_log(log, project_name):
    log_file_name = "success_log_" + project_name + ".txt";
    with open(log_file_name, "a") as log_file:
        log_file.write(log+'\n')

# merge tiles into one image
def _mosaic(left, right, top, bottom, zoom, output, project):

    size_x = (right - left + 1) * 256
    size_y = (bottom - top + 1) * 256
    output_im = Image.new("RGBA", (size_x, size_y))

    for x in trange(left, right + 1):
        for y in trange(top, bottom + 1, desc="Merge image zoom :{}".format(zoom)):
            path = './tiles/%s/%i/%i/%i.png' % (project, zoom, x, y)
            if os.path.exists(path):
                target_im = Image.open(path)
                # if target_im.mode == 'P':
                output_im.paste(target_im, (256 * (x - left), 256 * (y - top)))
                target_im.close()
    output = "merged/{}/{}/{}.png".format(project, zoom, output)
    # output = "merged/"+output+".png"
    output_path = os.path.split(output)
    if len(output_path) > 1 and len(output_path) != 0:
        if not os.path.isdir(output_path[0]):
            os.makedirs(output_path[0])
    output_im.save(output)
    output_im.close()


def latlng2tilenum(lat_deg, lng_deg, zoom):
    """
    convert latitude, longitude and zoom into tile in x and y axis
    referencing http://www.cnblogs.com/Tangf/archive/2012/04/07/2435545.html

    Keyword arguments:
    lat_deg -- latitude in degree
    lng_deg -- longitude in degree
    zoom    -- map scale (0-18)

    Return two parameters as tile numbers in x axis and y axis
    """
    n = math.pow(2, int(zoom))
    xtile = ((lng_deg + 180) / 360) * n
    lat_rad = lat_deg / 180 * math.pi
    ytile = (1 - (math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi)) / 2 * n
    return math.floor(xtile), math.floor(ytile)


# get float range
def frange(min_v, max_v, step = 1):
    assert(max_v >= min_v)
    range_list = []
    range_list.append(min_v)
    tem_v = min_v + step
    while tem_v < max_v:
        range_list.insert(0, tem_v)
        tem_v = tem_v + step
    range_list.insert(0, max_v)
    return range_list

# slice lng and lat
def break_into_process(nw_lat, nw_lng, se_lat, se_lng, min_zoom, max_zoom, step, slice_level=10):
    process_list = []
    y_list = frange(se_lat, nw_lat, step)
    x_list = frange(nw_lng, se_lng, step)
    x_list.reverse()
    for zoom in range(min_zoom, max_zoom+1):
        if zoom < slice_level:
            process_list.append({"nw_lat": nw_lat, "nw_lng": nw_lng, "se_lat": se_lat, "se_lng": se_lng, "zoom": zoom})
        else:
            for i in range(len(x_list) -1):
                start_x = x_list[i]
                end_x = x_list[i+1]
                for j in range(len(y_list) -1):
                    start_y = y_list[j]
                    end_y = y_list[j + 1]
                    process_list.append({"nw_lat":start_y, "nw_lng": start_x, "se_lat": end_y, "se_lng": end_x, "zoom": zoom})
    return process_list

def config():
    cf = configparser.ConfigParser()
    cf.read("config.conf", encoding="utf-8")
    configs = {}
    configs["mode"] = cf.get("config", "MODE")
    is_tile_code_mode = configs.get("mode") == "TILE_CODE"
    configs["nw_lat"] = is_tile_code_mode and int(cf.get("config", "NW_LAT")) or float(cf.get("config", "NW_LAT"))
    configs["nw_lng"] = is_tile_code_mode and int(cf.get("config", "NW_LNG")) or float(cf.get("config", "NW_LNG"))
    configs["se_lat"] = is_tile_code_mode and int(cf.get("config", "SE_LAT")) or float(cf.get("config", "SE_LAT"))
    configs["se_lng"] = is_tile_code_mode and int(cf.get("config", "SE_LNG")) or float(cf.get("config", "SE_LNG"))
    configs["min_zoom"] = int(cf.get("config", "MIN_ZOOM"))
    configs["max_zoom"]= int(cf.get("config", "MAX_ZOOM"))
    configs["project"] = cf.get("config", "PROJECT")
    configs["mixture"] = cf.get("config", "MIXTURE")
    configs["map_type"] = cf.get("config", "MAP_TYPE")
    configs["slice_level"] = int(cf.get("config", "SLICE_LEVEL"))
    configs["slice_step"] = float(cf.get("config", "SLICE_STEP"))
    configs["process_num"] = int(cf.get("config", "PROCESS_NUM"))
    return configs;

def test_mode():
    if not len(sys.argv) in [7, 8]:
        print('Input 7 parameter nw_lat, nw_lng, se_lat, se_lng, zoom, output_file, map_type\n')
        print("Script will use config file")
        return config()
    else:
        configs = {}
        configs["mode"] = "lng_lat"
        configs["nw_lat"] = float(sys.argv[1])
        configs["nw_lng"] = float(sys.argv[2])
        configs["se_lat"] = float(sys.argv[3])
        configs["se_lng"] = float(sys.argv[4])
        configs["min_zoom"] = int(sys.argv[5])
        configs["max_zoom"]= int(sys.argv[6])
        configs["project"] = str(sys.argv[7])
        configs["mixture"] = "mosaic"
        configs["map_type"] = str(sys.argv[8])
        configs["slice_level"] = 11
        configs["slice_step"] = 1
        configs["process_num"] = 4
        return configs
def tile_code_mode(configs):
    print("tile code mode start")
    for zoom in range(configs.get("min_zoom"), configs.get("max_zoom")+1):
        process_tilenum(configs.get("nw_lng"), configs.get("se_lng"), configs.get("nw_lat"), configs.get("se_lat"), zoom, configs.get("project"), configs.get("map_type"), configs.get("mixture"))


def lng_lat_mode(configs):
    print("lng lat mode start")
    process_list = break_into_process(configs.get("nw_lat"), configs.get("nw_lng"), configs.get("se_lat"), configs.get("se_lng"), configs.get("min_zoom"), configs.get("max_zoom"), configs.get("slice_step"), configs.get("slice_level"))
    t_pool = Pool(configs.get("process_num"))
    for val in process_list:
        t_pool.apply_async(process_latlng, args=(val.get("nw_lat"), val.get("nw_lng"), val.get("se_lat"), val.get("se_lng"), val.get("zoom"), configs.get("project"), configs.get("map_type"), configs.get("mixture"),))
    t_pool.close()
    t_pool.join()

def clear_log(project):
    error_log_file = "error_log_" + project + ".txt"
    success_log_file = "success_log_" + project +".txt"
    open(error_log_file, 'w').close()
    open(success_log_file, 'w').close()


def run_download():
    configs = test_mode()
    print("Configs is : {}".format(configs))
    if configs.get("mode") == "TILE_CODE":
        tile_code_mode(configs)
    else:
        lng_lat_mode(configs)
    print("Download end, end time is {}".format(str(datetime.now())))



if __name__ == '__main__':
    run_download()
