#!/bin/bash

aws ec2 create-network-acl-entry --network-acl-id acl-970f02f3 --rule-number 50 --protocol tcp --port-range From=443,To=443 --cidr-block 0.0.0.0/0 --rule-action deny --ingress
