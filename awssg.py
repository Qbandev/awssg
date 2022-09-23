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
            "all", "ec2", "eni", "elb", "alb", "rds",
            "redshift", "elasticache", "eks", "ecs", "efs", "emr"),
        help="AWS Service to check security group (default 'all')",
    )
    parser.add_argument(
        "-o",
        "--output",
        action="store",
        type=str,
        help="Set output file name (default 'securitygroupid-region.json')",
    )
    args = parser.parse_args()

    # Set boto3 environment variable to use new endpoint format.
    # See FutureWarning https://github.com/boto/botocore/issues/2705 for more details
    os.environ['BOTO_DISABLE_COMMONNAME'] = 'True'

    # Open Boto3 session
    session = boto3.session.Session(profile_name=args.profile)

    # Create the SG dictionary to store the data
    sg_associations = []

    try:
        # Get security group by instances
        if args.service in ("all", "ec2"):
            ec2_client = session.client("ec2", region_name=args.region)
            instances_dict = ec2_client.describe_instances()
            reservations = instances_dict["Reservations"]
            for i in reservations:
                for j in i["Instances"]:
                    for k in j["SecurityGroups"]:
                        if k["GroupId"] == args.securitygroupid:
                            sg_associations.append(
                                "ec2InstanceId: " + i["Instances"][0]["InstanceId"])

        # Security Groups in use by Network Interfaces
        if args.service in ("all", "eni"):
            eni_dict = ec2_client.describe_network_interfaces()
            for i in eni_dict["NetworkInterfaces"]:
                for j in i["Groups"]:
                    if j["GroupId"] == args.securitygroupid:
                        sg_associations.append(
                            "eniNetworkInterfaceId: " + i["NetworkInterfaceId"])

        # Security groups used by classic ELBs
        if args.service in ("all", "elb"):
            elb_client = session.client("elb", region_name=args.region)
            elb_dict = elb_client.describe_load_balancers()
            for i in elb_dict["LoadBalancerDescriptions"]:
                for j in i["SecurityGroups"]:
                    if j == args.securitygroupid:
                        sg_associations.append(
                            "elbLoadBalancerName: " + i["LoadBalancerName"])

        # Security groups used by ALBs
        if args.service in ("all", "alb"):
            elb2_client = session.client("elbv2", region_name=args.region)
            elb2_dict = elb2_client.describe_load_balancers()
            for i in elb2_dict["LoadBalancers"]:
                if "SecurityGroups" in i.keys():
                    for j in i["SecurityGroups"]:
                        if j == args.securitygroupid:
                            sg_associations.append(
                                "albLoadBalancerName: " + i["LoadBalancerName"])

        # Security groups used by RDS
        if args.service in ("all", "rds"):
            rds_client = session.client("rds", region_name=args.region)
            rds_dict = rds_client.describe_db_instances()
            for i in rds_dict["DBInstances"]:
                for j in i["VpcSecurityGroups"]:
                    if j["VpcSecurityGroupId"] == args.securitygroupid:
                        sg_associations.append(
                            "rdsDBInstanceIdentifier: " + i["DBInstanceIdentifier"])

        # Security groups used by Redshift
        if args.service in ("all", "redshift"):
            redshift_client = session.client(
                "redshift", region_name=args.region)
            redshift_dict = redshift_client.describe_clusters()
            for i in redshift_dict["Clusters"]:
                for j in i["VpcSecurityGroups"]:
                    if j["VpcSecurityGroupId"] == args.securitygroupid:
                        sg_associations.append(
                            "redshiftClusterIdentifier: " + i["ClusterIdentifier"])

        # Security groups used by Elasticache
        if args.service in ("all", "elasticache"):
            elasticache_client = session.client(
                "elasticache", region_name=args.region)
            elasticache_dict = elasticache_client.describe_cache_clusters()
            for i in elasticache_dict["CacheClusters"]:
                for j in i["SecurityGroups"]:
                    if j["SecurityGroupId"] == args.securitygroupid:
                        sg_associations.append(
                            "elasticacheCacheClusterId: " + i["CacheClusterId"])

        # Security groups used by EKS
        if args.service in ("all", "eks"):
            eks_client = session.client("eks", region_name=args.region)
            eks_dict = eks_client.list_clusters()
            for i in eks_dict["clusters"]:
                eks_sg_dict = eks_client.describe_cluster(name=i)
                for j in eks_sg_dict["cluster"]["resourcesVpcConfig"]["securityGroupIds"]:
                    if j == args.securitygroupid:
                        sg_associations.append("eksClusterId: " + i)

        # Security groups used by ECS
        if args.service in ("all", "ecs"):
            ecs_client = session.client("ecs", region_name=args.region)
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
            efs_client = session.client("efs", region_name=args.region)
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
            emr_client = session.client("emr", region_name=args.region)
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

    except botocore.exceptions.ClientError as err:
        if err.response['Error']['Code'] == 'InternalError':  # Generic error
            # We grab the message
            print("Internal error: " + err.response['Error']['Message'])
        else:
            raise err

    # Save the results to a file
    filename = args.output
    if filename is None:
        filename = args.securitygroupid+"-"+args.region+".json"

    with open(filename, "w", encoding="utf-8") as file:
        file.write(json.dumps(sg_associations, indent=2, sort_keys=True))

except KeyboardInterrupt:
    print("\nCtrl+C Caught, Terminating")
