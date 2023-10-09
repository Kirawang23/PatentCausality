
from netgraph import Graph
import random
from ChromaPalette.chroma_palette import *
import multiprocessing
import json
from pyecharts import options as opts
from pyecharts.charts import Graph
from itertools import islice
from multiprocessing import Pool

def open_json(data_path):
    with open(data_path,encoding='utf-8') as f:
        data_name = [json.loads(line.strip()) for line in f]
    return data_name

def cluster_by_cls(data):
    cls_set = set()
    cnt = 0
    for i in data:
        i['index'] = cnt
        cnt += 1
        if type(i['cls']) != str:
            i['cls'] = i['cls'][0]
        if i['cls'] not in cls_set:
            cls_set.add(i['cls'])
    print(cnt)
    cls_set = list(cls_set)
    cluster_dict = {}
    for i in cls_set:
        tmp_dict = {i:[]}
        for j in data:
            if j['cls'] == i:
                tmp_dict[i].append(j)
        cluster_dict[i] = tmp_dict[i]
    return cls_set,cluster_dict

def text_save(content,filename,mode='a'):
    file = open(filename,mode)
    for i in range(len(content)):
        file.write(str(content[i])+'\n')
    file.close()

def text_read(filename):
    try:
        file = open(filename, 'r')
    except IOError:
        error = []
        return error
    content = file.readlines()

    for i in range(len(content)):
        content[i] = content[i][:len(content[i]) - 1]

    file.close()
    return content

def test_data(data_dict,threshold_cls_number,cls_set_dict):
    test_data = {}
    for index, (cls, cls_list) in enumerate(data_dict.items()):
        test_list = []
        for i in range(len(cls_list)):
            if i < threshold_cls_number:
                cls_list[i]['cls'] = cls_set_dict[cls]
                test_list.append(cls_list[i])
        test_data[cls_set_dict[cls]] = test_list
    return test_data

def get_link_meaeff(score_dict,link_dict):
    link_means,link_effect = {},{}
    for key, value in score_dict.items():
        for key_m, value_m in link_dict.items():
            if key_m == key:
                for key_n, value_n in value_m.items():
                    if key_n == 'means' and value > 0.5:
                        link_means[str(value_n[0])+'#'+str(value_n[1])] = value_n
                    elif key_n == 'effect' and value < 0.5:
                        link_effect[str(value_n[0])+'#'+str(value_n[1])] = value_n
    return link_means,link_effect

def chunk_process(data_dict):
    sub_list = []
    num_processes = multiprocessing.cpu_count()
    chunk_size = len(data_dict) // num_processes
    it = iter(data_dict)
    for i in range(0, len(data_dict), chunk_size):
        sub =  {k: data_dict[k] for k in islice(it, chunk_size)}
        sub_list.append(sub)
    return sub_list

def multi_process(args):
    return get_link_meaeff(*args)

def get_link_satisfied(link_means,link_effect,link_dict):
    link = []
    for index, (key, value) in enumerate(link_means.items()):
        for index_e, (key_e, value_e) in enumerate(link_effect.items()):
            if key_e == key:
                link_dict_tmp = {'source':link_dict[key_e][0], 'target': link_dict[key_e][1]}
                link.append(link_dict_tmp)
    return link

def index_to_cls(test_dict,ind):
    for index, (key, value) in enumerate(test_dict.items()):
        for each_dict in value:
            if ind == each_dict['index']:
                return each_dict['cls']

def get_link_cls(cross_link,threshold):
    cross_cls_set = set()
    cross_cls_dict = {}
    cross_cls_list = []
    for index, (key, value) in enumerate(cross_link.items()):
        print(index)
        link_cls = '#'.join([index_to_cls(test_dict,value[0]),index_to_cls(test_dict,value[1])])
        if link_cls not in cross_cls_set:
            cross_cls_set.add(link_cls)
    cnt = 0
    for i in list(cross_cls_set):
        for index, (key, value) in enumerate(cross_link.items()):
            link_cls = '#'.join([index_to_cls(test_dict,value[0]),index_to_cls(test_dict,value[1])])
            if link_cls == i:
                cnt += 1
                cross_cls_dict[i] = cnt
    for index, (key, value) in enumerate(cross_cls_dict.items()):
        if value > threshold:
            link_dict_tmp = opts.GraphLink(source=key.split('#')[0],
                                           target=key.split('#')[1],
                                           value=value,
                                           linestyle_opts=opts.LineStyleOpts(width=threshold, color='#000000',
                                                                             curve=0.05, opacity=0.7))
        else:
            link_dict_tmp = opts.GraphLink(source=key.split('#')[0],
                                           target=key.split('#')[1],
                                           value=value,
                                           linestyle_opts=opts.LineStyleOpts(width=value, color='#000000',
                                                                             curve=0.05, opacity=0.7))

        cross_cls_list.append(link_dict_tmp)
    return cross_cls_list

def index_to_pairs(test_dict,ind,mode='means'):
    for index, (key, value) in enumerate(test_dict.items()):
        for each_dict in value:
            if ind == each_dict['index']:
                if mode == 'means':
                    return each_dict['causal_pairs']['means']
                elif mode == 'effect':
                    return each_dict['causal_pairs']['effect']

def pyecharts_graph(color_list,data_dict,len_data_dict,cross_link):
    nodes,links,categories = [],[],[]

    random.shuffle(color_list)
    colorlist = color_list[:len_data_dict]

    for index, (cls, cls_list) in enumerate(data_dict.items()):
        color = colorlist[index]
        categories.append({'name': cls, "itemStyle": {"normal": {"color": color}}})
        for i in range(len(cls_list)):
            if i == 0:
                node_point = {'name': cls_list[i]['cls'], 'category': cls, 'symbolSize': len(cls_list)//2,
                              'value': len(cls_list),
                              "itemStyle": {"normal": {"color": color}}}
                nodes.append(node_point)
            else:
                node_point = {'name': str(cls_list[i]['index']), 'category': cls, 'symbolSize': 1,
                              'value': 1,
                              "itemStyle": {"normal": {"color": color}}}
                nodes.append(node_point)
                link_cls_point = opts.GraphLink(source=cls_list[0]['cls'],
                                               target=str(cls_list[i]['index']),
                                               value=1,
                                               linestyle_opts=opts.LineStyleOpts(width=0.1,color="#000000"))
                links.append(link_cls_point)
    print('number of node_point:',len(nodes))
    print('number of links:', len(links))
    c = (
        Graph(init_opts=opts.InitOpts(width="2000px", height="2000px"))
        .add(
            "",
            nodes=nodes,
            links=links,
            categories=categories,
            layout="force",
            linestyle_opts=opts.LineStyleOpts(color="#000000", curve=0.3,opacity=0.2),
            label_opts=opts.LabelOpts(is_show=False),
            repulsion=1000,
            gravity=0.5

        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="Patent Classification"),
            legend_opts=opts.LegendOpts(page_icon_size=1,
                                        pos_right='48%',pos_top='52%'),
        )
        .render("Patent_Classification.html")
    )
    links_cross = links + cross_link
    d = (
        Graph(init_opts=opts.InitOpts(width="1000px", height="1000px"))
        .add(
            "",
            nodes=nodes,
            links=links_cross,
            categories=categories,
            layout="force",
            linestyle_opts=opts.LineStyleOpts(curve=0.3,opacity=0.2),
            label_opts=opts.LabelOpts(is_show=False),
            repulsion=1000,
            gravity=0.5

        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="Patent Cross-domain Adaption"),
            legend_opts=opts.LegendOpts(page_icon_size=1,pos_bottom='0.05%'),
        )
        .render("Patent_Cross_Adaption.html")
    )


random.seed(10)
hex_dict = table_reader(file_name="ColorBars.csv")
color_list = []
for index, (cls, cls_list) in enumerate(hex_dict.items()):
    for i in cls_list:
        color_list.append(i)

data = open_json('data.json')[0]
link_dict = open_json('node.json')[0]
score_dict = open_json('cossim.json')[0]
dict(sorted(link_dict.items()))
dict(sorted(score_dict.items()))

cls_set,cluster_data = cluster_by_cls(data)
eng_ja_dict = open_json('eng_ja_dict.json')[0]
test_dict = test_data(cluster_data,100000000000000000,eng_ja_dict)

p = Pool()

link_means = {}
link_effect = {}
mutli_list = []
sub_score_dict = chunk_process(score_dict)
sub_link_dict = chunk_process(link_dict)
for i in  range(len(sub_score_dict)):
    sub_multi_list = (sub_score_dict[i],sub_link_dict[i])
    mutli_list.append(sub_multi_list)

del score_dict,link_dict,sub_score_dict,sub_link_dict,cluster_data,data

result = p.map(multi_process,mutli_list)

for sub_tuple in result:
    link_means.update(sub_tuple[0])
    link_effect.update(sub_tuple[1])

link_satisfied = {}
for key,value in link_means.items():
    for key_e, value_e in link_effect.items():
        if key == key_e:
            link_satisfied[key] = value

del link_means,link_effect,mutli_list,result

#link_satisfied = open_json('link_satisfied.json')[0]

cross_link = get_link_cls(link_satisfied,15)

with open('cross_link.json', 'wb') as fp:
    fp.write(json.dumps(cross_link, ensure_ascii=False).encode("utf8"))

pyecharts_graph(color_list,test_dict,len(eng_ja_dict),cross_link)
