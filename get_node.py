import json
import time
import MeCab
from ja_stopword_remover.remover import StopwordRemover
from sentence_transformers import SentenceTransformer, util
import random
import easynmt
from ChromaPalette.chroma_palette import *

import multiprocessing
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

def translate_eng_cls_set(cls_set_original):
    eng_cls = []
    model = easynmt.EasyNMT('mbart50_m2en')
    for i in cls_set:
        translated = model.translate(i, target_lang="en", max_length=1000)
        eng_cls.append(translated)
    return eng_cls

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

def add_token(list):
    tagger = MeCab.Tagger('-Owakati')
    stopwordRemover = StopwordRemover()
    for i in range(len(list)):
        list[i] = [tagger.parse(str(list[i])).split()]
        list[i] = stopwordRemover.remove(list[i],demonstrative=True,
                                     symbol=True,
                                     verb=False,
                                     one_character=True,
                                     postpositional_particle=True,
                                     slothlib=False,
                                     auxiliary_verb=True,
                                     adjective=False
                                     )
        list[i] = ' '.join(list[i][0])

    return list[0]

def get_simi(sentences):

    list1, list2 = [], []
    for data_dict in sentences:
        for index, (key, value) in enumerate(data_dict.items()):
            sen1, sen2 = value
            list1.append(sen1)
            list2.append(sen2)

    print(f'len of list1:{len(list1)}')
    print(f'len of list2:{len(list2)}')

    if len(list1) != len(sentences):
        raise Exception('sentence length does not match')
    elif len(list2) != len(sentences):
        raise Exception('sentence length does not match')


    embeddings1 = model.encode(list1, convert_to_tensor=True,show_progress_bar=True)
    embeddings2 = model.encode(list2, convert_to_tensor=True,show_progress_bar=True)

    # Compute cosine-similarities for each sentence with each other sentence
    cosine_scores = util.cos_sim(embeddings1, embeddings2)

    # Find the pairs with the highest cosine similarity scores
    score = []
    for i in range(len(cosine_scores)):
        cossim = round(float(cosine_scores[i][i]), 4)
        score.append(cossim)
    pairs = {}
    for i in range(len(score)):
        pairs[list(sentences[i].keys())[0]] = score[i]

    return pairs

def process_range(args):
    start, end = args
    print(f'cls processing number {start}')
    multi_list = []
    multi_dict = {}

    for i in range(start, end - 1):
        for j in range(i + 1, end):
            if total_list[i]['cls'] != total_list[j]['cls']:
                multi_list.append({str(i)+'#'+str(j)+'#'+'means': [add_token([total_list[i]['causal_pairs']['means']]),
                                              add_token([total_list[j]['causal_pairs']['means']])]})
                multi_dict[str(i)+'#'+str(j)+'#'+'means'] = {'means': [total_list[i]['index'], total_list[j]['index']]}

                multi_list.append({str(i)+'#'+str(j)+'#'+'effect': [add_token([total_list[i]['causal_pairs']['effect']]),
                                              add_token([total_list[j]['causal_pairs']['effect']])]})
                multi_dict[str(i)+'#'+str(j)+'#'+'effect'] = {'effect': [total_list[i]['index'], total_list[j]['index']]}

    return multi_dict, multi_list

def loop_diff_cls(total_list):
    with multiprocessing.Pool() as pool:
        num_processes = multiprocessing.cpu_count()  # Number of CPU cores available
        chunk_size = len(total_list) // num_processes
        ranges = [(i * chunk_size, (i + 1) * chunk_size) for i in range(num_processes)]
        results = pool.map(process_range, ranges)

    multi_dict = {}
    multi_list = []
    cnt = 0
    for res in results:
        sub_dict, sub_list = res[0],res[1]
        if sub_dict != {} and sub_list != []:
            for index,(key,value) in enumerate(sub_dict.items()):
                sub_list[index][str(cnt)] = sub_list[index][key]
                del sub_list[index][key]
                multi_dict[str(cnt)] = sub_dict[key]
                cnt += 1
            multi_list += sub_list

    if len(multi_dict) != cnt or len(multi_list) != cnt:
        raise ValueError(f"Error: the length of multi_dict {len(multi_dict)} does not match the index {cnt}.")

    print(f'need to process {len(multi_list)} sentences')
    print(f'finish processing {cnt} sentences')

    return multi_dict, multi_list

def get_sbert_simi(sentences, chunk_size=1000):
    all_pairs = {}
    key_set = set()

    for i in range(0, len(sentences), chunk_size):
        chunk = sentences[i:i + chunk_size]

        list1, list2 = [], []
        for data_dict in chunk:
            for key, value in data_dict.items():
                sen1, sen2 = value[0],value[1]
                list1.append(sen1)
                list2.append(sen2)

        embeddings1 = model.encode(list1, convert_to_tensor=True, show_progress_bar=True)
        embeddings2 = model.encode(list2, convert_to_tensor=True, show_progress_bar=True)

        cosine_scores = util.cos_sim(embeddings1, embeddings2)

        score = []
        for m in range(len(cosine_scores)):
            cossim = round(float(cosine_scores[m][m]), 4)
            score.append(cossim)

        pairs = {}
        for j in range(len(chunk)):
            pair_key = list(chunk[j].keys())[0]
            if pair_key in key_set:
                raise ValueError(f"Error: keys overlapped with {pair_key}")
            else:
                key_set.add(pair_key)
            pairs[pair_key] = score[j]

        all_pairs.update(pairs)

    if len(all_pairs) != len(sentences):
        raise ValueError("Error: the length of multi_score does not match the length of multi_list.")

    return all_pairs


hex_dict = table_reader(file_name="ColorBars.csv")
color_list = []
for index, (cls, cls_list) in enumerate(hex_dict.items()):
    for i in cls_list:
        color_list.append(i)

random.seed(10)

data = open_json('data.json')[0]

cls_set,cluster_data = cluster_by_cls(data)

eng_ja_dict = open_json('eng_ja_dict.json')[0]

test_dict = test_data(cluster_data,10000000000,eng_ja_dict)

stopwords = ['こと','請求','項','前記','(',')']

model = SentenceTransformer('SBERT_1000')

total_list = []
for index, (cls, cls_list) in enumerate(test_dict.items()):
    for i in range(len(cls_list)):
        total_list.append(cls_list[i])

multi_dict, multi_list = loop_diff_cls(total_list)

start = time.time()
multi_score = get_sbert_simi(multi_list)
end = time.time()
print(f'sbert needs {end - start} second')

with open('node.json', 'wb') as fp:
    fp.write(json.dumps(multi_dict, ensure_ascii=False).encode("utf8"))

with open('cossim.json', 'wb') as fp:
    fp.write(json.dumps(multi_score, ensure_ascii=False).encode("utf8"))

