import pytest
from unittest.mock import Mock, patch, MagicMock
from vm_monitor import AzureVMScanner, AzureVMScheduler, VMInfo
from datetime import datetime, timedelta

class TestAzureVMScanner:
    @pytest.fixture
    def mock_credential(self):
        return Mock()

    @pytest.fixture
    def scanner(self, mock_credential):
        with patch('vm_monitor.ComputeManagementClient') as mock_compute, \
             patch('vm_monitor.ResourceManagementClient') as mock_resource:
            scanner_instance = AzureVMScanner("test-sub-id", mock_credential)
            scanner_instance.compute_client = mock_compute
            scanner_instance.resource_client = mock_resource
            return scanner_instance

    def test_vm_info_dataclass(self):
        vm = VMInfo(
            name="test-vm",
            resource_group="test-rg",
            location="eastus",
            tags={"Environment": "Dev", "AutoShutdown": "True"},
            power_state="Running",
            subscription_id="test-sub"
        )
        
        assert vm.name == "test-vm"
        assert vm.resource_group == "test-rg"
        assert vm.tags["Environment"] == "Dev"
        assert vm.tags["AutoShutdown"] == "True"

    def test_should_shutdown_vm_production(self, scanner):
        vm = VMInfo(
            name="test-vm",
            resource_group="test-rg",
            location="eastus",
            tags={"Environment": "Production"},
            power_state="Running",
            subscription_id="test-sub"
        )
        
        assert scanner.should_shutdown_vm(vm) == False

    def test_should_shutdown_vm_autosShutdown_true(self, scanner):
        vm = VMInfo(
            name="test-vm",
            resource_group="test-rg",
            location="eastus",
            tags={"AutoShutdown": "True", "Environment": "Dev"},
            power_state="Running",
            subscription_id="test-sub"
        )
        
        assert scanner.should_shutdown_vm(vm) == False

    def test_should_shutdown_vm_dev(self, scanner):
        vm = VMInfo(
            name="test-vm",
            resource_group="test-rg",
            location="eastus",
            tags={"Environment": "Dev"},
            power_state="Running",
            subscription_id="test-sub"
        )
        
        assert scanner.should_shutdown_vm(vm) == True

    def test_should_shutdown_vm_no_tags(self, scanner):
        vm = VMInfo(
            name="test-vm",
            resource_group="test-rg",
            location="eastus",
            tags={},
            power_state="Running",
            subscription_id="test-sub"
        )
        
        assert scanner.should_shutdown_vm(vm) == True

    def test_list_vms(self, scanner):
        mock_vm = Mock()
        mock_vm.name = "test-vm"
        mock_vm.id = "/subscriptions/test-sub/resourceGroups/test-rg/providers/Microsoft.Compute/virtualMachines/test-vm"
        mock_vm.location = "eastus"
        mock_vm.tags = {"Environment": "Dev"}
        mock_vm.hardware_profile.vm_size = "Standard_B2s"
        
        scanner.compute_client.virtual_machines.list.return_value = [mock_vm]
        
        vms = scanner.list_vms("test-rg")
        
        assert len(vms) == 1
        assert vms[0].name == "test-vm"
        assert vms[0].resource_group == "test-rg"
        assert vms[0].tags["Environment"] == "Dev"

    def test_get_vm_tags(self, scanner):
        mock_vm = Mock()
        mock_vm.tags = {"Environment": "Prod", "AutoShutdown": "False"}
        
        scanner.compute_client.virtual_machines.get.return_value = mock_vm
        
        tags = scanner.get_vm_tags("test-rg", "test-vm")
        
        assert tags["Environment"] == "Prod"
        assert tags["AutoShutdown"] == "False"

class TestAzureVMScheduler:
    @pytest.fixture
    def mock_scanner(self):
        scanner = Mock(spec=AzureVMScanner)
        scanner.should_shutdown_vm = Mock(side_effect=lambda vm: vm.tags.get("Environment") == "Dev")
        scanner.list_vms.return_value = []
        return scanner

    @pytest.fixture
    def scheduler(self, mock_scanner):
        return AzureVMScheduler(mock_scanner)

    def test_run_daily_scan_skips_if_recent(self, scheduler):
        scheduler.last_run = datetime.now() - timedelta(hours=12)
        
        result = scheduler.run_daily_scan()
        
        assert result["status"] == "skipped"
        assert "Scan already performed" in result["message"]
        assert scheduler.scanner.list_vms.call_count == 0

    def test_run_daily_scan_full_run(self, scheduler):
        scheduler.last_run = datetime.now() - timedelta(days=2)
        
        vm1 = VMInfo(
            name="vm1",
            resource_group="rg1",
            location="eastus",
            tags={"Environment": "Dev"},
            power_state="Running",
            subscription_id="sub1"
        )
        
        vm2 = VMInfo(
            name="vm2",
            resource_group="rg2",
            location="eastus",
            tags={"Environment": "Production"},
            power_state="Running",
            subscription_id="sub1"
        )
        
        scheduler.scanner.list_vms.return_value = [vm1, vm2]
        
        with patch.object(scheduler, '_shutdown_vm') as mock_shutdown:
            result = scheduler.run_daily_scan()
        
        assert result["vms_found"] == 2
        assert result["vms_shutdown"] == 1
        assert result["vms_ignored"] == 1
        assert mock_shutdown.call_count == 1
        
        assert any(r["vm_name"] == "vm1" and r["action_taken"] == "shutdown" for r in result["detailed_results"])
        assert any(r["vm_name"] == "vm2" and r["action_taken"] == "ignored" for r in result["detailed_results"])

    def test_get_shutdown_reason_dev(self, scheduler):
        vm = VMInfo(
            name="test-vm",
            resource_group="rg",
            location="eastus",
            tags={"Environment": "Dev"},
            power_state="Running",
            subscription_id="sub"
        )
        
        reason = scheduler._get_shutdown_reason(vm)
        assert "VM in Dev environment" in reason

    def test_get_shutdown_reason_production(self, scheduler):
        vm = VMInfo(
            name="test-vm",
            resource_group="rg",
            location="eastus",
            tags={"Environment": "Production"},
            power_state="Running",
            subscription_id="sub"
        )
        
        reason = scheduler._get_shutdown_reason(vm)
        assert "Skipped - Production environment" in reason

    def test_get_shutdown_reason_no_tags(self, scheduler):
        vm = VMInfo(
            name="test-vm",
            resource_group="rg",
            location="eastus",
            tags={},
            power_state="Running",
            subscription_id="sub"
        )
        
        reason = scheduler._get_shutdown_reason(vm)
        assert "No tags present" in reason

@pytest.fixture
def test_vm_monitoring_logic():
    """Test helper for VM monitoring logic"""
    vm = VMInfo(
        name="test-vm",
        resource_group="test-rg",
        location="eastus",
        tags={"Environment": "Dev"},
        power_state="Running",
        subscription_id="test-sub"
    )
    
    scanner = Mock(spec=AzureVMScanner)
    scheduler = AzureVMScheduler(scanner)
    
    return vm, scanner, scheduler

if __name__ == "__main__":
    pytest.main([__file__, "-v"])