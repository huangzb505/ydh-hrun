from httprunner.context import Context
import copy
import os
import re
import sys

from httprunner import exception, testcase, utils
from httprunner.compat import OrderedDict


class YDHcontext(Context):


    def do_validation(self, validator_dict):
        """ validate with functions
        """
        comparator = utils.get_uniform_comparator(validator_dict["comparator"])
        validate_func = self.testcase_parser.get_bind_function(comparator)

        if not validate_func:
            raise exception.FunctionNotFound("comparator not found: {}".format(comparator))

        check_item = validator_dict["check"]
        check_value = validator_dict["check_value"]
        expect_value = validator_dict["expect"]

        # if (check_value is None or expect_value is None) \
        #     and comparator not in ["is", "eq", "equals", "=="]:
        #     raise exception.ParamsError("Null value can only be compared with comparator: eq/equals/==")

        try:
            validate_func(validator_dict["check_value"], validator_dict["expect"])
        except (AssertionError, TypeError):
            err_msg = "\n" + "\n".join([
                "\tcheck item name: %s;" % check_item,
                "\tcheck item value: %s (%s);" % (check_value, type(check_value).__name__),
                "\tcomparator: %s;" % comparator,
                "\texpected value: %s (%s)." % (expect_value, type(expect_value).__name__)
            ])
            raise exception.ValidationError(err_msg)