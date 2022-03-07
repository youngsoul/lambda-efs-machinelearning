from aws_cdk import (
    Stack,
    aws_apigatewayv2_alpha as api_gw,
    aws_apigatewayv2_integrations_alpha as integrations,
    CfnOutput,
    aws_lambda_python_alpha as lambda_alpha_,
    aws_lambda as _lambda,
    aws_ec2 as ec2,
    aws_efs as efs,
    RemovalPolicy,
    Duration

)
from constructs import Construct

resources_prefix = "ML"

class ApiLambdaExampleStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # EFS needs to be setup in a VPC
        self.vpc = ec2.Vpc(self, id=f'{resources_prefix}-VPC',
                           cidr='10.40.0.0/16',  # 65536 available addresses in vpc
                           max_azs=1,  # max availability zones
                           enable_dns_hostnames=True,
                           # enable public dns address, and gives EC2 auto-assign dns host names to instances
                           enable_dns_support=True,  # 0.2 dns server is used, use Amazon DNS server
                           subnet_configuration=[
                               ec2.SubnetConfiguration(
                                   name="Public",
                                   subnet_type=ec2.SubnetType.PUBLIC,  # has internet gateway associated.
                                   # resources are accessible from the internet
                                   # resources can access internet
                                   cidr_mask=24  # means a subnet mask of: 255.255.255.0 meaning there
                                   # are 251  usable IP addresses in the PUBLIC subnet
                               )
                           ],
                           # keep nat gateways off unless you really need
                           # this because it costs money
                           nat_gateways=None  # always provisioned in public subnet.
                           # should be same as azs for failure
                           )

        self.bastion_sg = ec2.SecurityGroup(self, id=f'{resources_prefix}-bastion-sg',
                                            security_group_name=f'{resources_prefix}-cdk-bastion-sg',
                                            vpc=self.vpc,
                                            description=f'{resources_prefix} SG for Bastion',
                                            allow_all_outbound=True)

        # create a security group that allows anyone associated with the
        # security group to access the NFS 2049 port
        self.efs_access_sg = ec2.SecurityGroup(self, id=f'{resources_prefix}-efs-access-sg',
                                            security_group_name=f'{resources_prefix}-cdk-efs-access-sg',
                                            vpc=self.vpc,
                                            description=f'{resources_prefix} SG for EFS',
                                            allow_all_outbound=False)
        self.efs_access_sg.add_ingress_rule(peer=self.efs_access_sg,
                                         connection=ec2.Port.tcp(2049),
                                        description='EFS Access')

        # commented out because below I am instructing the filesystem
        # to specifically grant access to the bastion.
        # self.efs_access_sg.add_ingress_rule(peer=self.bastion_sg,
        #                                  connection=ec2.Port.tcp(2049),
        #                                 description='EFS Access')


        # add SSH inbound rule
        # self.bastion_sg.add_ingress_rule(ec2.Peer.any_ipv4(), # any machine is allowed to ssh
        #                                  ec2.Port.tcp(22),
        #                                 description='SSH Access')
        self.bastion_sg.add_ingress_rule(peer=ec2.Peer.ipv4('73.209.223.60/32'),  # only my machine
                                         connection=ec2.Port.tcp(22),
                                         description='SSH Access')



        # The following 2 ingress rules add access to port 8000, which is not needed right now
        # self.bastion_sg.add_ingress_rule(ec2.Peer.any_ipv4(), # any machine is allowed to ssh
        #                                  ec2.Port.tcp(8000),
        #                                 description='HTTP Access')
        # self.bastion_sg.add_ingress_rule(ec2.Peer.ipv4('73.209.223.60/32'),  # only my machine
        #                                  ec2.Port.tcp(8000),
        #                                  description='HTTP Access')

        self.bastion_host = ec2.Instance(self, id=f'{resources_prefix}-bastion-host',
                                         instance_type=ec2.InstanceType(instance_type_identifier='t2.micro'),
                                         machine_image=ec2.AmazonLinuxImage(
                                             edition=ec2.AmazonLinuxEdition.STANDARD,
                                             generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
                                             virtualization=ec2.AmazonLinuxVirt.HVM,
                                             storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE
                                         ),
                                         vpc=self.vpc,
                                         key_name='pryan-aws',  # must create the key name manually first
                                         # this is the pem private/public key
                                         vpc_subnets=ec2.SubnetSelection(
                                             # this will create the ec2 instance in one of the PUBLIC subnets of the VPC that we just defined above
                                             subnet_type=ec2.SubnetType.PUBLIC
                                         ),
                                         security_group=self.bastion_sg
                                         )


        # Create the FileSystem before adding user data to the bastion host
        # Create a file system in EFS to store information
        fs = efs.FileSystem(self, f'{resources_prefix}-FileSystem',
                            vpc=self.vpc,
                            security_group=self.efs_access_sg,
                            removal_policy=RemovalPolicy.DESTROY)

        # if we use user: 1000, I believe this is the ec2-user so
        # we would  not have to create a user.
        # uid: 1000 ec2-user
        # uid: 1001 yet to be created user
        access_point = fs.add_access_point(f'{resources_prefix}-LambdaAccessPoint',
                                           create_acl=efs.Acl(owner_gid='1001', owner_uid='1001', permissions='755'),
                                           path="/export/lambda",
                                           posix_user=efs.PosixUser(gid="1000", uid="1001"))

        """
        from: https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_efs/README.html
           section: "Mounting the FileSystem using UserData 
        
        instance.user_data.add_commands("yum check-update -y", "yum upgrade -y", "yum install -y amazon-efs-utils", "yum install -y nfs-utils", "file_system_id_1=" + fs.file_system_id, "efs_mount_point_1=/mnt/efs/fs1", "mkdir -p "${efs_mount_point_1}"", "test -f "/sbin/mount.efs" && echo "${file_system_id_1}:/ ${efs_mount_point_1} efs defaults,_netdev" >> /etc/fstab || " + "echo "${file_system_id_1}.efs." + Stack.of(self).region + ".amazonaws.com:/ ${efs_mount_point_1} nfs4 nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport,_netdev 0 0" >> /etc/fstab", "mount -a -t efs,nfs4 defaults")

        """



        # if I do this, do I still need to setup the security groups?
        fs.connections.allow_default_port_from(self.bastion_host)


        # The code that defines your stack goes here
        lb1 = lambda_alpha_.PythonFunction(self, f"{resources_prefix}-heartfailure-function",
                                           entry="./ml_lambda",
                                           index="heart_failure_lambda.py",
                                           handler="lambda_handler",
                                           runtime=_lambda.Runtime.PYTHON_3_7,
                                           vpc=self.vpc,
                                           security_groups=[
                                               self.efs_access_sg
                                           ],
                                           timeout=Duration.seconds(300),
                                           allow_public_subnet=True,
                                           filesystem=_lambda.FileSystem.from_efs_access_point(access_point,'/mnt/model'),
                                           environment={
                                               "PYTHONPATH": "/mnt/model/venv"
                                           }

        )

        # defines an API Gateway Http API resource backed by our "efs_lambda" function.
        api = api_gw.HttpApi(self, f'{resources_prefix}-Test API Lambda',
                             default_integration=integrations.HttpLambdaIntegration(id="lb1-lambda-proxy",
                                                                                    handler=lb1))

        CfnOutput(self, 'HTTP API Url', value=api.url)
        CfnOutput(self, 'FileSystem ID', value=fs.file_system_id)
        CfnOutput(
            scope=self,
            id="PublicIp",
            value=self.bastion_host.instance_public_ip,
            description="public ip of bastion host",
            export_name="ec2-public-ip")

        ec2_init_script_template = f"""
sudo mkdir /mnt/efs
sudo yum install -y amazon-efs-utils
sudo mount -t efs {fs.file_system_id}:/ /mnt/efs
# make sure lambda creates the export/lambda access pt
mkdir /mnt/efs/export/lambda/venv
sudo chmod -R go+rwx /mnt/efs
sudo pip3 install --target /mnt/efs/export/lambda/venv pandas
sudo pip3 install --target /mnt/efs/export/lambda/venv scikit-learn

"""
        print(ec2_init_script_template)
        print("--------")
        print(f"scp -i ~/.ssh/pryan-aws.pem /Users/patrickryan/Development/aws/cdk-sandbox/api-lambda-example/ml-model/heart_model.pkl ec2-user@{self.bastion_host.instance_public_ip}:/mnt/efs/export/lambda")
