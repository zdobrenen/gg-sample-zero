// ----------------------------------------------------------------------------
// VPC
// ----------------------------------------------------------------------------


output "vpc_id" {
  value = "${aws_vpc.main.id}"
}


output "vpc_cidr" {
  value = "${aws_vpc.main.cidr_block}"
}



// ----------------------------------------------------------------------------
// Subnets
// ----------------------------------------------------------------------------


# External Subnets
output "external_subnet_ids" {
  value = ["${aws_subnet.external.*.id}"]
}


output "external_subnet_cidrs" {
  value = ["${aws_subnet.external.*.cidr_block}"]
}


output "external_subnet_availability_zones" {
  value = ["${aws_subnet.external.*.availability_zone}"]
}


# Internal Subnets
output "internal_subnet_ids" {
  value = ["${aws_subnet.internal.*.id}"]
}


output "internal_subnet_cidrs" {
  value = ["${aws_subnet.internal.*.cidr_block}"]
}


output "internal_subnet_availability_zones" {
  value = ["${aws_subnet.internal.*.availability_zone}"]
}



// ----------------------------------------------------------------------------
// Bastion Instances
// ----------------------------------------------------------------------------


output "bastion_instance_ids" {
  value = ["${aws_instance.bastion.*.id}"]
}

output "bastion_instance_public_ips" {
  value = ["${aws_instance.bastion.*.public_ip}"]
}

output "bastion_instance_private_ips" {
  value = ["${aws_instance.bastion.*.private_ip}"]
}



// ----------------------------------------------------------------------------
// Security Groups
// ----------------------------------------------------------------------------


output "bastion_sg_id" {
  value = ["${aws_security_group.bastion_sg.id}"]
}

output "bastion_ssh_sg_id" {
  value = ["${aws_security_group.bastion_ssh_sg.id}"]
}
