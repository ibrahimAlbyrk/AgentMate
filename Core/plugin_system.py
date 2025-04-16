"""
Plugin System for AgentMate

This module provides a flexible plugin system for dynamically discovering
and loading plugins such as agents and subscribers.
"""

import os
import sys
import inspect
import importlib
import pkgutil
from typing import Dict, List, Type, TypeVar, Generic, Optional, Any, Callable, Set

from Core.logger import LoggerCreator

T = TypeVar('T')


class PluginRegistry(Generic[T]):
    """
    Registry for plugins of a specific type.
    
    This class provides methods for registering, discovering, and instantiating
    plugins of a specific type.
    """
    
    def __init__(self, plugin_type: Type[T], plugin_dirs: List[str] = None):
        """
        Initialize the plugin registry.
        
        Args:
            plugin_type: The base type of plugins to register
            plugin_dirs: Directories to search for plugins
        """
        self.plugin_type = plugin_type
        self.plugin_dirs = plugin_dirs or []
        self.plugins: Dict[str, Type[T]] = {}
        self.logger = LoggerCreator.create_advanced_console(f"{plugin_type.__name__}Registry")
    
    def register(self, name: str, plugin_class: Type[T]) -> None:
        """
        Register a plugin.
        
        Args:
            name: The name of the plugin
            plugin_class: The plugin class
            
        Raises:
            ValueError: If the plugin is not a subclass of the plugin type
            ValueError: If a plugin with the same name is already registered
        """
        if not issubclass(plugin_class, self.plugin_type):
            raise ValueError(f"Plugin {name} must be a subclass of {self.plugin_type.__name__}")
        
        if name in self.plugins:
            raise ValueError(f"Plugin {name} is already registered")
        
        self.plugins[name] = plugin_class
        self.logger.debug(f"Registered plugin: {name}")
    
    def get(self, name: str) -> Optional[Type[T]]:
        """
        Get a plugin by name.
        
        Args:
            name: The name of the plugin
            
        Returns:
            The plugin class or None if not found
        """
        return self.plugins.get(name)
    
    def get_all(self) -> Dict[str, Type[T]]:
        """
        Get all registered plugins.
        
        Returns:
            A dictionary of plugin names to plugin classes
        """
        return self.plugins.copy()
    
    def create(self, name: str, *args, **kwargs) -> T:
        """
        Create an instance of a plugin.
        
        Args:
            name: The name of the plugin
            *args: Positional arguments to pass to the plugin constructor
            **kwargs: Keyword arguments to pass to the plugin constructor
            
        Returns:
            An instance of the plugin
            
        Raises:
            ValueError: If the plugin is not registered
        """
        plugin_class = self.get(name)
        if plugin_class is None:
            raise ValueError(f"Plugin {name} is not registered")
        
        return plugin_class(*args, **kwargs)
    
    def discover(self) -> None:
        """
        Discover plugins in the plugin directories.
        
        This method searches for plugins in the specified directories
        and registers them.
        """
        for plugin_dir in self.plugin_dirs:
            self._discover_in_package(plugin_dir)
    
    def _discover_in_package(self, package_name: str) -> None:
        """
        Discover plugins in a package.
        
        Args:
            package_name: The name of the package to search
        """
        try:
            package = importlib.import_module(package_name)
        except ImportError:
            self.logger.error(f"Failed to import package: {package_name}")
            return
        
        for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
            if is_pkg:
                # Recursively discover plugins in subpackages
                self._discover_in_package(module_name)
            else:
                try:
                    module = importlib.import_module(module_name)
                    self._register_from_module(module)
                except ImportError:
                    self.logger.error(f"Failed to import module: {module_name}")
    
    def _register_from_module(self, module: Any) -> None:
        """
        Register plugins from a module.
        
        Args:
            module: The module to search for plugins
        """
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, self.plugin_type) and 
                obj is not self.plugin_type and
                not inspect.isabstract(obj)):
                
                # Use the class name as the plugin name if not explicitly specified
                plugin_name = getattr(obj, "plugin_name", name)
                self.register(plugin_name, obj)


class PluginManager:
    """
    Manager for all plugin registries.
    
    This class provides methods for creating and accessing plugin registries
    for different plugin types.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PluginManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.registries: Dict[Type, PluginRegistry] = {}
        self.logger = LoggerCreator.create_advanced_console("PluginManager")
    
    def create_registry(self, plugin_type: Type[T], plugin_dirs: List[str] = None) -> PluginRegistry[T]:
        """
        Create a plugin registry for a specific plugin type.
        
        Args:
            plugin_type: The base type of plugins to register
            plugin_dirs: Directories to search for plugins
            
        Returns:
            A plugin registry for the specified plugin type
        """
        if plugin_type in self.registries:
            return self.registries[plugin_type]
        
        registry = PluginRegistry(plugin_type, plugin_dirs)
        self.registries[plugin_type] = registry
        return registry
    
    def get_registry(self, plugin_type: Type[T]) -> Optional[PluginRegistry[T]]:
        """
        Get a plugin registry for a specific plugin type.
        
        Args:
            plugin_type: The base type of plugins
            
        Returns:
            The plugin registry or None if not found
        """
        return self.registries.get(plugin_type)
    
    def discover_all(self) -> None:
        """
        Discover plugins for all registered plugin types.
        """
        for registry in self.registries.values():
            registry.discover()


# Create a global instance
plugin_manager = PluginManager()