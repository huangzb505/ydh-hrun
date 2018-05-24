#!/usr/local/bin/python3.6
# -*- coding: <encoding name> -*-
import os
import sys
import socket
import argparse
import logging
import subprocess
from collections import defaultdict
import copy

from httprunner import logger
from ydh_httprunner.YDHHttpRunner import YDHHttpRunner
from ydh_httprunner.YDHHtmlTestResult import YDHHtmlTestResult
from ydh_httprunner.YDHCommon import clean_redis
from config import Config,ROOT_DIR,Env
from modules import dependency_parser



#获取登录依赖的根节点，Example: CorpV2LogisticsDeliver的登录依赖的节点为CorpAuthentication
def get_login_depend_root(testcase,valid_full_testcase_dependency):

    assert testcase, "Please input correct testcase"
    for each in valid_full_testcase_dependency:
        if testcase in each:
            return each.split('/')[-1]
    return None

#获取所有登录的session，以及global_variables（例如global_access_token）
def get_login_session_variabls(test_path_dict = None,valid_full_dep_path=None,test_result = None):

    login_session_dict = defaultdict(list)
    temp_global_variables = defaultdict(list)
    global_variables = defaultdict(list)
    login_list = ['CorpLogin','AgentLogin','CorpOauth2Token','AgentOauth2Token','GetToken']

    if not test_path_dict or not valid_full_dep_path:
        return login_session_dict

    temp_login_list = []
    for lgn in login_list:
        lgn_depend_root = get_login_depend_root(lgn, valid_full_dep_path)
        temp_login_list.append(lgn_depend_root)

    login_set = list(set(temp_login_list))
    for login in login_set:
        if test_path_dict[login]:
            ydh = YDHHttpRunner(test_path_dict = test_path_dict,test_result=test_result)
            dic = ydh.load_yaml_file(test_path_dict[login])
            out = ydh.dependent_runner(dic)

            for key,values in out.items():
                if key.startswith("global_"):
                    temp_global_variables[key] = values

            temp_global_variables_copy = copy.copy(temp_global_variables)    #浅拷贝字典引用
            login_depend_root = get_login_depend_root(login,valid_full_dep_path)
            login_session_dict[login_depend_root] = ydh.http_client_session_dict
            global_variables[login_depend_root] = temp_global_variables_copy

    logger.log_debug('global_variables::::::::::::::{}'.format(global_variables))
    logger.log_debug('login_session_dict::::::::::::::{}'.format(login_session_dict))

    return login_session_dict,global_variables


def runTest():

    """ API test: parse command line options and run commands.
    """
    parser = argparse.ArgumentParser(
        description='YDH HTTP test runner, not just about api test and load test.')

    parser.add_argument(
        'testset_paths', nargs='*',
        help="testset file path")
    parser.add_argument(
        '--html-report-name',
        help="specify html report name, only effective when generating html report.")
    parser.add_argument(
        '--html-report-template',
        help="specify html report template path.")
    parser.add_argument(
        '--log-level', default='INFO',
        help="Specify logging level, default is INFO.")
    parser.add_argument(
        '--env', nargs='*', choices=['develop', 'master', 'release', 'gray', 'production'],
        help="environment")
    parser.add_argument(
        '--testcases', nargs='*',
        help="specified the testcase name to run")

    args = parser.parse_args()
    logger.setup_logger(args.log_level)


    logger.color_print("specified testcase:{}".format(args.testcases))

    #若指定参数优先，则优先覆盖为参数值，否则从ini文件中读取
    env_list = []
    if args.env:
        Env.init_require_envs(args.env)
        env_list = args.env
    else:
        Env.init_require_envs(Env.target_env_list)
        env_list = Env.target_env_list
    logger.color_print("environment:{}".format(env_list))

    #解析依赖路径
    if not args.testset_paths:
        logger.log_info("Reading testcase from conf/setting.ini")
        test_dep_dict, test_path_dict = dependency_parser.load_test_dependency_map_by_path(os.path.join(ROOT_DIR, Config.testcase_path))

    else:
        test_dep_dict, test_path_dict = dependency_parser.load_test_dependency_map_by_path(args.testset_paths)
        logger.log_info("Reading testcase from argument")

    #提取完整子路径
    testcase_dependency = dependency_parser.get_all_dep_paths_with_separator(test_dep_dict, '/')
    valid_full_testcase_dependency = dependency_parser.extract_full_dep_paths(testcase_dependency)

    logger.color_print("test_dep_dict(len is {}):\n{}".format(len(test_dep_dict),test_dep_dict))
    logger.color_print("test_path_dict(len is {}): \n{}".format(len(test_path_dict),test_path_dict))
    logger.color_print("testcase_dependency(len is {}):\n{}".format(len(testcase_dependency),testcase_dependency))
    logger.color_print("valid_full_testcase_dependency(len is {}):\n{}".format(len(valid_full_testcase_dependency),valid_full_testcase_dependency))

    #生成可视化依赖关系图，包含：1)每条完整最长依赖路径   2)一张图for Overall
    if Config.debug_output_enable:
        overall_png = 'Overall.png'
        reversed_graph_overall = dependency_parser.convert_to_reversed_std_graph(test_dep_dict)
        dependency_pic_path = os.path.join(ROOT_DIR, Config.debug_root_path, Config.dependency_pic_path)
        pic_saved_path = os.path.join(dependency_pic_path, overall_png)
        if not os.path.exists(dependency_pic_path):
            os.makedirs(dependency_pic_path)

        dependency_parser.save_graph(reversed_graph_overall, pic_saved_path)

        std_graph = dependency_parser.get_std_graphs_dict_from_full_path(valid_full_testcase_dependency)
        for key,graph in std_graph.items():
            reversed_graph = dependency_parser.convert_to_reversed_std_graph(graph)
            file_name = str(key) + '.png'
            file_path = os.path.join(dependency_pic_path, file_name)
            dependency_parser.save_graph(reversed_graph, file_path)

    #依赖根节点测试
    testcase_to_root = 'GetToken'
    login_depend_root = get_login_depend_root(testcase_to_root,valid_full_testcase_dependency)
    logger.color_print('get_login_depend function test:  {} ---> {}'.format(testcase_to_root,login_depend_root))

    #从完整子路径中，找出依赖最深的用例名。例如1/2/4，则提取出1
    to_run_list = []
    test_login_depend_dict = defaultdict(list)
    for testcase in test_path_dict:
        for test in valid_full_testcase_dependency:
            if testcase == test.split('/')[1]:
                to_run_list.append(test_path_dict[testcase])
                if not test_login_depend_dict[testcase]:
                    test_login_depend_dict[testcase] = test.split('/')[-1]
                else:
                    assert test_login_depend_dict[testcase] == test.split('/')[-1],'!!!!!!!Error:One testcase depend on different login'
                    #报错条件：一个用例依赖不同登录视为异常, 如CorpV2LogisticsDeliver，依赖路径上最后的依赖节点只应该为CorpAuthentication

    logger.color_print("login_depend_dict is:\n{}".format(test_login_depend_dict))
    logger.color_print('testcase list to run(len:{}):\n{}'.format(len(to_run_list),to_run_list))

    to_run_set = list(set(to_run_list))
    logger.color_print("Remove duplicates(len:{}):\n{}".format(len(to_run_set),to_run_set))
    if args.testcases:
        logger.color_print('The specified testcase to run is:{}'.format(args.testcases))

    clean_redis()
    try:
        #切换环境，替换IP
        for target_env in env_list:
            Env.reload_env(target_env)

            ydh_testresult = YDHHtmlTestResult()

            login_session_dict,global_variables = get_login_session_variabls(test_path_dict,valid_full_dep_path=valid_full_testcase_dependency, test_result = ydh_testresult)
            logger.color_print("Login Session Data:\n{}".format(login_session_dict))

            http_client_session_dict = dict()
            if args.testcases:
                if isinstance(args.testcases, (list, set)):  # 若参数中指定用例名，则只跑指定的用例
                    for testcase in args.testcases:
                        login_dep_root = get_login_depend_root(testcase, valid_full_testcase_dependency)

                        ydhrunner = YDHHttpRunner(test_path_dict, http_client_session_dict=http_client_session_dict,
                                                  test_result=ydh_testresult, dependent_root=login_dep_root,
                                                  global_variables=global_variables[login_dep_root])
                        dic = ydhrunner.load_yaml_file(test_path_dict[testcase])
                        ydhrunner.dependent_runner(dic)
            else:
                for test_file in to_run_set:
                    for test,file_path in test_path_dict.items():
                        if file_path == test_file:
                            login_dep_root = get_login_depend_root(test,valid_full_testcase_dependency)
                            ydhrunner = YDHHttpRunner(test_path_dict,http_client_session_dict=http_client_session_dict, test_result= ydh_testresult,dependent_root= login_dep_root,global_variables= global_variables[login_dep_root])

                            dic = ydhrunner.load_yaml_file(test_file)
                            ydhrunner.dependent_runner(dic)

            ydh_testresult.render_html_report()


    except Exception as e:
        logger.log_error('Exception running in main() function:{}'.format(e))

    finally:
        clean_redis()



def get_process_id(name):
    child = subprocess.Popen(['pgrep', '-f', name],stdout=subprocess.PIPE, shell=False)
    response = child.communicate()[0]
    return [int(pid) for pid in response.split()]

def main():
    clean_redis()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("", 44400))  # bind to a port will fail if we are already running
    except OSError as e:

        logging.error('A main.py is already running on this host')
        pid = get_process_id('main.py')
        logging.error('Running main.py pid: {}'.format(pid))
        return 88
    sock.listen(5)

    runTest()

    logger.color_print("End of main")



if __name__ == '__main__':
    sys.exit(main())



