# Virtual Machine Creation (CIS4010 Assignment 3)

The Virtual Machine creation module creates virtual machines in Azure and GCP cloud services based on specifications given in the config files.


## Requirements

It is assumed that the user has the Azure and GCP CLI installed already.
The Azure CLI can be installed using the following commands:
>for Windows: winget install -e --id Microsoft.AzureCLI
for macOS: brew update && brew install azure-cli
for Debian: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

The GCP CLI can be installed using the following commands:
>for Windows: (New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe") & $env:Temp\GoogleCloudSDKInstaller.exe
for macOS: see https://cloud.google.com/sdk/docs/install#mac
for Debian/Ubuntu: see https://cloud.google.com/sdk/docs/install#deb


## Usage

The program can be run using the command:
```
py automate.py
```
The program reads from *Azure.conf* and *GCP.conf* files to get the information about the VMs to provision; these config files should be in the same directory as the script *automate.py*.
*automate.py* is the python file to run; it imports the *gcpFunctions* and *azureFunctions* modules, which contain helper functions in the creation of virtual machines using the CLI of their respective cloud service. The *gcpFunctions* and *azureFunctions* modules import helper functions from *helperFunctions*.
The documentation of the created virtual machines will be in text files found in the *logs* subdirectory, which the program will create if it doesn't already exist.

## Implementation Details

The provisioning of Azure VMs was done using the Azure CLI, and the provisioning of GCP VMs was done using the GCP CLI.
If an invalid VM name is found, the program continues to run, ignoring the configuration settings for the VM with the invalid name. The same is done for if one of the required properties (ie. name, resource-group, etc.)
The documentation file and copies of the .conf files are stored in the logs directory, which the script creates if it doesn't already exist.
The CLI commands used are printed to console as per the requirements. However, I did not display the output for every CLI command run as some commands were used for validation purposes, and I opted to not display the output so as to not clutter the console.
When creating the virtual machines in Azure, I used the flag *--generate-ssh-keys* to generate SSH public and private key files if missing. The keys will be stored in the ~/.ssh directory.

## Assumptions, Limitations, and Improvements

The program assumes the Azure and GCP config files are named *Azure.conf* and *GCP.conf* respectively.
I assumed that the *project* property in *GCP.conf* is for documentation, and thus it was not used as the actual name for the projects the virtual machines are created under. It is assumed that the user has an existing project, for which the program will ask the user to provide the *projectId*.
When testing the program with the settings in the given GCP.conf, the provided images were not included in the list of valid images for my project, so I replaced them with valid images.