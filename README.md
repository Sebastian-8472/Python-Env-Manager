# Python Environment Manager & Auto-Updater

A professional-grade Python utility designed to automate the maintenance of virtual environment packages. This tool ensures your development environment stays up-to-date while prioritizing stability through automated backups, logging, and rollback mechanisms.

## 🌟 Key Features

* **Automated Dependency Scanning**: Identifies outdated packages using `pip` and parses the results via JSON for precise version control.
* **Safety First (Rollback System)**: Automatically creates an environment snapshot (`requirements.txt` style) before performing updates, allowing for immediate recovery if a conflict occurs.
* **Professional Logging**: Implements the `logging` module to provide real-time console feedback and maintain a persistent `updater_debug.log` for audit trails.
* **Environment Restoration**: Includes a dedicated method to rebuild an environment from a requirements file, ensuring reproducibility across different machines.
* **Process Management**: Uses the `subprocess` module to interface safely with the Python interpreter and `pip` CLI.

## 🛠️ Technical Implementation

This project demonstrates core software engineering competencies:
- **OOP (Object-Oriented Programming)**: Logic encapsulated in a clean, maintainable, and reusable class.
- **System Integration**: Managing external CLI tools through Python scripts.
- **Robust Error Handling**: Advanced `try-except` blocks to manage network timeouts, permission issues, and command failures.
- **Documentation**: Methods documented according to the **Google Style Python Docstrings** standard.



## 🚀 Quick Start

### Prerequisites
- Python 3.6+
- Pip 21.0+

### Basic Usage
Simply import the `PyUpdater` class and execute the maintenance cycle:

```python
from py_updater import PyUpdater

# Initialize the manager
updater = PyUpdater()

# Run the full cycle: 
# 1. Backup -> 2. Check Updates -> 3. Upgrade -> 4. Final Logging
updater.update_all(auto_rollback=True)
