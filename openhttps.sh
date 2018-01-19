#!/bin/bash

aws ec2 delete-network-acl-entry --network-acl-id acl-970f02f3 --rule-number 50 --ingress
