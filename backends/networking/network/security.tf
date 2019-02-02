// ----------------------------------------------------------------------------
// Security Groups
// ----------------------------------------------------------------------------


# VPC Security Group
resource "aws_security_group" "vpc_sg" {
  vpc_id        = "${aws_vpc.main.id}"
  name          = "${var.vpc_name}-sg"

  # Allow all outbound
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [
      "0.0.0.0/0"
    ]
  }

  # Allow all internal
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [
      "10.0.0.0/16"
    ]
  }

  tags = "${
    map(
      "Name", "${var.vpc_name}-sg",
    )
  }"
}


# Bastion Instance Security Group
resource "aws_security_group" "bastion_sg" {
  name          = "bastion-security-group"
  description   = "Allow SSH to Bastion host from approved ranges"

  vpc_id        = "${aws_vpc.main.id}"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = "${var.whitelist_ip_ranges}"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [
      "0.0.0.0/0"
    ]
  }

  tags = "${
    map(
      "Name", "bastion-security-group",
    )
  }"
}


# Bastion Instance SSH Security Group
resource "aws_security_group" "bastion_ssh_sg" {
  name          = "bastion-ssh-security-group"
  description   = "Allow SSH from Bastion host(s)"
  
  depends_on    = ["aws_security_group.bastion_sg"]

  vpc_id        = "${aws_vpc.main.id}"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [
      "${aws_subnet.external.*.cidr_block}"
    ]

    security_groups = [
      "${aws_security_group.bastion_sg.id}"
    ]
  }

  tags = "${
    map(
      "Name", "bastion-ssh-security-group",
    )
  }"
}
