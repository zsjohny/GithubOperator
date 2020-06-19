#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# @Time    : 2020/6/1 4:10 下午
# @Author  : Johny Zheng
# @Site    : 
# @File    : update_requirements.sh
# @Software: PyCharm

set -e

export PGRDIR=$(cd `dirname $0`; pwd)
export WORKDIR=${PGRDIR}/../

pip freeze > ${WORKDIR}requirements.txt