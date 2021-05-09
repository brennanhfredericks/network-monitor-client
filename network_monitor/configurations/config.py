
import os

from typing import Optional, List, Dict

from ..services import Filter


class BaseConfig:
    AppLogEndpoint: str = "General"
    UnknownLogEndpoint: str = "Undefined_Protocols"
    OfflineLogEndpoint: str = "Local"

    def __init__(self, base_log_directory: Optional[str] = "./logs") -> None:
        """
            base_log_directory: base directory where the application will output data generated
        """
        self.BaseLogDirectory: str = base_log_directory

        # create base directories
        os.makedirs(self.local_metadata_storage_path(), exist_ok=True)
        os.makedirs(self.log_storage_path(), exist_ok=True)
        os.makedirs(self.undefined_storage_path(), exist_ok=True)

        self.InterfaceName: str = "eth0"
        self.RemoteMetadataStorage: str = "http://localhost:5050/packets"
        self.ResubmissionInterval: int = 300
        self.FilterSubmissionTraffic: bool = True
        self.Filters: List[Filter] = []

    def local_metadata_storage_path(self) -> str:
        """
            return path where processed packed metadata will be stored
        """
        return os.path.join(self.BaseLogDirectory, self.OfflineLogEndpoint)

    def log_storage_path(self) -> str:
        """
            return path where the logger will store it's data
        """
        return os.path.join(self.BaseLogDirectory, self.AppLogEndpoint)

    def undefined_storage_path(self) -> str:
        """
            return path where the extracter service will store the raw bytes for the undefined protocols
        """
        return os.path.join(self.BaseLogDirectory, self.UnknownLogEndpoint)

    def __str__(self) -> str:

        return f"Interface: {self.InterfaceName} Remote Metadata Storaga: {self.RemoteMetadataStorage}"


class DevConfig(BaseConfig):

    def __init__(self) -> None:

        super(BaseConfig, self).__init__()

        self.RemoteMetadataStorage: str = "http://localhost:5050/packets"
        self.ResubmissionInterval: int = 15
        self.Filters: List[Filter] = [
            Filter("local_traffic", {
                "AF_Packet": {"Interface_Name": "lo",
                              },
            }),
            Filter("backend_traffic", {
                "IPv4": {"Destination_Address": "127.0.0.1"},
                "TCP": {"Destination_Port": 5050}
            })
        ]
