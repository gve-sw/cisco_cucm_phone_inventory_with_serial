""" Copyright (c) 2020 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
           https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied. 
"""
import json
import requests
import time
import functions


# Model Number: CP-8865
# Hardware Revision: V01

# Model Number: CP-8945
# Hardware Revision: 4

# from https://www.cisco.com/c/en/us/support/docs/smb/collaboration-endpoints/cisco-ip-phone-8800-series/1534-Conversion-enterprise-phone-to-mmp-or-vice-versa.html#traditional-licensing
ELIGIBLE = [
    "CP-7811",
    "CP-7821",
    "CP-7841",
    "CP-7861",
    "CP-7832",
    "CP-8811",
    "CP-8841",
    "CP-8851",
    "CP-8861",
    "CP-8832",
    "CP-8845",
    "CP-8856",
]

SUPPORTED_MIN_HW_CHECK = {"CP-7821": "V03", "CP-7841": "V04", "CP-7861": "V03"}


def main():
    device_list = []

    # makes call to retrieve a list of devices with several attributes from the CUCM evironment
    # axl is for administrative details like phone name, location, model, product etc
    # risport of for realtimeservice like ip address

    list_of_devices_axl = functions.axl_request()
    list_of_devices_risport = functions.risport_request()

    deviceExtensionsDict = functions.getDevicesDN()

    # indexed_devices_axl = {}
    indexed_devices_risport = {}

    for index1, device_risport in enumerate(list_of_devices_risport):
        if device_risport["Status"] == "Registered":
            indexed_devices_risport[device_risport["Name"]] = device_risport

    # for index2, device_axl in enumerate(list_of_devices_axl):
    #    indexed_devices_axl[device_axl["name"]] = device_axl

    device_risport = {}

    for index1, device_axl in enumerate(list_of_devices_axl):
        device_name = device_axl["name"]
        device = {}
        if device_name[0:3] == "SEP":
            print("device created for ", device_name)

            device["name"] = device_name

            if device_name in deviceExtensionsDict.keys():
                device["extension"] = deviceExtensionsDict[device_name]
            else:
                device["extension"] = ""

            device["model"] = device_axl["model"]
            device["networkLocation"] = device_axl["networkLocation"]
            device["product"] = device_axl["product"]
            device["description"] = device_axl["description"]
            try:
                device["ownerUserName"] = device_axl["ownerUserName"]["value"]
            except:
                device["ownerUserName"] = ""
            device["locationName"] = device_axl["locationName"]
            device["callingSearchSpaceName"] = device_axl["callingSearchSpaceName"][
                "value"
            ]
            device["devicePoolName"] = device_axl["devicePoolName"]["value"]

            if device_name in indexed_devices_risport.keys():
                device_risport = indexed_devices_risport[device_name]

                device["ip_address"] = device_risport["IpAddress"]
                device["status"] = device_risport["Status"]

                if device["ip_address"] is None:
                    device["ip_address"] = "unassigned"
                    device["serial_number"] = "unavailable"
                    device["mac"] = "unavailable"
                    device["hardware_revision"] = "unavailable"
                    device["model_number"] = "unavailable"
                    device["mpp_eligible"] = "unavailable"
                else:
                    # calling function to retrieve serial number based on IP address (visiting the phone web page)
                    device_data = functions.get_scraped_phone_data(device["ip_address"])
                    device["mac"] = device_data[0]
                    device["serial_number"] = device_data[1]
                    device["hardware_revision"] = device_data[2]
                    device["model_number"] = device_data[3]
                    if device["model_number"] in ELIGIBLE:
                        device["mpp_eligible"] = "ELIGIBLE"
                        if device["model_number"] in SUPPORTED_MIN_HW_CHECK.keys():
                            if (
                                device["hardware_revision"]
                                < SUPPORTED_MIN_HW_CHECK[device["model_number"]]
                            ):
                                device["mpp_eligible"] = "NOT SUPPORTED"
                    else:
                        device["mpp_eligible"] = "NON ELIGIBLE"
            else:
                device["ip_address"] = "unassigned"
                device["serial_number"] = "unavailable"
                device["mac"] = "unavailable"
                device["hardware_revision"] = "unavailable"
                device["model_number"] = "unavailable"
                device["mpp_eligible"] = "unavailable"

            device_list.append(device)

    return device_list


devices_list = main()
# print(devices_list)

f = open("inventory_w_serial.csv", "w+")
f.write(
    "Description,"
    + "Extension,"
    + "Owner UserID,"
    + "MAC Address,"
    + "Serial,"
    + "Product Type"
    + "\n"
)
for device in devices_list:
    f.write(
        device["description"]
        + ","
        + device["extension"]
        + ","
        + device["ownerUserName"]
        + ","
        + device["mac"]
        + ","
        + device["serial_number"]
        + ","
        + device["product"]
        + "\n"
    )
