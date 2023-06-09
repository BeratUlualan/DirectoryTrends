#!/usr/bin/env python3

# MIT License
#
# Copyright (c) 2022 Qumulo
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
# DirectoryTrends.py
#

import sys
import os
from os import path
import time
import json
import functools
import platform

import dominate
from dominate.tags import table, tr, td, th, span

#  Import local Python libraries
# from operators import SMBShares, NFSExports, DirQuotas, Replications
from utils.Logger import Logger
from utils import ArgParsing
from utils import Authentication
from utils.Email import Email
from utils.ConfigFileParser import ConfigFileParser


# Define the name of the Program, Description, and Version.
progname = "DirectoryTrends"
progdesc = "Qumulo DirectoryTrends - Show the capacity changes of the defined directories daily and weekly basis."
progvers = "6.1.0"

logger = Logger()

def check_capacity(args, rc):
    CONFIG_FILE_PATH = args.config_file
    with open(CONFIG_FILE_PATH, "r") as configFile:
        config = json.load(configFile)
        directories = config["directories"]["dir_paths"]
        dir_capacity_usages = []
        
        for directory in directories:
            dir_aggregates = rc.fs.read_dir_aggregates(path=directory, max_depth=config["directories"]["max_depth"], recursive=True)
            for dir_aggregate in dir_aggregates:
                usages = {}
                path = rc.fs.get_file_attr(path=directory)["path"]
                usages["data"] = round(int(dir_aggregate["total_data"]) / 10 ** 9, 2)
                usages["metadata"] = round(int(dir_aggregate["total_meta"]) / 10 ** 9, 2)
                usages["directory"] = path
                dir_capacity_usages.append(usages) 
    
    with open("./config/previous_dir_usages.json", "r") as previousUsages:
        previous_dir_usages = json.load(previousUsages)
        
        doc = dominate.document(title='Qumulo Storage Report')

        with doc:
            with table():
                with tr():
                    with th(style="text-align:left"):
                        span("Directory")
                    with th(style="text-align:center"):
                        span("Data Change")
                    with th(style="text-align:center"):
                        span("Metadata Change")
                for dir_capacity_usage in dir_capacity_usages:
                    with tr():
                        directory = dir_capacity_usage["directory"]

                        if directory in previous_dir_usages:
                            data_change = round(dir_capacity_usage["data"] - previous_dir_usages[directory]["data"], 2)
                            if data_change > 0:
                                data_change = "+" + str(data_change) + " GB"
                            else:
                                data_change = str(data_change) + " GB"
                                
                            metadata_change = round(dir_capacity_usage["metadata"] - previous_dir_usages[directory]["metadata"], 2)
                            if metadata_change > 0:
                                metadata_change = "+" + str(metadata_change) + " GB"
                            else:
                                metadata_change = str(metadata_change) + " GB"
                                
                            previous_dir_usages[directory]["data"] = dir_capacity_usage["data"]
                            previous_dir_usages[directory]["metadata"] = dir_capacity_usage["metadata"]
                            
                            with td(style="text-align:left"):
                                span(directory)
                            with td(style="text-align:center"):
                                span(data_change) 
                            with td(style="text-align:center"):
                                span(metadata_change)
                
                        else:
                            usages = {}
                            usages["data"] = dir_capacity_usage["data"]
                            usages["metadata"] = dir_capacity_usage["metadata"]
                            previous_dir_usages[directory] = usages
                        
                            with td(style="text-align:left"):
                                span(directory)
                            with td(style="text-align:center"):
                                span("New directory") 
                            with td(style="text-align:center"):
                                span("New directory")      
                
    with open("./config/previous_dir_usages.json", "w") as previousUsagesFile:
        json.dump(previous_dir_usages, previousUsagesFile, indent=4)
    
    return doc

def main():    
    args = ArgParsing.main()
    
    if args.config_file:
        # Get the configuration file so that we can figure out how often to run the program
        config = ConfigFileParser(args.config_file, logger)
        
        # Validate the config
        try:
            config.validate()
            configs = config.get_configs()
                
            try:
                if args.cluster:
                    rc = Authentication.login_with_args(args)
                else:
                    rc = Authentication.login_with_configs(configs)
            except:
                sys.exit(1)
                
            try:
                cluster = rc.cluster.get_cluster_conf()["cluster_name"]
                email_from = configs['email']['from']
                email_to = configs['email']['to']
                email_login = configs['email']['login']
                email_password = configs['email']['password']
                email_server = configs['email']['server']
                email_port = configs['email']['port']
                email_use = configs['email']['use']
            except:
                sys.exit(1)
            
        except Exception as err:
            logger.error(f'Configuration would not validate, error is {err}')
            sys.exit(1)
            
    else:
        if args.cluster:
            rc = Authentication.login_with_args(args)
        else:
            logger.error(f"No cluster was defined.")
            sys.exit(1)
            
        try:
            cluster = rc.cluster.get_cluster_conf()["cluster_name"]
            if args.email:
                email_from = args.email.email_from
                email_to = args.email.email_to
                email_login = args.email.login
                email_password = args.email.password
                email_server = args.email.server
                email_port = args.email.port
                email_use = args.email.use
        except:
            sys.exit(1)

    capacity_changes = check_capacity(args, rc)

    email = Email(logger= logger)

    # Build a subject and message line
    subject = f'Latest directory trend report for "{cluster}"'
    message = capacity_changes

    email.send_mail(email_from, email_to, subject, message,
                    email_server, email_port, email_login,
                    email_password, email_use)

        
if __name__ == "__main__":
    main()
