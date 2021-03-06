
import re,time

from httprunner import exception, logger, testcase, utils
from httprunner.response import ResponseObject
from httprunner.compat import OrderedDict, basestring
import jsonpath
from requests.structures import CaseInsensitiveDict
text_extractor_regexp_compile = re.compile(r".*\(.*\).*")


class YDHResponseObject(ResponseObject):
    def __init__(self, resp_obj):
        super().__init__(resp_obj)

    def extract_field(self, field):
        """ extract value from requests.Response.
        """
        msg = "extract field: {}".format(field)

        try:
            if field.startswith("$"):
                value = self._extract_field_with_jsonpath(field)
            elif text_extractor_regexp_compile.match(field):
                value = self._extract_field_with_regex(field)
            else:
                value = self._extract_field_with_delimiter(field)

            msg += "\t=> {}".format(value)
            logger.log_debug(msg)
        except exception.ParseResponseError:
            logger.log_error("failed to extract field: {}".format(field))
            raise

        return value

    def _extract_field_with_jsonpath(self,field):
        result = jsonpath.jsonpath(self.resp_body,field)
        if result:
            return result
        else:
            raise exception.ParamsError("jsonpath {} get nothing".format(field))


    def _extract_field_with_delimiter(self, field):
        """ response content could be json or html text.
        @param (str) field should be string joined by delimiter.
        e.g.
            "status_code"
            "content"
            "headers.content-type"
            "content.person.name.first_name"
        """
        try:
            # string.split(sep=None, maxsplit=-1) -> list of strings
            # e.g. "content.person.name" => ["content", "person.name"]
            try:
                top_query, sub_query = field.split('.', 1)
            except ValueError:
                top_query = field
                sub_query = None

            if top_query in ["body", "content", "text"]:
                top_query_content = self.resp_body
            elif top_query == "cookies":
                cookies = self.resp_obj.cookies
                try:
                    return cookies[sub_query]
                except KeyError:
                    err_msg = u"Failed to extract attribute from cookies!\n"
                    err_msg += u"cookies: {}\n".format(cookies)
                    err_msg += u"attribute: {}".format(sub_query)
                    logger.log_error(err_msg)
                    raise exception.ParamsError(err_msg)
            else:
                try:
                    top_query_content = getattr(self.resp_obj, top_query)
                except AttributeError:
                    err_msg = u"Failed to extract attribute from response object: resp_obj.{}".format(top_query)
                    logger.log_error(err_msg)
                    raise exception.ParamsError(err_msg)

            if sub_query:
                if not isinstance(top_query_content, (dict, CaseInsensitiveDict, list)):
                    err_msg = u"Failed to extract data with delimiter!\n"
                    err_msg += u"response: {}\n".format(self.parsed_dict())
                    err_msg += u"regex: {}\n".format(field)
                    logger.log_error(err_msg)
                    raise exception.ParamsError(err_msg)

                # e.g. key: resp_headers_content_type, sub_query = "content-type"
                return utils.query_json(top_query_content, sub_query)
            else:
                # e.g. key: resp_status_code, resp_content
                return top_query_content

        except AttributeError:
            err_msg = u"Failed to extract value from response!\n"
            err_msg += u"response: {}\n".format(self.parsed_dict())
            err_msg += u"extract field: {}\n".format(field)
            logger.log_error(err_msg)

            raise exception.ParamsError(err_msg)


    def extract_response(self, extractors):
        """ extract value from requests.Response and store in OrderedDict.
        @param (list) extractors
            [
                {"resp_status_code": "status_code"},
                {"resp_headers_content_type": "headers.content-type"},
                {"resp_content": "content"},
                {"resp_content_person_first_name": "content.person.name.first_name"}
            ]
        @return (OrderDict) variable binds ordered dict
        """
        if not extractors:
            return {}

        logger.log_info("start to extract from response object.")
        extracted_variables_mapping = OrderedDict()
        extract_binds_order_dict = utils.convert_to_order_dict(extractors)

        for key, field in extract_binds_order_dict.items():
            if not isinstance(field, basestring):
                raise exception.ParamsError("invalid extractors in testcase!")
            result = self.extract_field(field)
            extracted_variables_mapping[key] = result
            if not (isinstance(result, bool) or bool(result)):  # False 可以return
                err_msg = u"extract data with delimiter can be None!\n"
                err_msg += u"response: {}\n".format(self.parsed_dict())
                err_msg += u"regex: {}\n".format(field)
                logger.log_error(err_msg)
                raise exception.ParamsError(err_msg)
        return extracted_variables_mapping
