import sys
import os
import unittest
import paramiko
import time

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 
from azure_utils.vm_manager import VirtualMachineManager
from config import SSH_PUBLIC_KEY_PATH, SSH_PRIVATE_KEY_PATH, NETWORK_SECURITY_GROUP_NAME

class TestVirtualMachineManager(unittest.TestCase):
    def setUp(self):
        self.vm_manager = VirtualMachineManager()
        self.vm_name = "test-vm"
        self.gpu_vm_name = "test-gpu-vm"
        self.username = "testuser"
        self.test_dir = "./test_dir"
        self.test_file = "test_file.txt"
        self.temp_dir = "./temp_dir"
        self.ssh_public_key_path = SSH_PUBLIC_KEY_PATH
        self.ssh_private_key_path = SSH_PRIVATE_KEY_PATH
        self.network_security_group_name = NETWORK_SECURITY_GROUP_NAME
        
        # Create test_dir and test_file.txt
        os.makedirs(self.test_dir, exist_ok=True)
        with open(os.path.join(self.test_dir, self.test_file), "w") as f:
            f.write("Hello world")
    
    def tearDown(self):
        # Clean up test_dir and temp_dir
        os.remove(os.path.join(self.test_dir, self.test_file))
        os.rmdir(self.test_dir)
        if os.path.exists(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, self.test_file))
            os.rmdir(self.temp_dir)
        
        # Delete the standard VM and GPU VM if they exist
        try:
            self.vm_manager.delete_vm(self.vm_name)
        except:
            pass
        
        try:
            self.vm_manager.delete_vm(self.gpu_vm_name)
        except:
            pass
    
    def test_create_vm(self):
        vm = self.vm_manager.create_vm(self.vm_name, self.username, self.ssh_public_key_path, self.network_security_group_name)
        self.assertIsNotNone(vm)
        self.assertEqual(vm.name, self.vm_name)
        self.vm_manager.delete_vm(self.vm_name)
    
    def test_create_gpu_vm(self):
        gpu_vm = self.vm_manager.create_gpu_vm(self.gpu_vm_name, self.username, self.ssh_public_key_path, self.network_security_group_name)
        self.assertIsNotNone(gpu_vm)
        self.assertEqual(gpu_vm.name, self.gpu_vm_name)
        
        # Check if the GPU is connected to the VM
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        public_ip_address = self.vm_manager.network_client.public_ip_addresses.get(
            self.vm_manager.resource_group_name, f"{self.gpu_vm_name}-public-ip"
        ).ip_address
        
        ssh_private_key = paramiko.RSAKey.from_private_key_file(self.ssh_private_key_path)
        ssh_client.connect(hostname=public_ip_address, username=self.username, pkey=ssh_private_key)
        
        # Wait for the GPU driver installation to complete
        time.sleep(60)  # Adjust the delay as needed
        
        # Execute a command to check the GPU presence
        stdin, stdout, stderr = ssh_client.exec_command("nvidia-smi")
        output = stdout.read().decode("utf-8")
        print("output", output)
        # Assert that the output contains information about the GPU
        self.assertIn("NVIDIA-SMI", output)
        
        ssh_client.close()
        self.vm_manager.delete_vm(self.gpu_vm_name)
    
    def test_delete_vm(self):
        self.vm_manager.create_vm(self.vm_name, self.username, self.ssh_public_key_path, self.network_security_group_name)
        self.vm_manager.create_gpu_vm(self.gpu_vm_name, self.username, self.ssh_public_key_path, self.network_security_group_name)
        
        self.vm_manager.delete_vm(self.vm_name)
        self.vm_manager.delete_vm(self.gpu_vm_name)
        
        with self.assertRaises(Exception):
            self.vm_manager.compute_client.virtual_machines.get(
                self.vm_manager.resource_group_name, self.vm_name
            )
        
        with self.assertRaises(Exception):
            self.vm_manager.compute_client.virtual_machines.get(
                self.vm_manager.resource_group_name, self.gpu_vm_name
            )
    
    def test_copy_files_to_vm(self):
        self.vm_manager.create_vm(self.vm_name, self.username, self.ssh_public_key_path, self.network_security_group_name)
        self.vm_manager.copy_files_to_vm(self.test_dir, self.vm_name, self.username, self.ssh_private_key_path)
        
        # Verify if the file exists on the VM
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        vm = self.vm_manager.compute_client.virtual_machines.get(self.vm_manager.resource_group_name, self.vm_name)
        public_ip_address = self.vm_manager.network_client.public_ip_addresses.get(
            self.vm_manager.resource_group_name, f"{self.vm_name}-public-ip"
        ).ip_address
        
        ssh_private_key = paramiko.RSAKey.from_private_key_file(self.ssh_private_key_path)
        ssh_client.connect(hostname=public_ip_address, username=self.username, pkey=ssh_private_key)
        sftp_client = ssh_client.open_sftp()
        self.assertTrue(self.test_file in sftp_client.listdir(f"/home/{self.username}"))
        sftp_client.close()
        ssh_client.close()
        self.vm_manager.delete_vm(self.vm_name)
    
    def test_copy_files_to_gpu_vm(self):
        self.vm_manager.create_gpu_vm(self.gpu_vm_name, self.username, self.ssh_public_key_path, self.network_security_group_name)
        self.vm_manager.copy_files_to_vm(self.test_dir, self.gpu_vm_name, self.username, self.ssh_private_key_path)
        
        # Verify if the file exists on the GPU VM
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        gpu_vm = self.vm_manager.compute_client.virtual_machines.get(self.vm_manager.resource_group_name, self.gpu_vm_name)
        public_ip_address = self.vm_manager.network_client.public_ip_addresses.get(
            self.vm_manager.resource_group_name, f"{self.gpu_vm_name}-public-ip"
        ).ip_address
        
        ssh_private_key = paramiko.RSAKey.from_private_key_file(self.ssh_private_key_path)
        ssh_client.connect(hostname=public_ip_address, username=self.username, pkey=ssh_private_key)
        sftp_client = ssh_client.open_sftp()
        self.assertTrue(self.test_file in sftp_client.listdir(f"/home/{self.username}"))
        sftp_client.close()
        ssh_client.close()
        self.vm_manager.delete_vm(self.gpu_vm_name)
    
    def test_copy_results_from_vm(self):
        self.vm_manager.create_vm(self.vm_name, self.username, self.ssh_public_key_path, self.network_security_group_name)
        
        # Create a results file on the VM
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        vm = self.vm_manager.compute_client.virtual_machines.get(self.vm_manager.resource_group_name, self.vm_name)
        public_ip_address = self.vm_manager.network_client.public_ip_addresses.get(
            self.vm_manager.resource_group_name, f"{self.vm_name}-public-ip"
        ).ip_address
        
        ssh_private_key = paramiko.RSAKey.from_private_key_file(self.ssh_private_key_path)
        ssh_client.connect(hostname=public_ip_address, username=self.username, pkey=ssh_private_key)
        sftp_client = ssh_client.open_sftp()
        sftp_client.mkdir(f"/home/{self.username}/results")
        with sftp_client.open(f"/home/{self.username}/results/{self.test_file}", "w") as f:
            f.write("Test results")
        sftp_client.close()
        ssh_client.close()
        
        os.makedirs(self.temp_dir, exist_ok=True)
        self.vm_manager.copy_files_from_vm(self.vm_name, self.username, self.ssh_private_key_path, self.temp_dir)
        
        # Verify if the results file is copied to the destination directory
        self.assertTrue(self.test_file in os.listdir(self.temp_dir))
        self.vm_manager.delete_vm(self.vm_name)
    
    def test_copy_results_from_gpu_vm(self):
        self.vm_manager.create_gpu_vm(self.gpu_vm_name, self.username, self.ssh_public_key_path, self.network_security_group_name)
        
        # Create a results file on the GPU VM
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        gpu_vm = self.vm_manager.compute_client.virtual_machines.get(self.vm_manager.resource_group_name, self.gpu_vm_name)
        public_ip_address = self.vm_manager.network_client.public_ip_addresses.get(
            self.vm_manager.resource_group_name, f"{self.gpu_vm_name}-public-ip"
        ).ip_address
        
        ssh_private_key = paramiko.RSAKey.from_private_key_file(self.ssh_private_key_path)
        ssh_client.connect(hostname=public_ip_address, username=self.username, pkey=ssh_private_key)
        sftp_client = ssh_client.open_sftp()
        sftp_client.mkdir(f"/home/{self.username}/results")
        with sftp_client.open(f"/home/{self.username}/results/{self.test_file}", "w") as f:
            f.write("Test results")
        sftp_client.close()
        ssh_client.close()
        
        os.makedirs(self.temp_dir, exist_ok=True)
        self.vm_manager.copy_files_from_vm(self.gpu_vm_name, self.username, self.ssh_private_key_path, self.temp_dir)
        
        # Verify if the results file is copied to the destination directory
        self.assertTrue(self.test_file in os.listdir(self.temp_dir))
        
        self.vm_manager.delete_vm(self.gpu_vm_name)

if __name__ == "__main__":
    unittest.main()