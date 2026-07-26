"""
Plugin registry — auto-discovers and runs analysis plugins.

Usage:
    # Register
    PluginRegistry.register(MyPlugin)

    # Run all plugins
    results = await PluginRegistry.run_all(ticker, context)

    # Run specific plugin
    result = await PluginRegistry.run("my_plugin", ticker, context)
"""

import logging
import importlib
import pkgutil
from typing import Dict, Any, List, Optional, Type

from app.plugins.base_plugin import BaseAnalysisPlugin

logger = logging.getLogger(__name__)

_REGISTRY: Dict[str, BaseAnalysisPlugin] = {}


class PluginRegistry:
    @classmethod
    def register(cls, plugin_class: Type[BaseAnalysisPlugin]) -> None:
        instance = plugin_class()
        _REGISTRY[instance.name] = instance
        logger.info(f"Registered plugin: {instance.name}")

    @classmethod
    def unregister(cls, name: str) -> None:
        _REGISTRY.pop(name, None)

    @classmethod
    def list_plugins(cls) -> List[Dict[str, str]]:
        return [
            {"name": p.name, "description": p.description, "version": p.version}
            for p in _REGISTRY.values()
        ]

    @classmethod
    async def run(cls, plugin_name: str, ticker: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        plugin = _REGISTRY.get(plugin_name)
        if not plugin:
            logger.warning(f"Plugin '{plugin_name}' not found")
            return None
        try:
            return await plugin.analyze(ticker, context)
        except Exception as e:
            logger.error(f"Plugin '{plugin_name}' failed for {ticker}: {e}")
            return {"error": str(e)}

    @classmethod
    async def run_all(cls, ticker: str, context: Dict[str, Any]) -> Dict[str, Any]:
        results = {}
        for name, plugin in _REGISTRY.items():
            try:
                result = await plugin.analyze(ticker, context)
                if result is not None:
                    results[name] = result
            except Exception as e:
                logger.error(f"Plugin '{name}' error: {e}")
                results[name] = {"error": str(e)}
        return results

    @classmethod
    def auto_discover(cls, package_path: str = "app.plugins.modules") -> None:
        """Auto-discover plugins in a sub-package."""
        try:
            pkg = importlib.import_module(package_path)
            for _, module_name, _ in pkgutil.iter_modules(pkg.__path__):
                mod = importlib.import_module(f"{package_path}.{module_name}")
                for attr_name in dir(mod):
                    attr = getattr(mod, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, BaseAnalysisPlugin)
                        and attr is not BaseAnalysisPlugin
                    ):
                        cls.register(attr)
        except ModuleNotFoundError:
            pass  # No custom plugins yet — that's fine
