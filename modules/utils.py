#!/usr/local/bin/python3.6
# -*- coding: <encoding name> -*-
import os
import copy
from modules import dependency_parser


def setup_debug_return_json_path(old_path_list, new_path_list, src_dir):
    assert (old_path_list and new_path_list and src_dir), 'One of the input is empty!{}'.format(old_path_list,new_path_list,src_dir)

    test_dep_dict, test_path_dict = dependency_parser.load_test_dependency_map_by_path(src_dir)
    copy_test_path_dict = copy.copy(test_path_dict)

    old_path = ''
    for src_path in old_path_list:
        tmp_path = os.path.join(old_path, src_path)
        old_path = tmp_path

    new_path = ''
    for dst_path in new_path_list:
        tmp_path = os.path.join(new_path, dst_path)
        new_path = tmp_path

    for test, path in test_path_dict.items():
        assert test + '.yml' == os.path.basename(path), 'testcase_name and filename NOT consistent! test:{} != file_name:{}'.format(test, os.path.basename(path))
        new_filepath = os.path.dirname(path).replace(old_path, new_path)
        copy_test_path_dict[test] = new_filepath

        os.makedirs(new_filepath, exist_ok=True)

    return copy_test_path_dict