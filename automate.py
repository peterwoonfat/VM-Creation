import configparser
import os
import sys
import subprocess
import json
import re
from datetime import datetime
import azureFunctions as azFuncs
import gcpFunctions as gcpFuncs



if __name__ == "__main__":
    # check if Azure.conf and GCP.conf exist
    if os.path.exists('./Azure.conf') == False or os.path.exists('./GCP.conf') == False:
        print('Missing required .conf files. Closing program...')
        sys.exit(-1)

    # get the current datetime stamp
    current_time = datetime.now()
    time_stamp = current_time.timestamp()
    date_time = datetime.fromtimestamp(time_stamp)
    str_date_time = date_time.strftime('%d-%m-%Y;%H;%M;%S')
    print("Date time: " + str_date_time)

    # create logs directory to store logs if it doesn't already exist
    if os.path.exists('logs') == False:
        os.mkdir('logs')

    # copy Azure.conf and GCP.conf to another .conf files with datetime stamps appended after the org name
    azure_filename = 'Azure' + str_date_time + '.txt'
    azure_filepath = os.path.join('./logs', azure_filename)
    with open('Azure.conf', 'r') as f1, open(azure_filepath, 'w') as f2:
        for line in f1:
            f2.write(line)
    gcp_filename = 'GCP' + str_date_time + '.txt'
    gcp_filepath = os.path.join('./logs', gcp_filename)
    with open('GCP.conf', 'r') as f1, open(gcp_filepath, 'w') as f2:
        for line in f1:
            f2.write(line)

    # write to text file to log creation of VMs
    log_filename = 'VMCreation_' + str_date_time + '.txt'
    log_filepath = os.path.join('./logs', log_filename)
    doc_file = open(log_filepath, 'w')
    system_admin_name = input('Enter system admin name: ')
    doc_file.write('Date Stamp: ' + str_date_time + '\n')
    doc_file.write('System Admin Name: ' + system_admin_name + '\n')

    azure_config = configparser.ConfigParser()
    gcp_config = configparser.ConfigParser()

    # log in to Azure account
    azFuncs.azureLogin()
    # read the Azure configuration files with specifications for the creation of the VMs
    azure_vm_configs = azFuncs.parseAzureConfig(azure_config)
    # call function to run CLI commands to create VMs
    print('Provisioning Azure VMs...')
    azFuncs.provisionAzureVMs(azure_vm_configs, doc_file)
    print('Finished provisioning Azure VMs.')

    # log in to GCP 
    gcpFuncs.gcpLogin()
    # read the GCP configuration files with specifications for the creation of the VMs
    gcp_vm_configs = gcpFuncs.parseGCPConfig(gcp_config)
    # # provision VMs using specificatios parsed from GCP.conf
    print('Provisioning GCP VMs...')
    gcpFuncs.provisionGCPVMs(gcp_vm_configs, doc_file)
    print('Finished provisioning GCP VMs.')

    # delete Azure and GCP VMs
    azFuncs.deleteAzureVMs()
    gcpFuncs.deleteGCPVMs()

    # close logging file
    doc_file.close()