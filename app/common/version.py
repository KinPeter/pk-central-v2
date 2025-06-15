import os


def get_version() -> str:
    version_file_path = os.path.join(os.path.dirname(__file__), "../../.version")
    if os.path.exists(version_file_path):
        with open(version_file_path, "r") as version_file:
            return version_file.read().strip()
    else:
        return "unknown"
