# awssg

Python script to check one aws security group in use by services in one region

## Motivation

There are many tools to check security group in use, but I wanted to create a tool that would to check the use of one specific security group in a region, and all the aws services using it.

## AWS Security Group basics

A [security group](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html) controls the traffic that is allowed to reach and leave the resources that it is associated with.

You can associate a security group only with resources in the VPC for which it is created.

For example, after you associate a security group with an EC2 instance, it controls the inbound and outbound traffic for the instance.

Services in the VPC with aws security group associated (WIP):

- Amazon EC2 instances

- Elastic Netowrk Interfaces

- Elastic Load Balancing

- Apliaction Load Balancing

- Services that use Amazon EC2 instances:

  - Amazon RDS
  - Amazon Redshift
  - Amazon ElastiCache
  - Amazon ECS
  - Amazon EKS

- Services that launch EC2 instances:

  - Amazon Elastic MapReduce

- Lambda

- Services that use ENI (Elastic Network Interface) and are not directly associated with them:

  - VPC endpoints
  - EFS mountpoint (use VPC endpoints)

## About

The script will check the specified security group id in one region and will return the services using it from this list:

- Amazon EC2 instances (ec2)
- Elastic Network Interface (eni)
- Elastic Load Balancing (elb)
- Application Load Balancer (alb)
- Amazon RDS (rds)
- Amazon Redshift (redshift)
- Amazon ElastiCache (elasticache)
- Amazon ECS (ecs)
- Amazon EKS (eks)
- EFS mountpoint (efs)
- Amazon Elastic MapReduce (emr)
- Lambda (lambda)
- VPC endpoint (vpc)

It is possible check all of them or one specified in the command line. The list of aws resources using the security group will be stored in one json file in the current directory with the format sgid-svc-region.json.

### Prerequisites

- [python3](https://www.python.org/downloads/) or higher and [pip3](https://docs.python.org/3/installing/index.html) (already installed with python3)

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
usage: awssg.py [-h] [-r REGION] [-p PROFILE] -sgid SECURITYGROUPID [-svc [{all,ec2,eni,elb,alb,rds,redshift,elasticache,eks,ecs,efs,emr,lambda,vpc}]] [-o OUTPUT]

Python script to check aws security group use by services in one region

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
                        Set output file name (default 'securitygroupid-region.json')
```

## Usage

First need to be authenticated in AWS with your credentials.

You can use the default profile or use a specific profile with the `-p` option.

You must specify the security group id to check with the `-sgid` option, the other options are optional and have default values availbles in the help `-h`.

You can check all the services in one region or just one, here is a simple example of the use:

```bash
python3 sgcheck.py -p prod -sgid sg-567892f85d -svc alb -r us-east-2
```

The command return the application load balancers (alb) that use the security group `sg-567892f85d` in the region `us-east-2` using the profile `prod` to connect to aws, and save the result in a json file in the current directory with the name `./sg-567892f85d-alb-us-east-2json`.
