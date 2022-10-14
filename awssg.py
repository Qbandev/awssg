#!/usr/bin/env python
"""Import modules"""
import os
import argparse
import json
import boto3
import botocore

try:
    parser = argparse.ArgumentParser(
        description="Python script to check aws security group use by services in one region")
    parser.add_argument(
        "-r",
        "--region",
        type=str,
        default="us-east-1",
        help="The AWS region to check (default 'us-east-1')"
    )
    parser.add_argument(
        "-p",
        "--profile",
        type=str,
        default="default",
        help="The profile to use for the connection to AWS (default 'default')",
    )
    parser.add_argument(
        "-sgid",
        "--securitygroupid",
        type=str,
        default=None,
        help="The Security Group ID to check (required)",
        required=True,
    )
    parser.add_argument(
        "-svc",
        "--service",
        action="store",
        type=str,
        default="all",
        nargs="?",
        choices=(
            "all", "ec2", "elb", "alb", "rds",
            "redshift", "elasticache", "eks", "ecs", "efs", "emr", "lambda", "vpc", "eni"),
        help="AWS Service to check security group (default 'all')",
    )
    parser.add_argument(
        "-o",
        "--output",
        action="store",
        type=str,
        help="Set output file name (default 'securitygroupid-service-region.json')",
    )
    args = parser.parse_args()

    # Set boto3 environment variable to use new endpoint format.
    # See FutureWarning https://github.com/boto/botocore/issues/2705 for more details
    os.environ['BOTO_DISABLE_COMMONNAME'] = 'True'

    # Open Boto3 session
    session = boto3.session.Session(profile_name=args.profile, region_name=args.region)

    # Create the SG dictionary to store the data
    sg_associations = []

    try:
        # Get security group by instances
        if args.service in ("all", "ec2"):
            ec2_client = session.client("ec2")
            instances_dict = ec2_client.describe_instances()
            reservations = instances_dict["Reservations"]
            for i in reservations:
                for j in i["Instances"]:
                    for k in j["SecurityGroups"]:
                        if k["GroupId"] == args.securitygroupid:
                            sg_associations.append(
                                "ec2Id: " + i["Instances"][0]["InstanceId"])

        # Security groups used by classic ELBs
        if args.service in ("all", "elb"):
            elb_client = session.client("elb")
            elb_dict = elb_client.describe_load_balancers()
            for i in elb_dict["LoadBalancerDescriptions"]:
                for j in i["SecurityGroups"]:
                    if j == args.securitygroupid:
                        sg_associations.append(
                            "elbName: " + i["LoadBalancerName"])

        # Security groups used by ALBs
        if args.service in ("all", "alb"):
            elb2_client = session.client("elbv2")
            elb2_dict = elb2_client.describe_load_balancers()
            for i in elb2_dict["LoadBalancers"]:
                if "SecurityGroups" in i.keys():
                    for j in i["SecurityGroups"]:
                        if j == args.securitygroupid:
                            sg_associations.append(
                                "albName: " + i["LoadBalancerName"])

        # Security groups used by RDS
        if args.service in ("all", "rds"):
            rds_client = session.client("rds")
            rds_dict = rds_client.describe_db_instances()
            for i in rds_dict["DBInstances"]:
                for j in i["VpcSecurityGroups"]:
                    if j["VpcSecurityGroupId"] == args.securitygroupid:
                        sg_associations.append(
                            "rdsId: " + i["DBInstanceIdentifier"])

        # Security groups used by Redshift
        if args.service in ("all", "redshift"):
            redshift_client = session.client(
                "redshift")
            redshift_dict = redshift_client.describe_clusters()
            for i in redshift_dict["Clusters"]:
                for j in i["VpcSecurityGroups"]:
                    if j["VpcSecurityGroupId"] == args.securitygroupid:
                        sg_associations.append(
                            "redshiftId: " + i["ClusterIdentifier"])

        # Security groups used by Elasticache
        if args.service in ("all", "elasticache"):
            elasticache_client = session.client(
                "elasticache")
            elasticache_dict = elasticache_client.describe_cache_clusters()
            for i in elasticache_dict["CacheClusters"]:
                for j in i["SecurityGroups"]:
                    if j["SecurityGroupId"] == args.securitygroupid:
                        sg_associations.append(
                            "elasticacheId: " + i["CacheClusterId"])

        # Security groups used by EKS
        if args.service in ("all", "eks"):
            eks_client = session.client("eks")
            eks_dict = eks_client.list_clusters()
            for i in eks_dict["clusters"]:
                eks_sg_dict = eks_client.describe_cluster(name=i)
                for j in eks_sg_dict["cluster"]["resourcesVpcConfig"]["securityGroupIds"]:
                    if j == args.securitygroupid:
                        sg_associations.append("eksId: " + i)

        # Security groups used by ECS
        if args.service in ("all", "ecs"):
            ecs_client = session.client("ecs")
            ecs_dict = ecs_client.list_clusters()
            for i in ecs_dict["clusterArns"]:
                ecs_svc_dict = ecs_client.list_services(cluster=i)
                for k in ecs_svc_dict["serviceArns"]:
                    ecs_sg_dict = ecs_client.describe_services(
                        cluster=i, services=[k])
                    for j in ecs_sg_dict["services"][0]["networkConfiguration"]["awsvpcConfiguration"]["securityGroups"]:
                        if j == args.securitygroupid:
                            sg_associations.append(
                                "ecsClusterId: " +
                                i.split(":cluster/", 1)[1] +
                                " ecsServiceName: "
                                + ecs_sg_dict["services"][0]["serviceArn"].split(":service/")[1])

        # Security groups used by EFS
        if args.service in ("all", "efs"):
            efs_client = session.client("efs")
            efs_dict = efs_client.describe_file_systems()
            for i in efs_dict["FileSystems"]:
                efs_mount_dict = efs_client.describe_mount_targets(
                    FileSystemId=i["FileSystemId"])
                for j in efs_mount_dict["MountTargets"]:
                    efs_dict_sg = efs_client.describe_mount_target_security_groups(
                        MountTargetId=j["MountTargetId"])
                    for k in efs_dict_sg["SecurityGroups"]:
                        if k == args.securitygroupid:
                            sg_associations.append(
                                "efsFileSystemId: " + j["FileSystemId"]
                                + " efsMountTargetId: " + j["MountTargetId"])

        # Security groups used by EMR
        if args.service in ("all", "emr"):
            emr_client = session.client("emr")
            emr_dict = emr_client.list_clusters()
            for i in emr_dict["Clusters"]:
                if i["Status"]["State"] == "WAITING":
                    emr_sg_dict = emr_client.describe_cluster(
                        ClusterId=i["Id"])
                    # Get the security group ID from the EMR cluster
                    if emr_sg_dict["Cluster"]["Ec2InstanceAttributes"]["EmrManagedMasterSecurityGroup"] == args.securitygroupid:
                        sg_associations.append(
                            "emrClusterName: " + i["Name"])
                    if emr_sg_dict["Cluster"]["Ec2InstanceAttributes"]["EmrManagedSlaveSecurityGroup"] == args.securitygroupid:
                        sg_associations.append(
                            "emrClusterName: " + i["Name"])
                    if emr_sg_dict["Cluster"]["Ec2InstanceAttributes"]["AdditionalMasterSecurityGroups"] == args.securitygroupid:
                        sg_associations.append(
                            "emrClusterName: " + i["Name"])
                    if emr_sg_dict["Cluster"]["Ec2InstanceAttributes"]["AdditionalSlaveSecurityGroups"] == args.securitygroupid:
                        sg_associations.append(
                            "emrClusterName: " + i["Name"])

        # Security groups used by Lambda
        if args.service in ("all", "lambda"):
            lambda_client = session.client("lambda")
            lambda_dict = lambda_client.list_functions()
            for i in lambda_dict["Functions"]:
                if "VpcConfig" in i.keys():
                    for j in i["VpcConfig"]["SecurityGroupIds"]:
                        if j == args.securitygroupid:
                            sg_associations.append(
                                "lambdaFunctionName: " + i["FunctionName"])

        # Security groups used by VPC endpoints
        if args.service in ("all", "vpc"):
            vpc_client = session.client("ec2")
            vpc_dict = vpc_client.describe_vpc_endpoints()
            for i in vpc_dict["VpcEndpoints"]:
                if "Groups" in i.keys():
                    for j in i["Groups"]:
                        if j["GroupId"] == args.securitygroupid:
                            sg_associations.append(
                                "vpcEndpointId: " + i["VpcEndpointId"])

        # Security Groups in use by Network Interfaces
        if args.service in ("all", "eni"):
            ec2_client = session.client("ec2")
            eni_dict = ec2_client.describe_network_interfaces()
            for i in eni_dict["NetworkInterfaces"]:
                for j in i["Groups"]:
                    if j["GroupId"] == args.securitygroupid:
                        sg_associations.append(
                            "eniId: " + i["NetworkInterfaceId"])


    except botocore.exceptions.ClientError as err:
        if err.response['Error']['Code'] == 'InternalError':  # Generic error
            # We grab the message
            print("Internal error: " + err.response['Error']['Message'])
        else:
            raise err

    # Save the results to a file
    filename = args.output
    if filename is None:
        filename = args.securitygroupid+"-"+args.service+"-"+args.region+".json"

    with open(filename, "w", encoding="utf-8") as file:
        file.write(json.dumps(sg_associations, indent=2, sort_keys=True))

except KeyboardInterrupt:
    print("\nCtrl+C Caught, Terminating")
