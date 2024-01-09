import configparser
import os
import sys
import subprocess
import json
import re
from datetime import datetime


# function valides VM names (ex. azure01 and gcp01)
def checkValidVMNames(org, vm_list):
    # check if VMs are named properly and there are at max 10
    if len(vm_list) > 10:
        print('Error: Can only create max 10 VMs. The config file contains ' + len(vm_list))
        sys.exit(-1)
    vm_count = 1
    for vm in vm_list:
        vm_name = None
        if vm_count < 10:
            vm_name = org + '0' + str(vm_count)
        else:
            vm_name = org + str(vm_count)
        vm_count += 1
        if vm != vm_name:
            print('Error: Invalid ' + org + ' VM name \'' + vm + '\'')
            vm_count -= 1
    return vm_count


# function documents the provisioning of an Azure VM in a log file
def documentVMProvision(doc_file, vm, org):
    doc_file.write('Provisioned ' + org + ' VM:\n')
    doc_file.write('\tName: ' + vm['name'] + '\n')
    if (vm.get('project') != None):
        doc_file.write('\tProject: ' + vm['project'] + '\n')
    doc_file.write('\tPurpose: ' + vm['purpose'] + '\n')
    doc_file.write('\tTeam: ' + vm['team'] + '\n')
    doc_file.write('\tOS: ' + vm['os'] + '\n')
    if org == 'Azure':
        # get relevant info pertaining to the VM
        cmd = ['az', 'vm', 'show', '--resource-group', vm['resource-group'], '--name', vm['name']]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, error = process.communicate()
        relevant_info = json.loads(output.decode('utf-8'))
        doc_file.write('\tRelevant Information: ' + str(relevant_info) + '\n')
        # get VM status
        cmd2 = ['az', 'vm', 'show', '-d', '--resource-group', vm['resource-group'], '--name', vm['name'], '--query', 'powerState']
        print('> ' + ' '.join(cmd))
        process2 = subprocess.Popen(cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output2, error2 = process2.communicate()
        status = json.loads(output2)
        doc_file.write('\tStatus: ' + str(status) + '\n')
    elif org == 'GCP':
        # get relevant info pertaining to the VM
        print(f'> gcloud compute instances describe {vm["name"]} --zone={vm["zone"]} --format=json')
        relevant_info = json.loads(os.popen(f'gcloud compute instances describe {vm["name"]} --format=json').read())
        doc_file.write('\tRelevant Information: ' + str(relevant_info) + '\n')
        # get VM status
        status = os.popen(f'gcloud compute instances describe {vm["name"]} --zone={vm["zone"]} --format=value(status)').read()
        doc_file.write('\tStatus: ' + str(status) + '\n')
