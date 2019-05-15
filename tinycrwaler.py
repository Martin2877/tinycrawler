#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author = ali0th
import re
import requests
from bs4 import BeautifulSoup
from time import sleep
from urllib.parse import urljoin,urlparse

'''
tinycrawler

Usage:

url = "https://www.baidu.com" # don't forget to add http
webcrawler = Webcrawler(url)
webcrawler.crawl(None,True)
print(webcrawler.urls)

TODO:
1. proxy pool
2. content crawler
'''

verbose = True
debug = True

class Webcrawler(object):

    def __init__(self,_website,_depth=1,_proxies=None,_cookie=None):
        self.website = _website
        self.depth = _depth
        self.proxies = {"http": _proxies}
        self.urls = []
        self.cookie = _cookie
        self.content = {}

    def req(self,_url):
        if verbose : print(f"[+] requesting : {_url}")
        _url = _url if "http://" in _url or "https://" in _url else "http://" + _url
        for i in range(3):
            try:
                g = requests.get(_url, timeout=5, proxies=self.proxies,headers=self.cookie)
                if debug : print(f"[DEBUG] {g.content}")
                return g.content
            except Exception as e : print(f"[Error] {e}")
            sleep(0.8)
        return False

    def is_parent_path(self,_url,_source):
        if debug : print(f"[DEBUG] _url : {_url}, _source :{_source}")
        if not _source : return True
        return True if urlparse(_source).path in urlparse(_url).path else False

    def rules(self,_url):
        if "?C=" in _url or "javascript" in _url:
            return False
        if not self.match: return True
        for key,value in self.match.items():
            if value : 
                if key in _url : continue
                return False
            else :
                if key in _url : return False
        return True

    def fetch_links(self,_url,_content):
        urls = []
        if self.mode == None :
            soup = BeautifulSoup(_content,"lxml")
            links =  soup.find_all(['a','link'])
            # links_file = soup.find_all(['img','script'])
            if debug : print(f"[DEBUG] links : {links}")
            for i in links : 
                try:
                    if debug : print(f"[DEBUG] i : {i}")
                    name = i['href']
                    if debug : print(f"[DEBUG] name : {name}")
                    urls.append(urljoin(_url,name))
                except Exception as e : 
                    if debug : print(f"[Error]{e}")
        elif self.mode == "regex" :
            ret = re.findall(r"\"http.*?\"",str(_content))
            urls = [x.strip("\"") for x in ret]
        return urls

    def filter_links(self,_url,_links):
        urls = []
        for link in _links:
            if self.rules(link): # check match
                if verbose : print("[+] url : {}".format(link))
                urls.append(link)
            if self.count :
                if len(urls) >= self.count : break
        return urls

    def url_html(self,_url):
        '''
        crawl urls of a single html
        :param _url: url
        :return list: new urls
        '''
        if debug : print(f"[DEBUG] start url html : {_url}")
        # if _url[-1] != '/' : return []
        if not self.is_parent_path(_url,self.website) : return []
        html = self.req(_url)
        if not html: return None
        fetch_links = self.fetch_links(_url,html) # fetch the urls from html to list
        if debug : print(f"[DEBUG] fetch links : {fetch_links}")
        filter_links = self.filter_links(_url,fetch_links) # filter linkes
        new_links = self.comp(filter_links) # compare for origin
        return new_links

    def comp(self,_urls):
        '''
        compare the _urls and self.urls,return the urls that not in self.urls
        :param _urls: urls
        :return list: new urls
        '''
        # check for same-origin
        def comp_netloc(a,b):
            if type(b) == list:
                if not b: return True
                for u in b:
                    if urlparse(a.strip()).netloc == urlparse(u.strip()).netloc : return False
            else:
                return self.origin if urlparse(a.strip()).netloc == urlparse(b.strip()).netloc else not self.origin

        # check for exist url
        source = self.urls if self.new_domain else self.website
        return [x for x in _urls if x not in self.urls and comp_netloc(x,source)]

    def flat_list(self,the_list):
        # falt list to one layer
        now = the_list[:]
        res = []
        while now:
            head = now.pop(0)
            now = head+now if isinstance(head, list) else res.append(head)
        return res

    def crawl(self,_match=None,_origin=True,_count=None,_find_new_domain=None,_mode=None):
        '''
        crawl all the url
        :param _match: match rule likes {".com":True,".org":False,"fault":False}
        :param _origin: if origin url
        :param _count: count of result you want
        :param _find_new_domain: if you only fetch new domain
        :param _mode : normal mode or regex mode
        '''
        self.match = _match
        self.origin = _origin if _origin is not None else False
        self.count = _count
        self.new_domain = _find_new_domain if _origin is not None else False
        self.mode = _mode
        urls_new = self.url_html(self.website) # crawl html
        if not urls_new : return
        self.urls.extend(urls_new)
        for dp in range(1,self.depth):
            urls_new = self.comp(set(self.flat_list(list(map(self.url_html,urls_new)))))
            if len(urls_new) == 0:break
            if verbose : print("[result]urls_new:{0},self.urls:{1}".format(urls_new,self.urls))
            self.urls.extend(urls_new)

if __name__ == '__main__':
    pass