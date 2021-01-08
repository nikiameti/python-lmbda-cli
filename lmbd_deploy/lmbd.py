import json
import os
import sys
from pathlib import Path
import argparse
from .util import Util
from pprint import pprint
import boto3
import zipfile
import botocore

class LambdaDeploy:
    def __init__(self,params):
        self.params = params
        self.basepath = Path(os.getcwd()) / self.params['location']
        self.abspath = os.path.abspath(self.basepath)
        if sys.platform == "win32":
            self.abspath= self.abspath.replace('\\','/')
        self.util = Util(self.basepath,self.abspath)
        
        self.rc = self.util.get_rc(params['config'])
        if self.rc != None:
            if self.rc["AwsAccessKey"]!="" and self.rc["AwsSecretKey"]!="":
                self.lambdaClient = boto3.client('lambda',aws_access_key_id=self.rc["AwsAccessKey"], aws_secret_access_key=self.rc["AwsSecretKey"])
            else:
                self.lambdaClient = boto3.client('lambda')
        else:
            self.lambdaClient = boto3.client('lambda')
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
        

    def build(self):
        zipf = zipfile.ZipFile(self.abspath + '/archive.zip', 'w', zipfile.ZIP_DEFLATED)
        for root, dirs, files in os.walk(self.abspath):
            for file in files:
                absname = os.path.join(root, file)
                arcname = absname[len(self.abspath) + 1:]
                if(file not in self.rc["LambdaIgnores"] and not file.lower().endswith(".pyc")):
                    zipf.write(absname, arcname)

    def deploy(self):
        self.update_lambda_function()
    def create_lambda_function(self):
        try:
            with open(self.abspath + "/archive.zip", 'rb') as file_data:
                archive = file_data.read()
            vpc = {}
            if self.rc["VpcConfig"]["VpcId"]:
                vpc = self.rc["VpcConfig"]
            response = self.lambdaClient.create_function(
                FunctionName=self.rc["FunctionName"],
                Runtime=self.rc["Runtime"],
                Role=self.rc["Role"],
                Handler=self.rc["Handler"],
                Code={
                    'ZipFile': archive},
                Description=self.rc["Description"],
                Timeout=self.rc["Timeout"],
                MemorySize=self.rc["Memory"],
                Publish=True,
                Environment={
                    'Variables': self.rc["Environment"]
                },
                VpcConfig=vpc
            )
        except Exception as e:
            print(e)
    def update_lambda_function(self):
        try:
            with open(self.abspath + "/archive.zip", 'rb') as file_data:
                archive = file_data.read()
            response = self.lambdaClient.update_function_code(
                FunctionName=self.rc["FunctionName"],
                ZipFile=archive
            )

            vpc = {}
            if self.rc["VpcConfig"]["VpcId"]:
                vpc = self.rc["VpcConfig"]
            response = self.lambdaClient.update_function_configuration(
                FunctionName=self.rc["FunctionName"],
                Runtime=self.rc["Runtime"],
                Role=self.rc["Role"],
                Handler=self.rc["Handler"],
                Description=self.rc["Description"],
                Timeout=self.rc["Timeout"],
                MemorySize=self.rc["Memory"],
                Environment={
                    'Variables': self.rc["Environment"]
                },
                VpcConfig=vpc
            )
            pprint(response)
        except Exception as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                response = self.create_lambda_function()
                pprint(response)
            else:
                raise e
    def delete(self):
        try:
            response = self.lambdaClient.delete_function(
                FunctionName=self.rc["FunctionName"]
            )
            pprint(response)
        except Exception as e:
            pprint(e)
            pass
    def run_local(self):
        event = self.util.get_event(self.params["event"])
        if event == None:
            event = {}
        handler = self.rc['Handler']
        handler = handler.split('.')
        if self.rc['Runtime'].lower().startswith('node'):
            str = "node -e \"require(\'{path}/{filename}\').{functionName}({event},{{}})\"".format(path=self.abspath,filename=handler[0],functionName=handler[1],event=event)
            os.system(str)
        else:
            os.system("python -c \"import sys; sys.path.append(\'{path}\'); import {filename}; {filename}.{functionName}({event},{{}})\"".format(path=self.abspath,filename=handler[0],functionName=handler[1],event=event))

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
