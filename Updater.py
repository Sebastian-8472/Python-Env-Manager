import subprocess
import sys
import json
import datetime
import os
import logging

# Logger configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler("updater_debug.log"),  # Save on a file
        logging.StreamHandler(sys.stdout)  # Show in the screen
    ]
)
logger = logging.getLogger(__name__)


class PyUpdater:
    """
        A utility class to manage and automate Python package updates.

        Attributes:
            python_exe (str): The path to the current Python executable.
    """

    def __init__(self):
        self.python_exe = sys.executable
        self.last_backup = None
        logger.info(f"Initialized PyUpdater using: {self.python_exe}")

    def get_outdated_packages(self):
        """
        Retrieves a list of outdated packages using pip.

        Returns:
            list: A list of dictionaries containing package details
                  (name, current version, latest version).
        """
        logger.info("Checking for obsolete packages...")
        try:
            result = subprocess.run(
                [self.python_exe, "-m", "pip", "list", "--outdated", "--format=json"],
                capture_output=True, text=True, check=True
            )
            packages = json.loads(result.stdout)
            logger.info(f"Found {len(packages)} obsolete packages.")
            return packages
        except subprocess.CalledProcessError as e:
            logger.error(f"Critical error while checking packets: {e.stderr}")
            raise e

    def update_package(self, package_name, current_version, latest_version):
        """
        Updates a specific package to a target version or the latest available.

        Args:
            package_name (str): The name of the package to update.
            current_version (str): The current version installed (use "any" for targeted updates).
            latest_version (str): The version to install. If "latest", it uses --upgrade.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        try:
            if latest_version == "latest":
                command = [self.python_exe, "-m", "pip", "install", "--upgrade", package_name]
            else:
                command = [self.python_exe, "-m", "pip", "install", f"{package_name}=={latest_version}"]

            subprocess.run(command, check=True, capture_output=True)
            logger.info(f"Successfully updated {package_name} to {latest_version}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to update {package_name}: {e}")
            return False

    def update_from_file(self, file_path):
        """
        Updates packages based on a list provided in a text file.

        The file should contain one package name per line. Empty lines or
        lines starting with '#' (comments) are automatically ignored.

        Args:
            file_path (str): The path to the text file containing package names.

        Returns:
            dict: A summary of the operation containing 'success' and 'failed' counts.
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return {"success": 0, "failed": 0}

        logger.info(f"Reading target packages from: {file_path}")

        packages = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Skips empty line
                    if line and not line.startswith("#"):
                        # If the line has pkg==version, it takes only the name
                        pkg_name = line.split("==")[0].split(">=")[0].strip()
                        packages.append(pkg_name)
        except IOError as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return {"success": 0, "failed": 0}

        if not packages:
            logger.warning("No valid package names found in the file.")
            return {"success": 0, "failed": 0}

        return self.update_target(packages)

    def create_backup(self, filename=None):
        """
        Creates a backup of the current environment's packages.

        Args:
            filename (str): The name of the file where the backup will be saved.

        Returns:
            str: The path to the created backup file, or None if the operation fails.
        """
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backup_env_{timestamp}.txt"

        logger.info(f"Creating a security backup: {filename}")
        try:
            result = subprocess.run(
                [self.python_exe, "-m", "pip", "freeze"],
                capture_output=True, text=True, check=True
            )
            with open(filename, "w", encoding="utf-8") as f:
                f.write(result.stdout)
            self.last_backup = filename
            logger.info("Backup created successfully.")
            return filename
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return None

    def install_from_requirements(self, filename="requirements_updated.txt"):
        """
        Installs the packages listed in a requirements file to recreate an environment.

        This method is the opposite of generate_requirements. It reads the specified file
        and performs a bulk installation of all listed dependencies and versions.

        Args:
        filename (str): The path to the .txt file to read the packages from.
        Default: 'requirements_updated.txt'.

        Returns:
        bool: True if the installation was successful, False otherwise.

        Raises:
        FileNotFoundError: If the specified file does not exist.
        """
        if not os.path.exists(filename):
            logger(f"Error: The file {filename} does not exist.")
            return False

        logger.info(f"Start installing packages from {filename}...")
        try:
            # -r tells pip to read from a requirements file
            subprocess.run(
                [self.python_exe, "-m", "pip", "install", "-r", filename],
                check=True
            )
            logger.info(f"Environment successfully restored from file {filename}.")
            return True
        except subprocess.CalledProcessError as e:
            logger.info(f"Error during mass installation: {e}")
            return False

    def update_all(self, export_requirements=True):
        """
        Automatically updates all outdated packages in the current environment.

        This method identifies all packages with available updates and iterates
        through them to perform the installation. Optionally, it can trigger
        a generation of an updated requirements file after the process.

        Args:
            export_requirements (bool): If True, calls generate_requirements()
                                        after all updates are completed.
                                        Defaults to True.

        Returns:
            None
        """
        outdated = self.get_outdated_packages()
        if not outdated:
            logger.info("All packages are already up to date.")
            return

        for pkg in outdated:
            # We assume update_package handles the logic for each individual module
            self.update_package(pkg['name'])

        if export_requirements:
            self.generate_requirements()

    def rollback(self, backup_file):
        """
        Reverts the Python environment to a previous state using a backup file.

        This method attempts to restore the environment by installing the exact
        versions specified in the backup requirements file. It is typically
        called when an update process fails.

        Args:
            backup_file (str): The path to the requirements backup file (e.g., 'requirements_backup.txt').

        Returns:
            bool: True if the rollback was successful, False otherwise.
        """
        if not os.path.exists(backup_file):
            logger.error(f"Rollback failed: Backup file {backup_file} not found.")
            return False

        logger.info(f"Initiating rollback using backup: {backup_file}...")

        try:
            # Optional: You may want to uninstall everything first,
            # but pip install -r usually overrides correctly.
            command = [self.python_exe, "-m", "pip", "install", "-r", backup_file]

            # performing the recovery
            subprocess.run(command, check=True, capture_output=True)

            logger.info("Rollback completed successfully. Environment restored.")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Critical error during rollback: {e}")
            # Here you could add some additional emergency logic
            return False

    def generate_requirements(self, filename="requirements.txt"):
        """
        Generates a requirements.txt file based on the currently installed packages.

        This method uses the 'pip freeze' command to capture the exact state
        of the environment and saves it to a file. This is useful for
        environment reproducibility after updates.

        Args:
            filename (str): The name or path of the file to be created.
                            Defaults to "requirements.txt".

        Returns:
            bool: True if the file was generated successfully, False otherwise.
        """
        logger.info(f"Generating updated requirements file: {filename}...")

        try:
            # Run 'pip freeze' to get the current state
            result = subprocess.run(
                [self.python_exe, "-m", "pip", "freeze"],
                check=True,
                capture_output=True,
                text=True
            )

            # Write output to file
            with open(filename, "w", encoding="utf-8") as f:
                f.write(result.stdout)

            logger.info(f"Successfully exported dependencies to {filename}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to capture installed packages: {e}")
            return False
        except IOError as e:
            logger.error(f"Failed to write to file {filename}: {e}")
            return False

# --- Example of use ---
if __name__ == "__main__":
    updater = PyUpdater()

    # Example A: Update all and save
    # updater.update_all()

    # Example B: Restore the environment from an existing file
    # updater.install_from_requirements("requirements_updated.txt")