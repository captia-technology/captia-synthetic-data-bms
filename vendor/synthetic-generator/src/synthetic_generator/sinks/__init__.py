"""Output sink adapters for data egress (MQTT, file, stdout, etc.)."""
from .mqtt import MQTTSinkAdapter
from .file import FileSinkAdapter
from .stdout import StdoutSinkAdapter
from .composite import CompositeSink
from .null import NullSink
