
import json
import os
import neologdn
import re
import functools
import CaboCha
import crossbootstrapping_tree_analyze
from bs4 import BeautifulSoup
from ja_sentence_segmenter.common.pipeline import make_pipeline
from ja_sentence_segmenter.concatenate.simple_concatenator import concatenate_matching
from ja_sentence_segmenter.normalize.neologd_normalizer import normalize
from ja_sentence_segmenter.split.simple_splitter import split_newline, split_punctuation
import MeCab
from ja_stopword_remover.remover import StopwordRemover
import copy
from sentence_transformers import SentenceTransformer
import pandas as pd
import glob

class causal_extraction():
    def __init__(self):
        return
    def return_each_patent_path_in_filepath(self,filepath):
        # input:file path
        # output:patent paths
        def check_if_dir(file_path):
            temp_list = os.listdir(file_path)  # put file name from file_path in temp_list
            for temp_list_each in temp_list:
                if os.path.isfile(file_path + '/' + temp_list_each):
                    temp_path = file_path + '/' + temp_list_each
                    if os.path.splitext(temp_path)[-1] == '.txt':  # check if it is a .txt file
                        patent_path.append(temp_path)
                    else:
                        continue
                else:
                    check_if_dir(file_path + '/' + temp_list_each)  # loop traversal
        patent_path = []  # path_read saves all executable files
        check_if_dir(filepath)  # put all path in patent_path

        return patent_path
    def file_name(self,filepath):
        # input: file paths
        # output: file names
        patent_text = causal_extraction.return_each_patent_path_in_filepath(filepath)
        filename = []
        for i in range(len(patent_text)):
            name = patent_text[i].split('/')[-1]
            filename.append(name)

        return filename
    def patent_content(self,filepath):
        # input: file path
        # output: patent content list
        def read_text_file(file_path):
            with open(file_path, encoding='utf-8') as f:
                text = f.read()
                return text
        patent_text = causal_extraction.return_each_patent_path_in_filepath(filepath)
        for i in range(len(patent_text)):
            patent_text[i] = [read_text_file(patent_text[i])]
            patent_text[i] = "".join(map(str, patent_text[i]))

        return patent_text
    def preprocess(self,filepath):
        def normalize_text(text):
            return neologdn.normalize(text)
        def remove_html(text):
            remove = BeautifulSoup(text, 'html5lib').get_text()
            remove_html = re.sub(r'https?://[\w/:%#\$&\?\(\)~\.=\+\-]+', '', remove)
            return remove_html
        def delete_space(text):
            delete = re.sub(r"\s", "", text)
            return delete
        def joined_devided(text):
            devided = text.splitlines()
            joined_devided = ' '.join(devided)
            return joined_devided
        def text_cleaning(text):
            text = normalize_text(text)
            text = remove_html(text)
            text = delete_space(text)
            text = joined_devided(text)
            return text
        patent_text = causal_extraction.patent_content(filepath)
        clean_text = []
        for i in range(len(patent_text)):
            clean = text_cleaning(patent_text[i])
            clean_text.append(clean)
            clean_text[i] = clean_text[i].replace('【', ':【')
        split_punc2 = functools.partial(split_punctuation, punctuations=r":】。")
        concat_tail_no = functools.partial(concatenate_matching, former_matching_rule=r"^(?P<result>.+)$",
                                           remove_former_matched=False)
        segmenter = make_pipeline(normalize, split_newline, concat_tail_no, split_punc2)
        preprocess_text = []
        for i in range(len(clean_text)):
            preprocess = list(segmenter(clean_text[i]))
            preprocess_text.append(preprocess)
        for i in range(len(preprocess_text)):
            for j in range(len(preprocess_text[i])):
                preprocess_text[i][j] = re.sub(':', '', preprocess_text[i][j])
            preprocess_text[i] = [k for k in preprocess_text[i] if k != '']

        return preprocess_text
    def create_cls_dictionary(self,excel_path_list):
        cls_dictionary = {}
        for i in excel_path_list:
            senti_excel = pd.read_excel(i, header=0)
            senti_excel.columns = ['index','cls','dot','type']
            for index, value in enumerate(senti_excel.cls):
                if not str(value)[0].isalpha():
                    senti_excel = senti_excel.drop(index)
                elif len(str(value))!=3:
                    senti_excel = senti_excel.drop(index)
                elif pd.isnull(value):
                    senti_excel = senti_excel.drop(index)

            for j in range(len(senti_excel['cls'].to_list())):
                cls_dictionary[senti_excel['cls'].to_list()[j]] = senti_excel['type'].tolist()[j]
        with open('cls_dictionary.json', 'wb') as fp:
            fp.write(json.dumps(cls_dictionary, ensure_ascii=False).encode("utf8"))

        return cls_dictionary

    def get_company(self,filepath):
        preprocess_text = causal_extraction.preprocess(filepath)
        companyname = []
        for i in range(len(preprocess_text)):
            pretext = preprocess_text[i]
            start_extract_flag = False
            result = []
            for j in range(len(pretext)):
                tex = pretext[j]
                if tex[0] == '【' and tex[1].isdigit() == False:
                    start_extract_flag = False
                if start_extract_flag == True:
                    result.append(tex)
                if tex == "【氏名又は名称】":
                    start_extract_flag = True
            companyname.append(result)
        for i in range(len(companyname)):
            sublist = companyname[i]
            if sublist != ([]):
                companyname[i] = sublist[0]
            if sublist == ([]):
                sublist.append('なし')

        return companyname
    def get_date(self,filepath):
        preprocess_text = causal_extraction.preprocess(filepath)
        date = []
        for i in range(len(preprocess_text)):
            pretext = preprocess_text[i]
            start_extract_flag = False
            result = []
            for j in range(len(pretext)):
                tex = pretext[j]
                if tex[0] == '【' and tex[1].isdigit() == False:
                    start_extract_flag = False
                if start_extract_flag == True:
                    result.append(tex)
                if tex == "【発行日】":
                    start_extract_flag = True
                elif tex == '【公開日】':
                    start_extract_flag = True
                elif tex == '【公表日】':
                    start_extract_flag = True
            date.append(result)
        for i in range(len(date)):
            sublist = date[i]
            if sublist != ([])  :
                date[i] = sublist[0]
            if sublist == ([]):
                sublist.append('なし')
            if date[i][-1] == ')' and date[i][-4] == '(':
                date[i] = date[i][:-4]

        return date
    def get_cls(self,filepath):
        preprocess_text = causal_extraction.preprocess(filepath)
        excel_path_list = glob.glob('ipc_excel/*.xlsx')
        cls_dictionary = causal_extraction.create_cls_dictionary(excel_path_list)

        cls = []
        for i in range(len(preprocess_text)):
            pretext = preprocess_text[i]
            start_extract_flag = False
            result = []
            for j in range(len(pretext)):
                tex = pretext[j]
                if tex[0] == '【' and tex[1].isdigit() == False:
                    start_extract_flag = False
                if start_extract_flag == True:
                    result.append(tex)
                if tex == "【国際特許分類】":
                    start_extract_flag = True
            cls.append(result)
        for i in range(len(cls)):
            if len(cls[i]) > 0:
                cls[i] = cls[i][0].split('/')[0][:3]
                cls[i] = cls_dictionary[cls[i]]
            else:
                cls[i].append('NaN')

        return cls
    def pure_text(self,filepath):
        def abs_effc(preprocess_text):
            total_result = []
            for i in range(len(preprocess_text)):
                pretext = preprocess_text[i]
                start_extract_flag = False
                result = []
                for j in range(len(pretext)):
                    tex = pretext[j]
                    if tex[0] == '【' and tex[1].isdigit() == False:
                        start_extract_flag = False
                    if start_extract_flag == True:
                        result.append(tex)
                    if tex == "【発明の効果】":
                        start_extract_flag = True
                    elif tex == '【考案の効果】':
                        start_extract_flag = True
                total_result.append(result)
            return total_result
        def pure(text):
            for i in range(len(text)):
                text1 = text[i]
                if text1 != ([]):
                    text1.remove(text1[0])
            return text
        preprocess_text = causal_extraction.preprocess(filepath)
        extract_text = abs_effc(preprocess_text=preprocess_text)
        pure_text = pure(extract_text)

        return pure_text
    def cross_bootstrapping(self,filepath):
        global means_clues, effect_clues
        clue_file = "clues.txt"
        means_clues = []
        effect_clues = []
        mat_koro = re.compile(" : ")
        for line in open(clue_file, 'r'):
            (c_id, clue) = mat_koro.split(line.strip())
            if c_id == "[mclue]":
                means_clues.append(clue)
            elif c_id == "[eclue]":
                effect_clues.append(clue)
            elif c_id == "[evpclue]":
                effect_clues.append(clue)
        means_clues.append("でき、")
        def get_me(m_clue, e_clue, sentence):
            c = CaboCha.Parser()

            num_id = 10000
            flag = 0
            temp_flag = 0
            mvp_flag = 0
            evp_flag = 0
            e_vp = ""
            m_vp = ""
            temp_sentence = ""
            temp_word = ""
            temp_b_word = ""
            temp_clue = ""
            means = ""

            for cabo_list in crossbootstrapping_tree_analyze.analyze(c.parse(sentence).toString(1)):
                pass

            for bunsetu in reversed(cabo_list):
                for temp in bunsetu['str']:
                    temp_word = temp_word + temp
                temp_sentence = temp_word + temp_sentence
                temp_word = ""
                for temp_mclue in means_clues:
                    if temp_mclue in temp_sentence:
                        m_id = bunsetu['id']
                        temp_flag = 1
                if temp_flag == 1:
                    break
            temp_word = ""

            for cabo_list in crossbootstrapping_tree_analyze.analyze(c.parse(sentence).toString(1)):
                pass

            for bunsetu in reversed(cabo_list):
                if m_id < bunsetu['chunk'] and m_id > bunsetu['id']:
                    break

                temp_b_word = temp_word + temp_b_word
                temp_word = ""
                for temp in bunsetu['str']:
                    temp_word = temp_word + temp

                if flag == 1:
                    means = temp_word + means

                if m_clue in temp_b_word and flag == 0:
                    flag = 1
                    means = re.sub(m_clue + ".*", "", temp_word + temp_b_word)

                temp_id = bunsetu['id']

            m = re.match(".+" + m_clue + "(?P<effect>.+?)" + e_clue, sentence)

            for temp_mclue in means_clues:
                if temp_mclue in means:
                    if re.match(".*" + temp_mclue + "(?P<means>.+)", means):
                        mm = re.match(".*" + temp_mclue + "(?P<means>.+)", means)
                        means = mm.group('means')

            if m_clue == "でき、":
                means = means + m_clue
            if not m == None:
                return (means, m.group('effect') + e_clue)
            else:
                return (None, None)

        def selectClue(c1, c2, sentence):
            temp = ""
            c1Num = 0
            c2Num = 0
            for i in range(len(sentence) - 1, -1, -1):
                temp = sentence[i] + temp
                if c1 in temp and c1Num == 0:
                    c1Num = i + len(c1) - 1
                if c2 in temp and c2Num == 0:
                    c2Num = i + len(c2) - 1
            if c1Num > c2Num:
                return c1
            elif c2Num > c1Num:
                return c2
            else:
                if len(c1) > len(c2):
                    return c1
                else:
                    return c2

        def getCausal(sen):  # sen is byte
            global means_clues, effect_clues
            data = {}
            temp_mclue = ""
            temp_eclue = ""
            for m_clue in means_clues:
                for e_clue in effect_clues:
                    if m_clue in sen and e_clue in sen:
                        if temp_mclue == "":
                            temp_mclue = m_clue
                            temp_eclue = e_clue
                        else:
                            temp_mclue = selectClue(temp_mclue, m_clue, sen)  # byte
                            if len(e_clue) > len(temp_eclue):
                                temp_eclue = e_clue
            m_clue = temp_mclue
            e_clue = temp_eclue
            if not m_clue == "":
                (means, effect) = get_me(m_clue, e_clue, sen)  # byte
                if means == None or effect == None:
                    return None
                if means == "この" or means == "その":
                    return None
                if len(means) < 2 or len(effect) < 2:
                    return None
                data['sentence'] = sen
                data['means'] = means
                data['effect'] = effect
                data['mClue'] = m_clue
                data['eClue'] = e_clue
                return data
            return None
        def causal_extract(list):
            output = []
            for i in range(len(list)):
                save = []
                for j in range(len(list[i])):
                    data = getCausal(list[i][j])
                    save.append(data)
                output.append(save)

            return output
        def delete_empty(causalpairs):
            output = []
            for sublist in causalpairs:
                output.append(list(filter(None, sublist)))
            return output
        pure_text = causal_extraction.pure_text(filepath)
        causal_pairs = causal_extract(pure_text)
        pure_pairs = delete_empty(causal_pairs)

        return pure_pairs
    def add_all_token(string):
        tagger = MeCab.Tagger('-Owakati')
        stopwordRemover = StopwordRemover()
        string = [tagger.parse(string).split()] # means
        string = stopwordRemover.remove(string, demonstrative=True,
                                     symbol=True,
                                     verb=False,
                                     one_character=True,
                                     postpositional_particle=True,
                                     slothlib=False,
                                     auxiliary_verb=True,
                                     adjective=False
                                     )
        string = ' '.join(string[0])

        return string
    def get_causal_token_embedding(causal_dict):
        model = SentenceTransformer('SBERT_1000')  # paraphrase-multilingual-MiniLM-L12-v2
        for i in causal_dict:
            for j in i['causal_pairs']:
                j['means_token'], j['effect_token'],j['means_embedding'],j['effect_embedding'] = [],[],[],[]
                j['means_token'] = causal_extraction.add_all_token(copy.deepcopy(j['means']))
                j['effect_token'] = causal_extraction.add_all_token(copy.deepcopy(j['effect']))
                j['means_embedding'] = model.encode([j['means_token']],convert_to_numpy=True,show_progress_bar=True,device='cpu')
                j['effect_embedding'] = model.encode([j['effect_token']],convert_to_numpy=True,show_progress_bar=True,device='cpu')
        return causal_dict
    def main(self):
        filepath = './data'
        patent_path = causal_extraction.return_each_patent_path_in_filepath(filepath)
        file_name = causal_extraction.file_name(filepath)
        company_name = causal_extraction.get_company(filepath)
        cls = causal_extraction.get_cls(filepath)
        date = causal_extraction.get_date(filepath)
        causal_pairs = causal_extraction.cross_bootstrapping(filepath)
        output = []
        for i in range(len(causal_pairs)):
            if causal_pairs[i] != ([]):
                for j in range(len(causal_pairs[i])):
                    causal_dict = {'path': [], 'filename': [], 'company': [], 'cls':[],
                                   'date': [], 'causal_pairs': []}
                    causal_dict['path'] = patent_path[i]
                    causal_dict['filename'] = file_name[i]
                    causal_dict['company'] = company_name[i]
                    causal_dict['cls'] = cls[i]
                    causal_dict['date'] = date[i]
                    causal_dict['causal_pairs'] = causal_pairs[i][j]
                    output.append(causal_dict)
        return output

if __name__ == '__main__':
    causal_extraction = causal_extraction()
    data = causal_extraction.main()
    with open('data.json', 'wb') as fp:
        fp.write(json.dumps(data, ensure_ascii=False).encode("utf8"))



































