package ec2

// Resource definitions for the EC2 compute module.
// These mirror the Python resource_modules/ec2/resource.py definitions.

// ResourceName constants
const (
	NameEC2              = "EC2"
	NameSecurityGroup    = "SecurityGroup"
	NameNetworkInterface = "NetworkInterface"
)

// AWSService methods
const (
	APIDescribeInstances       = "ec2.describe_instances"
	APIDescribeSecurityGroups = "ec2.describe_security_groups"
	APIDescribeNetworkInterfaces = "ec2.describe_network_interfaces"
)

// BindKey fields
const (
	BindKeyInstanceID       = "instance_id"
	BindKeyGroupID          = "group_id"
	BindKeyNetworkInterfaceID = "network_interface_id"
)

// CMDB resource field mappings
var EC2Fields = map[string]string{
	"instance_id":     "instance_id",
	"instance_type":   "instance_type",
	"state":           "state",
	"vpc_id":          "vpc_id",
	"subnet_id":       "subnet_id",
	"security_groups": "security_groups",
	"private_ip":      "private_ip",
	"public_ip":       "public_ip",
	"name":            "name",
	"launch_time":     "launch_time",
	"availability_zone": "availability_zone",
}

var SecurityGroupFields = map[string]string{
	"group_id":   "group_id",
	"group_name": "group_name",
	"vpc_id":     "vpc_id",
	"description": "description",
}

var NetworkInterfaceFields = map[string]string{
	"network_interface_id": "network_interface_id",
	"vpc_id":               "vpc_id",
	"subnet_id":            "subnet_id",
	"status":               "status",
	"private_ip":           "private_ip",
}
