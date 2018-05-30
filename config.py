# -*- coding: utf-8 -*-
import configparser
import os
import json

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

conf_parser = configparser.ConfigParser()
with open(os.path.join(ROOT_DIR, 'conf', 'setting.ini'), 'r') as cfg:
    conf_parser.read_file(cfg)


class Config(object):

    redis_host = conf_parser.get('Redis', 'redis_host')
    redis_port = conf_parser.get('Redis', 'redis_port')
    redis_db   = conf_parser.get('Redis', 'redis_db')
    testcase_root_path = conf_parser.get('Testcase', 'testcase_root_path')
    testcase_files_path = conf_parser.get('Testcase', 'testcase_files_path')
    testcase_dep_parse_dir = conf_parser.get('Testcase', 'testcase_dep_parse_dir')

    testcase_output_templates_path = conf_parser.get('Testcase', 'testcase_output_templates_path')

    resource_path = os.path.join(ROOT_DIR, conf_parser.get("Resource", "resource_path"))

    debug_output_enable  = int(conf_parser.get("Debug", "debug_output_enable"))
    debug_root_path      = conf_parser.get("Debug", "debug_root_path")
    return_json_path     = conf_parser.get("Debug", "return_json_path")
    dependency_pic_path  = conf_parser.get("Debug", "dependency_pic_path")




class Environment(object):
    __instance = None

    def __init__(self, env=None):
        self.current_env_name_host_map = {}
        self.all_env_name_host_map = {}
        self.current_env = env

        self.conf_env_parser = configparser.ConfigParser()
        with open(os.path.join(ROOT_DIR, 'conf', 'environment.ini'), 'r') as cfg_env:
            self.conf_env_parser.read_file(cfg_env)
        self.target_env_list = self.conf_env_parser.get('target_env', 'target').split(',')

    def load_env(self,env):
        if env != 'production':
            name_host_list = self.conf_env_parser.items(env)
            for name_host in name_host_list:
                self.current_env_name_host_map[name_host[0]] = name_host[1]
        else:
            assert env == 'production', "Not the expected env in one of [production,develp,release,master,gray] "

        self.current_env = env

    def init_require_envs(self, env_list):
        for target_env in env_list:
            if target_env == 'production':
                continue
            target_env_ini = target_env + '.ini'
            with open(os.path.join(ROOT_DIR, 'conf', target_env_ini), 'r') as cfg_f:
                self.conf_env_parser.read_file(cfg_f)

    def load_embeded_envs(self, env_list):
        #复合嵌套字典，视情况使用，默认不用
        for env in env_list:
            self.all_env_name_host_map[env] = {}
            if env != 'production':
                name_host_list = self.conf_env_parser.items(env)
                for name_host in name_host_list:
                    self.all_env_name_host_map[env][name_host[0]] = name_host[1]

    def reload_env(self, env):
        self.load_env(env)

    def __new__(cls,*args, **kwargs):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls,*args, **kwargs)
        return cls.__instance


Env = Environment()

if __name__ == '__main__':
    Environment = Environment()
    print(Environment.current_env)
    print(Env.current_env)
    Env.load_env('production')
    print(Env.current_env)
    print(Environment.current_env)


