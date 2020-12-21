import json
import os
import sys
from pathlib import Path
import argparse
from .util import Util
from pprint import pprint
class LambdaDeploy:
    def __init__(self,params):
        self.params = params
        self.basepath = Path(os.getcwd()) / self.params['location']
        self.abspath = os.path.abspath(self.basepath)
        if sys.platform == "win32":
            self.abspath= self.abspath.replace('\\','/')
        self.util = Util(self.basepath,self.abspath)

        
        self.rc = self.util.get_rc(params['config'])
    def main(self):
        if self.params['action']=='init':
            self.init()
        else:
            if self.rc:
                if self.params['action']=='clean':
                    self.clean()
                elif self.params['action']=='build':
                    self.build()
                elif self.params['action']=='deploy':
                    pprint(self.rc, indent=4)
                    inp = input("Are you sure you want to deploy? y/N")
                    if(inp == "y"):
                        self.clean()
                        self.build()
                        self.deploy()
                elif self.params['action']=='delete':
                    self.delete()
                elif self.params['action'] == 'run-local':
                    self.run_local()
            else:
                print(".lmbrc configuration does not exist. You must initialize first.")

    def init(self):
        self.util.create_app()
    def clean(self):
        try:
            os.remove('{}/archive.zip'.format(self.abspath))
        except FileNotFoundError:
            pass
        finally:
            print("Clean Completed")
        

    def build(self):
        excludes = ""
        for x in self.rc["LambdaIgnores"]:
            excludes+="--exclude=" + x + " "
        os.system('zip -j -r9 {path}/archive.zip {path} {excludes}'.format(path=self.basepath, excludes=excludes))

    def deploy(self):
        env='Variables={'
        for k,v in self.rc["Environment"].items():
            env+=k + '=' + v + ','
        env = env[:-1]
        env +='}'
        res = os.system('aws lambda update-function-code --function-name {} --zip-file fileb://{}/archive.zip'.format(self.rc["FunctionName"],self.abspath))
        if res!=0:
            os.system('aws lambda create-function --function-name {} --memory-size {} --description "{}" --runtime {} --role {} --handler {} --zip-file fileb://{}/archive.zip --environment "{}"'.format(self.rc["FunctionName"],self.rc["Memory"],self.rc["Description"],self.rc["Runtime"],self.rc["Role"],self.rc["Handler"],self.abspath,env))
        os.system('aws lambda update-function-configuration --function-name {} --memory-size {} --description "{}" --environment "{}"'.format(self.rc["FunctionName"],self.rc["Memory"],self.rc["Description"],env))
    def delete(self):
        #os.system('aws lambda delete-function --function-name "{}"'.format(self.rc["FunctionName"]))
        pass
    def run_local(self):
        event = self.util.get_event(self.params["event"])
        if event == None:
            event = {}
        handler = self.rc['Handler']
        handler = handler.split('.')
        if self.rc['Runtime'].lower().startswith('node'):
            os.system("node -e \"require(\'{path}/{filename}\').{functionName}({event},{{}})\"".format(path=self.abspath,filename=handler[0],functionName=handler[1],event=event))
        else:
            os.system("python -c 'import sys; sys.path.append(\"{path}\"); import {filename}; {filename}.{functionName}({event},{{}})'".format(path=self.abspath,filename=handler[0],functionName=handler[1],event=event))

def parseArgs():
    parser = argparse.ArgumentParser(description='Script for running and deploying Aws Lambda Functions')
    parser.add_argument('init',nargs="?")
    parser.add_argument('clean',nargs="?")
    parser.add_argument('build',nargs="?")
    parser.add_argument('deploy',nargs="?")
    parser.add_argument('delete',nargs="?")
    parser.add_argument('run-local',nargs="?")
    parser.add_argument('-v', '--version', action='version',
                    version='%(prog)s {version}'.format(version='0.0.1'))
    parser.add_argument('-p', '--path')
    parser.add_argument('-e', '--event')
    parser.add_argument('-c', '--config')
    args = parser.parse_args()
    try:
        action = sys.argv[1]
        if action != "init" and action!="clean" and action!="build" and action!="deploy" and action!="run-local" and action!="delete":
            parser.print_help()
            exit()
        else:
            parsed = {
                "action":action,
                "location":"",
                "event":None,
                "config":None
            }
            if args.path:
                parsed['location'] = args.path
            if args.config:
                parsed['config'] = args.config
            if args.event:
                parsed['event'] = args.event
            return parsed
    except Exception as e:
        parser.print_help()
        exit()

def main():
    args = parseArgs()
    ld = LambdaDeploy(args)
    ld.main()
if __name__ == "__main__":
    main()