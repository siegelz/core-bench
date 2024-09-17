# Azure FAQ
This document contains some frequently asked questions when setting up the Azure environment for the CORE-Bench harness.

Please reach out to us if you are having any trouble.

## How do I install Azure CLI and log in to my Azure account?
See [here](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd) for instructions on how to install the Azure CLI. After installing the Azure CLI, run `azd auth login` to log in to your Azure account.

If you are attempting to install Azure CLI to a Linux machine without root access, you can modify the `install-azd.sh` script (found in the above link) to install Azure CLI to a user directory. Specifically, modify line 149 to `symlink_folder="/home/$USER/bin"` and line 150 to `install_folder="/home/$USER/microsoft/azd"`.

## Where can I find the Azure credentials for the `config.py` file?
The `config.py` file should contain the following Azure credentials:
```python
AZURE_SUBSCRIPTION_ID = "XXX-XXX-XXX-XXX-XXX"
AZURE_RESOURCE_GROUP_NAME = "XXX"
AZURE_LOCATION = "XXX"
NETWORK_SECURITY_GROUP_NAME = "XXX"
SSH_PUBLIC_KEY_PATH = "/Users/XXX/.ssh/id_rsa.pub"
SSH_PRIVATE_KEY_PATH = "/Users/XXX/.ssh/id_rsa"
```

To find `AZURE_SUBSCRIPTION_ID`, search for "Subscriptions" in the top search bar and either create a subscription or use the ID of an existing subscription. 

To find `AZURE_RESOURCE_GROUP_NAME`, search for "Resource groups" in the top search bar and either create a new resource group or use the name of an existing resource group.

The `AZURE_LOCATION` should correspond to the location of the resource group. To find the location of the resource group, click on the resource group and look for the "Location" field. See [here](https://gist.github.com/ausfestivus/04e55c7d80229069bf3bc75870630ec8) for a list of Azure locations.

To find `NETWORK_SECURITY_GROUP_NAME`, search for "Network security groups" in the top search bar and either create a new network security group or use the name of an existing network security group.

For `SSH_PUBLIC_KEY_PATH` and `SSH_PRIVATE_KEY_PATH`, use the path to your SSH public and private keys, respectively. Feel free to generate a new key pair if you wish. The keys are used to SSH into the VMs that the harness creates.

## How do I request a quota increase for the `Standard_NC4as_T4_v3` machine type?
To request a quota increase for the `Standard_NC4as_T4_v3` machine type, go to the [Azure portal](https://portal.azure.com/#view/Microsoft_Azure_Capacity/QuotaMenuBlade/~/myQuotas) and request a quota increase for the `Standard_NC4as_T4_v3` machine type.

## How can I safely delete the Azure resources created by the harness?
The harness automatically deletes the Azure resources it creates after the task has been completed. However, if the harness is interrupted or you wish to manually delete the resources, **make sure you delete the associated OS disk, network interface, and public IP address**. You must manually check these boxes when deleting the VM in the Azure portal.