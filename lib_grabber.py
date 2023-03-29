import lib_adb
import os,logging,time
import cv2

cropFiles = []
buttonDict = {}
for (dir_path,dir_names,file_names) in os.walk(lib_adb.path_crop):
    cropFiles=cropFiles+file_names    
for file in cropFiles: 
    if '.png' in file: 
        buttonDict[file[:-4]] = lib_adb.path_crop+file

def get_screenshot():        
    lib_adb.get_screenshot()

def match_Mask(template_path,target_path):
    ##input:  target_path(str),template_path(str)
    ##output: similarity(float),top_left(x,y),size(w,h)    
    # 读取目标图像和模板图像
    target_img = cv2.imread(target_path, cv2.IMREAD_UNCHANGED)
    target_img = cv2.flip(target_img, 0)
    template_img = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
    template_img = cv2.flip(template_img, 0)
    template_gray = cv2.cvtColor(template_img, cv2.COLOR_BGRA2GRAY)
    # 创建模板图像的掩码图像
    if template_img.shape[2]<4:
        # 若仅有RGB，无alpha数据
        match_result_b = cv2.matchTemplate(target_img[:,:,0], template_img[:,:,0], cv2.TM_CCOEFF_NORMED)
        match_result_g = cv2.matchTemplate(target_img[:,:,1], template_img[:,:,1], cv2.TM_CCOEFF_NORMED)
        match_result_r = cv2.matchTemplate(target_img[:,:,2], template_img[:,:,2], cv2.TM_CCOEFF_NORMED)
    else:
        template_masak = template_img[:, :, 3]
        match_result_b = cv2.matchTemplate(target_img[:,:,0], template_img[:,:,0], cv2.TM_CCORR_NORMED, mask=template_masak)
        match_result_g = cv2.matchTemplate(target_img[:,:,1], template_img[:,:,1], cv2.TM_CCORR_NORMED, mask=template_masak)
        match_result_r = cv2.matchTemplate(target_img[:,:,2], template_img[:,:,2], cv2.TM_CCORR_NORMED, mask=template_masak)
    match_result_g[match_result_g == float('inf')] = 0
    match_result_r[match_result_r == float('inf')] = 0
    match_result_b[match_result_b == float('inf')] = 0
    match_result   = (match_result_b + match_result_g + match_result_r) / 3.0
    # 找到匹配程度最高的像素位置
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(match_result)
    size = template_gray.shape[::-1]
    h_img, w_img = target_img.shape[:2]
    flip_max_loc = (max_loc[0],h_img-max_loc[1]-size[1])
    return  max_val,flip_max_loc,size

def compare_screen(buttonName,takeScreenshot=False):
    ##input: buttonName(str)
    ##output: similarity(float),center(x,y)
    if takeScreenshot: get_screenshot()
    
    templates = [val for key, val in buttonDict.items() if buttonName in key]
    target = lib_adb.path_screenshot+lib_adb.file_screenshot+".png"
    if not templates: return 0,(0,0)
    largerSimilarity = 0
    for template in templates:
        similarity,top_left,size = match_Mask(template,target)
        if similarity > largerSimilarity:
            largerSimilarity = similarity
            center = (top_left[0]+int(size[0]/2),top_left[1]+int(size[1]/2))
    return largerSimilarity,center

threshold_isInScreen = 0.98
retryTime_isInScreen = 1
sleepTime_isInScreen = 0.01

def isInScreen(template,takeScreenshot=False,isNot=False):
    if not len(template): return True^isNot
    retryChance = retryTime_isInScreen
    
    while retryChance:
        if takeScreenshot: get_screenshot()
        similarity = compare_screen(template)[0]
        if 2> similarity > threshold_isInScreen: 
            logging.debug("Successfully found <%s>.",template)
            return True^isNot
        else:
            logging.debug("Didn't find button <%s>...threshold=%f, retry.",template,similarity)
        retryChance -= 1
        time.sleep(sleepTime_isInScreen)
    logging.debug("Cannot find <%s>",template)
    return False^isNot

threshold_click_on_button = 0.98
sleepTime_click_on_button = 0.01

def click_on_button(buttonName):
    similarity,center = compare_screen(buttonName)
    if 2> similarity > threshold_click_on_button: 
        lib_adb.click_at(*center)
        logging.debug("Clicked button <%s>.",buttonName)
        time.sleep(sleepTime_click_on_button)
        return True
    else: 
        logging.error("Cannot find button <%s>...threshold=%f",buttonName,similarity)
        return False
    
def runStep(checkbefore,stepName,stepPara,checkafter,beforeIsNot=False,afterIsNot=False):
    logging.debug("STEP=%s,%s%s,%s.",checkbefore,stepName,stepPara,checkafter)
    if not isInScreen(checkbefore,takeScreenshot=True,isNot=beforeIsNot):
        logging.debug("Check-before cannot find %s.",checkbefore)
        return False
    else:
        logging.debug("Check-before successfully found %s.",checkbefore)

    step_decoder(stepName,stepPara)
    time.sleep(0.01)
    if isInScreen(checkafter,takeScreenshot=True,isNot=afterIsNot):
        logging.debug("Check-after successfully found %s.",checkafter)
        return True
    logging.debug("Check-after cannot find %s.",checkafter)
    return False
            
def step_decoder(stepName,stepPara):
    logging.debug("Run step <%s,%s>.",stepName,stepPara)
    if stepName == "button":
        click_on_button(stepPara)
    if stepName == "click":
        x = int(stepPara.split(',')[0])
        y = int(stepPara.split(',')[1])
        lib_adb.click_at(x,y)       
    if stepName == "scrolldown":
        lib_adb.scroll_down()      
    if stepName == "text":
        lib_adb.textInput(stepPara)
    if stepName == "keyBack":
        lib_adb.click_back()

def connect():
    if not lib_adb.connect_emulator(): return False
    if not lib_adb.connect_app(): return False
    return True

def grab(button,cap=lib_adb.grab_retrySearchButton):
    # input button(str) 
    if cap<0: return False
    if not isInScreen(button,takeScreenshot=True):
        time.sleep(0.2)
        return grab(button,cap-1)
    else:
        #print("grab"+button)
        runStep("","button",button,"")
        return True

def sendText(text):
    runStep("","click","550,1900","")
    runStep("","text",text,"")
    time.sleep(1)
    runStep("send","button","send","send",afterIsNot=True)
    return True

def checkStatus():
    # check newest mesg
    get_screenshot()
    if isInScreen("imageError"):
        lib_adb.click_back()
        time.sleep(0.2)
        return checkStatus()
    if isInScreen("end"):
        runStep("","button","end","")
        time.sleep(0.2)
        return checkStatus()
    if isInScreen("ErrorChannel"):
        runStep("","click","700,100","")
        time.sleep(0.2)
        return checkStatus()
    return True