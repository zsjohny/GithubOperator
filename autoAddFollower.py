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
from concurrent.futures import ThreadPoolExecutor, wait, as_completed
from multiprocessing import cpu_count
import threading


class OperateFiles:
    def __init__(self, file_name, write_str):
        self.str = write_str
        self.file_name = file_name

    def write(self):
        # 打开文件
        logging.info(f"write file name: {self.file_name}")

        with open(self.file_name, 'a+') as f:
            # Move read cursor to the start of file.
            f.seek(0)
            # If file is not empty then append '\n'
            data = f.read()
            if len(data) > 0:
                f.write("\n")
            f.write(self.str)

    def delete(self):
        # 打开文件
        logging.info(f"delete file name: {self.file_name}")

        with open(self.file_name, "r+") as f:
            lines = f.readlines()

        with open(self.file_name, "w+") as f:
            for line in lines:
                if line.strip("\n") != self.str:
                    f.write(line)

    def read(self):
        # 打开文件
        logging.info(f"read file name: {self.file_name}")

        with open(self.file_name, 'r+') as f:
            lines = f.readlines()
            print(lines)
            numbers = [int(e.strip()) for e in lines if len(e.strip()) != 0]
            print(numbers)
            logging.debug(f"read file list {numbers}")
            return numbers


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
            logging.error(f'Get token fail, code: {response.status_code}, Please retry...')
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
    print("login github ok")
    c = login.get_cookies()
    t = login.get_token()

    # print(cr)
    # print(login.get_token())
    # print(login.get_cookies())

    # print(config.Base().password)
    # total_count = AutoAddFollowing().get_following_total_count()
    # logging.info(f"current total count: {total_count}")

    def task(p: int):
        """
        :param p:
        :return:
        """
        # loop & reset
        exist_list = []
        user_list = []
        count = 0

        retry_count = int(config.Base().retryCount)
        retry_detail_file = config.Base().retryDetailFile

        logging.info(f"current page: {p}")

        while not exist_list:
            if bool(config.Base().exceeded):
                exist_list = GetSomeoneInfo(config.Base().user, 1).get_followings()
            else:
                exist_list = AutoAddFollowing().get_following()
        logging.debug(f"exist_list: {exist_list}")

        while not user_list and count <= retry_count:
            user_list = GetSomeoneInfo(config.Base().sourceUser, p).get_followings()
            count = count + 1
            if count == retry_count:
                OperateFiles(retry_detail_file, str(p)).write()
                continue
            logging.info(f"get page: {p} user_list retry counts: {count-1}")
        # print(bool(user_list))
        # sleep(3)
        logging.debug(f"user_list: {user_list}")

        need_followings = list(set(user_list)-set(exist_list))
        logging.debug(f"need_followings: {need_followings}")
        if need_followings:
            for u in need_followings:
                put_result = AutoAddFollowing().add_following(u)
                while put_result != 200 and count <= retry_count:
                    AutoAddFollowing().add_following(u)
                    count = count + 1
                    if count == retry_count:
                        OperateFiles("put_"+retry_detail_file, str(p)).write()
                        continue
                    logging.info(f"Add following: {p} retry counts: {count-1}")
                logging.info(f"AutoAddFollowing: {u}")
        OperateFiles("put_" + retry_detail_file, str(p)).delete()

    total_page = int(config.Base().totalPage)
    retry_detail_file = config.Base().retryDetailFile
    step = 5
    try:
        workers = cpu_count()*2
    except NotImplementedError:
        workers = 1

    fail_range_page = list(set(OperateFiles("put_"+retry_detail_file, "none").read() +
                               OperateFiles(retry_detail_file, "none").read()))
    if not fail_range_page:
        range_page = range(3, total_page//step)
        print("Init range pages")
    else:
        range_page = fail_range_page
        print("Retry put fail pages")

    for page in range_page:
        pool = ThreadPoolExecutor(workers)
        futures = []
        thread_id = page//step
        # Submit multi parameters function to Executor
        # https://github.com/Joldnine/joldnine.github.io/issues/10
        if fail_range_page:
            for fail_page in fail_range_page:
                futures.append(pool.submit(task, fail_page))
                logging.info(f"Retry put fail page {fail_page}")
                logging.info("Added: Thread-{}".format(threading.currentThread().ident))
                print(f"Following Fail Page: {fail_page} Followings")
        else:
            while page < total_page:
                futures.append(pool.submit(task, page))
                logging.info("Added: Thread-{}".format(threading.currentThread().ident))
                print(f"Following Page: {page} Followings")
                page = page + step

        if not fail_range_page:
            group = 1
            print(f"Current Group: {group}, Total Group: {step}")
            group = group + 1
        print(f"Just a moment, please wait...")

        for x in as_completed(futures):
            logging.info("{} completed".format(x.result()))

        print(f"Follow Page: {page} Done")


