from httprunner.client import HttpSession
from httprunner import logger
from requests_toolbelt import MultipartEncoder
from debugtalk import boundary
import json
from config import Env


class YDHHttpSession(HttpSession):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

    def request(self, method, url, name=None, **kwargs):
        #print(kwargs)
        if kwargs.get("headers",""):
            if "multipart/form-data" in kwargs.get("headers").get("content-type",""):
                data = kwargs["data"]
                kwargs["data"] = MultipartEncoder(fields=data,boundary=boundary)

        if kwargs.get("params",""):
            params = kwargs.get("params","")
            for key,value in params.items():
                if isinstance(value,list):
                    if all(isinstance(i,dict) for i in value):
                        params[key]=json.dumps(value)

        #替换base_url为目标环境的IP---例如url: https://api.dinghuo123.com/v2/goods/goods_list为https://192.168.1.200/v2/goods/goods_list
        if Env.current_env != 'production':
            base_url = url.split('//')[1].split('/')[0]
            url_actual = url.replace(base_url, Env.current_env_name_host_map[base_url])
            logger.log_debug('base url:{},--------- replaces with actual ip: {}'.format(base_url,url_actual))
            response = super().request(method, url_actual, name, **kwargs)
        else:
            response = super().request(method, url, name, **kwargs)

        if isinstance(self.meta_data["request_body"],MultipartEncoder):
            self.meta_data["request_body"] = str(self.meta_data["request_body"])

        return response