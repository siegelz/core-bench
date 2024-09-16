from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.identity import DefaultAzureCredential
import paramiko
import os
import tarfile

class VirtualMachineManager:
    def __init__(self):
        from config import AZURE_SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP_NAME, AZURE_LOCATION
        self.subscription_id = AZURE_SUBSCRIPTION_ID
        self.resource_group_name = AZURE_RESOURCE_GROUP_NAME
        self.location = AZURE_LOCATION
        self.credential = DefaultAzureCredential()
        self.compute_client = ComputeManagementClient(self.credential, self.subscription_id)
        self.network_client = NetworkManagementClient(self.credential, self.subscription_id)
        self.resource_client = ResourceManagementClient(self.credential, self.subscription_id)

    def create_vm(self, vm_name, username, ssh_public_key_path, network_security_group_name, vm_size="Standard_E2as_v5", image_reference=None, disk_size=80):
        # Create a virtual network and subnet
        vnet_name = f"{vm_name}-vnet"
        subnet_name = f"{vm_name}-subnet"
        vnet = self.network_client.virtual_networks.begin_create_or_update(
            self.resource_group_name,
            vnet_name,
            {
                "location": self.location,
                "address_space": {"address_prefixes": ["10.0.0.0/16"]},
                "subnets": [{"name": subnet_name, "address_prefix": "10.0.0.0/24"}],
            }
        ).result()
        subnet = vnet.subnets[0]

        # Create a public IP address
        public_ip_name = f"{vm_name}-public-ip"
        public_ip = self.network_client.public_ip_addresses.begin_create_or_update(
            self.resource_group_name,
            public_ip_name,
            {
                "location": self.location,
                "sku": {"name": "Standard"},
                "public_ip_allocation_method": "Static",
            }
        ).result()

        # Get the existing network security group
        network_security_group = self.network_client.network_security_groups.get(
            self.resource_group_name, network_security_group_name
        )

        # Create a network interface
        nic_name = f"{vm_name}-nic"
        nic = self.network_client.network_interfaces.begin_create_or_update(
            self.resource_group_name,
            nic_name,
            {
                "location": self.location,
                "ip_configurations": [
                    {
                        "name": "default",
                        "subnet": {"id": subnet.id},
                        "public_ip_address": {"id": public_ip.id},
                    }
                ],
                "network_security_group": {"id": network_security_group.id},
            }
        ).result()

        # Read the SSH public key from the specified file
        with open(ssh_public_key_path, "r") as file:
            ssh_public_key = file.read().strip()

        # Define the VM configuration
        if image_reference is None:
            image_reference = {
                "publisher": "Canonical",
                "offer": "0001-com-ubuntu-server-jammy",
                "sku": "22_04-lts-gen2",
                "version": "latest"
            }

        vm_parameters = {
            "location": self.location,
            "storage_profile": {"image_reference": image_reference, 
                                "os_disk": {
                                    "createOption": "FromImage",
                                    "diskSizeGB": disk_size
                                    }
                                },
            "hardware_profile": {"vm_size": vm_size},
            "os_profile": {
                "computer_name": vm_name,
                "admin_username": username,
                "linux_configuration": {
                    "disable_password_authentication": True,
                    "ssh": {
                        "public_keys": [
                            {
                                "path": f"/home/{username}/.ssh/authorized_keys",
                                "key_data": ssh_public_key,
                            }
                        ]
                    },
                },
            },
            "network_profile": {"network_interfaces": [{"id": nic.id}]},
        }

        # Create the VM
        vm = self.compute_client.virtual_machines.begin_create_or_update(
            self.resource_group_name, vm_name, vm_parameters
        ).result()

        return vm

    def create_gpu_vm(self, vm_name, username, ssh_public_key_path, network_security_group_name, vm_size="Standard_NC4as_T4_v3", image_reference=None, disk_size=80):
        # Create a virtual network and subnet
        vnet_name = f"{vm_name}-vnet"
        subnet_name = f"{vm_name}-subnet"
        vnet = self.network_client.virtual_networks.begin_create_or_update(
            self.resource_group_name,
            vnet_name,
            {
                "location": self.location,
                "address_space": {"address_prefixes": ["10.0.0.0/16"]},
                "subnets": [{"name": subnet_name, "address_prefix": "10.0.0.0/24"}],
            }
        ).result()
        subnet = vnet.subnets[0]

        # Create a public IP address
        public_ip_name = f"{vm_name}-public-ip"
        public_ip = self.network_client.public_ip_addresses.begin_create_or_update(
            self.resource_group_name,
            public_ip_name,
            {
                "location": self.location,
                "sku": {"name": "Standard"},
                "public_ip_allocation_method": "Static",
            }
        ).result()

        # Get the existing network security group
        network_security_group = self.network_client.network_security_groups.get(
            self.resource_group_name, network_security_group_name
        )

        # Create a network interface
        nic_name = f"{vm_name}-nic"
        nic = self.network_client.network_interfaces.begin_create_or_update(
            self.resource_group_name,
            nic_name,
            {
                "location": self.location,
                "ip_configurations": [
                    {
                        "name": "default",
                        "subnet": {"id": subnet.id},
                        "public_ip_address": {"id": public_ip.id},
                    }
                ],
                "network_security_group": {"id": network_security_group.id},
            }
        ).result()

        # Read the SSH public key from the specified file
        with open(ssh_public_key_path, "r") as file:
            ssh_public_key = file.read().strip()

        # Define the GPU VM configuration
        if image_reference is None:
            image_reference = {
                "publisher": "Canonical",
                "offer": "0001-com-ubuntu-server-jammy",
                "sku": "22_04-lts-gen2",
                "version": "latest"
            }

        vm_parameters = {
            "location": self.location,
            "storage_profile": {"image_reference": image_reference, 
                    "os_disk": {
                        "createOption": "FromImage",
                        "diskSizeGB": disk_size
                        }
                    },
            "hardware_profile": {"vm_size": vm_size},
            "os_profile": {
                "computer_name": vm_name,
                "admin_username": username,
                "linux_configuration": {
                    "disable_password_authentication": True,
                    "ssh": {
                        "public_keys": [
                            {
                                "path": f"/home/{username}/.ssh/authorized_keys",
                                "key_data": ssh_public_key,
                            }
                        ]
                    },
                },
            },
            "network_profile": {"network_interfaces": [{"id": nic.id}]},
            "uefi_settings": {"secure_boot_enabled": False},
        }

        # Create the GPU VM
        vm = self.compute_client.virtual_machines.begin_create_or_update(
            self.resource_group_name, vm_name, vm_parameters
        ).result()

        # Define the NVIDIA GPU driver extension configuration
        extension_name = "NvidiaGpuDriverLinux"
        extension_publisher = "Microsoft.HpcCompute"
        extension_type = "NvidiaGpuDriverLinux"
        type_handler_version = "1.9"

        extension_parameters = {
            "location": self.location,
            "publisher": extension_publisher,
            "type_properties_type": extension_type,
            "type_handler_version": type_handler_version,
            "auto_upgrade_minor_version": True,
            "settings": {}
        }

        # Add the NVIDIA GPU driver extension to the VM
        self.compute_client.virtual_machine_extensions.begin_create_or_update(
            self.resource_group_name,
            vm_name,
            extension_name,
            extension_parameters
        ).result()

        return vm

    def delete_vm(self, vm_name):
        # Get the VM
        vm = self.compute_client.virtual_machines.get(self.resource_group_name, vm_name)

        # Delete the VM
        self.compute_client.virtual_machines.begin_delete(
            self.resource_group_name, vm_name
        ).result()

        # Delete the associated disks
        for disk in vm.storage_profile.data_disks:
            self.compute_client.disks.begin_delete(
                self.resource_group_name, disk.name
            ).result()

        # Delete the OS disk
        os_disk_name = vm.storage_profile.os_disk.name
        self.compute_client.disks.begin_delete(
            self.resource_group_name, os_disk_name
        ).result()

        # Delete the network interface
        nic_name = f"{vm_name}-nic"
        self.network_client.network_interfaces.begin_delete(
            self.resource_group_name, nic_name
        ).result()

        # Delete the public IP address
        public_ip_name = f"{vm_name}-public-ip"
        self.network_client.public_ip_addresses.begin_delete(
            self.resource_group_name, public_ip_name
        ).result()

        # Delete the virtual network (if not used by other resources)
        vnet_name = f"{vm_name}-vnet"
        try:
            self.network_client.virtual_networks.begin_delete(
                self.resource_group_name, vnet_name
            ).result()
        except Exception as e:
            print(f"Failed to delete virtual network {vnet_name}: {str(e)}")

    def copy_files_to_vm(self, source_directory, vm_name, username, ssh_private_key_path):
        # Get the public IP address of the VM
        vm = self.compute_client.virtual_machines.get(self.resource_group_name, vm_name)
        public_ip_address = self.network_client.public_ip_addresses.get(
            self.resource_group_name, f"{vm_name}-public-ip"
        ).ip_address

        # Create an SSH client
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Load the SSH private key
        ssh_private_key = paramiko.RSAKey.from_private_key_file(ssh_private_key_path)

        # Connect to the VM using SSH
        ssh_client.connect(hostname=public_ip_address, username=username, pkey=ssh_private_key)

        # Create an SFTP client
        sftp_client = ssh_client.open_sftp()

        # Copy files from the source directory to the VM
        # Compress the source directory
        source_directory = os.path.abspath(source_directory)
        tar_file_path = f"{source_directory}.tar.gz"
        with tarfile.open(tar_file_path, "w:gz") as tar:
            tar.add(source_directory, arcname=os.path.basename(source_directory))
        
        # Copy the compressed file to the VM
        remote_tar_file_path = f"/home/{username}/{os.path.basename(tar_file_path)}"
        sftp_client.put(tar_file_path, remote_tar_file_path)

        # Extract the compressed file on the VM
        _, stdout, _ = ssh_client.exec_command(f"tar -xzf {remote_tar_file_path} --strip-components=1 -C /home/{username}")
        for _ in stdout: pass # Block until the tar command completes

        # Remove the compressed file from the VM and the local machine
        sftp_client.remove(remote_tar_file_path)
        os.remove(tar_file_path)

        # Close the SFTP client and SSH connection
        sftp_client.close()
        ssh_client.close()

    def copy_files_from_vm(self, vm_name, username, ssh_private_key_path, destination_directory):
        # Get the public IP address of the VM
        vm = self.compute_client.virtual_machines.get(self.resource_group_name, vm_name)
        public_ip_address = self.network_client.public_ip_addresses.get(
            self.resource_group_name, f"{vm_name}-public-ip"
        ).ip_address

        # Create an SSH client
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Load the SSH private key
        ssh_private_key = paramiko.RSAKey.from_private_key_file(ssh_private_key_path)

        # Connect to the VM using SSH
        ssh_client.connect(hostname=public_ip_address, username=username, pkey=ssh_private_key)

        # Create an SFTP client
        sftp_client = ssh_client.open_sftp()

        # Compress all files in the home directory on the VM
        remote_tar_file_path = f"/home/{username}/{os.path.basename(destination_directory)}_back.tar.gz"
        remote_home_directory = f"/home/{username}"
        _, stdout, _ = ssh_client.exec_command(f"tar -czf {remote_tar_file_path} -C {remote_home_directory} .")
        for _ in stdout: pass # Block until the tar command completes

        # Copy the compressed file from the VM
        sftp_client.get(remote_tar_file_path, f"{destination_directory}.tar.gz")

        # Extract the compressed file on the local machine
        with tarfile.open(f"{destination_directory}.tar.gz", "r:gz") as tar:
            tar.extractall(destination_directory)

        # Remove the compressed file from the VM and the local machine
        # sftp_client.remove(remote_tar_file_path)
        os.remove(f"{destination_directory}.tar.gz")

        # Close the SFTP client and SSH connection
        sftp_client.close()
        ssh_client.close()

    def check_task_completion(self, vm_name, username, ssh_private_key_path, filename = "task_completed.log"):
        # Get the public IP address of the VM
        vm = self.compute_client.virtual_machines.get(self.resource_group_name, vm_name)
        public_ip_address = self.network_client.public_ip_addresses.get(
            self.resource_group_name, f"{vm_name}-public-ip"
        ).ip_address

        # Create an SSH client
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Load the SSH private key
        ssh_private_key = paramiko.RSAKey.from_private_key_file(ssh_private_key_path)

        # Connect to the VM using SSH
        ssh_client.connect(hostname=public_ip_address, username=username, pkey=ssh_private_key, timeout=5)

        # Create an SFTP client
        sftp_client = ssh_client.open_sftp()

        # Return the contents of log.txt if it exists, otherwise return None
        log_file_path = f"/home/{username}/{filename}"
        try:
            with sftp_client.open(log_file_path) as file:
                log_contents = file.read().decode("utf-8")
        except FileNotFoundError:
            log_contents = None

        # Close the SFTP client and SSH connection
        sftp_client.close()
        ssh_client.close()

        return log_contents

    def run_agent_on_vm(self, agent_script, vm_name, username, ssh_private_key_path, timeout=8100):
        # Start the VM
        self.compute_client.virtual_machines.begin_start(
            self.resource_group_name, vm_name
        ).result()

        # Get the public IP address of the VM
        public_ip_address = self.network_client.public_ip_addresses.get(
            self.resource_group_name, f"{vm_name}-public-ip"
        ).ip_address

        # Create an SSH client
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Load the SSH private key
        ssh_private_key = paramiko.RSAKey.from_private_key_file(ssh_private_key_path)

        # Connect to the VM using SSH
        ssh_client.connect(hostname=public_ip_address, username=username, pkey=ssh_private_key)

        # Run the agent script on the VM
        _, stdout, stderr = ssh_client.exec_command(f"sudo nohup bash -c '(timeout {timeout} bash /home/{username}/{agent_script}) ; touch /home/{username}/task_completed.log' > /home/{username}/output.log 2>&1 &", timeout=1)

        # Close the SSH connection
        ssh_client.close()