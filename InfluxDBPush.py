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
# InfluxDBPush.py
#

# Standard Python libaries
import datetime
import sys
import os
from os import path
import time
import json
import functools
import platform

# InfluxDB libraries
from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS

#  Import local Python libraries
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

def write_data_points(config, write_api, path, capacity, data, metadata, dir_count, file_count, current_time):
    data_points = [
        Point("CapacityDetails")
        .tag("path", path)
        .field("capacity", capacity)
        .time(time=current_time),
        Point("CapacityDetails")
        .tag("path", path)
        .field("data_capacity", data)
        .time(time=current_time),
        Point("CapacityDetails")
        .tag("path", path)
        .field("metadata_capacity", metadata)
        .time(time=current_time),
        Point("CapacityDetails")
        .tag("path", path)
        .field("dir_count", dir_count)
        .time(time=current_time),
        Point("CapacityDetails")
        .tag("path", path)
        .field("file_count", file_count)
        .time(time=current_time)
    ]
    write_api.write(bucket=config["influxdb"]["bucket_name"], record=data_points)

def check_capacity(args, rc):
    CONFIG_FILE_PATH = args.config_file
    
    with open(CONFIG_FILE_PATH, "r") as configFile:
        config = json.load(configFile)
        directories = config["directories"]["dir_paths"]
        
        # Create an instance of the InfluxDB client
        influxdb_address = config["influxdb"]["address"]
        client = InfluxDBClient(
            url=f"http://{influxdb_address}:8086",
            token=config["influxdb"]["token"],
            org=config["influxdb"]["org_name"],
        )
        
        # Create a write API instance
        write_api = client.write_api()
        
        current_time = datetime.datetime.utcnow()
        
        for directory in directories:
            usages = {}
            top_dir_aggregates = rc.fs.read_dir_aggregates(path=directory)
            path = rc.fs.get_file_attr(path=directory)["path"]
            capacity = int(top_dir_aggregates["total_capacity"])
            data = int(top_dir_aggregates["total_data"])
            metadata = int(top_dir_aggregates["total_meta"])
            file_count = int(top_dir_aggregates["total_files"])
            dir_count = int(top_dir_aggregates["total_directories"])
            
            # Write the data point to InfluxDB
            write_data_points(config, write_api, path, capacity, data, metadata, dir_count, file_count, current_time)
            
            
            if config["directories"]["max_depth"] != 0:
                for file in top_dir_aggregates["files"]:
                    if file["type"] == "FS_FILE_TYPE_DIRECTORY":
                        path = rc.fs.get_file_attr(id_=file["id"])["path"]
                        capacity = int(file["capacity_usage"])
                        data = int(file["data_usage"])
                        metadata = int(file["meta_usage"])
                        file_count = int(file["num_files"])
                        dir_count = int(file["num_directories"])

                        # Write the data point to InfluxDB
                        write_data_points(config, write_api, path, capacity, data, metadata, dir_count, file_count, current_time)

            # Close the write API and InfluxDB client
    write_api.close()
    client.close()

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
                logger.info(f"Capacity details are being collected")
                check_capacity(args, rc)
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
            logger.info(f"Capacity details are being collected")
            check_capacity(args, rc)
        except:
            sys.exit(1)

        
if __name__ == "__main__":
    main()
    

