#!/usr/bin/python
# -*- coding: UTF-8 -*-

import json
import sys
import threading

import requests
import time
import re
import os
from bs4 import BeautifulSoup

proxyFile = "./list.txt" #/etc/proxychains.conf
url = "https://www.kuaidaili.com/free/"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; W0W64; rv:57.0) Gecko/20100101 Firefox/57.0'}
seg_name = "[ProxyList]"


class ProxyInfo:
    def __init__(self,proto,ip,port):
        self.proto = proto
        self.ip = ip
        self.port = port

    def __eq__(self, rhs):
        if self.proto == rhs.proto and self.ip == rhs.ip and self.port == rhs.port:
            return True
        else:
            return False

    def to_string(self):
        return "protocol:% ip:% port:%".format(self.proto, self.ip, self.port)


def grab_proxy(check):
    r = requests.get(url, headers=headers)
    content = r.content
    soup = BeautifulSoup(content, 'lxml')
    protos = soup.find_all('td', attrs={'data-title': u'类型'})
    ips = soup.find_all('td', attrs={'data-title': 'IP'})
    ports = soup.find_all('td', attrs={'data-title': 'PORT'})
    proxy_infos = []
    for i in range(0, len(protos)):
        proxy_infos.append(ProxyInfo(protos[i].string.lower(), ips[i].string, ports[i].string))
    print("start  writing proxy ip and port")
    add_conf(proxy_infos)
    if check:
        check_proxies(get_proxies_in_file())
    print("write finished,leaving...")


def get_proxies_in_file():
    with open(proxyFile, 'r') as f:
        content = f.read(sys.maxint)
        start_pos = content.index(seg_name)+len(seg_name)
        proxy_lines = content[start_pos:].split('\n')
        result = []
        for l in proxy_lines:
            if len(l) == 0 or l[0] == '#':
                continue
            match_result = re.match(r'(http(s?))\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+)\s*?', l)
            result.append(ProxyInfo( \
                match_result.group(1), \
                match_result.group(3), \
                match_result.group(4)))
    return result

#http 192.168.31.1 233

def add_conf(proxy_infos):
    finfos = get_proxies_in_file()
    infos = [p for p in proxy_infos if p not in finfos]
    with open(proxyFile, 'a+') as f:
        f.write('\n')
        for i in infos:
            print("---> Protocol:" + i.proto + " IP: " + i.ip + " PORT: " + i.port + " <---",)
            f.write('%s %s %s\n' % (i.proto,i.ip, i.port))


def check_proxies(proxy_list):
    proxy_count = len(proxy_list)
    finish_count = 0
    good_list = []

    def check_one(proxy_info):
        p = os.subprocess.Popen([r"./ping", proxy_info], stdout=os.subprocess.PIPE)
        result = p.stdout.read()
        if result != '1\n':
            ++finish_count

    for px in proxy_list:
        t = threading.Thread(target=check_one, args=(px,))
    while finish_count >= proxy_count:
        time.sleep(1)
    return good_list


grab_proxy(True)