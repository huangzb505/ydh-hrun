
from httprunner import logger
import yaml
from httprunner.report import render_html_report,get_summary
from ydh_httprunner.YDHTextTestRunner import YdhTextTestRunner
from ydh_httprunner.YDHHtmlTestResult import YDHHtmlTestResult
from ydh_httprunner.YDHCommon import check_case_result,clean_redis,set_case_result,get_case_result
from ydh_httprunner.YDHHttpSession import YDHHttpSession
from ydh_httprunner.YDHtask import YDHTestSuite
from modules import dependency_parser
from config import Config, ROOT_DIR
import os
import copy
from collections import defaultdict


class YDHHttpRunner(object):

    def __init__(self,test_path_dict, runner=None, http_client_session_dict=None, test_result=None, global_variables=None,dependent_root=None, **kwargs):
        self.test_result = test_result if test_result else YDHHtmlTestResult()
        self.test_path_dict = test_path_dict
        self.runner = runner if runner else YdhTextTestRunner(ResultInstance=self.test_result)
        self.http_client_session_dict = http_client_session_dict if http_client_session_dict is not None else dict()
        self.http_client_session_dict["default"] = YDHHttpSession()
        # self.login_flag = True if http_client_session else False
        self.global_variables = global_variables if global_variables else {}
        self.dependent_root = dependent_root if dependent_root else []

    @staticmethod
    def load_yaml_file(yaml_file):
        assert yaml_file,"yaml_file is empty, check if missing dependency file in your specified path!"
        with open(yaml_file, 'r', encoding='utf-8') as stream:
            yaml_content = yaml.load(stream)
            return yaml_content

    @staticmethod
    def dump_yaml_file(yaml_content):
        return yaml.dump(yaml_content, encoding='utf-8').decode('unicode-escape')

    def get_dependent_testcase(self,dependent_testcase_name):
        return self.load_yaml_file(self.test_path_dict[dependent_testcase_name])

    def dependent_runner(self, Origion_dic):

        # if self.login_flag:
        #     for item in Origion_dic:
        #         if item.get("test",""):
        #             if item.get("test","").get("name","") in self.dependent_root:
        #                 logger.log_debug('Inside dependent_runner login_flag-------------````````````````````````````')
        #                 logger.log_debug('test name:{}'.format(item.get("test","").get("name","")))
        #                 logger.log_debug('global_variables: {}'.format(self.global_variables))
        #                 logger.log_debug('http_client_session: {}'.format(self.http_client_session))
        #                 return {}

        dependent_variables = defaultdict(list)
        dependent_list = []
        logger.log_debug('Origion_dic: {}'.format(Origion_dic))
        for item in Origion_dic:
            if item.get("test", ""):
                testcase_name = item.get("test", "").get("name", "")
                idempotency = item.get("test", "").pop("idempotency", "")
                session = item.get("test", "").pop("session", "")
                if session:
                    if not self.http_client_session_dict.get(testcase_name,""):
                        self.http_client_session_dict[testcase_name] = self.http_client_session_dict["default"]
                    self.http_client_session_dict["default"] = self.http_client_session_dict[testcase_name]
                if check_case_result(testcase_name):
                    item.get("test", "")["skip"] = "case fail"
                else:
                    last_result = get_case_result(testcase_name)
                    if isinstance(last_result, dict):
                        return last_result
                raw_testcase_dep = item.get("test", "").pop("dependent", "")

                if raw_testcase_dep and not isinstance(raw_testcase_dep, (list, set)):
                    testcase_list = raw_testcase_dep.split(',')
                    dependent_list.extend(testcase_list)
                else:
                    dependent_list.extend(raw_testcase_dep)

        for dependent_testcase_name in dependent_list:
            for key, value in self.dependent_runner(self.get_dependent_testcase(dependent_testcase_name)).items():
                if key.startswith("global_"):
                    self.global_variables[key] = value   #所有全testsuit的参数使用k-v？
                else:
                    if dependent_variables.get(key,""):
                        if not isinstance(dependent_variables.get(key,""),list):
                            temp = dependent_variables[key]
                            dependent_variables[key] = [temp]
                        dependent_variables[key].append(value)
                    else:
                        dependent_variables[key] = value

        for key, value in self.global_variables.items():
            if not dependent_variables.get(key,""):
                dependent_variables[key] = value

        for item in Origion_dic:
            if item.get("test", ""):
                if any([check_case_result(dependent_case) for dependent_case in dependent_list]):
                    item.get("test", "")["skip"] = "dependent case fail"
            if item.get("config", ""):
                for variables in (item.get("config", "").pop("variables", "")):
                    for key,value in variables.items():
                        dependent_variables[key] = value
        logger.log_debug('dependent_variabls------:')
        logger.log_debug('{}'.format(dependent_variables))
        dic = dependency_parser.load_test_file(Origion_dic)
        logger.log_debug('dic-----:')
        logger.log_debug('{}'.format(dic))
        testcase = YDHTestSuite(dic,http_client_session=self.http_client_session_dict["default"],variables_mapping=dependent_variables)
        logger.log_debug('testcase------:')
        logger.log_debug('{}'.format(testcase.output))
        self.runner.run(testcase)
        if idempotency:
            set_case_result(testcase_name,testcase.output[0].get('out',""))
        return testcase.output[0].get('out',"")


    def render_html_report(self, html_report_name=None, html_report_template=None):
        return render_html_report(
            get_summary(self.test_result),
            html_report_name,
            html_report_template
        )


if __name__ == '__main__':
    test_dep_dict, test_path_dict = dependency_parser.load_test_dependency_map_by_path(os.path.join(ROOT_DIR, Config.testcase_path))
    yml_dep = dependency_parser.get_all_dep_paths_with_separator(test_dep_dict, '/')
    full_yml_dep = dependency_parser.extract_full_dep_paths(yml_dep)
    YDHHttpRunner = YDHHttpRunner(test_path_dict)

    YDHHttpRunner.dependent_runner(YDHHttpRunner.load_yaml_file(os.path.join(ROOT_DIR, Config.testcase_path) + '/CorpLogin.yml'))
    YDHHttpRunner.render_html_report()
    clean_redis()

    print("End")
