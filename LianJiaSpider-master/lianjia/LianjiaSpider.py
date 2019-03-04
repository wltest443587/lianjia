import requests
import json,re,random,time
from lxml import etree
from bs4 import BeautifulSoup
import queue
import threading
from config import Config
from proxy import Proxy
from SqlSpider import MysqlHelper

class BaseSpider:
    '''页面爬取操作和转化操作类'''
    def __init__(self):
        self.proxy_url = 'http://www.xicidaili.com/nn/'
        # 创建配置文件对象，从而导入各项配置
        self.config = Config()
        self.headers = self.config.headers
        # 创建
        self.pro = Proxy()
        self.ip_list = self.pro.check_ip_list(self.proxy_url,self.headers)


    def get_random_ip(self):
        # 生成代理地址
        proxy_list = []
        for ip in self.ip_list:
            proxy_list.append(ip['type']+'://'+ip['ip']+':'+ip['port'])
        proxies = {'http:':random.choice(proxy_list)}
        return proxies

    def getHtmlText(self,url):
        '''爬取指定路径的页面'''
        proxies = self.get_random_ip()
        r = requests.get(url,headers=self.headers,proxies = proxies)
        time.sleep(1+random.random())
        html = r.text
        return html


    def parseSoup(self,url):
        # 将获取的页面转化成bs4对象，方面对页面进行解析
        html = self.getHtmlText(url)
        return BeautifulSoup(html, 'lxml')


class ProduceSpider(threading.Thread):
    '''生产者模型，专门爬取网页的url,将其添加到队列中'''
    def __init__(self,q):
        threading.Thread.__init__(self)
        self.bs = BaseSpider()
        self.q = q


    def analyBaseHtml(self,url):
        '''获取每一页中具体页面的链接url'''
        html = self.bs.getHtmlText(url)
        patter = re.compile(r'https://bj.lianjia.com/ershoufang/\d+.html')
        href_list = patter.findall(html)
        return href_list

    def run(self):
        i = 1
        while i<=100:
            url = self.bs.config.base_url + 'pg' + str(i)
            hrefs = self.analyBaseHtml(url)
            for href in hrefs:
                self.q.put(href)
            i += 1


class CustomSpider(threading.Thread):
    '''消费者模型，从队列中读取url专门爬取解析网页'''
    def __init__(self,threadname,q):
        threading.Thread.__init__(self)
        self.name = threadname
        self.q = q
        self.bs = BaseSpider()
        self.obj_sql = MysqlHelper()


    def analyPersonHtml(self, url):
        '''解析具体页面中的数据'''
        soup = self.bs.parseSoup(url)
        name = soup.find('h1',class_ = 'main').text.strip()  # 房屋名称
        price = soup.find('span',class_ = 'total').text.strip() + '万' # 总价
        no_room = soup.find('span',class_ = 'unitPriceValue').text.strip()   # 均价
        area = soup.find('div',class_ = 'area').contents[0].text.strip()   # 面积
        room = soup.find('div',class_ = 'room').contents[0].text.strip()   # 几室几厅
        houseData = {'name':name,
                     'price':price,
                     'no_room':no_room,
                     'area':area,
                     'room':room}
        return houseData
        # {'area': '62.61平米', 'no_room': '57340元/平米', 'name': '大丰台 文体路 得一居 莫着急 来这里', 'price': '359万', 'room': '1室1厅'}

    def run(self):
        while True:
            url = self.q.get()
            print(self.name,url,'\t')
            houseData = self.analyPersonHtml(url)
            time.sleep(1)
            sql = 'insert into lianjia(area,price,name,room,no_room) values(%s,%s,%s,%s,%s)'
            params = (houseData['area'],houseData['price'],houseData['name'],houseData['room'],houseData['no_room'],)
            print(houseData)
            self.obj_sql.insert(sql,params)
            time.sleep(random.randint(1, 3) + random.random())




if __name__ == '__main__':
    # 创建工作队列
    work_queue = queue.Queue()
    # 对象列表
    obj_list = []

    # 创建生产者线程实例，用于爬取url
    product = ProduceSpider(work_queue)
    # 线程开始
    product.start()

    for i in range(4):
        custom = CustomSpider('thread'+str(i),work_queue)
        obj_list.append(custom)

    for obj in obj_list:
        obj.start()

    for obj in obj_list:
        obj.join()

    #spder = Spider()
    #spder.runSpider()





