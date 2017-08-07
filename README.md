# pyMap

Map tiles Download Helper

## Base on Projects

 - [brandonxiang/pyMap](https://github.com/brandonxiang/pyMap) Raster Map Download Helper by python.
 - [brandonxiang/pyMap_GFW](https://github.com/brandonxiang/pyMap_GFW) Raster Map Download Helper with [selenium](https://github.com/SeleniumHQ/selenium/) and [PhantomJS](http://phantomjs.org/)


一个简单的地图下载工具，其中地图tile的x、y、z计算方法使用的是上述依赖项目的的方法；在此基础上修改了下载配置方法，添加多进程和同一zoom切片下载的功能提高下载速度，并让进度显示更加有好，
增加请求失败的日志和请求失败进行重试的方法。

This is a simple tool which is used to download map tiles png image. This tool is based on  [brandonxiang/pyMap](https://github.com/brandonxiang/pyMap);
Some new feature is added to the tool: 1. download with multi process, 2. split lng and lat at same zoom, 3.add error log, 4. retry when connect failed


经供参考，不要从事商业用途，后果自负。

## dependency

- python 3.5+
- requests 负责下载功能
- pillow 负责图片拼接
- tqdm 负责进度条

## install

1. install python 3.5+

2. install python module
```
    pip install requests
    pip install Pillow
    pip install tqdm
```

## usage

### config file

#### config file example

##### tile number mode

```
[config]
MODE = tile_code
NW_LAT = 803
NW_LNG = 984
SE_LAT = 1061
SE_LNG = 857
ZOOM = 15
FOLDER = test
MIXTURE = mosaic
MAP_TYPE = default
SLICE_LEVEL = 10
SLICE_STEP = 1
```

##### lng and lat scope

```
[config]
MODE = 地理编码
NW_LAT = 22.456671
NW_LNG = 113.889962
SE_LAT = 22.345576
SE_LNG = 114.212686
ZOOM = 15
FOLDER = test
MIXTURE = mosaic
MAP_TYPE = default
SLICE_LEVEL = 10
SLICE_STEP = 1
```


### command line

```
python pyMap.py 22.456671 113.889962 22.345576 114.212686 13 FOLDER MAP_TYPE

```

- param1: NW_LAT
- param2: NW_LNG
- param3: SE_LAT
- param4: SE_LNG
- param5: ZOOM
- param6: FOLDER（default 'mixture/mosaic.png'）
- param7: MAP_TYPE（default 'MAP_TYPE/mosaic.png'）


## License

[MIT](LICENSE)
