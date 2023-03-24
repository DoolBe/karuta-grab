import discord
from discord.ext import commands, tasks
import time,random,json
import asyncio
from lib_imgRanker import ranker
from lib_grabber import grab,connect,sendText,checkStatus
from system import allowChannelList,allowUserList, \
    grab_waitButton_DeltaTime,grab_waitButton_BaseTime,ktb_rank

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
loop = asyncio.get_event_loop()

t_drop,t_grab,kt_b = -30*60,-10*60,0

if not connect():quit()

@client.event
async def on_ready():
    dropCard.start()
    print("We have logged in as {0.user}".format(client))
    
@tasks.loop(seconds=2*60)
async def dropCard():
    checkStatus()
    global t_drop,t_grab
    if time.time()-t_drop<30*60: return
    if time.time()-t_grab<10*60: 
        print("No grab NO drop "+str(10-(time.time()-t_grab)/60))
        return
    print("gonna drop")
    sendText("kd")

@client.event 
async def on_message(msg):
    if msg.author == client.user :return 
    if msg.channel.id not in allowChannelList:return
    if msg.author.id  not in allowUserList:return
    if msg.content.startswith('hi'):await msg.channel.send("Hi, I am ready") 
    
    global t_grab,t_drop,kt_b
    if msg.content.startswith("<@822990845799170058> took the "):
        t_grab = time.time()
        cur_time = time.strftime("%H:%M:%S", time.localtime())
        print("Grabed at "+cur_time)
        if kt_b: sendText("kt b")
        return
    if msg.content.startswith("<@822990845799170058> is dropping "):
        t_drop_rand = int(random.randint(0,1000)/1000*60*10)
        cur_time = time.strftime("%H:%M:%S", time.localtime())
        print("Droped at "+cur_time+",next drop="+str(int(t_drop_rand/60)))
        t_drop = time.time()+t_drop_rand
    
    inmesg = msg.content
    #print(inmesg)
    if "fought off <@822990845799170058> and took the" in inmesg:
        sendText("Fuck you!")
        return
    if ' is dropping ' in inmesg or "I'm dropping " in inmesg:
        if not msg.attachments: return 
        best_b,best_rank,res,res_detail = ranker(msg.attachments[0].url)
        #logMsg = res+'\nGrab '+best_b
        #logMsg = res_detail+'\nGrab '+best_b
        #await msg.channel.send(logMsg)
        
        if time.time()-t_grab<10*60:
            print("Grab CD"+str(10-(time.time()-t_grab)/60))
            return
        time.sleep(grab_waitButton_DeltaTime*(int(best_b)-1)+grab_waitButton_BaseTime)
        print("Gonna grab")
        grab(best_b)
        if best_rank<ktb_rank: kt_b = 1
        else:                  kt_b = 0
    else:return



client.run('ODczNjQ1OTM2NDYxNjI3NDYy.YQ7cLg.h_X_c0ct4h85cUf9cQJTx0s_rDY')