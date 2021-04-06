import socks
import socket
import urllib.request
from urllib.request import urlopen, Request
import re
from lxml import html
import time
import csv
from selenium import webdriver
from PIL import Image
from pytesseract import image_to_string
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import sys
import normalize_date
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
import os
import contextlib
from selenium.webdriver.common.proxy import *
import urllib3
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By




"""
URLLIB PROXY

proxy_support = urllib.request.ProxyHandler({'http' : '127.0.0.1:8118'})
opener = urllib.request.build_opener(proxy_support)
urllib.request.install_opener(opener)
"""

"""
TOR CONNECTION

def send(s, string):
    print('>', string)
    s.send(bytes(string.encode('utf8')))
    s.send(b'\n')
    data = recv(s)
    if not data.startswith('250 '):
        raise Exception()
    print(data)
 
def recv(s):
    return s.recv(1024).decode('utf8')

def create_connection(address, timeout=None, source_address=None):
    sock = socks.socksocket()
    sock.connect(address)
    return sock

@contextlib.contextmanager
def connectTor():
    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9050, True)
    old_socket = socket.socket
    old_connection = socket.create_connection
    socket.socket = socks.socksocket
    socket.create_connection = create_connection
    yield
    socket.socket = old_socket 
    socket.create_connection = old_connection

def newIdentity():      
    raw_password = 'over'  
    with socket.socket() as s:
        s.connect(('127.0.0.1', 9051))
        send(s, 'authenticate "%s"' % raw_password)
        send(s, 'setevents signal')
        send(s, 'signal newnym')
"""
"""
EXCEPTIONS
"""
class IPBlockedError(Exception):
    def __init__(self, text):
        self.txt = text


"""
PARSER
"""
class AvitoParser(object):

    def __init__(self, proxy):
        self.page = ""
        self.proxy = proxy
        print('Proxy: ' + proxy)
        if proxy != 'no':
            proxy_support = urllib.request.ProxyHandler({'http' : proxy, 'https': proxy})
            opener = urllib.request.build_opener(proxy_support)
            urllib.request.install_opener(opener)
        fp = webdriver.FirefoxProfile(r'C:\Users\User\AppData\Roaming\Mozilla\Firefox\Profiles\6ypz1xjt.default-release')
        binary = FirefoxBinary(r'C:\Program Files\Mozilla Firefox\firefox.exe')
        self.driver = webdriver.Firefox(firefox_binary=binary, firefox_profile=fp)
        self.driver.delete_all_cookies()
        self.data = []
        self.data.append(['ID', 'Имя аккаунта', 'Название объявления', 'Дата', 'Адрес', 'Телефон', 'Очищенный телефон', 'URL'])

    def takeScreenshot(self):
        self.driver.save_screenshot('avito_screenshot.png')

    def telRecon(self):
        image = Image.open('tel.gif')
        tel_string = image_to_string(image)
        return tel_string

    def crop(self, location, size):
        image = Image.open('avito_screenshot.png')
        x = location['x']
        y = location['y']
        width = size['width']
        height = size['height']
        image.crop((x, y, x+width, y+height)).save('tel.gif')

    def readPage(self, url):
        #with connectTor():
        self.driver.get(url)
        print("URL: " + str(url))
        fp = urllib.request.urlopen(url)
        mybytes = fp.read()
        html = mybytes.decode('utf8')
        self.page = html
        fp.close()
        """
        #headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        http = urllib3.ProxyManager("http://" + self.proxy)#127.0.0.1:8118")
        req = http.request('GET', url, headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36"})
        #req = Request(url=url, headers=headers) 
        html = req.read() 
        html = html.decode('utf8')
        self.page = html
        """

    def printPage(self):
        print(self.page)

    def getPages(self, url):
        self.readPage(url)
        tree = html.fromstring(self.page)
        pages = tree.xpath('//a[@class="pagination-page"]/@href')
        last_page_num = ''
        try:
            last_page_num = int(pages[-1].split('?')[1].split('&')[0].split('=')[1])
        except IndexError:
            print('[ERR] IP temprorary blocked. Try again later.')
            sys.exit()
        print("[INF] Pages for scrapping items URLs: " + str(last_page_num))
        pages = []
        if '?q=' in url:
            for i in range(1, last_page_num+1):
                pages.append(url + '&p=' + str(i))
        else:
            for i in range(1, last_page_num+1):
                pages.append(url + '?p=' + str(i))
        items_pages = []
        try:
            for page in pages:
                items = []
                try:
                    self.readPage(page)
                    tree = html.fromstring(self.page)
                    items = tree.xpath('//a[@class="snippet-link"]/@href')
                except Exception as e:
                    print('[ERR] Scrapping failed: ' + str(e))
                    continue   
                for item in items:
                    print('[INF] Item found: ' + item)
                    items_pages.append('https://www.avito.ru' + item)
                time.sleep(2)
        except KeyboardInterrupt:
            print('[INF] Keyboard interrupted. Saving data.')
            return items_pages
        return items_pages

    def parseHtml(self, category):
        line = []
        firewall = None
        tree = html.fromstring(self.page)
        try:
            firewall = tree.xpath('//h2[@class="firewall-title"]/text()')[0]
            if str(firewall) == 'Доступ с Вашего IP временно ограничен': 
                raise IPBlockedError('IP Blocked. Closing app.')
        except IPBlockedError:
            raise IPBlockedError('IP Blocked 1. Closing app.')
        except Exception as e:
            #print('[INF] IP OK ' + str(e))
            print('')
        try:
            firewall = tree.xpath('//h1/text()')
            #print('fw: ' + str(firewall))
            if str(firewall) == 'Доступ с&nbsp;вашего IP-адреса временно ограничен':  #Доступ с&nbsp;вашего IP-адреса временно ограничен
                raise IPBlockedError('IP Blocked 2. Closing app.')
        except IPBlockedError:
            raise IPBlockedError('IP Blocked. Closing app.')
        except Exception as e:
            print('[INF] IP OK ' + str(e))
        #ITEM ID
        item_id = '-'
        try:
            item_id = tree.xpath('//span[@data-marker="item-view/item-id"]/text()')[0]
            if '№' in item_id:
                item_id = item_id.replace('№', '')
            item_id = item_id.strip()
        except Exception as e:
            item_id = '-'
        line.append(item_id)
        #ACC NAME
        name = '-'
        try:
            name = tree.xpath('//div[@class="seller-info-value"]/div/a/text()')[0].split('\n')[1].strip()
        except Exception:
            name = '-'
        line.append(name)
        #AD NAME
        ad = '-'
        try:
            ad = tree.xpath('//span[@class="title-info-title-text"]/text()')[0].strip()
        except Exception:
            ad = '-'
        line.append(ad)
        #DATE
        date = '-'
        try:
            date = tree.xpath('//div[@class="title-info-metadata-item-redesign"]/text()')[0].split('\n')[1].strip().replace('\xa0', ' ')
            date = normalize_date.normalize_date(date)
        except Exception as e:
            date = '-'
        line.append(date)
        #REGION
        region = '-'
        try:
            region = tree.xpath('//span[@class="item-address__string"]/text()')[0].split('\n')[1].strip()
        except Exception:
            region = '-'
        line.append(region)
        #TELEPHONE
        tel = '-'
        try:
            if category == 1:
                button = self.driver.find_element_by_xpath('//a[@class="button item-phone-button js-item-phone-button button-origin button-origin-blue button-origin_full-width button-origin_large-extra item-phone-button_hide-phone item-phone-button_card js-item-phone-button_card"]')
            elif category == 2:
                #button = self.driver.find_element_by_xpath('//div[@class="js-item-phone-react"]')
                button = WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.XPATH, '//div[@class="js-item-phone-react"]')))
            button.click()
            time.sleep(5)
            self.takeScreenshot()
            if category == 1:
                image = self.driver.find_element_by_xpath('//div[@class="item-phone-big-number js-item-phone-big-number"]/img')
            elif category == 2:
                image = self.driver.find_element_by_xpath('//img[@class="contacts-phone-3KtSI"]')
            location = image.location
            size = image.size
            self.crop(location, size)
            tel = self.telRecon()
            tel.strip()
            counter_tel = 0
            while tel[0] != '8' and counter_tel < 5:
                print('[WRN] Screenshot failed. Waiting 5 seconds and trying again.')
                button.click()
                time.sleep(5)
                self.takeScreenshot()
                if category == 1:
                    image = self.driver.find_element_by_xpath('//div[@class="item-phone-big-number js-item-phone-big-number"]/img')
                elif category == 2:
                    image = self.driver.find_element_by_xpath('//img[@class="contacts-phone-3KtSI"]')
                location = image.location
                size = image.size
                self.crop(location, size)
                tel = self.telRecon()
                tel.strip()
                counter_tel = counter_tel + 1
            if 'O' in tel:
                tel = tel.replace('O', '0')
            #CLEAN TEL
            clean_tel = tel
            if '-' in clean_tel:
                clean_tel = clean_tel.replace('-', '')
            if ' ' in clean_tel:
                clean_tel = clean_tel.replace(' ', '')
            if len(clean_tel) > 10:
                clean_tel = clean_tel[1:]
            if counter_tel >= 5:
                print('Tel recog error: 5 attempts failed')
                tel = '-'
                clean_tel = '-'
        except Exception as e:
            print('Tel recog error: ' + str(e))
            tel = '-'
            clean_tel = '-'
        line.append(tel)
        line.append(clean_tel)
        #URL
        line.append
        print(line)
        if len(line)+1 == len(self.data[0]):
            #self.data.append(line)
            return line
        else:
            print('Parse error. Scrapped data != needed data.')

    def printTable(self):
        for line in self.data:
            print(line)

    def outputInCsv(self, outdir, save_descriptor):
        filename = outdir + '/avito_' + save_descriptor + '.csv'
        with open(filename, "w", newline="", encoding='utf8') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerows(self.data)

    def updateCsv(self, outdir, save_descriptor):
        filename = outdir + '/avito_' + save_descriptor + '.csv'
        self.data.remove(['ID', 'Имя аккаунта', 'Название объявления', 'Дата', 'Адрес', 'Телефон', 'Очищенный телефон', 'URL'])
        with open(filename, "a", newline="", encoding='utf8') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerows(self.data)

    def loadDataFromCsv(self, csv_file):
        with open(csv_file, newline='', encoding='utf8') as csvfile:
            read_data = csv.reader(csvfile, delimiter=';')
            self.data.remove(['ID', 'Имя аккаунта', 'Название объявления', 'Дата', 'Адрес', 'Телефон', 'Очищенный телефон', 'URL'])
            for row in read_data:
                self.data.append(row)

    def cleanTableFromTrash(self):
        for dt in self.data:
            if len(dt) < 7:
                self.data.remove(dt)
                continue
            if len(dt[5]) > 15 or dt[5] == '-':
                self.data.remove(dt)



def compareItemsForUpdate(old_items, new_items):
    output = []
    booler = True
    for new_item in new_items:
        for old_item in old_items:
            if booler == False:
                continue
            if new_item == old_item:
                booler = False
        if booler == True:
            print('[INF] Found new item: ' + new_item)
            output.append(new_item)
        else:
            booler = True
    return output




