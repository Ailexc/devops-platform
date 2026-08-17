package vpc

// Resource definitions for the VPC network module.

const (
	NameVPC    = "VPC"
	NameSubnet = "Subnet"
)

const (
	APIDescribeVpcs    = "ec2.describe_vpcs"
	APIDescribeSubnets = "ec2.describe_subnets"
)

const (
	BindKeyVPCID    = "vpc_id"
	BindKeySubnetID = "subnet_id"
)

var VPCFields = map[string]string{
	"vpc_id":     "vpc_id",
	"cidr_block": "cidr_block",
	"state":      "state",
	"is_default": "is_default",
	"name":       "name",
}

var SubnetFields = map[string]string{
	"subnet_id":     "subnet_id",
	"vpc_id":        "vpc_id",
	"cidr_block":    "cidr_block",
	"availability_zone": "availability_zone",
	"state":         "state",
}
