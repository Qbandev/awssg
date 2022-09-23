# awssg

Python script to check aws security group use by services in one region

## Motivation

There are many tools to check security group use, but I wanted to create a tool that would allow me to check the use of one specific security groups in a region, and all the services using it as possible.

## About

The script will check the specified security group id in one region and will return the services that use it.

The script will check the following aws services:

- "ec2"
- "eni"
- "elb"
- "alb"
- "rds"
- "redshift"
- "elasticache"
- "eks"
- "ecs"
- "efs"
- "emr"

It will check all of them or the one specified in the command line.

The script will return the information in the console and also in a json file in the current directory.

### Prerequisites

- [python3](https://www.python.org/downloads/) or higher and [pip3](https://docs.python.org/3/installing/index.html)(already installed with python3)

### Installing

Clone the repository to your local machine with the command:

```bash
git clone https://github.com/Qbandev/awssg.git
```

Access the directory with the command:

```bash
cd awssg
```

Install boto3 dependency in `requirements.txt` file. Install with the command:

```bash
python3 -m pip install -r requirements.txt
```

Check if the script is working with the command:

```bash
python3 awssg.py --help
```

Here is the help output:

```bash
python3 sgcheck.py -h
usage: sgcheck.py [-h] [-r REGION] [-p PROFILE] -sgid SECURITYGROUPID [-svc [{all,ec2,eni,elb,alb,rds,redshift,elasticache,eks,ecs,efs,emr}]] [-o OUTPUT]

Find Security Group in AWS region

options:
  -h, --help            show this help message and exit
  -r REGION, --region REGION
                        The AWS region to check (default 'us-east-1')
  -p PROFILE, --profile PROFILE
                        The profile to use for the connection to AWS (default 'default')
  -sgid SECURITYGROUPID, --securitygroupid SECURITYGROUPID
                        The Security Group ID to check (required)
  -svc [{all,ec2,eni,elb,alb,rds,redshift,elasticache,eks,ecs,efs,emr}], --service [{all,ec2,eni,elb,alb,rds,redshift,elasticache,eks,ecs,efs,emr}]
                        AWS Service to check security group (default 'all')
  -o OUTPUT, --output OUTPUT
                        Set output file name (default 'sgid.json').
```

## Usage

You must specify the security group id to check with the `-sgid` other options are optional and have default values.

You can check all the services in one region or just one, here is a simple example of the use:

```bash
python3 sgcheck.py -p prod -sgid sg-567892f85d -svc alb -r us-east-2

[
  "albLoadBalancerName: prod-lb",
  "albLoadBalancerName: system-staging-lb"
]
```

The command return the alb load balancers that use the security group `sg-567892f85d` in the region `us-east-2` and the profile `prod`.

The command output is also saved in a json file in the current directory with the default name `sg-567892f85d.json`.
