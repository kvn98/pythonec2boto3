import boto3

# step 1 create ec2 resource and client
ec2_resource = boto3.resource('ec2', region_name='us-west-1')
ec2_client = boto3.client('ec2', region_name='us-west-1')


#step 2: Create a security group that allows ssh and http access
try:
    vpcs =  ec2_client.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['true']}])
    if vpcs['Vpcs']:
        vpc_id= vpcs['Vpcs'][0]['VpcId']
        print(f"using default VPC: {vpc_id}")
    else:
        print("No default VPC fount")
        exit(1)

    # Create security group

    security_group = ec2_client.create_security_group(
        GroupName='web-ssh-access',
        Description='Allow SSH and HTTP access',
        VpcId=vpc_id
    )

    sg_id = security_group['GroupId']
    print(f"Created security group: {sg_id}")

    #add inbound rules

    ec2_client.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[
            {
                'IpProtocol': 'tcp',
                'FromPort': 22,
                'ToPort': 22,
                'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'SSH access'}]
            },
            {
                'IpProtocol': 'tcp',
                'FromPort': 80,
                'ToPort': 80,
                'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'HTTP access'}]
            },
            {
                'IpProtocol': 'tcp',
                'FromPort': 443,
                'ToPort': 443,
                'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'HTTPS access'}]
            }

        ]
    )

    print("Added security group rules for ssh(22), http (80), and https(443)")

except ec2_client.exceptions.ClientError as e :
    if 'InvalidGroup.Duplicate' in str(e):
        # Security group already exists, get its ID
        sgs = ec2_client.describe_security_groups(GroupNames=['web-ssh-access'])
        sg_id = sgs['SecurityGroups'][0]['GroupId']
        print(f"Using existing security group: {sg_id}")
    else:
        print(f"Error creating security group: {e}")
        exit(1)


#ec2 = boto3.resource('ec2', region_name='us-west-2')

# step 2: Launch an EC2 Instance

instances = ec2_resource.create_instances(
    ImageId='ami-043b59f1d11f8f189',
    MinCount = 1,
    MaxCount = 1,
    InstanceType='t2.micro',
    KeyName='ec2testboto33',
    SecurityGroupIds=[sg_id],
    BlockDeviceMappings = [
        {
            'DeviceName': '/dev/sda1',
            'Ebs' : {
                'VolumeSize':20,
                'VolumeType': 'gp2',
                'DeleteOnTermination': False
            }
        }
    ],
    TagSpecifications = [
        {
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key':'Name',
                    'Value': 'FinalEc2Server'
                },
                {
                    'Key':'Env',
                    'Value' : 'Preprod'
                }

            ]
        }
    ],
    UserData = '''#!/bin/bash
    # update the package list
    sudo apt update -y
    # install Apache
    sudo apt install apache2 -y
    # Start Apache Service
    sudo systemctl start apache2
    # Enable the apache service
    sudo systemctl enable apache2
    # Create a simple index.html file
    echo "<html><body><h1>Welcome to Apache Web Server - Lemonstre</h1></body></html>" | sudo tee /var/www/html/index.html
    # Allow Apache from firewall
    # sudo ufw allow 'Apache'
    ''',
)

print("My instance has been created")
