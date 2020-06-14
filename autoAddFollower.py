#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2020/6/11 6:05 下午
# @Author  : Johny Zheng
# @Site    : 
# @File    : autoAddFollower.py
# @Software: PyCharm
# Running based on python3.6.2 environment

from github import Github
import requests
import logging
import re
import base64
import config
import multiprocessing as mp
import os
from time import sleep


class Mp:
    def __init__(self):
        self.results = []
        self.pool = ""
        self.result = ""

    @staticmethod
    def info():
        # logging.info('current name:', title)
        logging.info('parent process:', os.getppid())
        logging.info('process id:', os.getpid())

    def task_pool(self, task, args):
        self.results = []
        self.pool = mp.Pool()
        self.result = self.pool.apply_async(task, args=(args,))
        self.results.append(self.result)
        self.pool.close()
        self.pool.join()
        for self.result in self.results:
            logging.info(self.result.get())


class OperateFiles:
    def __init__(self, file_name, write_str):
        self.str = write_str
        self.file_name = file_name

    def write(self):
        # 打开文件
        logging.info(f"file name: {self.file_name}")

        with open(self.file_name, 'a+') as f:
            # Move read cursor to the start of file.
            f.seek(0)
            # If file is not empty then append '\n'
            data = f.read()
            if len(data) > 0:
                f.write("\n")
            f.write(self.str)


class InitLogin(config.Base):
    def __init__(self):
        super().__init__()
        self.g = Github(self.apiUrl, self.user, self.password)


class InitCrawler(config.Base):
    def __init__(self, someone, page):
        super().__init__()
        self.baseUrls = self.baseUrl + someone
        self.followingQueryString = {"page": page, "tab": "following", "_pjax": "#js-pjax-container"}
        self.followerQueryString = {"page": page, "tab": "followers", "_pjax": "#js-pjax-container"}

        self.cookies = GithubLogin().get_cookies()
        self.header = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'
        }


class GithubLogin(config.Base):

    def __init__(self):
        super().__init__()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
            'Referer': 'https://github.com/',
            'Host': 'github.com'
        }

        self.session = requests.Session()
        self.login_url = 'https://github.com/login'
        self.post_url = 'https://github.com/session'

    def login_github(self):
        # 登录入口
        post_data = {
            'commit': 'Sign in',
            'utf8': '✓',
            'authenticity_token': self.get_token(),
            'login': self.email,
            'password': self.password
        }
        resp = self.session.post(
            self.post_url, data=post_data, headers=self.headers)

        logging.debug('StatusCode:', resp.status_code)
        if resp.status_code != 200:
            logging.error('Login Fail')
        match = re.search(r'"user-login" content="(.*?)"', resp.text)
        user_name = match.group(1)
        logging.debug('UserName:', user_name)

    # Get login token
    def get_token(self):

        response = self.session.get(self.login_url, headers=self.headers)

        if response.status_code != 200:
            logging.error('Get token fail')
            return None
        match = re.search(
            r'name="authenticity_token" value="(.*?)"', response.text)
        if not match:
            logging.error('Get Token Fail')
            return None
        return match.group(1)

    # Get login cookies
    def get_cookies(self):
        response = self.session.get(self.login_url, headers=self.headers, timeout=120, allow_redirects=False)

        # keep cookie update
        if response.cookies.get_dict():
            self.session.cookies.update(response.cookies)
            logging.debug('自动更新cookie成功: %s' % response.cookies)

        # 根据location 获取的token去拿response cookie 并将CookieJar转为字典
        try:
            cookies = requests.utils.dict_from_cookiejar(response.cookies)
            logging.debug('获取cookie成功: %s' % cookies)
            return cookies
        except Exception as e:
            logging.error(f'获取cookie失败{e}')

        finally:
            response.cookies.clear()


class GetSomeoneInfo(InitCrawler):
    def __init__(self, someone, page):
        super().__init__(someone, page)

    def get_followings(self):
        following_raw = requests.get(self.baseUrls, cookies=self.cookies, headers=self.header, timeout=120,
                                     params=self.followingQueryString).content.decode('utf-8')
        pattern = re.compile('pl-1">(.*)<')
        following = pattern.findall(following_raw)
        # print(following)
        return following

    def get_followers(self):
        follower_raw = requests.get(self.baseUrls, cookies=self.cookies, headers=self.header, timeout=120,
                                    params=self.followerQueryString).content.decode('utf-8')
        pattern = re.compile('pl-1">(.*)<')
        follower = pattern.findall(follower_raw)
        # print(follower)
        return follower


class AutoAddFollowing(InitLogin):
    def __init__(self):
        super().__init__()
        self.credentials = base64.b64encode(f"{self.email}:{self.password}".encode()).decode()
        self.nicknames = []
        self.nickname = ""
        self.header = {
            'Authorization': "Basic {}".format(self.credentials),
        }

    def get_followers(self):
        for follower in self.g.get_user().get_followers():
            self.nickname = follower.login
            self.nicknames.append(self.nickname)
        return self.nicknames

    def get_following(self):
        for following in self.g.get_user().get_following():
            self.nickname = following.login
            self.nicknames.append(self.nickname)
        return self.nicknames

    def get_following_total_count(self):
        return self.g.get_user().get_following().totalCount

    def add_following(self, follow_user):
        # payload = {'username': follow_user}
        r = requests.put(self.apiUrl + f"/user/following/{follow_user}", headers=self.header)
        logging.debug(r.status_code)
        logging.debug(r.content)
        return r.status_code


if __name__ == '__main__':

    login = GithubLogin()
    login.login_github()
    logging.info("login github ok")
    c = login.get_cookies()
    t = login.get_token()

    # print(cr)
    # print(login.get_token())
    # print(login.get_cookies())

    # print(config.Base().password)
    # total_count = AutoAddFollowing().get_following_total_count()
    # logging.info(f"current total count: {total_count}")

    exist_list = []
    retry_count = int(config.Base().retryCount)
    retry_detail_file = config.Base().retryDetailFile

    while not exist_list:
        if bool(config.Base().exceeded):
            exist_list = GetSomeoneInfo(config.Base().user, 1).get_followings()
        else:
            exist_list = AutoAddFollowing().get_following()
    logging.debug(f"exist_list: {exist_list}")

    for p in range(2, 10000000):
        # loop & reset
        user_list = []
        count = 0

        logging.info(f"page: {p}")

        while not user_list and count < retry_count:
            user_list = GetSomeoneInfo(config.Base().sourceUser, p).get_followings()
            count = count + 1
            if count == retry_count:
                OperateFiles(retry_detail_file, str(p)).write()
                continue
            logging.info(f"get page: {p} user_list retry counts: {count}")
        # print(bool(user_list))
        # sleep(3)
        logging.debug(f"user_list: {user_list}")

        need_followings = list(set(user_list)-set(exist_list))
        logging.info(f"need_followings: {need_followings}")
        if need_followings:
            for u in need_followings:
                AutoAddFollowing().add_following(u)
                logging.info(f"AutoAddFollowing: {u}")

    # todo： multiThreath

