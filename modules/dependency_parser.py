#!/usr/local/bin/python3.6

import copy
import collections
import os
import pygraphviz
from dag import DAG,DAGValidationError
from httprunner import exception, logger
from httprunner.testcase import TestcaseLoader




def load_test_file(edit_dict_case):
    """ load testset file, get testset data structure.
    @param file_path: absolute valid testset file path
    @return testset dict
        {
            "name": "desc1",
            "config": {},
            "api": {},
            "testcases": [testcase11, testcase12]
        }
    """
    testset = {
        "name": "",
        "config": {
            "path": os.getcwd()+"/debugtalk",
            "output": []
        },
        "api": {},

        "testcases": []
    }
    tests_list = edit_dict_case

    for item in tests_list:
        if not isinstance(item, dict) or len(item) != 1:
            raise exception.FileFormatError("Testcase format error: {}".format(item))

        key, test_block = item.popitem()
        if not isinstance(test_block, dict):
            raise exception.FileFormatError("Testcase format error: {}".format(item))

        if key == "config":
            testset["config"].update(test_block)
            testset["name"] = test_block.get("name", "")

        elif key == "test":
            if "api" in test_block:
                ref_call = test_block["api"]
                def_block = TestcaseLoader._get_block_by_name(ref_call, "api")
                TestcaseLoader._override_block(def_block, test_block)
                testset["testcases"].append(test_block)
            elif "suite" in test_block:
                ref_call = test_block["suite"]
                block = TestcaseLoader._get_block_by_name(ref_call, "suite")
                testset["testcases"].extend(block["testcases"])
            else:
                testset["testcases"].append(test_block)
            if "extract" in test_block:
                for i in test_block.get("extract"):
                    testset["config"]["output"].extend(i.keys())


        else:
            logger.log_warning(
                "unexpected block key: {}. block key should only be 'config' or 'test'.".format(key)
            )

    return testset



def load_test_dependency_map_by_path(path):

    """Get test_dependency_map by the specified path(Relative or Absolute path).
    Example:
        dict1,dict2 = load_test_dependency_map_by_path('../my_test')
        print('{},{}'.format(dict1,dict2))
        >> {'nested_para': [''], 'nested_5': [''], 'nested_1': ['nested_3']}, {'nested':'/Users/..../xxx.yml'}

    @param path    String. Relative or Absolute path is accepted.

    @return        List. Two dict in the list.
    """

    all_result = TestcaseLoader.load_testsets_by_path(path)
    logger.log_debug('{}'.format(all_result))

    testcase_dep_dict = collections.defaultdict(list)
    testcase_path_dict = collections.defaultdict(list)

    for result in all_result:

        testcase_name  =  result['testcases'][0].get('name', '')
        raw_testcase_dep   =  result['testcases'][0].get('dependent', '')
        testcase_path  = result['config'].get('path', '')

        if not testcase_dep_dict[testcase_name]:
            if not isinstance(raw_testcase_dep, (list, set)):
                testcase_list = raw_testcase_dep.split(',')
                testcase_dep_dict[testcase_name].extend(testcase_list)
            else:
                testcase_dep_dict[testcase_name].extend(raw_testcase_dep)
        else:
            logger.log_warning("Duplicate testcase found!! Please check-->"\
                             "testcase_name:{},testcase_path:{}".format(testcase_name,testcase_path))
        #    raise Exception("Duplicate testcase found!!")   #根据需要决定是否抛出异常

        testcase_path_dict[testcase_name] = testcase_path

    return testcase_dep_dict,testcase_path_dict



def _dfs(graph, path, paths=[]):
    """Get all dependent paths by the specified path.
    Example:
        graph ={'a': ['b'],'d':['e'],'c':['k','f','z'],'b':['y','c'],'y':['z'],'z':[''],'k':[''],'f':[''],'e':['a','b','c']}
        dep_paths = get_dep_paths_by_start_node(graph,['a'],paths=[])
        print(dep_paths)
        >>[['a', 'b', 'y', 'z', ''], ['a', 'b', 'c', 'k', ''], ['a', 'b', 'c', 'f', ''], ['a', 'b', 'c', 'z', '']]

    @param graph   Dict. This parameter requires a dict that shows the key-value mapping of each node,imagine it as a graph

    @param path    List. A list whose last element as the start node to recursively get its dependent paths.

    @param paths   List. A list to get its paths once the deep node first ends.

    @return        List. Return the list of all dependent paths starts from path.
    """

    datum = path[-1]
    if datum in graph:
        for val in graph[datum]:
            new_path = path + [val]
            paths = _dfs(graph, new_path, paths)
    else:
        paths += [path]

    return paths


def get_all_dep_paths_with_separator(dep_graph, separator = '/'):
    """Get all dependent paths of the dep_graph.
    Example:
        graph ={'a': ['b'],'d':['e'],'c':['k','f','z'],'b':['y','c'],'y':['z'],'z':[''],'k':[''],'f':[''],'e':['a','b','c']}
        dep_paths = get_all_dep_paths(graph)
        print(dep_paths)
        >>['/a/b/y/z', '/a/b/c/k', ...]

    @param dep_graph   Dict. This parameter requires a dict that shows the key-value mapping of each node,imagine it as a graph

    @param separator   String. Define the separator and shows the dependency between nodes.

    @return            List.  Return the list of all dependent paths of dep_graph.
    """

    validate_dependency_debug(convert_to_std_graph(dep_graph))

    original_list = []
    for key in dep_graph.keys():
        paths = _dfs(dep_graph, [key],[])
        original_list.append(paths)

    # Turn
    # [[['a', 'b', 'y', 'z', ''], ['a', 'b', 'c', 'k', '']],...]
    # into
    # ['/a/b/y/z', '/a/b/c/k']
    # separator is defined by parameter, default is '/'.
    all_dep_path_list = []
    for each_original in original_list:
        for each_output in each_original:
            str_dep = separator + separator.join(each_output)
            all_dep_path_list.append(str_dep.rstrip(separator))

    l1 = len(list(set(all_dep_path_list)))
    l2 = len(all_dep_path_list)
    if l1 < l2:
        logger.log_warning('Found duplicates!!   len:  set->{}, list->{}'.format(l1,l2))

    count_dict = collections.Counter(all_dep_path_list)
    for key,value in count_dict.items():
        if value > 1:
            logger.log_warning('Duplicate:length of ( {} )is {}'.format(key,value))

    return all_dep_path_list



def extract_full_dep_paths(all_dep_paths):
    """Extract the full dependent paths from all_dep_path.
    Example:
        all_paths = ['/a/b/y/z', '/a/b','/y' ]
        full_dep_paths = extract_full_dep_paths(all_paths)
        print(full_dep_paths)
        >>['/a/b/y/z']

    @param all_dep_paths   List. All paths including sub-path and full path from the dependency graph.

    @return               List. Return the full dependency path of all_dep_path.
    """

    dup_list = copy.copy(all_dep_paths)
    full_dep_path_list = copy.copy(all_dep_paths)

    for each in dup_list:
        all_dep_paths.remove(each)
        for each_str in all_dep_paths:
            if each in each_str:
                if each in full_dep_path_list:
                    full_dep_path_list.remove(each)

        all_dep_paths.append(each)

    return full_dep_path_list


def get_std_graphs_dict_from_full_path(valid_full_testcase_dependency,seperator='/'):
    assert len(valid_full_testcase_dependency) >= 1, 'valid full path is empty!!'
    node = set()
    for dep_path in valid_full_testcase_dependency:
        root_node = dep_path.split(seperator)[1]
        node.add(root_node)

    std_graph = {}
    for each in node:
        std_graphs = collections.defaultdict(set)
        for dep_path in valid_full_testcase_dependency:
            node_list = dep_path.split(seperator)[1:]
            first_node = node_list[0]
            if each == first_node:

                length = len(node_list)
                for i in range(length):
                    if i == length - 1:
                        std_graphs[node_list[i]] = set()
                    else:
                        std_graphs[node_list[i]].add(node_list[i+1])

        std_graph[each] = std_graphs

    return std_graph


def get_std_graph_from_dep_path(dep_path, seperator='/'):
    assert dep_path, 'Empty dep_path!!'
    graph = collections.defaultdict(set)
    node_list = dep_path.split(seperator)[1:]
    length = len(node_list)
    assert length != 0, 'dep_path length is 0!!!'
    for i in range(length):
        if i == length - 1 :
            graph[node_list[i]] = set()
        else:
            graph[node_list[i]] = set([node_list[i+1]])

    return graph


def convert_to_std_graph(graph):
    assert graph, 'Empty graph'
    std_graph = {}
    for key,value in graph.items():
        if value == ['']:
            std_graph[key] = set()
        else:
            std_graph[key] = set(value)

    return std_graph


def convert_to_reversed_std_graph(graph):
    assert graph, 'Empty graph'
    std_reversed_list_graph = collections.defaultdict(set)

    std_graph = convert_to_std_graph(graph)
    for key,value in std_graph.items():
        for v in value:
            std_reversed_list_graph[v].add(key)

    return std_reversed_list_graph


def validate_dependency(graph):
    assert graph, "Graph is empty,please check!!"
    dag = DAG()
    is_valid, msg = dag.validate(graph)
    assert is_valid, msg


def validate_dependency_debug(graph):
    assert graph, "Graph is empty,please check!!"
    #convert_to_std_list_graph(graph)
    #dag.from_dict(graph)
    #noinspection PyBroadException
    is_valid = False
    dag = DAG()
    try:
        for key, value in graph.items():
            dag.add_node(key)

        for key, value in graph.items():
            for v in value:
                if v is not '':
                    dag.add_edge(key, v)
    except KeyError as e:
        logger.log_error("KeyError while adding to dag, msg is {}".format(e))
    except DAGValidationError as e:
        logger.log_error("DAGValidationError while adding to dag, msg is {},please check dependent relationship".format(e))
    except Exception as e:
        logger.log_error("Exception while adding to dag, msg is {}".format(e))
    else:
        is_valid = True

    assert is_valid, "===> key(testcase):{},value(dependent):{}".format(key,value)


def save_graph(graph,file_path):
    A = pygraphviz.AGraph(graph, directed=True, strict=True)
    #A.write('foo.dot')
    A.layout('dot')  # layout with dot
    A.draw(file_path)  # write to file



if __name__ == '__main__':

    graph = {
             'a': ['b'],
             'd': ['e'],
             'c': ['k', 'f', 'z'],
             'b': ['y', 'c'],
             'y': ['z'],
             'z': [''],
             'k': [''],
             'f': [''],
             'e': ['a', 'b', 'c']
             }

    all_dep_paths = get_all_dep_paths_with_separator(graph)
    full_dep_paths = extract_full_dep_paths(all_dep_paths)
    print(full_dep_paths)

    test_dep_dict,test_path_dict = load_test_dependency_map_by_path("testcase_files")

    yml_dep = get_all_dep_paths_with_separator(test_dep_dict,'/')
    full_yml_dep = extract_full_dep_paths(yml_dep)
    print(yml_dep)
    print(full_yml_dep)



