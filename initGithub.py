#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2020/6/19 3:05 下午
# @Author  : Johny Zheng
# @Site    : 
# @File    : initGithub.py
# @Software: PyCharm
# Running based on python3.6.2 environment

import config
import requests
import logging
import re

from github import Github


class InitLogin(config.Base):
    """
        https://github.com/PyGithub/PyGithub
    """
    def __init__(self):
        super().__init__()
        self.g = Github(self.user, self.password)


class InitCrawler(config.Base):
    def __init__(self, someone, page):
        super().__init__()
        self.baseUrls = self.baseUrl + someone
        self.followingQueryString = {"page": page, "tab": "following", "_pjax": "#js-pjax-container"}
        self.followerQueryString = {"page": page, "tab": "followers", "_pjax": "#js-pjax-container"}

        self.cookies = GithubLogin().get_cookies()
        # self.token = GithubLogin().get_token()
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