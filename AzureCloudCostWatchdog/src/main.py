#!/usr/bin/env python
"""
Main entry point for the Azure Cloud Cost Watchdog application.

This script provides command-line interface for running the VM monitoring
and shutdown scheduler. It can be used as a standalone script or imported
as a module.
"""

import sys
import argparse
from datetime import datetime
from src.vm_monitor import AzureVMScanner, AzureVMScheduler

def main():
    parser = argparse.ArgumentParser(
        description="Azure Cloud Cost Watchdog - Monitor and shutdown VMs"
    )
    
    parser.add_argument(
        "--subscription-id",
        required=True,
        help="Azure subscription ID to monitor"
    )
    
    parser.add_argument(
        "--resource-group",
        help="Specific resource group to monitor (optional)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode without actually shutting down VMs"
    )
    
    args = parser.parse_args()
    
    print(f"Azure Cloud Cost Watchdog - Starting at {datetime.now()}")
    print(f"Subscription ID: {args.subscription_id}")
    print(f"Resource Group: {args.resource_group or 'All'}")
    print(f"Dry Run: {args.dry_run}")
    
    try:
        scanner = AzureVMScanner(args.subscription_id)
        scheduler = AzureVMScheduler(scanner)
        
        results = scheduler.run_daily_scan()
        
        print("\nScan Results:")
        print(f"  VMs Found: {results['vms_found']}")
        print(f"  VMs Shutdown: {results['vms_shutdown']}")
        print(f"  VMs Ignored: {results['vms_ignored']}")
        
        print("\nDetailed Results:")
        for result in results['detailed_results']:
            print(f"  VM: {result['vm_name']} ({result['resource_group']})")
            print(f"    Action: {result['action_taken']}")
            print(f"    Reason: {result['reason']}")
            print(f"    Tags: {result['tags']}")
        
        if args.dry_run:
            print("\n[DRY RUN MODE] No VMs were actually shut down.")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())