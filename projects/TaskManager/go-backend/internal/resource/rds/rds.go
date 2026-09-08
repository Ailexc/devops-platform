package rds

// Resource definitions for the RDS storage module.

const (
	NameRDS = "RDS"
)

const (
	APIDescribeDBInstances = "rds.describe_db_instances"
)

const (
	BindKeyDBInstanceIdentifier = "db_instance_identifier"
)

var RDSFields = map[string]string{
	"db_instance_identifier": "db_instance_identifier",
	"db_instance_class":      "db_instance_class",
	"engine":                 "engine",
	"engine_version":         "engine_version",
	"status":                 "status",
	"vpc_id":                 "vpc_id",
	"availability_zone":      "availability_zone",
	"allocated_storage":      "allocated_storage",
	"multi_az":               "multi_az",
}
