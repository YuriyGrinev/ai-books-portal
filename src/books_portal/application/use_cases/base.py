from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from ..dto.common.base import BaseDTO

InputDTO = TypeVar("InputDTO", bound=BaseDTO)
OutputDTO = TypeVar("OutputDTO", bound=BaseDTO)


class UseCase(Generic[InputDTO, OutputDTO], ABC):
    """Base use case class"""
    
    @abstractmethod
    async def execute(self, input_dto: InputDTO) -> OutputDTO:
        """Execute use case"""
        pass 