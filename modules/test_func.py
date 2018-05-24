import hashlib
import hmac
import random
import string
import json
import jsonpath
from requests_toolbelt import MultipartEncoder
import os
from config import ROOT_DIR,Config
from httprunner import logger
import time

boundary="132b58fe4eb3406597cb960239571ca7"


def form_data_header():
    return "multipart/form-data; boundary={boundary}".format(boundary=boundary)


def form_data_file(path):
    return open(os.path.join(Config.resource_path,path), "rb")


def pop_list(variables_list):
    if len(variables_list) and isinstance(variables_list,list):
        return variables_list.pop(0)


def get_trimmed_lt_for_login(lt):

    lt_str = ''.join(lt)
    assert ('OK_LT' in lt_str),'Error:Wrong resp LT in get_trimmed lt_for_login()'

    logger.log_debug("LT is : {}".format(lt_str[3:]))
    return lt_str[3:]


def setup_hook(method,url,kwargs):
    pass


def teardown_hook_resp(resp_obj,testcase_name):
    #resp默认返回的格式是‘ISO-8859-1’
    resp_obj.encoding = "utf-8"
    logger.log_debug("------------in the teardown-----------------:")
    logger.log_debug(testcase_name)

    if Config.debug_output_enable:
        if not os.path.exists(Config.return_json_path):
            os.makedirs(Config.return_json_path)

        testcase_name_json = testcase_name + '.json'
        with open(os.path.join(Config.return_json_path, testcase_name_json), 'w') as f:
            json.dump(resp_obj.json(), fp=f, indent=4, sort_keys=True,ensure_ascii=False)


def teardown_hook_sleep_10_secs(resp_obj,testcase_name):
    """ sleep 10 seconds after request
    """
    time.sleep(10)

def toJSON(rawContent):
    return json.dumps(rawContent)


def jsonpath_contained_by(content, expect_value):
    assert isinstance(expect_value[1], (list,set,tuple)), 'Expect_value, must be list,set,tuple format, i.e: [1,3]!!'
    actual_list = jsonpath.jsonpath(content,expect_value[0])
    assert len(actual_list) >= 1, 'length of actual_list less than 1!!'
    assert set(actual_list) <= set(expect_value[1]), "type not in expect_value,  actual:{},item:{}".format(set(actual_list), set(expect_value[1]))

def jsonpath_contains(content, expect_value):
    assert isinstance(expect_value[1], (list,set,tuple,str)), 'Expect_value, must be list,set,tuple format, i.e: [1,3]!!'
    actual_list = jsonpath.jsonpath(content,expect_value[0])
    assert len(actual_list) >= 1, 'length of actual_list less than 1!!'
    assert set(actual_list) >= set(expect_value[1]), "type not in expect_value,  actual:{},item:{}".format(set(actual_list), set(expect_value[1]))


def if_exists(content,expect_value):
    orderNumList = jsonpath.jsonpath(content, "$.data.[*].orderNum")
    logger.log_debug("orderNumList is: {}".format(orderNumList))
    assert expect_value in orderNumList, "{} not in orderNumList".format(expect_value)

