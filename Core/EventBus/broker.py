import abc
from typing import Callable, Awaitable, Dict, List, Any, Optional, TypeVar, Generic

from Core.EventBus.message import Message

T = TypeVar('T')
MessageCallback = Callable[[Message], Awaitable[None]]


class MessageBroker(abc.ABC):
    """
    Abstract base class for message brokers.

    This class defines the interface that all message broker implementations
    must adhere to.
    """

    @abc.abstractmethod
    async def connect(self) -> None:
        """
        Connect to the message broker.

        This method should establish a connection to the underlying
        message broker system.
        """
        pass

    @abc.abstractmethod
    async def disconnect(self) -> None:
        """
        Disconnect from the message broker.

        This method should properly close the connection to the
        underlying message broker system.
        """
        pass

    @abc.abstractmethod
    async def publish(self, message: Message) -> None:
        """
        Publish a message to the broker.

        Args:
            message: The message to publish
        """
        pass

    @abc.abstractmethod
    async def subscribe(self, topic: str, callback: MessageCallback) -> None:
        """
        Subscribe to a topic.

        Args:
            topic: The topic to subscribe to
            callback: The callback to invoke when a message is received
        """
        pass

    @abc.abstractmethod
    async def unsubscribe(self, topic: str) -> None:
        """
        Unsubscribe from a topic.

        Args:
            topic: The topic to unsubscribe from
        """
        pass

    @abc.abstractmethod
    async def start_listening(self) -> None:
        """
        Start listening for messages.

        This method should start the process of listening for messages
        on all subscribed topics.
        """
        pass

    @abc.abstractmethod
    async def stop_listening(self) -> None:
        """
        Stop listening for messages.

        This method should stop the process of listening for messages.
        """
        pass


class BrokerFactory:
    """
    Factory for creating message broker instances.

    This class provides methods for creating and registering
    message broker implementations.
    """
    _brokers: Dict[str, type] = {}

    @classmethod
    def register(cls, name: str, broker_class: type) -> None:
        """
        Register a broker implementation.

        Args:
            name: The name of the broker
            broker_class: The broker class
        """
        cls._brokers[name] = broker_class

    @classmethod
    def create(cls, name: str, **kwargs) -> MessageBroker:
        """
        Create a broker instance.

        Args:
            name: The name of the broker to create
            **kwargs: Additional arguments to pass to the broker constructor

        Returns:
            MessageBroker: A new broker instance

        Raises:
            ValueError: If the broker name is not registered
        """
        if name not in cls._brokers:
            raise ValueError(f"Broker '{name}' not registered")

        return cls._brokers[name](**kwargs)

    @classmethod
    def get_available_brokers(cls) -> List[str]:
        """
        Get a list of available broker names.

        Returns:
            List[str]: A list of registered broker names
        """
        return list(cls._brokers.keys())