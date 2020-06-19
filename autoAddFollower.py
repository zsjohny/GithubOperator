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
import random
import string
from utils import str_to_bool, delta_time
from time import sleep
import json

from initGithub import InitCrawler, InitLogin, GithubLogin


class OperateFiles:
    def __init__(self, file_name, write_str):
        self.str = write_str
        self.file_name = file_name

    def write(self):
        # 打开文件
        logging.info(f"Ready to write file name: {self.file_name}")

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
        logging.info(f"Ready to delete file name: {self.file_name}")

        with open(self.file_name, "r+") as f:
            lines = f.readlines()

        with open(self.file_name, "w+") as f:
            if lines:
                for line in lines:
                    if line.strip("\n") != self.str or line.strip("\n") == "":
                        f.write(line)
                        logging.debug(f"delete file name: {self.file_name}, page{self.str}")

    def read(self):
        # 打开文件
        logging.info(f"Ready to read file name: {self.file_name}")

        with open(self.file_name, 'r+') as f:
            lines = f.readlines()
            numbers = [int(e.strip()) for e in lines if len(e.strip()) != 0]
            logging.debug(f"read file list {numbers}")
            return numbers


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

    def add_following(self, follow_user):
        # payload = {'username': follow_user}
        self.header = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'

        }
        self.followingQueryString = {"target": follow_user}
        payload = {'commit': 'Follow',
                   'authenticity_token': self.token}
        r = requests.post(self.baseUrl + f"users/follow/", data=payload, headers=self.header, cookies=self.cookies,
                          params=self.followingQueryString)
        logging.info(r.status_code)
        logging.info(r.request.body)
        # logging.info(r.content)
        return r.status_code


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

    def get_rate_limit(self):
        r = requests.get(self.apiUrl + f"/rate_limit", headers=self.header)
        logging.debug(r.status_code)
        logging.debug(r.content)
        rate_limit = int(json.loads(r.content.decode('utf-8'))['rate']['limit'])
        return rate_limit

    def get_rate_remaining(self):
        r = requests.get(self.apiUrl + f"/rate_limit", headers=self.header)
        logging.debug(r.status_code)
        logging.debug(r.content)
        remaining = int(json.loads(r.content.decode('utf-8'))['rate']['remaining'])
        return remaining

    def get_rate_reset(self):
        r = requests.get(self.apiUrl + f"/rate_limit", headers=self.header)
        logging.debug(r.status_code)
        logging.debug(r.content)
        rate_reset = int(json.loads(r.content.decode('utf-8'))['rate']['reset'])
        return rate_reset

    @staticmethod
    def random_user():
        random_str = ''.join(random.sample(string.ascii_letters + string.digits + '-' + '_', random.randint(4, 20)))
        random_list = []
        for i in range(1, 1000000):
            random_list.append(random_str)
        return random_list

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
    random_user = str_to_bool(config.Base().randomUser)
    retry_count = int(config.Base().retryCount)
    retry_detail_file = config.Base().retryDetailFile
    fail_range_page = list(set(OperateFiles("put_" + retry_detail_file, "none").read() +
                               OperateFiles(retry_detail_file, "none").read()))
    start_page = int(config.Base().startPage)
    group = int(config.Base().group)

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

        logging.info(f"current page: {p}")

        while not exist_list:
            if str_to_bool(config.Base().exceeded):
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

        need_followings = list(set(user_list) - set(exist_list))
        if random_user:
            need_followings = AutoAddFollowing.random_user()
        logging.debug(f"need_followings: {need_followings}")
        if need_followings:
            for u in need_followings:
                put_result = AutoAddFollowing().add_following(u)
                # put_result = GetSomeoneInfo(config.Base().sourceUser, p).add_following(u, t)
                while put_result != 204 and count <= retry_count:
                    if put_result == 404:
                        pass
                    AutoAddFollowing().add_following(u)
                    # GetSomeoneInfo(config.Base().sourceUser, p).add_following(u, t)
                    if count <= retry_count:
                        count = count + 1
                        if count == retry_count:
                            OperateFiles("put_"+retry_detail_file, str(p)).write()
                            continue
                        logging.info(f"Add following: {p}: {u} retry counts: {count-1}, code: {put_result}")
                        put_result = AutoAddFollowing().add_following(u)
                        if put_result == 429:
                            sleep(60)
                            logging.info(f"code: {put_result}, sleep: {60}")
                logging.info(f"AutoAddFollowing: {u}")

        if fail_range_page:
            OperateFiles("put_" + retry_detail_file, str(p)).delete()
            OperateFiles(retry_detail_file, str(p)).delete()


    total_page = int(config.Base().totalPage)
    retry_detail_file = config.Base().retryDetailFile
    step = group

    for start_page in range(start_page, group):
        try:
            workers = cpu_count()*2
        except NotImplementedError:
            workers = 1

        if not fail_range_page:
            range_page = range(start_page, total_page, step)
            print("Init range pages")
        else:
            range_page = fail_range_page
            print("Retry put fail pages")

        pool = ThreadPoolExecutor(workers)
        futures = []

        for page in range_page:

            # check limit
            limit = AutoAddFollowing().get_rate_limit()
            rate = AutoAddFollowing().get_rate_remaining()
            reset = AutoAddFollowing().get_rate_reset()
            sleep_time = delta_time(reset)

            logging.info(f"GitHub Api Remaining {rate}")
            if rate < 500:
                logging.info(f"sleep {sleep_time}s...")
                sleep(sleep_time + 1)

            thread_id = page // step
            # Submit multi parameters function to Executor
            # https://python-parallel-programmning-cookbook.readthedocs.io/zh_CN/latest/chapter4/02_Using_the_concurrent.futures_Python_modules.html
            # https://github.com/Joldnine/joldnine.github.io/issues/10
            futures.append(pool.submit(task, page))
            logging.info("Added: Thread-{}".format(threading.currentThread().ident))
            print(f"Following Page: {page} Followings")

            if not fail_range_page:
                page = page + step
                group = 1
                print(f"Current Group: {group}, Total Group: {step}")
                group = group + 1
            print(f"Follow Page: {page} Done")

        print(f"Just a moment, please wait...")

        for x in as_completed(futures):
            logging.info("{} completed".format(x))



