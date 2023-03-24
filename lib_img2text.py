import cv2,os
import numpy as np
import urllib.request
import easyocr
from system import gpuOrNot,path_frame

reader = easyocr.Reader(['en'], gpu=gpuOrNot)
lower_yellow = np.array([20, 100, 100])
upper_yellow = np.array([30, 255, 255])
class AppURLopener(urllib.request.FancyURLopener):
    version = "Mozilla/5.0"
    
def match_Mask(template_img,target_img):
    ##input:  target_path(str),template_path(str)
    ##output: similarity(float),top_left(x,y),size(w,h)    
    # 将目标图像和模板图像转换为灰度图像
    target_gray = cv2.cvtColor(target_img, cv2.COLOR_BGRA2GRAY)
    template_gray = cv2.cvtColor(template_img, cv2.COLOR_BGRA2GRAY)
    # 创建模板图像的掩码图像
    if template_img.shape[2]<4:
        # 若仅有RGB，无alpha数据
        match_result_b = cv2.matchTemplate(target_img[:,:,0], template_img[:,:,0], cv2.TM_CCOEFF_NORMED)
        match_result_g = cv2.matchTemplate(target_img[:,:,1], template_img[:,:,1], cv2.TM_CCOEFF_NORMED)
        match_result_r = cv2.matchTemplate(target_img[:,:,2], template_img[:,:,2], cv2.TM_CCOEFF_NORMED)
        match_result   = (match_result_b + match_result_g + match_result_r) / 3.0
    else:
        template_masak = template_img[:, :, 3]
        match_result_b = cv2.matchTemplate(target_img[:,:,0], template_img[:,:,0], cv2.TM_CCORR_NORMED, mask=template_masak)
        match_result_g = cv2.matchTemplate(target_img[:,:,1], template_img[:,:,1], cv2.TM_CCORR_NORMED, mask=template_masak)
        match_result_r = cv2.matchTemplate(target_img[:,:,2], template_img[:,:,2], cv2.TM_CCORR_NORMED, mask=template_masak)
        match_result   = (match_result_b + match_result_g + match_result_r) / 3.0
    # 找到匹配程度最高的像素位置
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(match_result)
    size = template_gray.shape[::-1]
    return  max_val,max_loc,size

def loadFrames(path_frame):
    frameFiles = []
    frameDict = {}
    for (dir_path,dir_names,file_names) in os.walk(path_frame):
        frameFiles=frameFiles+file_names  
    for file in frameFiles: 
        if '.png' in file: 
            frameDict[file[:-4]] = cv2.imread(path_frame+file, cv2.IMREAD_UNCHANGED)
    return frameDict

class Card:
    def  __init__(self,img,button,shape): 
        self.img = img
        self.button = button
        self.shape =shape
        self.ed = self.findEd()
        self.p = self.readText('p')
        self.c = self.readText('c')
        self.s = self.readText('s')
        
    def readText(self,part):
        # part = 'p' , 's' , 'c' 
        partFrame = frameDict[self.ed+part]
        s,topleft,size = match_Mask(partFrame,self.img)
        partImg = self.img[topleft[1]:topleft[1]+size[1],topleft[0]:topleft[0]+size[0]]
        mask_inv = partFrame[:, :, 3]
        mask = cv2.bitwise_not(mask_inv)
        img_masked = cv2.bitwise_and(partImg, partImg, mask=mask)
        x, y, w, h = cv2.boundingRect(mask)
        textImg = img_masked[y:y+h,x:x+w]

        if part == 'p':
            hsv = cv2.cvtColor(textImg, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
            res = cv2.bitwise_and(textImg, textImg, mask=mask)
            text = reader.readtext(res, detail = 0, paragraph=True)
            if not text:
                h, w = res.shape[:2]
                new_h, new_w = h * 2, w * 2
                resized_img = cv2.resize(res, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                text = reader.readtext(resized_img, detail = 0, paragraph=True)
        else:
            text = reader.readtext(textImg, detail = 0, paragraph=True)
        return ' '.join(text)
        
    def findEd(self):
        maxSimilarity = 0
        ret_ed = 0
        for ed in ['1','2','3','4','5']:
            frame = frameDict[ed]
            similarity = match_Mask(frame,self.img)[0]
            #print(ed,similarity)
            if 2>similarity > maxSimilarity:
                maxSimilarity = similarity
                ret_ed = ed
            if 2 > maxSimilarity >0.98:
                return ret_ed
        return ret_ed
        
    def __repr__(self):
        return "CARD(%s,%s,p%s,ed%s)" % (self.c,self.s,self.p,self.ed)
        
def imgToCards(target_img):
    cards = []
    # crop out transparent verically
    mask = target_img[:, :, 3]
    emptyPixels = []
    for i in range(mask.shape[1]):
        if not sum(mask[:,i]): emptyPixels.append(i)
    cardRange = []
    j=-1
    for i in emptyPixels:
        if i-j>1: cardRange.append((j,i))
        j = i
    b = 1
    for (leftside,rightside) in cardRange:
        cropped = target_img[:, leftside:rightside]
        
        # crop out transparent horizonally
        mask = cropped[:, :, 3]
        emptyPixels = []
        for i in range(mask.shape[0]):
            if not sum(mask[i,:]): emptyPixels.append(i)
        j=-1
        for i in emptyPixels:
            if i-j>1: cardRange=(j,i)
            j = i
        cropped = cropped[cardRange[0]:cardRange[1],:]
        shape = cropped.shape[:-1]        
        cards.append(Card(cropped,b,shape))
        b += 1
    return cards

def urlToCards(url):
    opener = AppURLopener()
    arr = np.asarray(bytearray(opener.open(url).read()), dtype=np.uint8)
    target_img = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
    return imgToCards(target_img)
    
frameDict = loadFrames(path_frame)

