# IP地址取自国内髙匿代理IP网站：http://www.xicidaili.com/nn/
# 仅仅爬取首页IP地址就足够一般使用

from bs4 import BeautifulSoup

from config import Config
import urllib
import requests
import random


class Proxy:
    def __init__(self):
        pass

    #从代理ip网站获取代理ip列表函数，并检测可用性，返回ip列表
    def get_ip_list(self,url,headers):
        web_data = requests.get(url, headers = headers)
        soup = BeautifulSoup(web_data.text, 'lxml')
        ips = soup.find_all('tr')
        ip_list = []
        for i in range(1, len(ips)):
            ip_info = ips[i]
            tds = ip_info.find_all('td')
            ip,port,type = tds[1].text,tds[2].text,tds[5].text
            #print(ip,port,type)

            ip_list.append({'ip':ip,'port':port,'type':type})
        print(ip_list)
        return ip_list

    def check_ip_list(self,url,headers):
        # 检测ip可用性，移除不可用ip：
        ip_list = self.get_ip_list(url,headers)
        for ip in ip_list:
            try:
                proxy_host = ip_list['type'] + '//' + ip_list['ip']
                proxy_temp = {"http": proxy_host}
                # print(proxy_temp)
                res = urllib.request.urlopen(url, proxies=proxy_temp).read()
            except Exception as e:
                ip_list.remove(ip)
                continue
        return ip_list

    #从ip池中随机获取ip列表
    def get_random_ip(self,url,headers):
        ip_list = self.check_ip_list(url,headers)
        proxy_list = []
        for ip in ip_list:
            proxy_list.append(ip['type']+'://'+ip['ip']+':'+ip['port'])
        proxies = {'http:':random.choice(proxy_list)}
        return proxies