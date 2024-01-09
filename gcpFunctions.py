import configparser
import os
import sys
import subprocess
import json
import re
from datetime import datetime
from helperFunctions import checkValidVMNames, documentVMProvision


# function logs in to GCP
def gcpLogin():
    print('> gcloud auth login --no-launch-browser')
    os.system('gcloud auth login --no-launch-browser')
    print('> gcloud projects list')
    os.system('gcloud projects list')
    project = input('Enter the projectId of the project you would like to create the VMs in: ')
    print(f'> gcloud config set project {project}')
    os.system(f'gcloud config set project {project}')


# function reads from the Azure.conf file to get the configuration settings for the Azure VMs
def parseGCPConfig(config):
    # can only be max 10 VMs
    config.read('GCP.conf')
    gcp_vms = config.sections()

    # call function to check for valid VM names in config file and count the number of VMs
    vm_count = checkValidVMNames('gcp', gcp_vms)
    
    # parse VM config settings and store them in a list of dicts
    # each dict has the settings for a single VM
    gcp_vm_configs = []
    i = 1
    if vm_count > 1:
        for i in range(1, vm_count):
            vm_name = None
            if i < 10:
                vm_name = 'gcp0' + str(i)
            else:
                vm_name = 'gcp' + str(i)
            # check for required settings
            # any VMs with invalid settings will not be provisioned and the program will continue provisioning other valid VMs if applicable
            if config[vm_name].get('name') == None:
               print('Error creating ' + vm_name + '. No name property found for ' + vm_name)
            if re.match(r'^[a-z0-9]+$', config[vm_name]['name']) == None:
                print('Error creating ' + vm_name + '. ' + config[vm_name]['name'] + ' is an invalid name.')
            if checkVMNameTaken(config[vm_name]['name']):
                print('Error creating ' + vm_name + '. Another virtual machine already exists in the project with the name ' + config[vm_name]['name'] + ' .')
            elif config[vm_name].get('image') == None:
                print('Error creating ' + vm_name + '. No image property found for ' + vm_name)
            elif config[vm_name].get('imageproject') == None:
                print('Error creating ' + vm_name + '. No imageproject property found for ' + vm_name)
            elif config[vm_name].get('zone') == None:
                print('Error creating ' + vm_name + '. No zone property found for ' + vm_name)
            elif checkValidImage(config[vm_name]['image']) == False:
                print('Error creating ' + vm_name + '. ' + config[vm_name]['image'] + ' is an invalid image.')
            else:
                config_settings = {}
                config_settings['name'] = config[vm_name]['name']
                config_settings['project'] = config[vm_name]['project']
                config_settings['team'] = config[vm_name]['team']
                config_settings['purpose'] = config[vm_name]['purpose']
                config_settings['os'] = config[vm_name]['os']
                config_settings['image'] = config[vm_name]['image']
                config_settings['imageproject'] = config[vm_name]['imageproject']
                config_settings['zone'] = config[vm_name]['zone']
                gcp_vm_configs.append(config_settings)
                i += 1
    return gcp_vm_configs


# function provisions GCP VM(s)
def provisionGCPVMs(configs, doc_file):
    # call other functions to provision necessary resources to provision a VM
    # need name, image, image-project, and zone
    for vm in configs:
        print(f"> gcloud compute instances create {vm['name']} --image {vm['image']} --image-project {vm['imageproject']} --zone {vm['zone']}")
        os.system(f"gcloud compute instances create {vm['name']} --image {vm['image']} --image-project {vm['imageproject']} --zone {vm['zone']}")
        print('Created ' + vm['name'] + '.')
        print(f'gcloud compute instances describe {vm["name"]}')
        os.system(f'gcloud compute instances describe {vm["name"]}')
        # log VM creation in the documentation file
        documentVMProvision(doc_file, vm, 'GCP')
    # output the creates VM instances under the current project
    cmd = ['gcloud', 'compute', 'instances', 'list']
    print('> ' + ' '.join(cmd))
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()


# # function creates the projects that the VMs will be assigned to
# def createProjects(configs):
#     print('Creating projects...')
#     # create all required projects
#     project_counter = 1
#     for vm in configs:
#         project_name = vm['project'].replace(' ', '-')
#         cmd = ['gcloud', 'projects', 'list', '--format=json']
#         print(' '.join(cmd))
#         process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
#         output, error = process.communicate()
#         projects = json.loads(output.decode('utf-8'))
#         print(str(projects))
#         project_exists = False
#         for project in projects:
#             if project['name'] == project_name:
#                 project_exists = True
#         if project_exists:
#             print(vm['project'] + ' project already exists.')
#         else:
#             project_id = 'pwoonfat-project-' + str(project_counter)
#             print(f"gcloud projects create {project_id} --name {vm['project'].replace(' ', '-')}")
#             os.system(f"gcloud projects create {project_id} --name {vm['project'].replace(' ', '-')}")
#             project_counter += 1
#     print('Finished creating projects:')
#     print('gcloud projects list --format="table(projectId, name, createTime)"')
#     os.system('gcloud projects list --format="table(projectId, name, createTime)"')
    


# function checks if the provided Azure VM image is included in the list of available images
def checkValidImage(vm_image):
    cmd = ['gcloud', 'compute', 'images', 'list', '--format=json']
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    images = json.loads(output.decode('utf-8'))
    isValid = False
    # check if the image name provided matches the urnAlias or urn
    for image in images:
        if vm_image == image['name']:
            isValid = True
    return isValid


# function checks whether there is already an existing VM by the given name in the given project
def checkVMNameTaken(name):
    # get list of VMs associated with the given project
    cmd = ['gcloud', 'compute', 'instances', 'list', '--format=json']
    print('> ' + ' '.join(cmd))
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    vms = json.loads(output.decode('utf-8'))
    # check if there is already an existing VM with the given name, if there is then return True
    for vm in vms:
        if vm['name'] == name:
            return True
    return False


# function deletes all existing Azure VMs
def deleteGCPVMs():
    print('Deleting GCP VMs...')
    # delete all VMs in the project then delete the project
    print('Deleting GCP VMs in the current project...')
    cmd = ['gcloud', 'compute', 'instances', 'list', '--format=json']
    print('> ' + ' '.join(cmd))
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    vms = json.loads(output.decode('utf-8'))
    for vm in vms:
        print(f"> gcloud compute instances delete {vm['name']}")
        os.system(f"gcloud compute instances delete {vm['name']} --zone {vm['zone']}")
        print(f"Deleted VM instance {vm['name']}.")
