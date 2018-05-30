import os, json


def extract_json(json_dic, path="content"):
    if isinstance(json_dic,dict):
        for key,value in json_dic.items():
            yield from extract_json(value, path = ".".join([path,key]))
    elif isinstance(json_dic,list):
        if json_dic:
            yield from extract_json(json_dic[0], ".".join([path, "0"]) )
    yield path+":"+json_dic.__class__.__name__


def read_file(path):
    for filename in os.listdir(path) :
        if not (filename.startswith(".") or filename.endswith(".py")):
            if os.path.isdir(os.path.join(path, filename)):
                read_file(os.path.join(path, filename))
            else:
                if filename.endswith("json"):
                    with open(os.path.join(path, filename),"r") as f:
                        print(os.path.join(path, filename))
                        check_list = list(extract_json(json.loads(f.read())))
                    with open(os.path.join(path, filename), "w") as f:
                        #print(check_list)

                        for i in sorted(check_list):
                            print(i)
                            f.write("""        - {{"check": "{}", "comparator": "check_type_and_exist", "expect": {}}}\n""".format(i.split(":")[0],i.split(":")[1]))

case_dic = {}
case_dic_back = {}
#read_file("./reports/debug_output")
