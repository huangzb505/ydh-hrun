from unittest.runner import _WritelnDecorator,TextTestRunner
from httprunner.report import HtmlTestResult






class YdhTextTestRunner(TextTestRunner):
    def __init__(self,ResultInstance,*args,**kwargs):
        self.ResultInstance = ResultInstance
        super().__init__(failfast=False, resultclass=HtmlTestResult, *args, **kwargs)

    def _makeResult(self):
        return self.ResultInstance
