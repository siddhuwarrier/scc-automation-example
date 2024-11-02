# MSSP Tenant Automation with Cisco Security Cloud Control APIs

This repository contains Python script to automate the set up of a new tenant using the Cisco Security
Cloud Control APIs.

## What does it do?

This is an example project that shows you how to use the SCC APIs to go from zero to having an MSP-managed customer tenant using the SCC APIs.

It does the following:

- Provision a new tenant for your customer, including a cloud-delivered FMC.
- Define a default security policy for your new tenant.
- Onboard your Next-Gen Firewalls to your new tenant.
- Monitor the performance of your Next-Gen Firewalls.

## Pre-requisites
- Python 3.12 or higher
- Pip
- A Security Cloud Control MSSP Portal Account, and a super-admin API token for the MSSP portal
- Cisco FTD firewalls

