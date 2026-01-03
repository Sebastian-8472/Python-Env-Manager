import subprocess
import sys
import json
import datetime
import os

# Logger Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler("updater_debug.log"),  # Save to file
        logging.StreamHandler(sys.stdout)          # Output to console
    ]
)
logger = logging.getLogger(__name__)

class PyUpdater:
    """
    Advanced manager for Python package maintenance with built-in logging.
    
    This class handles checking for outdated packages, creating environment backups,
    and performing batch updates with rollback capabilities.
    """

    def __init__(self):
        """Initializes the updater using the current Python executable."""
        self.python_exe = sys.executable
        self.last_backup = None
        logger.info(f"PyUpdater initialized using: {self.python_exe}")

    def get_outdated_packages(self):
        """
        Retrieves a list of outdated packages.
        
        Returns:
            list: A list of dictionaries containing package update info.
        """
        logger.info("Checking for outdated packages...")
        try:
            result = subprocess.run(
                [self.python_exe, "-m", "pip", "list", "--outdated", "--format=json"],
                capture_output=True, text=True, check=True
            )
            packages = json.loads(result.stdout)
            logger.info(f"Found {len(packages)} outdated packages.")
            return packages
        except subprocess.CalledProcessError as e:
            logger.error(f"Critical error during package check: {e.stderr}")
            raise

    def update_package(self, package_name, current_ver, latest_ver):
        """
        Updates a single package and logs the start and completion status.
        
        Args:
            package_name (str): Name of the package to upgrade.
            current_ver (str): Current installed version.
            latest_ver (str): Target version available.
            
        Returns:
            bool: True if success, False otherwise.
        """
        logger.info(f"STARTING UPDATE: {package_name} ({current_ver} -> {latest_ver})")

        try:
            subprocess.run(
                [self.python_exe, "-m", "pip", "install", "--upgrade", package_name],
                capture_output=True, text=True, check=True
            )
            logger.info(f"COMPLETED: {package_name} is now at version {latest_ver}.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"FAILED: Could not update {package_name}. Error: {e.stderr.strip()}")
            return False

    def create_backup(self, filename=None):
        """
        Creates a snapshot of the current environment.
        
        Args:
            filename (str, optional): Name of the backup file. Defaults to timestamped name.
            
        Returns:
            str: The filename of the created backup.
        """
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backup_env_{timestamp}.txt"

        logger.info(f"Creating safety backup: {filename}")
        try:
            result = subprocess.run(
                [self.python_exe, "-m", "pip", "freeze"],
                capture_output=True, text=True, check=True
            )
            with open(filename, "w", encoding="utf-8") as f:
                f.write(result.stdout)
            self.last_backup = filename
            logger.info("Backup successfully created.")
            return filename
        except Exception as e:
            logger.error(f"Error during backup creation: {e}")
            return None

    def install_from_requirements(self, filename="requirements_updated.txt"):
        """
        Installs packages listed in a requirements file to recreate an environment.

        Args:
            filename (str): Path to the .txt requirements file.

        Returns:
            bool: True if installation was successful, False otherwise.
        """
        if not os.path.exists(filename):
            logger.error(f"Error: The file '{filename}' does not exist.")
            return False

        logger.info(f"Starting package installation from '{filename}'...")
        try:
            # -r tells pip to read from a requirements file
            subprocess.run(
                [self.python_exe, "-m", "pip", "install", "-r", filename],
                check=True
            )
            logger.info(f"Environment successfully restored from '{filename}'.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error during bulk installation: {e}")
            return False

    def rollback(self, filename=None):
        """
        Restores the environment using a backup file.
        """
        target = filename or self.last_backup
        if not target:
            logger.error("No backup file available for rollback.")
            return False
        
        logger.warning(f"Initiating rollback from file: {target}")
        return self.install_from_requirements(target)

    def update_all(self, auto_rollback=False):
        """
        Performs the complete update cycle with detailed logging and optional rollback.

        Args:
            auto_rollback (bool): If True, restores backup if any update fails.
        """
        logger.info("=== Starting Global Maintenance Procedure ===")

        # 1. Backup
        backup_file = self.create_backup()
        if not backup_file:
            logger.critical("Procedure aborted: Backup failed.")
            return

        # 2. Identification
        outdated = self.get_outdated_packages()
        if not outdated:
            logger.info("All modules are up to date. Nothing to do.")
            return

        # 3. Update Loop
        success_count = 0
        failure_count = 0

        for pkg in outdated:
            if self.update_package(pkg['name'], pkg['version'], pkg['latest_version']):
                success_count += 1
            else:
                failure_count += 1

        # 4. Final Report
        logger.info("=== OPERATION SUMMARY ===")
        logger.info(f"Total packages processed: {len(outdated)}")
        logger.info(f"Successful updates: {success_count}")
        logger.info(f"Failed updates: {failure_count}")

        if failure_count > 0:
            if auto_rollback:
                logger.warning("Failures detected. Starting automatic rollback...")
                self.rollback(backup_file)
            else:
                logger.warning(f"Attention: {failure_count} packages were not updated. Check the log.")

        logger.info("=== Procedure Finished ===")

# --- Usage Example ---
if __name__ == "__main__":
    updater = PyUpdater()

    # Example A: Update everything and save
    updater.update_all(auto_rollback=True)

    # Example B: Restore environment from an existing file
    # updater.install_from_requirements("requirements_updated.txt")
