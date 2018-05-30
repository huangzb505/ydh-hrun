import json
import re
import jsonpath
import shortuuid
import time
import datetime
from dateutil.relativedelta import *
import random
import numpy as np



def check_page_size(content, expect_value):
    page_size = int(jsonpath.jsonpath(content,"$.data.pageSize")[0])
    total_count = int(jsonpath.jsonpath(content,"$.data.totalCount")[0])
    total_page = int(jsonpath.jsonpath(content,"$.data.totalPage")[0])
    currentPage = int(jsonpath.jsonpath(content,"$.data.currentPage")[0])
    item = len(jsonpath.jsonpath(content,"$.data.items.*"))
    assert page_size*total_page >= total_count,\
        "! page_size*total_page > total_count  " \
        "page_size:{},total_page:{},total_count:{},item:{}".format(page_size,total_page,total_count,item)
    assert item <= page_size,\
        "! item <= page_size  " \
        "page_size:{},total_page:{},total_count:{},item:{}".format(page_size,total_page,total_count,item)
    if currentPage == total_page:
        assert total_count == (currentPage-1)*page_size + item, \
        "! total_count == (currentPage-1)*page_size + item  " \
        "page_size:{},total_page:{},total_count:{},item:{},currentPage{}".format(page_size, total_page, total_count, item,currentPage)
    if total_count <= page_size:
        assert item == total_count,\
        "! item == total_count  " \
        "page_size:{},total_page:{},total_count:{},item:{}".format(page_size,total_page,total_count,item)


def check_size(content, expect_value):
    size = int(jsonpath.jsonpath(content,"$.data.size")[0])
    item = len(jsonpath.jsonpath(content,"$.data.items.*"))
    assert item == size,\
        "! item == size  " \
        "size:{},item:{}".format(size,item)


def check_type_and_exist(content, expect_value):
    if expect_value != "NoneType":
        assert content.__class__.__name__ == expect_value


def short_uuid(prefix=''):
    return ''.join([prefix,shortuuid.ShortUUID().random(length=10)])


def get_list_item(variables_list,num):
    if len(variables_list) > num and isinstance(variables_list,list):
        return variables_list[num]


def return_today():
    return str(time.strftime('%Y-%m-%d',time.localtime(time.time())))


def check_eq_by_jsonpath(content, expect_value):
    item = set(jsonpath.jsonpath(content,expect_value[0]))
    assert len(item) >= 1, 'NOT actual value in jsonpath: {}'.format(expect_value[0])
    if isinstance(expect_value[1],(str,int)):
        assert set({expect_value[1]}) == item, "jsonpath:{}, expected_value: {}, actual item: {}".format(expect_value[0],set({expect_value[1]}),item)
    else:
        assert set(expect_value[1]) == item, "jsonpath:{}, expected_value: {}, actual item: {}".format(expect_value[0],set(expect_value[1]),item)


def check_len_by_jsonpath(content, expect_value):
    assert len(expect_value) == 2
    count = len(jsonpath.jsonpath(content,expect_value.pop(0)))
    check_count = expect_value.pop(0)
    assert int(check_count) == count, "check_count:{} != count:{}".format(check_count,count)


def half_str(text):
    return text[:len(text)//2]


def turn_json(dict):
    return json.dumps(dict)


def get_str_list(text, num):
    if "," in text:
        text_list = text.split(",")
        assert num < len(text_list), "num {} > len(text_list) {}".format(str(num),str(text_list))
        return str(text_list[num])
    else:
        return text


def get_date_timestamp(strf,days=0):
    n_days = datetime.datetime.today()+relativedelta(days=-days)
    return str(n_days.strftime(strf))


def randam_int():
    return int(np.random.choice(range(1,100)))


def get_list_item_random(variables_list,seed):
    random.seed(seed)
    if isinstance(variables_list,list):
        return variables_list[random.randint(0, len(variables_list)-1)]


def get_content_item(content,item):
    assert isinstance(content,dict)
    #assert content[item], "{} not found, content: {}".format(item,content)
    return content[item]


def get_key_item(key,item):
    key_list = key.split()
    assert len(key_list) == 2
    return key_list[item]


def get_time():
    return str(int(time.time()*1000))


def sleep_5_second(method,url,kwargs):
    time.sleep(5)


if __name__ == "__main__":
    print(get_time())
