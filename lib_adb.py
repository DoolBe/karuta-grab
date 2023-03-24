import subprocess
import logging
from system import dpi,app_name,device_ip,resolutionx,resolutiony, \
    path_screenshot,file_screenshot,path_crop,grab_retrySearchButton

# 运行ADB命令的函数
def run_adb_command(cmd):
    result = subprocess.run(("adb -s "+device_ip+" "+cmd).split(), stdout=subprocess.PIPE)
    return result.stdout.decode('utf-8')

# 连接到Android设备
def connect_to_device(device_ip):
    cmd = "adb connect " + device_ip
    result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
    if "connected" in result.stdout.decode('utf-8'): 
        logging.debug("成功连接到设备：%s", device_ip)
        return True
    else: 
        logging.error("无法连接到设备：%s" , device_ip)
        return False

# 启动应用程序
def start_app(package_name, activity_name):
    cmd = "shell am start -n " + package_name + "/" + activity_name
    output = run_adb_command(cmd)
    if "Error" not in output: 
        logging.debug("应用程序已成功启动！")
        return True
    else: 
        logging.error("启动应用程序时出现错误。")
        return False

# 关闭应用程序
def stop_app(package_name):
    cmd = "shell am force-stop " + package_name
    output = run_adb_command(cmd)
    if "Error" not in output: 
        logging.debug("应用程序已成功关闭！")
        return True
    else: 
        logging.error("关闭应用程序时出现错误。")
        return False
        
# 获取应用程序名称，活动名称
def find_app(pkg_str,act_str):
    cmd = "shell pm list packages -3"
    apps = run_adb_command(cmd).split('\r\n')
    indices = [i for i, s in enumerate(apps) if pkg_str.lower() in s.lower()]
    if indices == []:
        logging.error("应用程序未安装！")
        return False
    package_name = apps[indices[0]].split('package:')[1]
    cmd = "shell dumpsys package "+ package_name +" | grep -E 'Activity|\bname='"
    activities = run_adb_command(cmd).split('\r\n')
    indices = [i for i, s in enumerate(activities) if act_str.lower() in s.lower()]
    activity = activities[indices[0]].split(' ')
    indices = [i for i, s in enumerate(activity) if act_str.lower() in s.lower()]
    activity_name = activity[indices[0]].split('/')[1]

    return package_name,activity_name

def get_resolution():
    cmd = "shell wm size"
    output = run_adb_command(cmd)
    if "x" not in output: return False
    resolution = output.split(":")[1]
    resolutionx = int(resolution.split("x")[0])
    resolutiony = int(resolution.split("x")[1])
    logging.debug("current resolution %dx%d.",resolutionx,resolutiony)
    return resolutionx,resolutiony

def get_dpi():
    cmd = "shell wm density"
    output = run_adb_command(cmd)
    dpi = int(output.split(":")[1])
    logging.debug("current dpi %d.",dpi)
    return dpi

def connect_emulator():    
    # 连接到设备
    if not connect_to_device(device_ip):return False
    # 检查分辨率
    out = get_resolution()
    if not out:return False
    if resolutionx*resolutiony != out[0]*out[1]:
        logging.error("resolution 出错！")
        return False    
    # 检查dpi
    if dpi != get_dpi():
        logging.error("dpi 出错！")
        return False
    logging.info("connect emulator successfully.")
    return True

def connect_app():
    # 测试是否安装应用程序
    found_app = find_app(app_name,"MainActivity")
    if not found_app: 
        logging.error("未安装应用程序！")
        return False
    package_name,activity_name = found_app
    if not start_app(package_name,activity_name):  return False
    logging.info("connect app successfully.")
    return True

def restart_app():
    package_name,activity_name = find_app(app_name,"MainActivity")
    if not stop_app(package_name):   return False
    if not start_app(package_name,activity_name):  return False
    logging.info("restart app successfully.")
    return True

def get_screenshot(file=file_screenshot,path=""):
    cmd = "shell screencap -p /sdcard/screenshot.png"
    output = run_adb_command(cmd)
    cmd = "pull /sdcard/screenshot.png " + path_screenshot+path+file+".png"
    output = run_adb_command(cmd)
    logging.debug("screenshot saved.")
    
def click_at(x,y):
    cmd = "shell input tap "+str(x)+" "+str(y)
    output = run_adb_command(cmd)
    logging.debug("clicked at <%d,%d>.",x,y)
    
def scroll_down():
    cmd = "shell input swipe 500 1000 300 300"
    output = run_adb_command(cmd)
    logging.debug("Scroll <down>.")
    
def textInput(text):
    cmd = 'shell input text "'+text+'"'
    output = run_adb_command(cmd)
    logging.debug("input Text:"+text)
    
def click_back():
    cmd = "shell input keyevent 4"
    output = run_adb_command(cmd)
    logging.debug("clicked <back>.")