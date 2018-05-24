import copy
import sys
import unittest
from unittest.case import SkipTest
from httprunner import exception, logger, testcase, utils,runner,response
from httprunner import exception, logger, testcase, utils,runner
from ydh_httprunner import YDHrunner


class YDHTestCase(unittest.TestCase):
    """ create a testcase.
    """
    def __init__(self, test_runner, testcase_dict):
        super(YDHTestCase, self).__init__()
        self.test_runner = test_runner
        self.testcase_dict = copy.copy(testcase_dict)

    def runTest(self):
        """ run testcase and check result.
        """
        try:
            self.meta_data = ""
            if self.testcase_dict.get("skip", ""):
                raise SkipTest(self.testcase_dict.get("skip", ""))
            self.test_runner.run_test(self.testcase_dict)
        except SkipTest as e:
            self.meta_data = {"skip": str(e),"request_headers":{},"request_body":"","response_headers":{},"response_body":"","response_time(ms)":0}
            raise e
        finally:
            if not len(self.meta_data):
                self.meta_data = getattr(self.test_runner.http_client_session, "meta_data", {})


class YDHTestSuite(unittest.TestSuite):
    """ create test suite with a testset, it may include one or several testcases.
        each suite should initialize a separate Runner() with testset config.
    @param
        (dict) testset
            {
                "name": "testset description",
                "config": {
                    "name": "testset description",
                    "requires": [],
                    "function_binds": {},
                    "parameters": {},
                    "variables": [],
                    "request": {},
                    "output": []
                },
                "testcases": [
                    {
                        "name": "testcase description",
                        "parameters": {},
                        "variables": [],    # optional, override
                        "request": {},
                        "extract": {},      # optional
                        "validate": {}      # optional
                    },
                    testcase12
                ]
            }
        (dict) variables_mapping:
            passed in variables mapping, it will override variables in config block
    """
    def __init__(self, testset, variables_mapping=None, http_client_session=None):
        super().__init__()
        self.test_runner_list = []

        config_dict = testset.get("config", {})
        self.output_variables_list = config_dict.get("output", [])
        self.testset_file_path = config_dict["path"]
        config_dict_parameters = config_dict.get("parameters", [])

        config_dict_variables = config_dict.get("variables", [])
        variables_mapping = variables_mapping or {}
        config_dict_variables = utils.override_variables_binds(config_dict_variables, variables_mapping)

        config_parametered_variables_list = self._get_parametered_variables(
            config_dict_variables,
            config_dict_parameters
        )
        self.testcase_parser = testcase.TestcaseParser()
        testcases = testset.get("testcases", [])

        for config_variables in config_parametered_variables_list:
            # config level
            config_dict["variables"] = config_variables
         #   test_runner = runner.Runner(config_dict, http_client_session)
            test_runner = YDHrunner.YDHRunner(config_dict, http_client_session)

            for testcase_dict in testcases:
                testcase_dict = copy.copy(testcase_dict)
                # testcase level
                testcase_parametered_variables_list = self._get_parametered_variables(
                    testcase_dict.get("variables", []),
                    testcase_dict.get("parameters", [])
                )
                for testcase_variables in testcase_parametered_variables_list:
                    testcase_dict["variables"] = testcase_variables

                    # eval testcase name with bind variables
                    variables = utils.override_variables_binds(
                        config_variables,
                        testcase_variables
                    )
                    self.testcase_parser.update_binded_variables(variables)
                    testcase_name = self.testcase_parser.eval_content_with_bindings(testcase_dict["name"])
                    self.test_runner_list.append((test_runner, variables))

                    self._add_test_to_suite(testcase_name, test_runner, testcase_dict)

    def _get_parametered_variables(self, variables, parameters):
        """ parameterize varaibles with parameters
        """
        cartesian_product_parameters = testcase.parse_parameters(
            parameters,
            self.testset_file_path
        ) or [{}]

        parametered_variables_list = []
        for parameter_mapping in cartesian_product_parameters:
            parameter_mapping = parameter_mapping or {}
            variables = utils.override_variables_binds(
                variables,
                parameter_mapping
            )

            parametered_variables_list.append(variables)

        return parametered_variables_list

    def _add_test_to_suite(self, testcase_name, test_runner, testcase_dict):
        YDHTestCase.runTest.__doc__ = testcase_name


        test = YDHTestCase(test_runner, testcase_dict)
        [self.addTest(test) for _ in range(int(testcase_dict.get("times", 1)))]

    @property
    def output(self):
        outputs = []

        for test_runner, variables in self.test_runner_list:
            outputs.append(
                {
                    "in": variables,
                    "out": test_runner.extract_output(self.output_variables_list)
                }
            )

        return outputs