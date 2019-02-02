// ----------------------------------------------------------------------------
// Bastion Instances
// ----------------------------------------------------------------------------


resource "aws_instance" "bastion" {
  count                       = "${var.az_count}"

  subnet_id                   = "${element(aws_subnet.external.*.id, count.index)}"
  ami                         = "${var.bastion_ami_id}"
  instance_type               = "t2.micro"
  key_name                    = "${var.key_name}"
  
  source_dest_check           = false
  associate_public_ip_address = true
  
  security_groups = [
    "${aws_security_group.bastion_sg.id}"
  ]

  tags = "${
    map(
      "Name", "bastion-${format("external-%03d", count.index + 1)}",
    )
  }"
}
