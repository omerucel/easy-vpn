import os
from argparse import Namespace

from pathlib import Path
from boto_wrapper import BotoWrapper


class EasyVPN:
    def __init__(self, boto_wrapper: BotoWrapper):
        self.boto_wrapper = boto_wrapper
        self.easy_vpn_home = Path.home() / '.easy-vpn'
        self.pem_file = self.easy_vpn_home / 'easy-vpn.pem'
        self.command_mapping = {
            'run': self.run_instance,
            'terminate': self.terminate_instance,
            'list': self.list_instances,
            'refresh-ip': self.refresh_ip,
            'install-openvpn': self.install_openvpn,
            'copy-client': self.copy_client,
            'connect': self.connect,
            'disconnect': self.disconnect
        }

    def run_command(self, command, args):
        self.configure()
        if command in self.command_mapping:
            self.command_mapping[command](args)
        else:
            print("Unknown command")

    def configure(self):
        easy_vpn_home = Path.home() / '.easy-vpn'
        pem_file = easy_vpn_home / 'easy-vpn.pem'
        if not easy_vpn_home.exists():
            os.mkdir(str(easy_vpn_home))
        self.boto_wrapper.create_key_pair(name='easy-vpn', pem_file=pem_file)
        self.boto_wrapper.create_security_group(name='easy-vpn')

    def run_instance(self, args: Namespace):
        self.boto_wrapper.run_instance(self.pem_file)

    def terminate_instance(self, args: Namespace):
        self.boto_wrapper.terminate_instance()

    def list_instances(self, args: Namespace):
        self.boto_wrapper.list_instances()

    def refresh_ip(self, args: Namespace):
        self.boto_wrapper.refresh_ip_address(pem_file=self.pem_file)

    def install_openvpn(self, args: Namespace):
        self.boto_wrapper.install_openvpn(pem_file=self.pem_file)

    def copy_client(self, args: Namespace):
        self.boto_wrapper.copy_client(pem_file=self.pem_file)

    def connect(self, args: Namespace):
        pass

    def disconnect(self, args: Namespace):
        pass
