import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";
import * as awsx from "@pulumi/awsx";
import * as fs from "fs/promises";

const main = async () => {
	const vpc = new aws.ec2.Vpc("gymbo", {
		cidrBlock: "10.0.0.0/16",
		enableDnsHostnames: true,
		enableDnsSupport: true,
		tags: {
			Name: "gymbo-vpc",
		},
	});

	const igw = new aws.ec2.InternetGateway("gymbo-igw", {
		vpcId: vpc.id,
		tags: {
			Name: "gymbo-igw",
		},
	});

	const routeTable = new aws.ec2.RouteTable("gymbo-rt-public-7a", {
		vpcId: vpc.id,
		routes: [
			{
				cidrBlock: "0.0.0.0/0",
				gatewayId: igw.id,
			},
		],
		tags: {
			Name: "gymbo-rt-public-7a",
		},
	});

	const public_subnet = new aws.ec2.Subnet("gymbo-public-subnet", {
		vpcId: vpc.id,
		availabilityZone: "ap-southeast-7a",
		cidrBlock: "10.0.0.0/24",
		mapPublicIpOnLaunch: true,
		tags: {
			Name: "gymbo-public-subnet",
		},
	});

	const routeTableAssociation = new aws.ec2.RouteTableAssociation(
		"gymbo-rt-assoc-public-7a",
		{
			subnetId: public_subnet.id,
			routeTableId: routeTable.id,
		}
	);

	const pubKey = await fs.readFile("/Users/marcolee/.ssh/aws/gymbo.pub", {
		encoding: "utf-8",
		flag: "r",
	});

	const keyPair = new aws.ec2.KeyPair("gymbo-keypair", {
		keyName: "gymbo-keypair",
		publicKey: pubKey,
	});

	const ec2SecurityGroup = new aws.ec2.SecurityGroup("gymbo-ec2-sg", {
		vpcId: vpc.id,
		egress: [
			{
				fromPort: 0,
				toPort: 0,
				protocol: "-1",
				cidrBlocks: ["0.0.0.0/0"],
			},
		],
		ingress: [
			{
				fromPort: 22,
				toPort: 22,
				protocol: "tcp",
				cidrBlocks: ["112.120.169.40/32"],
			},
			{
				fromPort: 443,
				toPort: 443,
				protocol: "tcp",
				cidrBlocks: ["0.0.0.0/0"],
			},
		],
		tags: {
			Name: "gymbo-ec2-sg",
		},
	});


	const instance = new aws.ec2.Instance("gymbo-instance", {
		instanceType: aws.ec2.InstanceTypes.T3_Medium,
		keyName: keyPair.keyName,
		subnetId: public_subnet.id,
		associatePublicIpAddress: true,
		vpcSecurityGroupIds: [ec2SecurityGroup.id],
    ami: "ami-019a40287c6e93276",
    ebsBlockDevices: [{
      deviceName: "/dev/sda1",
      volumeSize: 64,
      volumeType: "gp3",
      iops: 3000,
    }],
		tags: {
			Name: "gymbo-instance",
		},
	});

	const elasticIp = new aws.ec2.Eip("gymbo-eip", {
		instance: instance.id,
		domain: "vpc",
		tags: {
			Name: "gymbo-eip",
		},
	});

	// const gpuInstance = new aws.ec2.Instance("gymbo-gpu-instance", {
	// 	instanceType: aws.ec2.InstanceTypes.T3_Medium,
	// 	keyName: keyPair.keyName,
	// 	subnetId: public_subnet.id,
	// 	associatePublicIpAddress: true,
	// 	vpcSecurityGroupIds: [ec2SecurityGroup.id],
	// 	ami: "ami-0a6e6f0e5b49f8d0c",
	// 	ebsBlockDevices: [{
	// 		deviceName: "/dev/sda1",
	// 		volumeSize: 64,
	// 		volumeType: "gp3",
	// 		iops: 3000,
	// 	}],
	// 	instanceMarketOptions: {
	// 		marketType: 'spot',
	// 	},
	// 	tags: {
	// 		Name: "gymbo-gpu-instance",
	// 	},
	// });

  const hostedZone = new aws.route53.Zone("gymbo-zone", {
    name: "stixman.co",
  });

  const record = new aws.route53.Record("gymbo-record", {
    zoneId: hostedZone.zoneId,
    name: "api.stixman.co",
    type: "A",
    ttl: 300,
    records: [elasticIp.publicIp],
  });

	const frontendRecord = new aws.route53.Record("gymbo-frontend-record", {
    zoneId: hostedZone.zoneId,
    name: "gymbo.stixman.co",
    type: "CNAME",
    ttl: 300,
    records: ["cname.vercel-dns.com."],
  });

  const gradioRecord = new aws.route53.Record("gymbo-gradio-record", {
    zoneId: hostedZone.zoneId,
    name: "gymbo-gradio.stixman.co",
    type: "A",
    ttl: 300,
    records: [elasticIp.publicIp],
  });
};

main();
