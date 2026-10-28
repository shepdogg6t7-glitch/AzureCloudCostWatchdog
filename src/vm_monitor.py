from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.resource.resources import ResourceManagementClient
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class VMInfo:
    name: str
    resource_group: str
    location: str
    tags: Dict[str, str]
    power_state: str
    subscription_id: str

class AzureVMScanner:
    def __init__(self, subscription_id: str, credential=None):
        self.credential = credential or DefaultAzureCredential()
        self.subscription_id = subscription_id
        self.compute_client = ComputeManagementClient(self.credential, subscription_id)
        self.resource_client = ResourceManagementClient(self.credential, subscription_id)

    def list_vms(self, resource_group: Optional[str] = None) -> List[VMInfo]:
        vms = []
        
        if resource_group:
            vm_list = self.compute_client.virtual_machines.list(resource_group)
        else:
            vm_list = self.compute_client.virtual_machines.list_all()
        
        for vm in vm_list:
            vm_info = VMInfo(
                name=vm.name,
                resource_group=vm.id.split('/')[4] if vm.id else '',
                location=vm.location,
                tags=vm.tags or {},
                power_state=vm.hardware_profile.vm_size,
                subscription_id=self.subscription_id
            )
            vms.append(vm_info)
        
        return vms

    def get_vm_tags(self, resource_group: str, vm_name: str) -> Dict[str, str]:
        vm = self.compute_client.virtual_machines.get(resource_group, vm_name)
        return vm.tags or {}

    def should_shutdown_vm(self, vm: VMInfo) -> bool:
        tags = vm.tags
        
        if tags.get('Environment') == 'Production':
            return False
        
        if tags.get('AutoShutdown') == 'True':
            return False
        
        if tags.get('Environment') == 'Dev':
            return True
        
        if not tags:
            return True
        
        return False

class AzureVMScheduler:
    def __init__(self, scanner: AzureVMScanner):
        self.scanner = scanner
        self.last_run = None

    def run_daily_scan(self) -> Dict[str, Any]:
        current_time = datetime.now()
        
        if self.last_run and (current_time - self.last_run) < timedelta(hours=24):
            return {"status": "skipped", "message": "Scan already performed within last 24 hours"}
        
        results = {
            "timestamp": current_time.isoformat(),
            "vms_found": 0,
            "vms_shutdown": 0,
            "vms_ignored": 0,
            "detailed_results": []
        }
        
        vms = self.scanner.list_vms()
        results["vms_found"] = len(vms)
        
        for vm in vms:
            action_taken = None
            if self.scanner.should_shutdown_vm(vm):
                self._shutdown_vm(vm)
                action_taken = "shutdown"
                results["vms_shutdown"] += 1
            else:
                action_taken = "ignored"
                results["vms_ignored"] += 1
            
            results["detailed_results"].append({
                "vm_name": vm.name,
                "resource_group": vm.resource_group,
                "action_taken": action_taken,
                "tags": vm.tags,
                "reason": self._get_shutdown_reason(vm)
            })
        
        self.last_run = current_time
        return results

        async def _shutdown_vm(self, vm: VMInfo) -> None:
        # Call the Azure SDK directly
        async_poller = self.compute_client.virtual_machines.begin_deallocate(
            vm.resource_group, vm.name
        )
        
        # Wait for the shutdown to finish
        await async_poller.wait()
        
        logger.info(f"VM {vm.name} in {vm.resource_group} scheduled for shutdown")

    def _get_shutdown_reason(self, vm: VMInfo) -> str:
        tags = vm.tags
        
        if tags.get('Environment') == 'Production':
            return "Skipped - Production environment"
        
        if tags.get('AutoShutdown') == 'True':
            return "Skipped - AutoShutdown enabled"
        
        if tags.get('Environment') == 'Dev':
            return "VM has Dev environment"
        
        if not tags:
            return "No tags present"
        
        return "VM meets shutdown criteria"

if __name__ == "__main__":
    scanner = AzureVMScanner("test-subscription-id")
    scheduler = AzureVMScheduler(scanner)
    
    results = scheduler.run_daily_scan()
    print(f"Scan completed: {results}")