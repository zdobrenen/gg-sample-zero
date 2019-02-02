//-----------------------------------------------------------------------------
// K8S Cluster
//-----------------------------------------------------------------------------


variable "cluster_name" {
  description = "name of Kubernetes Cluster"
  type        = "string"
  default     = "k8s-cluster"
}



//-----------------------------------------------------------------------------
// VPC
//-----------------------------------------------------------------------------


variable "vpc_name" {
  description = "name of vpc"
  type        = "string"
  default     = "main"
}



//-----------------------------------------------------------------------------
// Availability Zones
//-----------------------------------------------------------------------------


variable "az_count" {
  description = "count of desired availabilty zones in region"
  type        = "string"
  default     = 2
}



//-----------------------------------------------------------------------------
// Subnets
//-----------------------------------------------------------------------------



//-----------------------------------------------------------------------------
// Bastion Instances
//-----------------------------------------------------------------------------


variable "bastion_ami_id" {
  description = "Bastion AMI ID"
  type        = "string"
  default     = "ami-9899c7f8"
}


variable "key_name" {
  description = "EC2 ssh Key Pair"
  type        = "string"
  default     = "dev-keys"
}


variable "whitelist_ip_ranges" {
  description = "External IP addresses to whitelist with Bastion instance(s)"
  type        = "list"
  default     = ["0.0.0.0/0"]
}
