import configparser
import os
import sys
import subprocess
import json
import re
from datetime import datetime
from helperFunctions import checkValidVMNames, documentVMProvision


# function logs user into their Azure account
def azureLogin():
    # get user input for login credentials
    azure_username = input("Enter your Azure username: ")
    azure_password = input("Enter your Azure password: ")
    azure_tenant = input("Enter your Azure tenant (if applicable, or press enter to skip): ")
    # login to Azure using credentials or service principal
    if azure_tenant == '':
        print('> az login -u ' + azure_username + ' -p ' + azure_password + ' --output tsv')
        os.system('az login -u ' + azure_username + ' -p ' + azure_password + ' --output tsv')
    else:
        print('> login -u ' + azure_username + ' -p ' + azure_password + ' --tenant ' + azure_tenant + ' --output tsv')
        os.system('login -u ' + azure_username + ' -p ' + azure_password + ' --tenant ' + azure_tenant + ' --output tsv')
    print('Successfully logged in...\nParsing config files...')


# function reads from the Azure.conf file to get the configuration settings for the Azure VMs
def parseAzureConfig(config):
    # can only be max 10 VMs
    config.read('Azure.conf')
    azure_vms = config.sections()

    # call function to check for valid VM names in config file and count the number of VMs
    vm_count = checkValidVMNames('azure', azure_vms)
    
    # parse VM config settings and store them in a list of dicts
    # each dict has the settings for a single VM
    azure_vm_configs = []
    i = 1
    if vm_count > 1:
        for i in range(1, vm_count):
            vm_name = None
            if i < 10:
                vm_name = 'azure0' + str(i)
            else:
                vm_name = 'azure' + str(i)
            # check for required settings and if image is valid
            # any VMs with invalid settings will not be provisioned and the program will continue provisioning other valid VMs if applicable
            if config[vm_name].get('name') == None:
                print('Error creating ' + vm_name + '. No count property found for ' + vm_name)
            elif config[vm_name].get('resource-group') == None:
                print('Error creating ' + vm_name + '. No resource-group property found for ' + vm_name)
            elif checkVMNameTaken(config[vm_name]['resource-group'], config[vm_name]['name']):
                print('Error creating ' + vm_name + '. There is already a VM named ' + vm_name + ' in the resource group ' + config[vm_name]['resource-group'])
            elif config[vm_name].get('image') == None:
                print('Error creating ' + vm_name + '. No image property found for ' + vm_name)
            elif config[vm_name].get('location') == None:
                print('Error creating ' + vm_name + '. No location property found for ' + vm_name)
            elif config[vm_name].get('admin-username') == None:
                print('Error creating ' + vm_name + '. No admin-username property found for ' + vm_name)
            elif checkValidImage(config[vm_name]['image'], config[vm_name]['location']) == False:
                print('Error creating ' + vm_name + '. ' + config[vm_name]['image'] + ' is an invalid image.')
            else:
                config_settings = {}
                config_settings['purpose'] = config[vm_name]['purpose']
                config_settings['os'] = config[vm_name]['os']
                config_settings['name'] = config[vm_name]['name']
                config_settings['resource-group'] = config[vm_name]['resource-group']
                config_settings['team'] = config[vm_name]['team']
                config_settings['image'] = config[vm_name]['image']
                config_settings['location'] = config[vm_name]['location']
                config_settings['admin-username'] = config[vm_name]['admin-username']
                azure_vm_configs.append(config_settings)
                i += 1
    return azure_vm_configs


# function provisions Azure VM(s)
def provisionAzureVMs(configs, doc_file):
    # call other functions to provision necessary resources to provision a VM
    # need resource-group, name, image, public-ip-sku, admin-username
    createResourceGroups(configs)
    for vm in configs:
        # ask user for admin password for VM, loop until valid password given
        valid_pass = False
        admin_password = None
        while valid_pass == False:
            admin_password = input('Enter admin password for ' + vm['name'] + ': ')
            if (len(admin_password) >= 12 and len(admin_password) <= 123):
                pattern_spec_count = 0
                if (re.search('[a-z]', admin_password)):
                    pattern_spec_count += 1
                if (re.search('[A-Z]', admin_password)):
                    pattern_spec_count += 1
                if (re.search('[0-9]', admin_password)):
                    pattern_spec_count += 1
                if (re.search('[^A-Za-z0-9]', admin_password)):
                    pattern_spec_count += 1
                if (pattern_spec_count >= 3):
                    valid_pass = True
                else:
                    print('Invalid password - try again.')
        cmd = ['az', 'vm', 'create', '--resource-group', vm['resource-group'], '--name', vm['name'], '--image', vm['image'], '--public-ip-sku', 'Standard', '--admin-username', vm['admin-username'], '--admin-password', admin_password,'--generate-ssh-keys']
        print('> ' + ' '.join(cmd))
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, error = process.communicate()
        print('Created ' + vm['name'] + ': ' + str(json.loads(output.decode('utf-8'))))
        # log VM creation in the documentation file
        documentVMProvision(doc_file, vm, 'Azure')
    print('> az vm list --output table')
    os.system('az vm list --output table')


# function creates the resource groups that the VMs will be assigned to
def createResourceGroups(configs):
    print('Creating resource groups...')
    # create all required resource groups
    for vm in configs:
        cmd = ['az', 'group', 'list', '--query', f"[?name=='{vm['resource-group']}']"]
        print('> ' + ' '.join(cmd))
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, error = process.communicate()
        resource_groups = json.loads(output.decode('utf-8'))
        if len(resource_groups) > 0:
            print(vm['resource-group'] + ' resource group already exists.')
        else:
            print('> az group create --name ' + vm['resource-group'] + ' --location ' + vm['location'])
            os.system('az group create --name ' + vm['resource-group'] + ' --location ' + vm['location'])
            print('> az group wait --created  --resource-group ' + vm['resource-group'])
            os.system('az group wait --created  --resource-group ' + vm['resource-group'])
            print(vm['resource-group'] + ' resource group created.')
    print('Finished creating resource groups:')
    print('> az group list --output table')
    os.system('az group list --output table')


# function deletes all existing Azure VMs
def deleteAzureVMs():
    print('Deleting Azure VMs...')
    cmd = ['az', 'group', 'list']
    print('> ' + ' '.join(cmd))
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    resource_groups = json.loads(output.decode('utf-8'))
    for resource_group in resource_groups:
        print('Deleting Azure VMs in resource group ' + resource_group['name'])
        print('> az group delete -n ' + resource_group['name'])
        os.system('az group delete -n ' + resource_group['name'])


# function checks if the provided Azure VM image is included in the list of available images
def checkValidImage(vm_image, location):
    cmd = ['az', 'vm', 'image', 'list', '--location', location]
    print('> ' + ' '.join(cmd))
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    images = json.loads(output.decode('utf-8'))
    isValid = False
    for image in images:
        if vm_image == image['urnAlias'] or vm_image == image['urn']:
            isValid = True
    return isValid


# function checks if there is already an existing VM in the given resource group with the given name
def checkVMNameTaken(resource_group, name):
    cmd = ['az', 'vm', 'list']
    print('> ' + ' '.join(cmd))
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    resource_groups = json.loads(output.decode('utf-8'))
    for resource_group in resource_groups:
        cmd = ['az', 'vm', 'list', '--resource-group', resource_group]
        print('> ' + ' '.join(cmd))
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, error = process.communicate()
        vms = json.loads(output.decode('utf-8'))
        for vm in vms:
            if name == vm['name']:
                # return True if there already exists a VM by the given name
                return True
    return False