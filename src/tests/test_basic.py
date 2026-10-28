import pytest
from unittest.mock import Mock
from vm_monitor import VMInfo, AzureVMScanner

class TestVMInfo:
    def test_vm_info_creation(self):
        vm = VMInfo(
            name="test-vm",
            resource_group="test-rg",
            location="eastus",
            tags={"Environment": "Dev"},
            power_state="Running",
            subscription_id="test-sub"
        )
        
        assert vm.name == "test-vm"
        assert vm.resource_group == "test-rg"
        assert vm.location == "eastus"
        assert vm.tags["Environment"] == "Dev"
        assert vm.power_state == "Running"
        assert vm.subscription_id == "test-sub"

    def test_vm_info_with_empty_tags(self):
        vm = VMInfo(
            name="test-vm",
            resource_group="test-rg",
            location="eastus",
            tags={},
            power_state="Stopped",
            subscription_id="test-sub"
        )
        
        assert vm.tags == {}
        assert vm.power_state == "Stopped"

class TestAzureVMScannerLogic:
    def test_should_shutdown_vm_logic(self):
        scanner = AzureVMScanner("test-sub")
        
        # Test production VM should not be shutdown
        prod_vm = VMInfo(
            name="prod-vm",
            resource_group="rg",
            location="eastus",
            tags={"Environment": "Production"},
            power_state="Running",
            subscription_id="test-sub"
        )
        
        assert scanner.should_shutdown_vm(prod_vm) == False
        
        # Test VM with AutoShutdown: True should not be shutdown
        auto_shutdown_vm = VMInfo(
            name="auto-vm",
            resource_group="rg",
            location="eastus",
            tags={"AutoShutdown": "True", "Environment": "Dev"},
            power_state="Running",
            subscription_id="test-sub"
        )
        
        assert scanner.should_shutdown_vm(auto_shutdown_vm) == False
        
        # Test Dev environment VM should be shutdown
        dev_vm = VMInfo(
            name="dev-vm",
            resource_group="rg",
            location="eastus",
            tags={"Environment": "Dev"},
            power_state="Running",
            subscription_id="test-sub"
        )
        
        assert scanner.should_shutdown_vm(dev_vm) == True
        
        # Test VM with no tags should be shutdown
        untagged_vm = VMInfo(
            name="untagged-vm",
            resource_group="rg",
            location="eastus",
            tags={},
            power_state="Running",
            subscription_id="test-sub"
        )
        
        assert scanner.should_shutdown_vm(untagged_vm) == True

    def test_should_shutdown_vm_edge_cases(self):
        scanner = AzureVMScanner("test-sub")
        
        # Test VM with Environment: Staging (should be shutdown based on current logic)
        staging_vm = VMInfo(
            name="staging-vm",
            resource_group="rg",
            location="eastus",
            tags={"Environment": "Staging"},
            power_state="Running",
            subscription_id="test-sub"
        )
        
        # Current logic: only Production and AutoShutdown=True prevent shutdown
        # So Staging should NOT be shutdown (falls through to return False)
        assert scanner.should_shutdown_vm(staging_vm) == False
        
        # Test VM with AutoShutdown: false (lowercase)
        false_auto_vm = VMInfo(
            name="false-auto-vm",
            resource_group="rg",
            location="eastus",
            tags={"AutoShutdown": "false"},
            power_state="Running",
            subscription_id="test-sub"
        )
        
        # AutoShutdown="false" is not "True", but there are tags and no specific conditions met
        # So should NOT be shutdown (falls through to return False)
        assert scanner.should_shutdown_vm(false_auto_vm) == False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])