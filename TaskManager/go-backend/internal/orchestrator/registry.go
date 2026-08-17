package orchestrator

import (
	"fmt"
)

// ResourceGroupDef defines a logical group of resources.
type ResourceGroupDef struct {
	Name      string        `json:"name"`
	Resources []*ResourceDef `json:"resources"`
}

// ResourceDef defines a single resource type.
type ResourceDef struct {
	Name         string         `json:"name"`
	AWSService   string         `json:"aws_service"`
	BindKey      string         `json:"bind_key"`
	Associations []Association  `json:"associations,omitempty"`
}

// Association defines a relationship between two resource types.
type Association struct {
	Target      string `json:"target"`
	Cardinality string `json:"cardinality"`
	Key         string `json:"key"`
	Description string `json:"description"`
}

// RelationDef defines a global association between two resource types.
type RelationDef struct {
	Source      string `json:"source"`
	Target      string `json:"target"`
	Cardinality string `json:"cardinality"`
	Key         string `json:"key"`
	Description string `json:"description"`
}

// Registry is the central registry of all known resource types, groups and relations.
type Registry struct {
	groups       map[string]*ResourceGroupDef
	individual   map[string]*ResourceDef
	relations    []*RelationDef
	relationKeys map[string]bool
}

// NewRegistry creates a new empty registry.
func NewRegistry() *Registry {
	return &Registry{
		groups:       make(map[string]*ResourceGroupDef),
		individual:   make(map[string]*ResourceDef),
		relations:    make([]*RelationDef, 0),
		relationKeys: make(map[string]bool),
	}
}

// RegisterGroup registers a resource group with its resources.
func (r *Registry) RegisterGroup(group *ResourceGroupDef) {
	r.groups[group.Name] = group
	for _, res := range group.Resources {
		r.individual[res.Name] = res
		for _, assoc := range res.Associations {
			key := res.Name + ":" + assoc.Target
			if !r.relationKeys[key] {
				r.relationKeys[key] = true
				r.relations = append(r.relations, &RelationDef{
					Source:      res.Name,
					Target:      assoc.Target,
					Cardinality: assoc.Cardinality,
					Key:         assoc.Key,
					Description: assoc.Description,
				})
			}
		}
	}
}

// GetGroup returns a resource group by name.
func (r *Registry) GetGroup(name string) *ResourceGroupDef {
	return r.groups[name]
}

// GetResource returns a resource definition by name.
func (r *Registry) GetResource(name string) *ResourceDef {
	return r.individual[name]
}

// ListGroups returns all registered resource groups.
func (r *Registry) ListGroups() []*ResourceGroupDef {
	groups := make([]*ResourceGroupDef, 0, len(r.groups))
	for _, g := range r.groups {
		groups = append(groups, g)
	}
	return groups
}

// ListResources returns all registered resource definitions.
func (r *Registry) ListResources() []*ResourceDef {
	resources := make([]*ResourceDef, 0, len(r.individual))
	for _, res := range r.individual {
		resources = append(resources, res)
	}
	return resources
}

// ListRelations returns all globally unique relation definitions.
func (r *Registry) ListRelations() []*RelationDef {
	return r.relations
}

// GetRelation returns a relation by source and target.
func (r *Registry) GetRelation(source, target string) *RelationDef {
	for _, rel := range r.relations {
		if rel.Source == source && rel.Target == target {
			return rel
		}
	}
	return nil
}

// GroupRelations returns relations whose source belongs to the given group.
func (r *Registry) GroupRelations(groupName string) []*RelationDef {
	group := r.groups[groupName]
	if group == nil {
		return nil
	}
	names := make(map[string]bool)
	for _, res := range group.Resources {
		names[res.Name] = true
	}
	var result []*RelationDef
	for _, rel := range r.relations {
		if names[rel.Source] {
			result = append(result, rel)
		}
	}
	return result
}

// ── Module Task Resolver ────────────────────────────────────────────

// ModuleTaskMap maps resource type names to their worker task types.
var ModuleTaskMap = map[string]string{
	"EC2":              "resource_sync",
	"SecurityGroup":    "resource_sync",
	"NetworkInterface": "resource_sync",
	"VPC":              "resource_sync",
	"Subnet":           "resource_sync",
	"RDS":              "resource_sync",
}

// ResolveResourceTaskType returns the task type for a resource.
func ResolveResourceTaskType(resName string) (string, error) {
	taskType, ok := ModuleTaskMap[resName]
	if !ok {
		return "", fmt.Errorf("no task mapping for resource type: %s", resName)
	}
	return taskType, nil
}

// ── Default Registry ────────────────────────────────────────────────

// DefaultRegistry creates and populates the default registry with EC2/VPC/RDS modules.
func DefaultRegistry() *Registry {
	r := NewRegistry()

	// EC2 / 计算 group
	ec2Group := &ResourceGroupDef{
		Name: "计算",
		Resources: []*ResourceDef{
			{
				Name:       "EC2",
				AWSService: "ec2",
				BindKey:    "instance_id",
				Associations: []Association{
					{Target: "VPC", Cardinality: "n:1", Key: "vpc_id", Description: "EC2所在的VPC"},
					{Target: "Subnet", Cardinality: "n:1", Key: "subnet_id", Description: "EC2所在的子网"},
					{Target: "SecurityGroup", Cardinality: "n:n", Key: "security_groups", Description: "EC2关联的安全组"},
				},
			},
			{
				Name:       "SecurityGroup",
				AWSService: "ec2",
				BindKey:    "group_id",
				Associations: []Association{
					{Target: "VPC", Cardinality: "n:1", Key: "vpc_id", Description: "安全组所属VPC"},
				},
			},
			{
				Name:       "NetworkInterface",
				AWSService: "ec2",
				BindKey:    "network_interface_id",
				Associations: []Association{
					{Target: "VPC", Cardinality: "n:1", Key: "vpc_id", Description: "网卡所属VPC"},
					{Target: "Subnet", Cardinality: "n:1", Key: "subnet_id", Description: "网卡所属子网"},
				},
			},
		},
	}

	// VPC / 网络 group
	vpcGroup := &ResourceGroupDef{
		Name: "网络",
		Resources: []*ResourceDef{
			{
				Name:       "VPC",
				AWSService: "ec2",
				BindKey:    "vpc_id",
				Associations: []Association{
					{Target: "EC2", Cardinality: "1:n", Key: "vpc_id", Description: "VPC内的EC2实例"},
					{Target: "Subnet", Cardinality: "1:n", Key: "vpc_id", Description: "VPC内的子网"},
				},
			},
			{
				Name:       "Subnet",
				AWSService: "ec2",
				BindKey:    "subnet_id",
				Associations: []Association{
					{Target: "VPC", Cardinality: "n:1", Key: "vpc_id", Description: "子网所属VPC"},
				},
			},
		},
	}

	// RDS / 存储 group
	rdsGroup := &ResourceGroupDef{
		Name: "存储",
		Resources: []*ResourceDef{
			{
				Name:       "RDS",
				AWSService: "rds",
				BindKey:    "db_instance_identifier",
				Associations: []Association{
					{Target: "VPC", Cardinality: "n:1", Key: "vpc_id", Description: "RDS实例所属VPC"},
					{Target: "EC2", Cardinality: "n:n", Key: "vpc_id", Description: "同VPC内的EC2"},
				},
			},
		},
	}

	r.RegisterGroup(ec2Group)
	r.RegisterGroup(vpcGroup)
	r.RegisterGroup(rdsGroup)

	return r
}
