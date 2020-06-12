#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2020/6/11 6:09 下午
# @Author  : Johny Zheng
# @Site    : 
# @File    : config.py
# @Software: PyCharm
# Running based on python3.6.2 environment


import logging
import configparser
import sys
import json

logging.basicConfig(level=logging.INFO)


class GlobalVar:
    def __init__(self):
        try:
            self.config = configparser.RawConfigParser()
            self.config.optionxform = str
            self.config.read("config.ini")
            logging.debug('读取配置文件成功')

        except Exception as e:
            logging.error('读取配置文件失败{}'.format(e))

    def config_info(self):
        """
        读取配置信息
        :return: str
        """
        config_info = {}
        try:

            for section in self.config.sections():
                config_info[section] = {}
                for option in self.config.options(section):
                    config_info[section][option] = self.config.get(section, option)
                logging.debug(f"load config {config_info[section]}")
                self.__dict__.update(config_info[section])

        except Exception as e:
            logging.error('读取变量失败{}'.format(e))
            sys.exit(0)

        finally:
            return config_info['default']

    def get_keys(self, keys):
        """
        获取key
        :param keys:
        :return:
        """
        _get_keys = self.config_info()
        sensitive_data_list = ["user", "password", "access_token"]

        if _get_keys != '':
            try:
                return self.config_info().get(keys)
            except Exception as e:
                logging.error(f'获取{keys}为空{e}')
            finally:
                # 日志级别 DEBUG: 10 ,INFO: 20
                if keys in sensitive_data_list:
                    logging_level = 10
                else:
                    logging_level = 10
                logging.log(logging_level, f"{keys} {_get_keys}")
        else:
            logging.error(f'获取{keys}为空')
            sys.exit(0)


class Base(GlobalVar):
    def __init__(self):
        super().__init__()
        self.__dict__.update(self.config_info())

    def expose(self):
        for k, v in self.config_info().items():
            setattr(self, k, v)


if __name__ == '__main__':
    print(Base().__dict__)
    print(Base().__getattribute__('accessToken'))


