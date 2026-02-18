"""Group read orchestration service.

Extracted from Client to reduce god object complexity.
Handles group-level block read operations (batch, detailed, streaming).
"""

import logging
from typing import Callable, Iterator, List, Tuple

from ..contracts.types import ParsedRecord
from ..devices.types import DeviceProfile
from ..models.types import BlockGroup

logger = logging.getLogger(__name__)


class ReadGroupResult:
    """Result of read_group_ex operation.

    Attributes:
        blocks: Successfully parsed blocks
        errors: List of (block_id, exception) for failed blocks
    """

    def __init__(
        self,
        blocks: List[ParsedRecord],
        errors: List[Tuple[int, Exception]],
    ):
        """Initialize result.

        Args:
            blocks: Successfully parsed blocks
            errors: Failed blocks with exceptions
        """
        self.blocks = blocks
        self.errors = errors

    @property
    def success(self) -> bool:
        """Check if all blocks were read successfully."""
        return len(self.errors) == 0

    @property
    def partial(self) -> bool:
        """Check if some (but not all) blocks failed."""
        return len(self.errors) > 0 and len(self.blocks) > 0


class GroupReader:
    """Handles group-level read orchestration (internal service).

    This service extracts group orchestration logic from Client:
    - Group validation against device profile
    - Block iteration and error handling
    - Batch reads, detailed error reporting, and streaming

    Uses dependency injection for read_block to remain transport-agnostic.
    """

    def __init__(
        self,
        profile: DeviceProfile,
        read_block_fn: Callable[[int], ParsedRecord],
    ):
        """Initialize group reader.

        Args:
            profile: Device profile with group definitions
            read_block_fn: Block read function (injected from Client)
        """
        self.profile = profile
        self.read_block = read_block_fn

    def read_group(
        self,
        group: BlockGroup,
        partial_ok: bool = True,
    ) -> List[ParsedRecord]:
        """Read a block group.

        Args:
            group: BlockGroup to read
            partial_ok: If True (default), return partial results on failures.
                       If False, fail fast on first error.

        Returns:
            List of ParsedRecord (one per block in group)

        Raises:
            ValueError: If group not supported by this device
            TransportError/ProtocolError: If any block read fails and partial_ok=False
        """
        result = self.read_group_ex(group, partial_ok=partial_ok)
        return result.blocks

    def read_group_ex(
        self,
        group: BlockGroup,
        partial_ok: bool = False,
    ) -> ReadGroupResult:
        """Read a block group with detailed error reporting.

        Args:
            group: BlockGroup to read
            partial_ok: If False (default), fail fast on first error.
                       If True, continue reading remaining blocks and collect errors.

        Returns:
            ReadGroupResult with blocks and errors

        Raises:
            ValueError: If group not supported by this device
            TransportError/ProtocolError: If any block read fails and partial_ok=False
        """
        # Validate group and get definition
        group_def = self._validate_group(group)
        group_name = group.value

        logger.info(f"Reading group '{group_name}': {len(group_def.blocks)} blocks")

        # Read all blocks in group
        blocks = []
        errors = []

        for block_id in group_def.blocks:
            try:
                parsed = self.read_block(block_id)
                blocks.append(parsed)
            except Exception as e:
                logger.error(f"Failed to read block {block_id}: {e}")
                errors.append((block_id, e))

                # In strict mode (partial_ok=False), fail immediately
                if not partial_ok:
                    raise

        # Log summary
        if errors and partial_ok:
            logger.warning(
                f"Group '{group_name}' read completed with {len(errors)} errors: "
                f"{len(blocks)}/{len(group_def.blocks)} blocks successful"
            )
        else:
            logger.info(
                f"Group '{group_name}' read complete: "
                f"{len(blocks)}/{len(group_def.blocks)} blocks successful"
            )

        return ReadGroupResult(blocks=blocks, errors=errors)

    def stream_group(
        self,
        group: BlockGroup,
        partial_ok: bool = True,
    ) -> Iterator[ParsedRecord]:
        """Stream blocks from a group as they are read.

        Yields blocks as they arrive instead of collecting them in memory.
        Useful for processing large groups or implementing real-time UIs.

        Args:
            group: BlockGroup to stream
            partial_ok: If True (default), skip failed blocks and continue.
                       If False, fail fast on first error.

        Yields:
            ParsedRecord for each successfully read block (in group order)

        Raises:
            ValueError: If group not supported by this device
            TransportError/ProtocolError: If any block read fails and partial_ok=False

        Example:
            for block in reader.stream_group(BlockGroup.BATTERY):
                print(f"Got {block.name}: {block.values}")
        """
        # Validate group and get definition
        group_def = self._validate_group(group)
        group_name = group.value

        logger.info(
            f"Streaming group '{group_name}': {len(group_def.blocks)} blocks"
        )

        success_count = 0
        error_count = 0

        # Stream blocks as they are read
        for block_id in group_def.blocks:
            try:
                parsed = self.read_block(block_id)
                success_count += 1
                yield parsed
            except Exception as e:
                error_count += 1
                logger.error(f"Failed to read block {block_id}: {e}")

                # In strict mode (partial_ok=False), fail immediately
                if not partial_ok:
                    raise

        # Log summary after streaming completes
        if error_count > 0 and partial_ok:
            logger.warning(
                f"Group '{group_name}' stream completed with {error_count} errors: "
                f"{success_count}/{len(group_def.blocks)} blocks successful"
            )
        else:
            logger.info(
                f"Group '{group_name}' stream complete: "
                f"{success_count}/{len(group_def.blocks)} blocks successful"
            )

    def _validate_group(self, group: BlockGroup):  # type: ignore[no-untyped-def]
        """Validate group exists in profile and return definition.

        Args:
            group: BlockGroup to validate

        Returns:
            GroupDefinition from profile

        Raises:
            ValueError: If group not supported by this device
        """
        group_name = group.value
        if group_name not in self.profile.groups:
            raise ValueError(
                f"Group '{group_name}' not supported by {self.profile.model}. "
                f"Available: {list(self.profile.groups.keys())}"
            )

        return self.profile.groups[group_name]

