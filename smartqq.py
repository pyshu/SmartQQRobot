# -*- coding: utf-8 -*-
__author__ = 'lius'

import tkinter
import requests
import random
import time
import json
from multiprocessing import Process

class SmartQQ():
    def __init__(self):
        self.headers = {'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.75 Safari/537.36 LBBROWSER",
                         'Referer' : 'https://ui.ptlogin2.qq.com/cgi-bin/login?daid=164&target=self&style=16&mibao_css=m_webqq&appid=501004106&enable_qlogin=0&no_verifyimg=1&s_url=http%3A%2F%2Fw.qq.com%2Fproxy.html&f_url=loginerroralert&strong_login=1&login_state=10&t=20131024001'}

        self.ssession= requests.session()
        self.ssession.headers.update(self.headers)
        self.cookies_qrsig = ""
        self.ptwebqq = ""
        self.vfwebqq = ""
        self.psessionid = ""
        self.uin = 0
        self.face = 0
        self.qqnum = 0
        self.qqname = ''
        self.getmsgcount = 0

    def show_QRC(self,content):
        '''
        通过 tkinter 显示二维码.
        '''
        if(content != None):
            root = tkinter.Tk()  #显示二维码
            root.title("扫描二维码")
            root.geometry('200x150') #设置窗口大小
            root.resizable(width=False, height=False) #窗口大小不可变

            size = '%dx%d+%d+%d' % (200, 150, (root.winfo_screenwidth() - 200) / 2, (root.winfo_screenheight() - 150) / 2)
            root.geometry(size)

            img = tkinter.PhotoImage(data=content)
            label = tkinter.Label(root, image=img)
            label.pack()
            root.mainloop()
        else:
            print("二维码获取失败.")

    def get_ptqrtoken(self):
        '''
        # ptqrtoken 计算
        '''
        token = 0
        for i in range(len(self.cookies_qrsig)):
            token += (token << 5) + ord(self.cookies_qrsig[i])
        return 2147483647 & token

    def check_login_status(self,p):
        '''
        # 登录状态检测
        '''
        url = "https://ssl.ptlogin2.qq.com/ptqrlogin?ptqrtoken=" + str(self.get_ptqrtoken()) +\
              "&webqq_type=10&remember_uin=1&login2qq=1&aid=501004106" \
              "&u1=http%3A%2F%2Fw.qq.com%2Fproxy.html%3Flogin2qq%3D1%26webqq_type%3D10" \
              "&ptredirect=0&ptlang=2052&daid=164&from_ui=1&pttype=1&dumy=&fp=loginerroralert" \
              "&action=0-0-" + str(random.randint(1000, 30000)) +\
              "&mibao_css=m_webqq&t=1&g=1&js_type=0&js_ver=10216&login_sig=&pt_randsalt=2"
        # 死循环检测扫码登陆状态
        while 1:
            content = self.ssession.get(url=url).content.decode("utf-8")
            # 登陆成功跳出循环
            if "二维码" not in content:
                data = content.split(',')
                # print(data)
                print("二维码认证成功.\n登录用户：%s\n" % (data[5])[:-3])
                # 结束进程 p
                if p.is_alive():
                    p.terminate()
                self.login_status = True
                return data[2].replace("'","")
            print("二维码认证中.....（请用手机QQ扫描二维码并确认登陆.）")
            time.sleep(3)

    def login(self):
        '''
        # qq登陆过程
        '''
        # 下面 url 中 t = ？，？为获取二维码请求随机数。
        url = "https://ssl.ptlogin2.qq.com/ptqrshow?appid=501004106&amp;e=0&amp;l=M&amp;s=5&amp;d=72&amp;v=4&amp;t=0.562284958449" + str(random.randint(10000,100000))
        content = self.ssession.get(url=url).content  #获取二维码数据（二进制）
        self.cookies_qrsig = (requests.utils.dict_from_cookiejar(self.ssession.cookies))["qrsig"]
        #使用进程显示二维码，等待扫描。
        p = Process(target=self.show_QRC,args=(content,))
        #启动进程 p
        p.start()
        time.sleep(1)

        #获取验证成功后返回的请求地址
        url = self.check_login_status(p)
        self.headers.pop("Referer")
        self.headers['Upgrade-Insecure-Requests'] = "1"
        self.ssession.headers.update(self.headers)
        # 请求获取 cookies 中 ptwebqq
        self.ssession.get(url=url)
        self.ptwebqq = (requests.utils.dict_from_cookiejar(self.ssession.cookies))["ptwebqq"]
        # print("ptwebqq : %s" % self.ptwebqq)

        # 请求获取 json 中 vfwebqq
        url = "http://s.web2.qq.com/api/getvfwebqq?ptwebqq=" + str(self.ptwebqq) +\
              "&clientid=53999199&psessionid=&t=1493177741164"
        j_data = json.loads(self.ssession.get(url=url).content.decode("utf-8"))
        self.vfwebqq = j_data["result"]["vfwebqq"]
        # print("vfwebqq : %s" % self.vfwebqq)

        # 请求获取  psessionid  uin
        self.headers.pop("Upgrade-Insecure-Requests")
        self.headers["Referer"] = "http://d1.web2.qq.com/proxy.html?v=20151105001&callback=1&id=2"
        self.headers["Origin"] = "http://d1.web2.qq.com"
        self.ssession.headers.update(self.headers)
        url = "http://d1.web2.qq.com/channel/login2"
        p_data = {"ptwebqq": str(self.ptwebqq),"clientid":53999199,"psessionid":"","status":"online"}
        r_data = {"r":json.dumps(p_data)}

        j_data = json.loads(self.ssession.post(url=url,data=r_data).content.decode("utf-8"))
        self.psessionid = j_data["result"]["psessionid"]
        self.uin = j_data["result"]["uin"]
        # print("psessionid : %s" % self.psessionid)
        print("恭喜，SmartQQ登录成功。\n")

    def get_hash(self):
        '''
        # hash 值计算
        '''
        uin = int(self.uin)
        ptwebqq = self.ptwebqq
        ptb = [0,0,0,0]
        for i in range(len(ptwebqq)):
            ptb[i % 4] ^= ord(ptwebqq[i])
        uin = int(uin)
        uinByte = [0,0,0,0]
        uinByte[0] = uin >> 24 & 255 ^ 69   # E
        uinByte[1] = uin >> 16 & 255 ^ 67   # C
        uinByte[2] = uin >> 8 & 255 ^ 79    # O
        uinByte[3] = uin & 255 ^ 75         # K
        result = [0 for x in range(8)]
        for i in range(0,8):
            if(i % 2 == 0):
                result[i] = ptb[i >> 1]
            else:
                result[i] = uinByte[i >> 1]
        hex = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F']
        buf = ""
        for i in result:
            buf += hex[i >> 4 & 15]
            buf += hex[i & 15]
        return buf

    def recur_list(self,lst):
        '''
        递归将list的元素处理成字符串，函数主要针对list内有list。
        '''
        con = ""
        for ele in lst:
            if isinstance(ele, list):
                con += self.recur_list(ele)
            else:
                con += str(ele)
        return con

    def get_self_info(self):
        '''
        # 获取个人信息
        '''
        url = "http://s.web2.qq.com/api/get_self_info2?t=1493263376886"
        try:
            j_data = json.loads(self.ssession.get(url=url).content.decode("utf-8"))
            self.face = j_data["result"]["face"]
            self.qqname = j_data["result"]["nick"]
            self.qqaccount = j_data["result"]["account"]
            print("我的QQ资料：%s" % j_data["result"])
            return j_data["result"]
        except:
            return None

    def get_group_list(self):
        '''
        # 获取QQ群
        '''
        url = "http://s.web2.qq.com/api/get_group_name_list_mask2"
        p_data = {"vfwebqq": str(self.vfwebqq), "hash": self.get_hash()}
        r_data = {"r": json.dumps(p_data)}
        try:
            j_data = json.loads(self.ssession.post(url=url, data=r_data).content.decode("utf-8"))
            groups_data = { k['name']: k for k in j_data["result"]["gnamelist"] }
            print("QQ群：%s" % groups_data)
            return groups_data
        except:
            return None

    def get_friends_info(self):
        '''
        # 获取QQ好友
        '''
        url = "http://s.web2.qq.com/api/get_user_friends2"
        p_data = {"vfwebqq": str(self.vfwebqq),"hash": self.get_hash()}
        r_data = {"r": json.dumps(p_data)}
        try:
            j_data = json.loads(self.ssession.post(url=url, data=r_data).content.decode("utf-8"))
            friends_data = { k['nick']: k for k in j_data["result"]["info"] }
            print("QQ好友信息：%s" % friends_data)
            return friends_data
        except:
            return None

    def get_chat_msg(self):
        '''
        # 接收消息
        '''
        if self.getmsgcount > 40:
            self.get_online_buddies2()
            self.getmsgcount = 0
        else:
            self.getmsgcount += 1
        get_msg_url = "https://d1.web2.qq.com/channel/poll2"
        self.headers["Origin"] = "https://d1.web2.qq.com"
        self.headers["Referer"] = "https://d1.web2.qq.com/cfproxy.html?v=20151105001&callback=1"
        self.ssession.headers.update(self.headers)
        p_data = {"ptwebqq": str(self.ptwebqq),
                  "clientid": 53999199,
                  "psessionid": str(self.psessionid),
                  "key": ""}
        r_data = {"r": json.dumps(p_data)}
        try:
            j_data = json.loads(self.ssession.post(url=get_msg_url, data=r_data).content.decode("utf-8"))
            if "errmsg" in j_data.keys():
                print(j_data)
                return None
            if "result" in j_data.keys():
                content = self.recur_list(j_data["result"][0]["value"]["content"][1:])
                data = {"poll_type": j_data["result"][0]["poll_type"],
                        "from_uin": j_data["result"][0]["value"]["from_uin"],
                        "content": content,
                        }
                if data["poll_type"] == "group_message":
                    data["send_uin"] = j_data["result"][0]["value"]["send_uin"]
                else:
                    data["send_uin"] = None
                return data
            return None
        except:
            print('Fetch message exception!')
            return None
        # {"result":[{"poll_type":"group_message",
            # "value":{
            # "content":[["font",{"color":"000000","name":"微软雅黑","size":10,"style":[0,0,0]}],"好"],
            # "from_uin":2324333159,
            # "group_code":2324333159,
            # "msg_id":18317,"msg_type":4,
            # "send_uin":1550070579,"time":1496933934,"to_uin":979885605}}],"retcode":0}
        # {"result":[{"poll_type":"message",
            # "value":{
            # "content":[["font",{"color":"000000","name":"微软雅黑","size":10,"style":[0,0,0]}],"哈哈哈哈"],
            # "from_uin":1550070579,
            # "msg_id":18321,
            # "msg_type":1,
            # "time":1496934177,
            # "to_uin":979885605}}],"retcode":0}

    def get_online_buddies2(self):
        '''
        # 获取QQ在线好友
        '''
        url = "http://d1.web2.qq.com/channel/get_online_buddies2?vfwebqq=" + str(self.vfwebqq) +\
              "&clientid=53999199&psessionid="+ str(self.psessionid) +\
              "&t=149429685" + str(random.randint(1000,10000))
        # headers = {"User-Agent":self.headers["User-Agent"]}
        # headers["Host"] = "d1.web2.qq.com"
        # headers["Referer"] = "http://d1.web2.qq.com/proxy.html?v=20151105001&callback=1&id=2"
        # self.ssession.headers.update(headers)
        try:
            j_data = json.loads(self.ssession.get(url=url).content.decode("utf-8"))
            print("QQ在线好友：%s" % j_data["result"])
            return j_data["result"]
        except:
            return None

    def get_recent_list2(self):
        '''
        # 获取最近列表
        '''
        url = "http://d1.web2.qq.com/channel/get_recent_list2"
        # self.headers["Host"] = "d1.web2.qq.com"
        # self.headers["Origin"] = "http://d1.web2.qq.com"
        # self.headers["Referer"] = "http://d1.web2.qq.com/proxy.html?v=20151105001&callback=1&id=2"
        # self.ssession.headers.update(self.headers)
        p_data = {"vfwebqq":str(self.vfwebqq),"clientid":53999199,"psessionid": str(self.psessionid)}
        r_data = {"r": json.dumps(p_data)}
        try:
            j_data = json.loads(self.ssession.post(url=url, data=r_data).content.decode("utf-8"))
            if "errmsg" in j_data.keys():
                print(j_data)
                return None
            print("QQ最近列表：%s" % j_data["result"])
            return j_data["result"]
        except:
            return None

    def send_qun_msg(self,group_uin,msg):
        '''
        # 发送QQ群信息
        '''
        url = "https://d1.web2.qq.com/channel/send_qun_msg2"
        p_data = {"group_uin":group_uin,
                "content":'[\"' + str(msg) + '\",[\"font\",{\"name\":\"宋体\",\"size\":10,\"style\":[0,0,0],\"color\":\"000000\"}]]',
                "face":self.face,
                "clientid":53999199,
                "msg_id":1530000 + random.randint(1000,10000),
                "psessionid":str(self.psessionid)}
        r_data = {"r": json.dumps(p_data)}
        j_data = json.loads(self.ssession.post(url=url, data=r_data).content.decode("utf-8"))
        if "errCode" in j_data.keys() and j_data["msg"] == "send ok":
            print("群消息发成功.")
            return True
        else:
            print("群消息发失败.")
            return False

    def send_buddy_msg(self,uin,msg):
        '''
        # 发送QQ好友消息
        '''
        url = "https://d1.web2.qq.com/channel/send_buddy_msg2"
        p_data = {"to": uin,
                  "content": "[\""+ str(msg) +"\",[\"font\",{\"name\":\"宋体\",\"size\":10,\"style\":[0,0,0],\"color\":\"000000\"}]]",
                  "face": self.face,
                  "clientid": 53999199,
                  "msg_id": 1530000 + random.randint(1000,10000),
                  "psessionid": str(self.psessionid)}
        r_data = {"r": json.dumps(p_data)}
        j_data = json.loads(self.ssession.post(url=url, data=r_data).content.decode("utf-8"))
        if "errCode" in j_data.keys() and j_data["msg"] == "send ok":
            print("好友消息发成功.")
            return True
        else:
            print("好友消息发失败.")
            return False

    def get_self_img(self):
        '''
        # 获取自己的头像
        '''
        # self.headers["Accept"] = "image/webp,image/*,*/*;q=0.8"
        # self.headers["Host"] = "q.qlogo.cn"
        # self.headers["Referer"] = "http://w.qq.com/"
        self.ssession.headers.update(self.headers)
        url = 'http://q.qlogo.cn/g?b=qq&nk='+ str(self.uin) +'&s=100&t=149673935' + str(random.randint(1000, 10000))
        try:
            content = self.ssession.get(url=url).content
            return content
        except:
            return None

    def get_group_info(self,gcode):
        '''
        # 获取群资料
        '''
        # self.headers["Host"] = "s.web2.qq.com"
        # self.headers["Referer"] = "http://s.web2.qq.com/proxy.html?v=20130916001&callback =1&id=1"
        self.ssession.headers.update(self.headers)
        url = 'http://s.web2.qq.com/api/get_group_info_ext2?gcode=' + str(gcode) + '&vfwebqq='+ str(self.vfwebqq) +'&t=149734532' + str(random.randint(1000, 10000))
        try:
            j_data = json.loads(self.ssession.get(url=url).content.decode("utf-8"))
            if "result" in j_data.keys():
                print("群成员信息：%s" % j_data['result']['minfo'])
                return {"ginfo":{"name":j_data['result']['ginfo']['name'],"gid":j_data['result']['ginfo']['gid']},"minfo":j_data['result']['minfo']}
            else:
                print("未获取到群资料. %s" % j_data)
                return None
        except:
            print("获取群资料异常.")
            return None