import lib_img2text
from thefuzz import fuzz,process
import os,re,csv

files = []
csvFilePaths = []
for (dir_path,dir_names,file_names) in os.walk("csvFiles/"):
    files=files+file_names  

threshold = 87  

# 读取CSV文件并将其转换为字典
def csv_to_dict(mydict,csv_path, key_col_name1, key_col_name2, value_col_name):
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            key1 = row[key_col_name1]
            key2 = row[key_col_name2]
            value = int(row[value_col_name])
            if key1 not in mydict:
                mydict[key1] = {}
            mydict[key1][key2] = value

# 读取CSV文件保存到 wishlistDict
wishlistDict = {}
for file in files: 
    if '.csv' in file: 
        csv_path = "csvFiles/"+file
        #csv_to_dict(wishlistDict,csv_path, "series","character","wishlists")
        csv_to_dict(wishlistDict, csv_path, 
                    re.sub(r'[^a-zA-Z0-9 ]', '', "series"), 
                    re.sub(r'[^a-zA-Z0-9 ]', '', "character"), 
                    "wishlists")
s_list = list(wishlistDict.keys())

def getWL(card):
    anime = ''
    similarity = threshold
    for animeName in s_list:
        s = fuzz.ratio(re.sub(r'[^a-zA-Z0-9 ]', '',card.s),animeName)
        if s > similarity:
            anime = animeName
            similarity = s
    if not similarity-threshold: return -10
    
    c_list = list(wishlistDict[anime].keys())
    chara = ''
    similarity = threshold
    for charaName in c_list:
        s = fuzz.ratio(re.sub(r'[^a-zA-Z0-9 ]', '',card.c),charaName)
        if s > similarity:
            chara = charaName
            similarity = s
    if not similarity-threshold: return -1

    return wishlistDict[anime][chara] 
    
def ranker(imgUrl):
    cards = lib_img2text.urlToCards(imgUrl)
    res,res_detail = '',''
    i,best_rank,best_b = 0,0,1
    for card in cards:
        i += 1
        wl = getWL(card)
        ptext = re.sub(r'[^0-9]', '',card.p)
        try:
            p = int(ptext)
        except ValueError: 
            p = 100
            print("card.p=? --"+card.c)
        if p<20:    prank = 300
        elif p<100: prank = 200
        elif p<500: prank = 100
        else:       prank = 1
        rank = wl + prank + int(card.ed)*3
        res_detail += str(card) + '\twl'+ str(wl) +'\trank'+ str(rank) +'\n'
        res +=  '\twl'+ str(wl) 
        if rank > best_rank:
            best_rank = rank
            best_b = i
    return str(best_b),best_rank,res,res_detail