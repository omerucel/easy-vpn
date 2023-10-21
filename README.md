# EasyVPN - AWS VPN Automation

EasyVPN is a command-line tool that simplifies the management of VPN instances on Amazon Web Services (AWS). With EasyVPN, you can easily create, manage, and ~~connect~~ to VPN instances for secure network communication.

## Prerequisites

Before using EasyVPN, you need to ensure that you have the following prerequisites in place:

- Python 3.6 or higher
- An AWS profile with the necessary [permissions and credentials](https://docs.aws.amazon.com/keyspaces/latest/devguide/access.credentials.html)

### Sample AWS credentials file:

AWS configuration files are located in the `.aws` directory in your home directory. The default location is `~/.aws/credentials`.

```bash
[tokyo]
region=ap-northeast-1
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
```

## Installation

1. Clone this repository to your local machine or download the script.
2. Install the required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

EasyVPN provides a range of commands and options to manage your AWS VPN instances. Here's how you can use it:

```bash
python main.py [options] command
```

### Options:

- `--profile`: The AWS profile name to use for the VPN instance. Default is 'default'.

### Commands:

- `run`: Run a VPN instance. This command will create a new VPN instance if there is no running instance.
- `terminate`: Delete a VPN instance.
- `list`: List VPN instances.
- `refresh-ip`: Refresh the IP address of a VPN instance. It downloads the latest client files from the VPN instance to root directory.
- `install-openvpn`: Install OpenVPN on a VPN instance. It downloads the latest client files from the VPN instance to root directory after installation.
- `copy-client`: Copy OpenVPN client files from the VPN instance to root directory.

### Example Usage:

#### Create a new VPN instance:
```bash
python main.py --profile=tokyo run
```

#### List VPN instances:
```bash
python main.py --profile=tokyo list
```

#### Install OpenVPN on a VPN instance:
```bash
python main.py --profile=tokyo install-openvpn
```

#### Refresh the IP address of a VPN instance:
```bash
python main.py --profile=tokyo refresh-ip
```

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/omerucel/easy-vpn/blob/main/LICENSE.txt) file for details.

## Issues

If you encounter any issues or have suggestions for improvements, please open an issue on the [GitHub repository](https://github.com/omerucel/easy-vpn).

Thank you for using EasyVPN!