# README.md
![CI](https://github.com/shepdogg6t7-glitch/costwatchdog/actions/workflows/ci.yml/badge.svg)
Azure Cloud Cost Watchdog 🐕💸

A serverless Azure solution designed to monitor resources and automatically shut down non-production or untagged Virtual Machines to prevent cloud bill shock.

## Features
- **Automated Scanning:** Runs on a timer (e.g., daily) to find VMs.
- **Tag-Based Logic:** Ignores VMs tagged with `Environment: Production`. Shuts down VMs missing the `AutoShutdown: True` tag or tagged as `Environment: Dev`.
- **Notifications:** Sends a summary report to a Microsoft Teams/Slack webhook or Email via Logic Apps.

## Architecture
![Architecture](architecture.mmd)

## Prerequisites
- [Terraform](https://www.terraform.io/downloads.html)
- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
- Python 3.9+

## Deployment
1. Authenticate to Azure: `az login`
2. Navigate to `terraform/`: `cd terraform`
3. Initialize: `terraform init`
4. Deploy: `terraform apply -var="webhook_url=<YOUR_WEBHOOK_URL>"`

## Testing
Run local unit tests for the Python function:
```bash
cd src
pip install -r requirements.txt
pytest
```

## Project Structure

```
AzureCloudCostWatchdog/
├── src/
│   ├── vm_monitor.py          # Core VM monitoring logic
│   ├── main.py               # CLI entry point
│   ├── tests/
│   │   ├── test_vm_monitor.py   # Unit tests for VM monitoring
│   │   └── test_basic.py        # Basic functionality tests
│   ├── requirements.txt       # Python dependencies
│   └── vision.md              # Project vision and roadmap
├── terraform/                 # Infrastructure as code
│   ├── main.tf               # Terraform configuration
│   ├── variables.tf          # Input variables
│   └── outputs.tf            # Output values
├── .gitignore                # Git ignore rules
├── LICENSE.md                # License information
└── README.md                 # This file
```

## Usage

### Running the Application

```bash
cd src
python main.py --subscription-id <your-subscription-id> --resource-group <resource-group-name>
```

### Running Tests

```bash
cd src
python -m pytest tests/ -v
```

### Dry Run Mode

To test the application without actually shutting down VMs:

```bash
cd src
python main.py --subscription-id <id> --dry-run
```

## Development

### Adding New Tag Rules

Modify the `should_shutdown_vm()` method in `src/vm_monitor.py` to add or modify tag-based logic.

### Adding New Notifications

Add notification handlers in the `AzureVMScheduler` class or create a separate notification module.

### Running Locally

1. Ensure you have Azure credentials configured (`az login`)
2. Install Python dependencies: `pip install -r src/requirements.txt`
3. Run the application: `cd src && python main.py`

## License

MIT

## Contributing

Contributions are welcome! Please follow the project's coding standards and create pull requests for any changes.

## Support

For issues or questions, please create an issue in the repository.
