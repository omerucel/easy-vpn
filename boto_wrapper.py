import time

import boto3
import paramiko

from pathlib import Path
from tabulate import tabulate
from pick import pick


class BotoWrapper:
    def __init__(self, profile_name: str):
        self.session = boto3.Session(profile_name=profile_name)
        self.ec2_client = self.session.client('ec2')

    def create_key_pair(self, name: str, pem_file: Path):
        if pem_file.exists():
            return
        if self.has_key_pair(name):
            raise ValueError(f'Key pair {name} already exists. Please download the key pair from AWS console and save it to {pem_file}')
        key_pair = self.ec2_client.create_key_pair(KeyName=name, KeyFormat='pem', KeyType='rsa')
        with open(pem_file, 'w') as f:
            f.write(key_pair.key_material)

    def has_key_pair(self, name: str) -> bool:
        for key_pair in self.ec2_client.describe_key_pairs()['KeyPairs']:
            if key_pair['KeyName'] == name:
                return True
        return False

    def create_security_group(self, name: str):
        if self.has_security_group(name):
            return
        response = self.ec2_client.create_security_group(GroupName=name, Description=name)
        security_group_id = response['GroupId']
        self.ec2_client.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                },
                {
                    'IpProtocol': 'udp',
                    'FromPort': 1194,
                    'ToPort': 1194,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                },
            ]
        )

    def has_security_group(self, name: str) -> bool:
        for security_group in self.ec2_client.describe_security_groups()['SecurityGroups']:
            if security_group['GroupName'] == name:
                return True
        return False

    def run_instance(self, pem_file: Path):
        instance_id = self.get_instance_id('easy-vpn')
        if instance_id:
            print(f"Instance {instance_id} already exists. Waiting for it to be running.")
            self.ec2_client.get_waiter('instance_running').wait(InstanceIds=[instance_id])
            return
        response = self.ec2_client.run_instances(
            ImageId='ami-09a81b370b76de6a2',
            InstanceType='t2.nano',
            KeyName='easy-vpn',
            SecurityGroups=['easy-vpn'],
            MinCount=1,
            MaxCount=1,
            Monitoring={
                'Enabled': False
            },
            BlockDeviceMappings=[
                {
                    'DeviceName': '/dev/sda1',
                    'Ebs': {
                        'VolumeSize': 8,
                        'VolumeType': 'gp2',
                        'DeleteOnTermination': True,
                        'Encrypted': False
                    },
                },
            ],
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': 'easy-vpn'
                        },
                    ]
                },
            ],
        )
        print(f"Instance {response['Instances'][0]['InstanceId']} is created. Waiting for it to be running.")
        self.ec2_client.get_waiter('instance_running').wait(InstanceIds=[response['Instances'][0]['InstanceId']])
        self.install_openvpn(pem_file)

    def get_instance_id(self, name: str) -> str:
        for reservation in self.ec2_client.describe_instances()['Reservations']:
            for instance in reservation['Instances']:
                if instance['State']['Name'] != 'terminated' and instance['Tags'][0]['Value'] == name:
                    return instance['InstanceId']
        return ''

    def get_public_ip(self, name: str) -> str:
        for reservation in self.ec2_client.describe_instances()['Reservations']:
            for instance in reservation['Instances']:
                if instance['State']['Name'] == 'running' and instance['Tags'][0]['Value'] == name:
                    return instance.get('PublicIpAddress', '')
        return ''

    def install_openvpn(self, pem_file: Path, public_ip_address: str = '', private_ip_address: str = ''):
        if not public_ip_address or not private_ip_address:
            instances = self.show_instance_list_selector()
            if not instances:
                return
            public_ip_address = instances[0]['public_ip_address']
            private_ip_address = instances[0]['private_ip_address']
        ssh_key = paramiko.RSAKey.from_private_key_file(str(pem_file))
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=public_ip_address, username='ubuntu', pkey=ssh_key)
        ssh_client.exec_command('mkdir -p /home/ubuntu/scripts/files')
        ftp_client = ssh_client.open_sftp()
        ftp_client.put('scripts/install_openvpn.sh', '/home/ubuntu/scripts/install_openvpn.sh')
        ftp_client.put('scripts/refresh_ip.sh', '/home/ubuntu/scripts/refresh_ip.sh')
        ftp_client.put('scripts/files/99-openvpn-forward.conf', '/home/ubuntu/scripts/files/99-openvpn-forward.conf')
        ftp_client.put('scripts/files/client-common.txt', '/home/ubuntu/scripts/files/client-common.txt')
        ftp_client.put('scripts/files/ip_forward.txt', '/home/ubuntu/scripts/files/ip_forward.txt')
        ftp_client.put('scripts/files/openvpn-iptables.service', '/home/ubuntu/scripts/files/openvpn-iptables.service')
        ftp_client.put('scripts/files/server.conf', '/home/ubuntu/scripts/files/server.conf')
        ssh_client.exec_command('chmod +x /home/ubuntu/scripts/install_openvpn.sh')
        ssh_client.exec_command('chmod +x /home/ubuntu/scripts/refresh_ip.sh')
        response = ssh_client.exec_command('sudo /home/ubuntu/scripts/install_openvpn.sh')
        print(response[1].read().decode('utf-8'))
        print(response[2].read().decode('utf-8'))
        response = ssh_client.exec_command(f'sudo /home/ubuntu/scripts/refresh_ip.sh {public_ip_address} {private_ip_address}')
        print(response[1].read().decode('utf-8'))
        print(response[2].read().decode('utf-8'))
        ftp_client.get('/home/ubuntu/client.ovpn', 'client.ovpn')
        ftp_client.close()

    def copy_client(self, pem_file: Path, public_ip_address: str = ''):
        if not public_ip_address:
            instances = self.show_instance_list_selector()
            if not instances:
                return
            public_ip_address = instances[0]['public_ip_address']
        ssh_key = paramiko.RSAKey.from_private_key_file(str(pem_file))
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=public_ip_address, username='ubuntu', pkey=ssh_key)
        ftp_client = ssh_client.open_sftp()
        ftp_client.get('/home/ubuntu/client.ovpn', 'client.ovpn')
        ftp_client.close()

    def list_instances(self):
        response = self.ec2_client.describe_instances()['Reservations']
        instance_list = []
        for reservation in response:
            for instance in reservation['Instances']:
                instance_list.append([instance['InstanceId'], instance.get('PublicIpAddress', '-'), instance.get('PrivateIpAddress', '-'), instance['State']['Name']])
        print(tabulate(instance_list, headers=['Instance ID', 'Public IP', 'Private IP', 'State']))

    def terminate_instance(self):
        instances = self.show_instance_list_selector()
        if not instances:
            return
        if not BotoWrapper.request_confirm('Are you sure you want to terminate the selected instances?'):
            print("Termination is cancelled.")
            return
        instance_ids = [instance['instance_id'] for instance in instances]
        print(f"Terminating instances ({instance_ids})...")
        self.ec2_client.terminate_instances(InstanceIds=instance_ids)
        self.ec2_client.get_waiter('instance_terminated').wait(InstanceIds=instance_ids)
        print(f"Instances are terminated.")

    def refresh_ip_address(self, pem_file: Path):
        instances = self.show_instance_list_selector()
        if not instances:
            return
        instance_ids = [instance['instance_id'] for instance in instances]
        print(f"Refreshing IP address of instances ({instance_ids})...")
        self.ec2_client.stop_instances(InstanceIds=instance_ids)
        self.ec2_client.get_waiter('instance_stopped').wait(InstanceIds=instance_ids)
        self.ec2_client.start_instances(InstanceIds=instance_ids)
        self.ec2_client.get_waiter('instance_running').wait(InstanceIds=instance_ids)
        time.sleep(10)
        instances = self.get_instances()
        for instance in instances:
            public_ip_address = instance['public_ip_address']
            private_ip_address = instance['private_ip_address']
            ssh_key = paramiko.RSAKey.from_private_key_file(str(pem_file))
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(hostname=public_ip_address, username='ubuntu', pkey=ssh_key)
            ftp_client = ssh_client.open_sftp()
            ftp_client.put('scripts/install_openvpn.sh', '/home/ubuntu/scripts/install_openvpn.sh')
            ftp_client.put('scripts/refresh_ip.sh', '/home/ubuntu/scripts/refresh_ip.sh')
            ftp_client.put('scripts/files/99-openvpn-forward.conf',
                           '/home/ubuntu/scripts/files/99-openvpn-forward.conf')
            ftp_client.put('scripts/files/client-common.txt', '/home/ubuntu/scripts/files/client-common.txt')
            ftp_client.put('scripts/files/ip_forward.txt', '/home/ubuntu/scripts/files/ip_forward.txt')
            ftp_client.put('scripts/files/openvpn-iptables.service',
                           '/home/ubuntu/scripts/files/openvpn-iptables.service')
            ftp_client.put('scripts/files/server.conf', '/home/ubuntu/scripts/files/server.conf')
            response = ssh_client.exec_command(f'sudo /home/ubuntu/scripts/refresh_ip.sh {public_ip_address} {private_ip_address}')
            print(response[1].read().decode('utf-8'))
            print(response[2].read().decode('utf-8'))
            ftp_client.get('/home/ubuntu/client.ovpn', 'client.ovpn')
            ftp_client.close()
            ssh_client.close()
        print(f"IP addresses are refreshed.")

    def show_instance_list_selector(self) -> list:
        title = 'Select instance: '
        options = []
        instances = self.get_instances()
        for instance in instances:
            options.append(f"{instance['instance_id']} (IP: {instance['public_ip_address']}) {instance['state']}")
        selected = pick(options, title, multiselect=True, min_selection_count=1)
        return [instances[option[1]] for option in selected]

    def get_instances(self) -> list:
        instances = []
        response = self.ec2_client.describe_instances()['Reservations']
        for reservation in response:
            for instance in reservation['Instances']:
                if instance['State']['Name'] == 'terminated':
                    continue
                instances.append({
                    'state': instance['State']['Name'],
                    'instance_id': instance['InstanceId'],
                    'public_ip_address': instance.get('PublicIpAddress', ''),
                    'private_ip_address': instance.get('PrivateIpAddress', '')
                })
        return instances

    @staticmethod
    def request_confirm(message: str) -> bool:
        options = ['No', 'Yes']
        selected = pick(options, message, min_selection_count=1)
        return selected[0] == 'Yes'
