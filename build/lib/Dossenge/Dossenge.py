import sys
import os
import toml

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

    

def equal(x, y, roundnum=3):
    diff = abs(x - y)
    return diff < 10**-roundnum

def chicken_rabbit(head,foot):
    chicken = head
    rabbit = 0
    solutions = []
    for i in range(1,head+2):
        if chicken*2+rabbit*4 == foot:
            solutions.append((chicken, rabbit))
        chicken -= 1
        rabbit += 1
    return solutions

def dossenge():
    # # # with open(file,'r') as f:
        # # # equal = f.readline(0)
        # # # cr = f.readline(1)
        # more
    # # # with open(current_dir+char+'config.toml','r') as f:
        # # # data = toml.load(f)
    # # # file = f'{data["path"]}/{data["lang"]}{data["ext"]}'
    equal = '判断两数是否相等'
    cr = '解决鸡兔同笼问题'
    try:
        if sys.argv[1]=='equal':
            print(equal(eval(sys.argv[2]),eval(sys.argv[3]),roundnum=eval(sys.argv[4])))
        elif sys.argv[1]=='cr':
            print(chicken_rabbit(eval(sys.argv[2]),eval(sys.argv[3])))
        else:
            print('Usage:')
            print(f'equal : {equal}')
            print(f'cr : {cr}')
    except:
        print('Usage:')
        print(f'equal : {equal}')
        print(f'cr : {cr}')

def fibonacci(number):
    if number < 0:
        raise ValueError('number cannot be < 0')
    elif number == 0:
        return 0
    elif number == 1:
        return 1
    else:
        return fibonacci(number-1)+fibonacci(number-2)

if __name__ == '__main__':
    pass