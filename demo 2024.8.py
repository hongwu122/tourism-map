from folium import plugins
import folium
import os
import pandas as pd
import random
import requests
from geojson import Feature, FeatureCollection, Polygon
import numpy as np

# 创建地图
main_map = folium.Map([30.546536, 114.307344],
                      tiles='OpenStreetMap',  # 图层 , tiles='OpenStreetMap'
                      attr='HONGWU的旅游图',  # 显示在地图右下角的自定义文字
                      zoom_start=4,  # 初始化放大级别
                      )  # 中心区域的确定
# 创建一个单独的FeatureGroup图层
marker_layer0 = folium.FeatureGroup(name='显示旅游城市', tiles='OpenStreetMap')
df = pd.read_excel('5 data//中国各省份城市编码以及经纬度数据.xlsx')

'''# 画路线'''


def draw_routes(city_route, color='green', have_been_to=True):
    location = []
    for city in city_route:
        # try:
        is_in_column = city in df['省份城市'].values
        if is_in_column:
            Latitude = df[df['省份城市'] == city].iloc[0, 3]  # ['纬度']
            Longtitude = df[df['省份城市'] == city].iloc[0, 4]  # ['经度']
            print(city, Latitude, Longtitude)
            # 输入坐标点（注意）folium包要求坐标形式以纬度在前，经度在后
            location.append([Latitude + random.uniform(0.05, 0.15), Longtitude + random.uniform(0.05, 0.15)])
        else:
            print('{}\n经纬度表格中找不到城市：{}'.format('#' * 20, city))
        # except IndexError as error: # 出错则跳过
        #     print('{}\n错误是：{}\n经纬度表格中找不到城市：{}'.format('#'*20,error,city))
    # print(location)
    folium.PolyLine(  # polyline方法为将坐标用线段形式连接起来
        location,  # 将坐标点连接起来
        weight=3,  # 线的大小为3
        color=color,  # 线的颜色为橙色
        opacity=0.8  # 线的透明度
    ).add_to(main_map if have_been_to == True else main_map)  # 将这条线添加到刚才的区域m内


'''# 画城市点'''


def draw_points(city, color_outline='yellow', color_fill='green'):
    print('city:', city)
    Latitude = df[df['省份城市'] == city].iloc[0, 3]  # ['纬度']
    Longtitude = df[df['省份城市'] == city].iloc[0, 4]  # ['经度']
    folium.CircleMarker(location=[Latitude, Longtitude],
                        radius=5,  # 浮点数，默认为 10 圆形标记的半径，单位为像素。
                        # popup= 'popup', # 输入文本或可视化对象，点击时显示。
                        tooltip=city,  # 将鼠标悬停在对象上时显示文本。
                        color=color_outline,  # 轮廓
                        fill=True,
                        fill_color=color_fill,  # 填充色
                        fill_opacity=0.4
                        ).add_to(marker_layer0)


'''# 涂区域'''


def draw_region(cities, have_been_to):
    city_codes = []
    # 遍历城市名字 城市名字转换为城市编码
    for name in cities:
        # 在Excel表格中查找对应的文件名
        dfname = df[df['省份城市'] == name]
        # if not dfname.empty: # 使用empty属性检查DataFrame是否为空。 # 容易出错
        # 获取对应行的第三列文件名
        code_name = dfname.iloc[0, 1]  # 第一行 第2列
        print(name,code_name)
        city_codes.append(code_name)

    # json获取地址：http://datav.aliyun.com/portal/school/atlas/area_selector
    # 自定义区域geojson：http://geojson.io
    # 备用：https://geo.datav.aliyun.com/areas_v3/bound/{}.json
    # https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json
    # https://geo.datav.aliyun.com/areas_v3/bound/100000.json
    # 'https://geo.datav.aliyun.com/areas_v3/bound/geojson?code={}'
    features = []  # 保存各个区域geojson信息
    color = []  # 保存区域id及对应颜色深浅相对值
    # print(city_codes)
    # print(cities)
    # print(len(cities),len(city_codes))
    for code in city_codes:
        # print(code,cities[city_codes.index(code)])
        if not os.path.exists("5 生成区域//{}.txt".format(code)):  # 如果在文件夹找不到文件 就去爬网页上的
            print('不存在city文件：{}，编码：{}'.format(cities[city_codes.index(code)], code))
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5'
            }
            districts = requests.get('https://geo.datav.aliyun.com/areas_v3/bound/{}.json'.format(code),
                                     headers=headers).json()
            # with open('district.geojson', 'rb') as f:
            # districts = geojson.load(data)  # 读取geojson格式文件
            with open("5 生成区域//{}.txt".format(code), "w", encoding='utf-8') as f:
                f.write(str(districts))
                f.close()
        else:
            f = open('5 生成区域//{}.txt'.format(code), 'r', encoding='utf-8')
            districts = eval(f.read())
            f.close()
        for idx, geometry in enumerate(districts['features']):  # 提取所有区域
            # 获取经纬度列表[[lon, lat], ...]，两次[0]是由于该列表被嵌套在两层列表中
            circle = geometry['geometry']['coordinates'][0][0]
            # 染色区域id，颜色相对深度, 这里设置为0~100的随机数
            color.append([str(idx), np.random.randint(100)])
            polygon = Polygon([circle])  # 区域经纬度
            features.append(Feature(
                id=str(idx),  # 指定geojson的id值，染色时使用该id与color中的idx匹配
                geometry=polygon
            ))
    feature_collection = FeatureCollection(features)  # 生成绘制所需格式的geojson
    folium.Choropleth(
        geo_data=feature_collection,  # 传入geojson 存放某地区经纬情况的文件
        name='choropleth',
        data=pd.DataFrame(color, columns=['idx', 'color']),  # 颜色数据
        columns=['idx', 'color'],  # 染色区域id，颜色相对深度列名
        key_on='feature.id',  # geojson区域id
        nan_fill_color='#a6a8e7',  # 浅紫色
        fill_color='BuPu',  # 颜色样式
        fill_opacity=0.5,  # 区域透明度
        line_opacity=0.01,  # 边缘透明度
        highlight=True,  # 当鼠标悬停在GeoJSON区域上时，启用高亮功能。
        overlay=False,
        legend_name='图例名'  # 图例名
    ).add_to(main_map if have_been_to == True else main_map)
    # 'BuGn', 'BuPu', 'GnBu', 'OrRd', 'PuBu', 'PuBuGn', 'PuRd', 'RdPu',
    # 'YlGn', 'YlGnBu', 'YlOrBr', and 'YlOrRd'


# 路线
route1汕尾到衡阳 = ['汕尾市', '惠东县', '深圳市', '广州市', '英德市', '韶关市', '郴州市', '衡阳市']
route2汕尾到珠海 = ['汕尾市', '惠东县', '深圳市', '广州市', '中山市', '珠海市']
route3汕尾到桂林 = ['汕尾市', '惠东县', '深圳市', '广州市', '贺州市', '桂林市']
route4衡阳到萍乡 = ['衡阳市', '萍乡市', '安福县']
route5衡阳到南昌 = ['衡阳市', '南昌市', '九江市', '庐山区', '景德镇市', '南昌市', '衡阳市']
route6衡阳到长沙 = ['衡阳市', '株洲市', '长沙市', '韶山市']
route7衡阳到武昌 = ['衡阳市', '株洲市', '长沙市', '岳阳市', '赤壁市', '武汉市']
route8衡阳到开封 = ['衡阳市', '株洲市', '长沙市', '岳阳市', '赤壁市', '武昌区', '驻马店市', '漯河市', '许昌市',
                    '郑州市', '开封市']
route8开封到衡阳 = ['开封市', '郑州市', '登封市', '洛阳市', '汝州市', '漯河市', '驻马店市', '信阳市', '武昌区',
                    '长沙市', '衡阳市']
route9衡阳到西安 = ['衡阳市', '株洲市', '长沙市', '岳阳市', '武昌区', '南阳市', '西安市', '华阴市']
route9西安到衡阳 = ['华阴市', '西安市', '镇安县', '安康市', '十堰市', '襄阳市', '石门县', '衡阳市']
route10衡阳到南宁 = ['衡阳市', '永州市', '桂林市', '柳州市', '南宁市']
route11衡阳到广州 = ['衡阳市', '郴州市', '韶关市', '英德市', '广州市']
route12汕尾到上海 = ['汕尾市', '揭阳市', '潮州市', '漳州市', '厦门市', '泉州市', '莆田市', '福州市', '福安市', '霞浦县',
                     '温州市', '台州市', '宁波市', '杭州市', '嘉兴市', '上海市']
route12上海到汕尾 = ['汕尾市', '汕头市', '揭阳市', '潮州市', '漳州市', '厦门市', '泉州市', '莆田市', '福州市', '福安市',
                     '霞浦县', '温州市', '台州市', '宁波市', '杭州市', '嘉兴市', '上海市']
route13上海到大同 = ['上海市', '无锡市', '常州市', '南京市', '德州市', '石家庄市', '阳泉市', '太原市', '忻州市',
                     '五台县', '忻州市', '代县', '原平市', '应县', '大同市', '浑源县']
route13大同到上海 = ['浑源县', '大同市', '太原市', '石家庄市', '淄博市', '济南市', '泰安市', '徐州市', '蚌埠市',
                     '合肥市', '南京市', '常州市', '无锡市', '上海市']

route14上海到杭州 = ['上海市', '杭州市', '绍兴市', '杭州市', '宣城市', '杭州市', '嘉兴市', '上海市']
route14上海到南京 = ['上海市', '苏州市', '南京市', '上海市']
route14上海到汕尾 = ['汕尾市', '汕头市', '揭阳市', '潮州市', '漳州市', '厦门市', '泉州市', '莆田市', '福州市', '福安市',
                     '霞浦县', '温州市', '台州市', '宁波市', '杭州市', '嘉兴市', '上海市']
route14汕尾到上海 = ['汕尾市', '潮州市', '漳州市', '厦门市', '泉州市', '莆田市', '福州市', '宁德市', '龙泉市', '衢州市',
                     '金华市', '杭州市', '嘉兴市', '上海市']

route15上海到北京 = ['上海市', '昆山市', '苏州市', '无锡市', '常州市', '南京市', '蚌埠市', '徐州市', '兖州区', '泰安市',
                     '济南市', '德州市', '沧州市', '河东区', '北京市']  # 天津市 有bug 不能显示
route15北京到上海 = ['北京市', '广阳区', '河东区', '青县', '泊头市', '吴桥县', '德州市', '禹城市', '济南市', '泰山区',
                     '宁阳县', '兖州区', '徐州市', '宿州市', '蚌埠市', '南京市', '常州市', '无锡市','苏州市','上海市']  # 天津市 有bug 不能显示

route15上海到南宁 = ['上海市', '嘉兴市', '杭州市', '衢州市', '南昌市','株洲市','湘乡市','衡阳市', '永州市', '桂林市', '柳州市', '南宁市']
route15广西环线 = ['南宁市', '防城港市', '东兴市', '防城港市', '钦州市', '南宁市']
route15南宁到上海 = ['南宁市', '柳州市', '桂林市', '永州市', '衡阳市', '株洲市', '萍乡市', '宜春市', '新余市', '南昌市', '九江市',
                     '池州市', '铜陵市', '芜湖市', '南京市', '镇江市', '常州市', '无锡市', '苏州市', '上海市']

route16上海到西安 = ['上海市', '苏州市', '南京市', '徐州市', '开封市', '郑州市', '渭南市', '西安市']
route16西安到西宁 = ['西安市', '咸阳市', '宝鸡市', '天水市', '定西市', '兰州市', '西宁市']
route16西宁青甘大环线 = ['西宁市', '海南藏族自治州', '乌兰县', '德令哈市', '海西蒙古族藏族自治州', '海西蒙古族藏族自治州直辖', '阿克塞哈萨克族自治县',
                         '敦煌市', '瓜州县', '玉门市', '嘉峪关市', '酒泉市', '张掖市', '门源回族自治县', '西宁市']
route16西宁到拉萨 = ['西宁市', '海西蒙古族藏族自治州', '格尔木市', '玉树藏族自治州', '那曲市', '拉萨市']
route16拉萨到西藏环线 = ['拉萨市', '山南市', '浪卡子县', '江孜县', '定结县', '定日县', '拉孜县', '日喀则市', '拉萨市']
route16拉萨到兰州 = ['拉萨市', '那曲市', '玉树藏族自治州', '格尔木市', '德令哈市', '海南藏族自治州', '西宁市', '海东市', '兰州市']

route17兰州到贵阳 = ['兰州市', '定西市', '陇西县', '天水市', '广元市', '绵阳市', '德阳市', '广汉市', '成都市', '遂宁市', '重庆市', '遵义市', '贵阳市']
route17贵州环线 = ['贵阳市','黔南布依族苗族自治州','黔东南苗族侗族自治州', '贵阳市','安顺市', '贵阳市']
route17贵阳到粤港澳环线 = ['贵阳市', '桂林市', '贺州市', '肇庆市', '广州市', '佛山市', '广州市', '深圳市',
                           '香港特别行政区', '澳门特别行政区', '珠海市', '中山市', '佛山市', '广州市', '深圳市', '惠州市','汕尾市']

# route17出国巴林线 = ['汕尾市','上海市','巴林']
# route17出国巴林线 = ['巴林','沙特利雅得','巴林']
# route17出国巴林线 = ['巴林',]



P_routes = [route1汕尾到衡阳,
            route2汕尾到珠海,
            route3汕尾到桂林,
            route4衡阳到萍乡,
            route5衡阳到南昌,
            route6衡阳到长沙,
            route7衡阳到武昌,
            route8衡阳到开封,
            route8开封到衡阳,
            route9衡阳到西安,
            route9西安到衡阳,
            route10衡阳到南宁,
            route11衡阳到广州,
            route12汕尾到上海,
            route12上海到汕尾,
            route13上海到大同,
            route13大同到上海,
            route14上海到杭州,
            route14上海到南京,
            route14上海到汕尾,
            route14汕尾到上海,
            route15上海到北京,
            route15北京到上海,
            route15上海到南宁,
            route15广西环线,
            route15南宁到上海,
            route16上海到西安,
            route16西安到西宁,
            route16西宁青甘大环线,
            route16西宁到拉萨,
            route16拉萨到西藏环线,
            route16拉萨到兰州,
            route17兰州到贵阳,
            route17贵州环线,
            route17贵阳到粤港澳环线
            ]
num  =  len(P_routes)
citylist = ['汕尾市', '惠来县', '深圳市', '广州市', '衡阳市',
            '汕尾市', '深圳市', '广州市', '中山市', '珠海市', '汕尾市',
            '汕尾市', '深圳市', '广州市', '桂林市', '汕尾市',
            '衡阳市', '萍乡市', '衡阳市',
            '衡阳市', '南昌市', '九江市', '景德镇市', '南昌市', '衡阳市',
            '衡阳市', '株洲市', '长沙市', '韶山市',
            '衡阳市', '岳阳市', '赤壁市', '武汉市', '衡阳市',
            '衡阳市', '郑州市', '开封市',
            '登封市', '洛阳市','衡阳市',
            '衡阳市', '西安市', '华阴市',
            '襄阳市', '衡阳市',
            '衡阳市', '柳州市', '南宁市',
            '衡阳市', '广州市',
            '上海市',
            '上海市',
            '太原市', '忻州市', '五台县', '代县', '应县','大同市', '浑源县',
            '浑源县', '石家庄市', '淄博市', '济南市', '泰安市', '徐州市', '合肥市', '南京市', '无锡市', '上海市',
            '上海市', '杭州市', '绍兴市', '杭州市', '宣城市', '杭州市', '嘉兴市', '上海市',
            '上海市', '苏州市', '南京市', '上海市',
            '汕头市',
            '汕尾市', '潮州市', '漳州市', '厦门市', '泉州市', '莆田市', '福州市', '宁德市', '衢州市', '上海市',
            '上海市', '天津市', '北京市',
            '北京市', '上海市',
            '上海市','南宁市',
            '防城港市', '东兴市', '防城港市', '钦州市',
            '南宁市', '上海市',
            '上海市', '西安市',
            '西安市', '西宁市',
            '西宁市', '门源回族自治县', '张掖市', '瓜州县', '酒泉市', '敦煌市', '海西蒙古族藏族自治州直辖', '格尔木市', '乌兰县', '西宁市',
            '西宁市', '海南藏族自治州', '格尔木市', '拉萨市',
            '拉萨市', '山南市', '浪卡子县', '定日县', '日喀则市', '拉萨市',
            '拉萨市', '西宁市', '兰州市',
            '广汉市', '成都市', '重庆市', '贵阳市',
            '贵阳市', '黔东南苗族侗族自治州', '贵阳市', '安顺市', '贵阳市',
            '贵阳市', '广州市', '佛山市', '深圳市','香港特别行政区', '澳门特别行政区', '佛山市', '广州市', '深圳市','汕尾市',
            ]
print(len(P_routes)) #35
print(len(citylist)) #35
color = ['#3c5be9', '#3ddab3', '#3ca9b9', '#d8c066', '#3b3205', '#5d372b', '#d9a59c', '#893f27',
         '#ace487', '#60ec62', '#66de88', '#769935', '#868ec3', '#266322', '#d9a59c', '#c44b41',
         '#66de88', '#d9a59c', '#893f27', '#868ec3', '#769935', '#266322', '#3b3205', '#d8c066',
         '#868ec3',
         '#3c5be9', '#3ddab3', '#3ca9b9', '#d8c066', '#3b3205', '#5d372b', '#d9a59c', '#893f27',
         '#ace487', '#60ec62', '#66de88', '#769935', '#868ec3', '#266322', '#d9a59c', '#c44b41',
         '#66de88', '#d9a59c', '#893f27', '#868ec3', '#769935', '#266322', '#3b3205', '#d8c066',
         '#868ec3'
         ]

# 根据去过的城市涂区域，城市越多次数，涂色越深
cities = [r for rs in P_routes for r in rs]  # == cities=[] for rs in routes: for r in rs: cities.append(r)
print(cities)
draw_region(cities, have_been_to=True)
# 画路线
c = 0
for r in P_routes:
    # c = random.randint(0, len(color) - 1)
    draw_routes(city_route=r, color=color[c], have_been_to=True)
    c += 1
# 标记去过的城市

for c in citylist:
    draw_points(city=c, color_outline='yellow', color_fill='green')  # CircleMarker


# 将标注图层添加到地图中
marker_layer0.add_to(main_map)

# 使用TileLayer添加不同的地图图层
folium.TileLayer(
    'http://thematic.geoq.cn/arcgis/rest/services/ThematicMaps/administrative_division_boundaryandlabel/MapServer/tile/{z}/{y}/{x}',
    attr='HONGWU的旅游图').add_to(main_map)  # 添加另一种地图图层
# folium.TileLayer('cartodbpositron').add_to(main_map)  # 英文地图 添加另一种地图图层
folium.TileLayer('OpenStreetMap').add_to(main_map)  # 中文地图 添加另一种地图图层
# 添加LayerControl以切换不同的地图图层
folium.LayerControl().add_to(main_map)

main_map.add_child(folium.LatLngPopup())  # 启用纬度/经度弹出窗口，点击地图可查询经纬度
main_map.save(os.path.join('test_9_map4 2024.8.9 {}.html'.format(num)))  # 将结果以HTML形式保存到桌面上
