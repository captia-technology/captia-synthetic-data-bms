"""Allow running as `python -m synthetic_generator`."""
import sys
from .cli import main
sys.exit(main())
