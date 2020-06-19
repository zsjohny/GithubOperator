#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2020/6/19 2:29 下午
# @Author  : Johny Zheng
# @Site    : 
# @File    : mockGithubContributions.py
# @Software: PyCharm
# Running based on python3.6.2 environment


from datetime import date, timedelta
from random import randint
import sys
import subprocess
import logging
import config
import base64
import requests
import datetime
import time

from initGithub import InitLogin
from github import Github


class OperatePrepare:
    def __init__(self, days, start_date):
        self.n_days_ago = start_date - timedelta(days=days)
        self.start_date = start_date
        self.days = days

    def get_date_string(self):
        result = self.n_days_ago.strftime("%a %b %d %X %Y %z -0400")
        return result


class MockContributions(InitLogin):
    def __init__(self):
        super().__init__()
        self.credentials = base64.b64encode(f"{self.email}:{self.password}".encode()).decode()
        self.header = {
            'Authorization': "Basic {}".format(self.credentials),
        }

        self.argv = ''
        self.start_date = ''

    def check_repos(self):
        check_repo_name = f"{self.user}/{self.repoName}"
        logging.info(f"check repo: {check_repo_name}")
        for repo in self.g.get_user().get_repos():
            if repo.full_name == check_repo_name:
                return True
        return False

    def create_repo(self):
        payload = {'name': config.Base().repoName,
                   'description': config.Base().repoName}
        r = requests.post(self.apiUrl + f"/user/repos", json=payload, headers=self.header)
        logging.info(r.status_code)
        logging.info(r.content)
        return r.status_code

    def mock_commit(self, argv):
        self.argv = argv
        if len(argv) == 1:
            self.start_date = date.today()
        if len(argv) == 2:
            self.start_date = date(int(argv[1][0:4]), int(argv[1][5:7]), int(argv[1][8:10]))

        if len(self.argv) < 1 or len(self.argv) > 2:
            logging.error("Error: Bad input. please input need mock github contributions's days. "
                          "eg. python mockGithubContributions.py 365")
            sys.exit(1)

        n = int(self.argv[0])
        init_result = subprocess.run(f"cd /tmp; rm -rf {config.Base().repoName}; mkdir -pv {config.Base().repoName}; "
                                     f"cd {config.Base().repoName}; "
                                     f"git init; "
                                     f"git remote add origin https://github.com/"
                                     f"{config.Base().user}/{config.Base().repoName}.git; ",
                                     shell=True, check=True
                                     )
        if init_result.returncode != 0:
            logging.warning(f"Init Repo Fail: {init_result}")
        else:
            logging.info(f"Init Repo success: {init_result}")

        for i in range(0, n):
            current_date = OperatePrepare(i, self.start_date).get_date_string()
            num_commits = randint(1, 10)
            for commit in range(0, num_commits):
                logging.debug(current_date)
                commit_result = subprocess.run(f"cd /tmp/{config.Base().repoName}; "
                                               f"echo '{current_date + str(randint(0, 1000000))}' > mock_commits.txt; "
                                               f"sync; "
                                               f"git add mock_commits.txt; "
                                               f"export GIT_AUTHOR_DATE='{current_date}' "
                                               f"export GIT_COMMITTER_DATE='{current_date}'; "
                                               f"git commit -m 'update' --date '{current_date}'; ",
                                               shell=True, check=True
                                               )
                if commit_result.returncode != 0:
                    logging.warning(f"Mock Commit Fail: {commit_result}")
                else:
                    logging.info(f"Mock Commit success: {commit_result}")
            i += 1

        push_result = subprocess.run(f"cd /tmp/{config.Base().repoName}; "
                                     f"git rm mock_commits.txt; "
                                     f"git commit -m 'clean'; "
                                     f"git push -f -u origin master;",
                                     shell=True, check=True)
        if push_result.returncode == 0:
            logging.info("Mock Github Contributions Successful")
        else:
            logging.warning(f"Mock Github Contributions Fail: {push_result}")


if __name__ == '__main__':
    print("Check repo libs...")
    if not MockContributions().check_repos():
        create_code = MockContributions().create_repo()
        print(f"Created repo: {config.Base().repoName}")
        if create_code != 201:
            logging.error(f"Please check repo name from config.ini and "
                          f"retry manually create repo: {config.Base().repoName}")
            exit(1)

    MockContributions().mock_commit(sys.argv[1:])


