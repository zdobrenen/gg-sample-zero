// ----------------------------------------------------------------------------
// VPC
// ----------------------------------------------------------------------------


resource "aws_vpc" "main" {

  cidr_block              = "10.0.0.0/16"
  enable_dns_hostnames    = true

  tags = "${
    map(
      "Name", "${var.cluster_name}-${var.vpc_name}-vpc",
      "kubernetes.io/cluster/${var.cluster_name}", "shared",
    )
  }"
}



// ----------------------------------------------------------------------------
// Subnets
// ----------------------------------------------------------------------------


# External Subnets
resource "aws_subnet" "external" {
  count                   = "${var.az_count}"
  
  vpc_id                  = "${aws_vpc.main.id}"
  availability_zone       = "${data.aws_availability_zones.available.names[count.index]}"
  cidr_block              = "${format("10.0.10%d.0/24", count.index + 1)}"

  map_public_ip_on_launch = "true"

  tags = "${
    map(
      "Name", "${var.cluster_name}-${var.vpc_name}-${format("external-%03d", count.index + 1)}",
      "kubernetes.io/cluster/${var.cluster_name}", "shared",
    )
  }"
}


# Internal Subnets
resource "aws_subnet" "internal" {
  count                   = "${var.az_count}"
  
  vpc_id                  = "${aws_vpc.main.id}"
  availability_zone       = "${data.aws_availability_zones.available.names[count.index]}"
  cidr_block              = "${format("10.0.11%d.0/24", count.index + 1)}"

  map_public_ip_on_launch = "false"

  tags = "${
    map(
      "Name", "${var.cluster_name}-${format("internal-%03d", count.index + 1)}",
      "kubernetes.io/cluster/${var.cluster_name}", "shared",
      "kubernetes.io/role/internal-elb", 1
    )
  }"
}



// ----------------------------------------------------------------------------
// Gateways
// ----------------------------------------------------------------------------


# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id                  = "${aws_vpc.main.id}"

  tags = "${
    map(    
      "Name", "${var.cluster_name}-igw",
    )
  }"
}


# NAT Gateways
resource "aws_eip" "nat" {
  count                   = "${var.az_count}"
  
  vpc                     = true
}


resource "aws_nat_gateway" "nat" {
  count                   = "${var.az_count}"
  
  depends_on              = ["aws_internet_gateway.main"]
  allocation_id           = "${element(aws_eip.nat.*.id, count.index)}"
  subnet_id               = "${element(aws_subnet.external.*.id, count.index)}"

  tags = "${
    map(
      "Name", "${var.cluster_name}-${format("external-%03d", count.index + 1)}-ngw",
    )
  }"
}



// ----------------------------------------------------------------------------
// Route Tables
// ----------------------------------------------------------------------------


# External Route Table
resource "aws_route_table" "external" {
  vpc_id                  = "${aws_vpc.main.id}"

  route {
      cidr_block          = "0.0.0.0/0"
      gateway_id          = "${aws_internet_gateway.main.id}"
  }

  tags = "${
    map(
      "Name", "${var.cluster_name}-external-rt",
    )
  }"
}


# External Route Table Association
resource "aws_route_table_association" "external" {
  count                   = "${var.az_count}"

  subnet_id               = "${element(aws_subnet.external.*.id, count.index)}"
  route_table_id          = "${aws_route_table.external.id}"
}


# Internal Route Table
resource "aws_route_table" "internal" {
  count                   = "${var.az_count}"
  
  vpc_id                  = "${aws_vpc.main.id}"

  route {
      cidr_block          = "0.0.0.0/0"
      nat_gateway_id      = "${element(aws_nat_gateway.nat.*.id, count.index)}"
  }

  tags = "${
    map(
      "Name", "${var.cluster_name}-${format("internal-%03d", count.index + 1)}-ngw",
    )
  }"
}


# Internal Route Table Association
resource "aws_route_table_association" "internal" {
  count                   = "${var.az_count}"
  
  subnet_id               = "${element(aws_subnet.internal.*.id, count.index)}"
  route_table_id          = "${element(aws_route_table.internal.*.id, count.index)}"
}
