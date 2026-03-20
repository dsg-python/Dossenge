# Copyright (c) 2026 Dossenge
# Released under the MIT License (see LICENSE file for details)

import toml
import os
import sys
def get_module_installation_path(module_name):
    try:
        # 导入指定的模块
        module = __import__(module_name)
        # 获取模块的文件路径
        module_path = module.__file__
        # print(f"模块 {module_name} 的安装路径是: {module_path}")
        return module_path
    except ImportError:
        # print(f"模块 {module_name} 未安装或无法导入。")
        return None
    except AttributeError:
        # print(f"模块 {module_name} 没有 __file__ 属性，可能是一个内置模块。")
        return None

current_file_path = os.path.abspath(get_module_installation_path("Dossenge"))
current_dir = os.path.dirname(current_file_path)
os.chdir(current_dir)
namer = {'posix':'/','nt':'\\'}
char = namer[os.name]
# with open(current_dir+char+'config.toml','r') as f:
#     data = toml.load(f)

class String():
    def __init__(self,value=None,file=None):
        if not file == None:
            self.file = file
            with open(file,'r') as f:
                self.value = f.readlines()
        elif not value == None:
            self.value = value
        else:
            raise SyntaxError('invalid syntax')

def countstr(st):
    output = {}
    for i in st:
        if i in output:
            output[i] += 1
        else:
            output[i] = 1
    return output

def save_add(filepath,string):
    with open(filepath,'a') as f:
        f.write(string)
    with open(filepath,'r') as f:
        content = f.readlines()
    return content