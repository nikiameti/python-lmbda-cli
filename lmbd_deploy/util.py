from os import path
import json
class Util:
    def __init__(self, basepath,abspath):
        self.basepath = basepath
        self.abspath = abspath

    def get_rc_template(self):
        return {
            "FunctionName":"",
            "Region":"",
            "Runtime":"",
            "Handler":"",
            "Role":"",
            "Memory":"",
            "Timeout":"",
            "Description":"",
            "Environment":{
                "DATABASE_URL":"TEST",
            },
            "LambdaIgnores":["*.DS_Store*", "script.sh","script.py","lambda_function.pyc",'.lmbdrc']
        }
    def get_rc(self,path):
        if path == None:
            path = ".lmbdrc"
        try:
            f = open(self.abspath + "/" + path,"r")
            data = json.loads(f.read())
            f.close()
            return data
        except:
            return None
    
    def get_event(self,location):
        try:
            f = open(self.abspath + "/" + location,"r")
            data = f.read()
            f.close()
            return data
        except:
            return location

    def create_app(self):
        if path.exists(self.abspath + '/.lmbdrc'):
            print(".lmbdrc file already exist. If you want to create from scratch please remove that file")
        else:
            rc = self.create_rc()
            try:
                filename = rc['Handler'].split('.')[0]
                function_name = rc['Handler'].split('.')[1]
                ext = ''
                if(rc["Runtime"].startswith('py')):
                    ext = '.py'
                    filename = filename + ext
                if(rc["Runtime"].startswith('node')):
                    ext = '.js'
                    filename = filename + ext
                if path.exists(self.abspath + '/' + filename):
                    pass
                else:
                    if ext == ".js":
                        self.create_node(filename,function_name)
                    else:
                        self.create_py(filename,function_name)
            except:
                pass
            


    def create_node(self,filename,function_name):
        f = open(self.abspath + "/" + filename,"w+")
        f.write("""exports.{} = async (event) => {{
    console.log('Hello from Lambda!')
    return {{
        statusCode: 200,
        body: "Hello World"
    }}
}};
""".format(function_name))
        f.close()

    def create_py(self,filename,function_name):
        f = open(self.abspath + "/" + filename,"w+")
        f.write("""def {}(event, context):
    print('Hello from Lambda!')
    return {{
        'statusCode': 200,
        'body': 'Hello from Lambda!'
    }}""".format(function_name))
        f.close()

    def create_rc(self):
        progList = ["","python3.8","nodejs12.x"]
        rc = self.get_rc_template()
        loop = True
        while(loop):
            l = int(input("(Required) Choose programming language:\n1:Python3.8\n2:NodeJs10.x\nEnter number: "))
            if(l not in [1,2]):
                print("Wrong input")
            else:
                rc["Runtime"] = progList[l]
                loop = False

        rc["FunctionName"] = input("(Required) Enter your function name: ")
        rc["Region"] = input("(Optional) Enter aws region: ")
        rc["Handler"] = input("(Optional) Enter handler ex (filename.lambda_handler): ")
        rc["Role"] = input("(Optional) Enter role arn: ")
        rc["Memory"] = int(input("(Optional) Enter memory: ") or 256)
        rc["Timeout"] = int(input("(Optional) Enter timeout (seconds): ") or 3)
        rc["Description"] = input("(Optional) Enter description: ")

        f = open(self.abspath + "/.lmbdrc","w+")
        f.write(json.dumps(rc,indent=4))
        f.close()
        return rc