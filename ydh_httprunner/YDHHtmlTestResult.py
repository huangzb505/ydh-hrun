from unittest.runner import _WritelnDecorator,TextTestRunner
from httprunner.report import HtmlTestResult
from .YDHCommon import rdp
import sys, redis, json
from httprunner.report import render_html_report,get_summary





class YDHHtmlTestResult(HtmlTestResult):
    def __init__(self,*args,**kwargs):
        super().__init__(stream=_WritelnDecorator(sys.stderr), descriptions=True, verbosity=1, *args, **kwargs)

    def _record_test(self, test, status, attachment=''):
        meta_data = test.meta_data
        if status == "success" :
            meta_data.update({"request_headers":{},"request_body":"......","response_headers":{},"response_body":"......"})
        self.records.append({
            'name': test.shortDescription(),
            'status': status,
            'attachment': attachment,
            "meta_data": meta_data
        })

    def addError(self, test, err):
        super().addError(test, err)
        rdc = redis.StrictRedis(connection_pool=rdp)
        rdc.set(test.shortDescription(),"fail")


    def addFailure(self, test, err):
        super().addFailure(test, err)
        rdc = redis.StrictRedis(connection_pool=rdp)
        rdc.set(test.shortDescription(), "fail")


    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        rdc = redis.StrictRedis(connection_pool=rdp)
        rdc.set(test.shortDescription(), "fail")


    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        rdc = redis.StrictRedis(connection_pool=rdp)
        rdc.set(test.shortDescription(), "fail")

    def render_html_report(self, html_report_name=None, html_report_template=None):
        return render_html_report(
            get_summary(self),
            html_report_name,
            html_report_template
        )
