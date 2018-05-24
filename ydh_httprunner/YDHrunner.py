from httprunner.runner import Runner
from unittest.case import SkipTest

from httprunner import exception, logger, response, testcase, utils
from httprunner.client import HttpSession
from httprunner.context import Context
from httprunner.events import EventHook
from ydh_httprunner import YDHresponse
from ydh_httprunner import YDHcontent

from httprunner.testcase import TestcaseLoader
class YDHRunner(Runner):
    def __init__(self, config_dict=None, http_client_session=None):
        #super().__init__(config_dict, http_client_session)
        self.context = YDHcontent.YDHcontext()
        self.http_client_session = http_client_session
        TestcaseLoader.load_test_dependencies()

        config_dict = config_dict or {}
        self.init_config(config_dict, "testset")

    def run_test(self, testcase_dict):
        """ run single testcase.
        @param (dict) testcase_dict
            {
                "name": "testcase description",
                "skip": "skip this test unconditionally",
                "times": 3,
                "requires": [],         # optional, override
                "function_binds": {},   # optional, override
                "variables": [],        # optional, override
                "request": {
                    "url": "http://127.0.0.1:5000/api/users/1000",
                    "method": "POST",
                    "headers": {
                        "Content-Type": "application/json",
                        "authorization": "$authorization",
                        "random": "$random"
                    },
                    "body": '{"name": "user", "password": "123456"}'
                },
                "extract": [],              # optional
                "validate": [],             # optional
                "setup_hooks": [],          # optional
                "teardown_hooks": []        # optional
            }
        @return True or raise exception during test
        """
        parsed_request = self.init_config(testcase_dict, level="testcase")

        try:
            url = parsed_request.pop('url')
            method = parsed_request.pop('method')
            group_name = parsed_request.pop("group", None)
        except KeyError:
            raise exception.ParamsError("URL or METHOD missed!")

        self._handle_skip_feature(testcase_dict)

        extractors = testcase_dict.get("extract", [])
        validators = testcase_dict.get("validate", [])
        setup_hooks = testcase_dict.get("setup_hooks", [])
        teardown_hooks = testcase_dict.get("teardown_hooks", [])

        testcase_name = testcase_dict.get("name", "")

        logger.log_info("{method} {url}".format(method=method, url=url))
        logger.log_debug("request kwargs(raw): {kwargs}".format(kwargs=parsed_request))
        self._call_setup_hooks(setup_hooks, method, url, parsed_request)
        resp = self.http_client_session.request(
            method,
            url,
            name=group_name,
            **parsed_request
        )
        resp.encoding = "utf-8"
        self._call_teardown_hooks(teardown_hooks,resp,testcase_name)

        resp_obj = YDHresponse.YDHResponseObject(resp)
        extracted_variables_mapping = resp_obj.extract_response(extractors)
        self.context.bind_extracted_variables(extracted_variables_mapping)

        try:
            self.context.validate(validators, resp_obj)
        except (exception.ParamsError, exception.ResponseError, exception.ValidationError):
            # log request
            err_req_msg = "request: \n"
            err_req_msg += "headers: {}\n".format(parsed_request.pop("headers", {}))
            for k, v in parsed_request.items():
                err_req_msg += "{}: {}\n".format(k, v)
            logger.log_error(err_req_msg)

            # log response
            err_resp_msg = "response: \n"
            err_resp_msg += "status_code: {}\n".format(resp.status_code)
            err_resp_msg += "headers: {}\n".format(resp.headers)
            err_resp_msg += "body: {}\n".format(resp.text)
            logger.log_error(err_resp_msg)

            raise

    def _call_teardown_hooks(self, hooks,resp_obj,testcase_name):
        """ call hook functions after request

        Listeners should take the following arguments:

        * *resp_obj*: response object
        """
        event = self._prepare_hooks_event(hooks)
        if not event:
            return

        event.fire(resp_obj=resp_obj, testcase_name=testcase_name)