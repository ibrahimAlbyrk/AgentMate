import inspect
from typing import Dict, Any, Type, TypeVar, Optional, get_type_hints

T = TypeVar('T')


class DependencyContainer:
    """
    A container for managing dependencies and their lifecycle.

    This class is responsible for registering, resolving, and managing
    the lifecycle of dependencies throughout the application.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DependencyContainer, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, callable] = {}
        self._singletons: Dict[Type, Any] = {}

    def register(self, service_type: Type[T], implementation: Optional[Any] = None) -> None:
        """
        Register a service with its implementation.

        Args:
            service_type: The type or interface to register
            implementation: The implementation instance or class
        """
        if implementation is None:
            implementation = service_type

        self._services[service_type] = implementation

    def register_factory(self, service_type: Type[T], factory: callable) -> None:
        """
        Register a factory function for creating service instances.

        Args:
            service_type: The type or interface to register
            factory: A callable that creates instances of the service
        """
        self._factories[service_type] = factory

    def register_singleton(self, service_type: Type[T], implementation: Optional[Any] = None) -> None:
        """
        Register a service as a singleton.

        Args:
            service_type: The type or interface to register
            implementation: The implementation instance or class
        """
        if implementation is None:
            implementation = service_type

        self._services[service_type] = implementation
        self._singletons[service_type] = None

    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve a service instance.

        Args:
            service_type: The type or interface to resolve

        Returns:
            An instance of the requested service

        Raises:
            KeyError: If the service type is not registered
        """
        if service_type in self._singletons and self._singletons[service_type] is not None:
            return self._singletons[service_type]

        if service_type in self._factories:
            instance = self._factories[service_type]()
            if service_type in self._singletons:
                self._singletons[service_type] = instance
            return instance

        if service_type not in self._services:
            raise KeyError(f"Service {service_type.__name__} not registered")

        implementation = self._services[service_type]

        if not inspect.isclass(implementation):
            return implementation

        instance = self._create_instance(implementation)

        if service_type in self._singletons:
            self._singletons[service_type] = instance

        return instance

    def _create_instance(self, cls: Type[T]) -> T:
        """
        Create an instance of a class with dependencies injected.

        Args:
            cls: The class to instantiate

        Returns:
            An instance of the class with dependencies injected
        """
        signature = inspect.signature(cls.__init__)
        parameters = signature.parameters

        # Skip self parameter
        parameters = list(parameters.values())[1:]

        type_hints = get_type_hints(cls.__init__)

        kwargs = {}
        for param in parameters:
            if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                continue

            param_name = param.name
            param_type = type_hints.get(param_name, None)

            if param.default is not param.empty and param_type not in self._services:
                continue

            if param_type:
                try:
                    kwargs[param_name] = self.resolve(param_type)
                except KeyError:
                    if param.default is not param.empty:
                        continue
                    raise

        return cls(**kwargs)


container = DependencyContainer()
