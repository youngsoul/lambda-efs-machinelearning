# AWS Lambda / EFS Machine Learning network architecture 

## Goal

Create a network architecture to allow a Lambda function to execute a Scikit-Learn machine learning model hosted on EFS.

![TI](./media/title_image.png)


## Overview

The project in this repo demonstrates the following:

* Python CDK to build out the architecture above
* Use an EC2 instance to mount EFS, install machine learning libraries and copy ScikitLearn model to EFS.
* Create a Lambda function in a VPC with access to EFS
* Create a Lambda that loads and executes ScikitLearn model
* Create an API HttpApi endpoint to run model

## Things to Note

* A Lambda must be in a VPC to access EFS
* EFS is accessed on port 2049
* You need to create a security group that allows for NFS traffic on 2049
* The EFS AccessPoint is not visible in EC2 until Lambda tries to mount it.  (I am not sure how to force that in CDK if that is even possible.)
* Lambda's are generally not put into a public subnet (put them in private subnets), and doing so does NOT give the Lambda access to the internet.
* Normally you would setup a 'UserData' script to initialize the EC2 instance but I left the commands as seperate commands.
* Yes, I meant to specify Python3.7
* Why - because the Python version of the Lambda has to match the Python version of the EC2 instance used to install the dependent machine learning library.
* I could have upgraded the Python on the EC2 to 3.9, but I am trying to keep this 'simple'
* I used CDK experimental alpha apis - so it is possible those apis will change and this repo will need to be updated.  It worked as of 3/7/2022.
* The stack creates a security group allowing inbound traffic to the EC2 from a specific IP address.  Update `api_lambda_example/api_lambda_example_stack.py`, line starting with `self.bastion_sg.add_ingress_rule` with you IP address.  Or open up the access, your call.


## Where to start

* Clone the repo
* `pip install -r requirements.txt`
* `cdk deploy --profile <yourprofile>`

## General Steps

* Deploy the stack
* Hit the HttpApi endpoint with a GET.  Again, this causes the `/export/lambda` access point to be visible in the EC2.
* SSH into the EC2 instance
* Run the commands ( shown later ) to install packages and upload model
* Hit the HttpApi endpoint with POST and payload

## Using EC2 to setup FileSystem

The EC2 instance is used to setup the Python environment that will be used by the Lambda function.  The EC2 is also used to copy the model Pickle file to the mounted file system.

```shell
sudo mkdir /mnt/efs
sudo yum install -y amazon-efs-utils
sudo mount -t efs <fs-ID>:/ /mnt/efs
sudo mkdir /mnt/efs/export/lambda/venv
sudo chmod -R go+rwx /mnt/efs
sudo pip3 install --target /mnt/efs/export/lambda/venv pandas
sudo pip3 install --target /mnt/efs/export/lambda/venv scikit-learn

# If you want/need to create the user used in the access point but if you CHMOD you do not need to
sudo useradd --uid 1001 mluser
sudo passwd mluser 
su mluser
```

### Copy Model File

```shell
scp -i ~/.ssh/pryan-aws.pem /Users/patrickryan/Development/aws/cdk-sandbox/api-lambda-example/ml-model/heart_model.pkl ec2-user@<IP address of EC2>:/mnt/efs/export/lambda
```


## Reference Links

A lot of what I put together was pulled from many resources each providing insight, background and gems of examples.

## AWS CDK V2 

https://aws.amazon.com/blogs/developer/experimental-construct-libraries-are-now-available-in-aws-cdk-v2/

### CDKv2 Python Reference

https://docs.aws.amazon.com/cdk/api/v2/python/index.html

### AWS Lambda VPC Endpoint Docs

https://www.alexdebrie.com/posts/aws-lambda-vpc/

https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html#vpc-samples

https://aws.amazon.com/blogs/compute/announcing-improved-vpc-networking-for-aws-lambda-functions/

[EFS with Lambda Playlist](https://www.youtube.com/watch?v=4cquiuAQBco&list=PL5KTLzN85O4L0rYTtGVKxPr4yQ5oHMYOn)
[How to install library on EFS & import in lambda](https://www.youtube.com/watch?v=FA153BGOV_A)

https://dev.to/cdkpatterns/attach-a-filesystem-to-your-aws-lambda-function-3bi9

#### Connecting EC2 to FileSystem
[Watch This: How to create and Mount an Amazon EFS Filesystem ](https://www.youtube.com/watch?v=I9GO3mYeNAM)

To see how to setup access from EC2 to FileSystem see:

https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_efs/README.html

search for: "Mounting the FileSystem using UserData"

#### Install Python3.9 on AWS Linux

https://tecadmin.net/install-python-3-9-on-amazon-linux/

#### Install Python Packages on EFS with EC2 for Lambda

https://towardsdatascience.com/deploying-large-packages-on-aws-lambda-using-efs-3a707f83d918


