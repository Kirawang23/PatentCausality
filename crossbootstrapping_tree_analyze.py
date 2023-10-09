# -*- coding: utf-8 -*-
# 渡されたCabochaの解析結果を受け取り、データをリスト化する(Mecab形式)

import re

def analyze(cabocha_str):
    tree_list = []

    for line in cabocha_str.split('\n'):

        if line.startswith('EOS') and line.strip() == 'EOS':
            yield tree_list
            tree_list = []
        elif line.startswith('* '):
            items = re.split('\s+', line.strip())
            if 'D' in items[2]:
                c = {
                    'id': int(items[1]),
                    'chunk': int(items[2][:-1]),
                    'str': [],
                    'morph': []
                }
            else:
                c = {
                    'id': int(items[1]),
                    'chunk': int(items[2]),
                    'str': [],
                    'morph': []
                }

            tree_list.append(c)
        elif line.strip() == "":
            pass
        else:
            temp_list = line.split('\t')
            items = temp_list[1].split(',')
            try:
                items2 = {'face': temp_list[0], 'base': items[-3], 'pos': items[0], 'posd': items[1]}
                tree_list[-1]['str'].append(temp_list[0])
                tree_list[-1]['morph'].append(items2)
            except IndexError:
                # print
                # "IndexError"
                # print
                # line
                fpout = open("errorlog.txt", 'a')
                fpout.write("%s\n" % (line))
                fpout.close()

