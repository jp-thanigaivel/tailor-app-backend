from abc import ABC, abstractmethod

from app.common.models import AppDTO

class ProcessInterface(ABC):

    @abstractmethod
    def process_data(self, app_data_trans_obj: AppDTO) -> AppDTO:
        pass

class OtpGenerationInterface(ABC):

    @abstractmethod
    def process_data(self, **kwargs) -> str:
        pass