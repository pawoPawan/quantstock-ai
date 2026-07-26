"""
Plugin base class — implement this interface to add new analysis modules
without touching existing code.

Example plugin:
    class VIXCorrelationPlugin(BaseAnalysisPlugin):
        name = "vix_correlation"
        description = "Correlates stock price with VIX fear index"

        async def analyze(self, ticker, data) -> dict:
            ...

    # Register via environment or auto-discovery
    PluginRegistry.register(VIXCorrelationPlugin)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PluginMetadata:
    name: str
    description: str
    version: str = "1.0.0"
    author: str = "QuantStock"
    requires: list = None  # list of required data keys


class BaseAnalysisPlugin(ABC):
    """Abstract base for all analysis plugins."""

    name: str = "unnamed_plugin"
    description: str = ""
    version: str = "1.0.0"

    @abstractmethod
    async def analyze(
        self,
        ticker: str,
        context: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Run the analysis.

        Parameters
        ----------
        ticker  : Stock ticker symbol
        context : Dict containing any combination of:
                  - stock_info, historical_data, technical, fundamental,
                    quant, options, news, score

        Returns
        -------
        Dict with analysis results, or None if insufficient data.
        """
        ...

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(name=self.name, description=self.description, version=self.version)

    def __repr__(self) -> str:
        return f"<Plugin: {self.name} v{self.version}>"
