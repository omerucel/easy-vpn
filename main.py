import argparse

from boto_wrapper import BotoWrapper
from easy_vpn import EasyVPN

parser = argparse.ArgumentParser(description='Easy VPN')
parser.add_argument('--profile', type=str, default='default', help='AWS profile name', required=True)
command = parser.add_subparsers(dest='command')
command.add_parser('run', help='Run VPN instance. This command will create a new VPN instance if there is no running instance')
command.add_parser('terminate', help='Delete VPN instance.')
command.add_parser('list', help='Delete VPN instance')
command.add_parser('refresh-ip', help='Refresh VPN instance IP address')
command.add_parser('install-openvpn', help='Install OpenVPN on VPN instance')
command.add_parser('copy-client', help='Copy OpenVPN client to local machine')
command.add_parser('connect', help='Connect to VPN instance')
command.add_parser('disconnect', help='Disconnect from VPN instance')
args = parser.parse_args()


def main():
    boto_wrapper = BotoWrapper(profile_name=args.profile)
    easy_vpn = EasyVPN(boto_wrapper=boto_wrapper)
    easy_vpn.run_command(args.command, args)


if __name__ == '__main__':
    main()
