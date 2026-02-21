"""Block 18300 (EPAD_SETTINGS) - Energy Pad Base Settings.

Source: ProtocolParserV2.reference switch case (0x477c -> sswitch_8)
Parser: EpadParser.baseSettingsParse (ProtocolParserV2.reference lines 1828-2023)
Bean: EpadBaseSettings.reference
Block Type: parser-backed (fully verified from reference)
Purpose: Energy Pad sensor configuration, alarm settings, and LCD control

Structure (VERIFIED):
- Min length: 152 bytes (0x98)
- Top-level fields (offsets 0-1, 150-151): Sensor type + LCD time
- Liquid sensors (3x 32 bytes): Non-contiguous base (14B) + extended (18B)
- Temp sensors (3x 10 bytes): Contiguous at offsets 98-127
- Reserved space: 22 bytes (offsets 128-149)

reference Evidence:
- Parser method: EpadParser.baseSettingsParse (lines 1828-2023)
- Sub-parser 1: liquidSensorSetItemParse (EpadParser lines 69-768)
  Bean: EpadLiquidSensorSetItem (17 fields per instance)
- Sub-parser 2: tempSensorSetItemParse (EpadParser lines 770-968)
  Bean: EpadTempSensorSetItem (5 fields per instance)
- Transform: hexStrToEnableList for sensorType field

Liquid Sensor Layout (Non-Contiguous):
- Sensor 1: Base @ 2-15, Extended @ 44-61
- Sensor 2: Base @ 16-29, Extended @ 62-79
- Sensor 3: Base @ 30-43, Extended @ 80-97

Temp Sensor Layout (Contiguous):
- Sensor 1: 98-107
- Sensor 2: 108-117
- Sensor 3: 118-127

CAUTION: Energy management control - verify safe operating limits before
modifying alarm thresholds or sampling parameters.

Verification Status: verified_reference (Agent G deep dive 2026-02-16)
Evidence: 70+ fields proven from 3 sub-parsers, all bean constructors traced
"""

from dataclasses import dataclass

from ..protocol.datatypes import Int16, UInt16
from .declarative import block_field, block_schema


@block_schema(
    block_id=18300,
    name="EPAD_SETTINGS",
    description="Energy Pad sensor settings (reference-verified EVENT block)",
    min_length=152,
    strict=False,
    verification_status="verified_reference",
)
@dataclass
class EPadSettingsBlock:
    """Energy Pad settings schema (reference-verified).

    Fully verified from EpadParser.baseSettingsParse analysis.
    Contains 70+ individual configuration parameters across:
    - 3 liquid sensors (17 fields each)
    - 3 temperature sensors (5 fields each)
    - LCD backlight timer

    Note: Liquid sensors have non-contiguous layout (base + extended sections).
    This flattened schema documents absolute byte offsets for each field.
    """

    # ===== Top-Level Fields =====
    sensor_type: int = block_field(
        offset=0,
        type=UInt16(),
        description=(
            "Sensor type enable flags (transform: hexStrToEnableList) "
            "[reference: lines 1828-1866, bean: setSensorType]"
        ),
        required=False,
        default=0,
    )

    # ===== Liquid Sensor 1 (Base: 2-15, Extended: 44-61) =====
    liquid_1_sensor_spec: int = block_field(
        offset=2,
        type=UInt16(),
        description=(
            "Liquid sensor 1: Sensor specification/model "
            "[reference: sub-parser liquidSensorSetItemParse lines 69-768]"
        ),
        required=False,
        default=0,
    )
    liquid_1_fluid_type: int = block_field(
        offset=4,
        type=UInt16(),
        description="Liquid sensor 1: Type of fluid being monitored",
        required=False,
        default=0,
    )
    liquid_1_volume_unit: int = block_field(
        offset=6,
        type=UInt16(),
        description="Liquid sensor 1: Volume measurement unit",
        required=False,
        default=0,
    )
    liquid_1_volume_total: int = block_field(
        offset=8,
        type=UInt16(),
        description="Liquid sensor 1: Total volume capacity",
        required=False,
        default=0,
    )
    liquid_1_sampling_period: int = block_field(
        offset=10,
        type=UInt16(),
        description="Liquid sensor 1: Sampling interval",
        required=False,
        default=0,
    )
    liquid_1_calibration_empty: int = block_field(
        offset=12,
        type=UInt16(),
        description="Liquid sensor 1: Calibration value when empty",
        required=False,
        default=0,
    )
    liquid_1_calibration_full: int = block_field(
        offset=14,
        type=UInt16(),
        description="Liquid sensor 1: Calibration value when full",
        required=False,
        default=0,
    )

    # ===== Liquid Sensor 2 (Base: 16-29, Extended: 62-79) =====
    liquid_2_sensor_spec: int = block_field(
        offset=16,
        type=UInt16(),
        description="Liquid sensor 2: Sensor specification/model",
        required=False,
        default=0,
    )
    liquid_2_fluid_type: int = block_field(
        offset=18,
        type=UInt16(),
        description="Liquid sensor 2: Type of fluid being monitored",
        required=False,
        default=0,
    )
    liquid_2_volume_unit: int = block_field(
        offset=20,
        type=UInt16(),
        description="Liquid sensor 2: Volume measurement unit",
        required=False,
        default=0,
    )
    liquid_2_volume_total: int = block_field(
        offset=22,
        type=UInt16(),
        description="Liquid sensor 2: Total volume capacity",
        required=False,
        default=0,
    )
    liquid_2_sampling_period: int = block_field(
        offset=24,
        type=UInt16(),
        description="Liquid sensor 2: Sampling interval",
        required=False,
        default=0,
    )
    liquid_2_calibration_empty: int = block_field(
        offset=26,
        type=UInt16(),
        description="Liquid sensor 2: Calibration value when empty",
        required=False,
        default=0,
    )
    liquid_2_calibration_full: int = block_field(
        offset=28,
        type=UInt16(),
        description="Liquid sensor 2: Calibration value when full",
        required=False,
        default=0,
    )

    # ===== Liquid Sensor 3 (Base: 30-43, Extended: 80-97) =====
    liquid_3_sensor_spec: int = block_field(
        offset=30,
        type=UInt16(),
        description="Liquid sensor 3: Sensor specification/model",
        required=False,
        default=0,
    )
    liquid_3_fluid_type: int = block_field(
        offset=32,
        type=UInt16(),
        description="Liquid sensor 3: Type of fluid being monitored",
        required=False,
        default=0,
    )
    liquid_3_volume_unit: int = block_field(
        offset=34,
        type=UInt16(),
        description="Liquid sensor 3: Volume measurement unit",
        required=False,
        default=0,
    )
    liquid_3_volume_total: int = block_field(
        offset=36,
        type=UInt16(),
        description="Liquid sensor 3: Total volume capacity",
        required=False,
        default=0,
    )
    liquid_3_sampling_period: int = block_field(
        offset=38,
        type=UInt16(),
        description="Liquid sensor 3: Sampling interval",
        required=False,
        default=0,
    )
    liquid_3_calibration_empty: int = block_field(
        offset=40,
        type=UInt16(),
        description="Liquid sensor 3: Calibration value when empty",
        required=False,
        default=0,
    )
    liquid_3_calibration_full: int = block_field(
        offset=42,
        type=UInt16(),
        description="Liquid sensor 3: Calibration value when full",
        required=False,
        default=0,
    )

    # ===== Liquid Sensor 1 Extended (44-61) =====
    liquid_1_alarm_enable: int = block_field(
        offset=44,
        type=UInt16(),
        description=(
            "Liquid sensor 1: Alarm enable flags "
            "(bits 0-1: low alarm, bits 2-3: high alarm) "
            "[reference: EpadLiquidSensorSetItem bean, extended section]"
        ),
        required=False,
        default=0,
    )
    liquid_1_alarm_value_high: int = block_field(
        offset=46,
        type=UInt16(),
        description="Liquid sensor 1: High alarm threshold value",
        required=False,
        default=0,
    )
    liquid_1_alarm_clean_value_high: int = block_field(
        offset=48,
        type=UInt16(),
        description="Liquid sensor 1: High alarm clear threshold",
        required=False,
        default=0,
    )
    liquid_1_alarm_delay_high: int = block_field(
        offset=50,
        type=UInt16(),
        description="Liquid sensor 1: High alarm delay time",
        required=False,
        default=0,
    )
    liquid_1_alarm_clean_delay_high: int = block_field(
        offset=52,
        type=UInt16(),
        description="Liquid sensor 1: High alarm clear delay time",
        required=False,
        default=0,
    )
    liquid_1_alarm_value_low: int = block_field(
        offset=54,
        type=UInt16(),
        description="Liquid sensor 1: Low alarm threshold value",
        required=False,
        default=0,
    )
    liquid_1_alarm_clean_value_low: int = block_field(
        offset=56,
        type=UInt16(),
        description="Liquid sensor 1: Low alarm clear threshold",
        required=False,
        default=0,
    )
    liquid_1_alarm_delay_low: int = block_field(
        offset=58,
        type=UInt16(),
        description="Liquid sensor 1: Low alarm delay time",
        required=False,
        default=0,
    )
    liquid_1_alarm_clean_delay_low: int = block_field(
        offset=60,
        type=UInt16(),
        description="Liquid sensor 1: Low alarm clear delay time",
        required=False,
        default=0,
    )

    # ===== Liquid Sensor 2 Extended (62-79) =====
    liquid_2_alarm_enable: int = block_field(
        offset=62,
        type=UInt16(),
        description=(
            "Liquid sensor 2: Alarm enable flags "
            "(bits 0-1: low alarm, bits 2-3: high alarm)"
        ),
        required=False,
        default=0,
    )
    liquid_2_alarm_value_high: int = block_field(
        offset=64,
        type=UInt16(),
        description="Liquid sensor 2: High alarm threshold value",
        required=False,
        default=0,
    )
    liquid_2_alarm_clean_value_high: int = block_field(
        offset=66,
        type=UInt16(),
        description="Liquid sensor 2: High alarm clear threshold",
        required=False,
        default=0,
    )
    liquid_2_alarm_delay_high: int = block_field(
        offset=68,
        type=UInt16(),
        description="Liquid sensor 2: High alarm delay time",
        required=False,
        default=0,
    )
    liquid_2_alarm_clean_delay_high: int = block_field(
        offset=70,
        type=UInt16(),
        description="Liquid sensor 2: High alarm clear delay time",
        required=False,
        default=0,
    )
    liquid_2_alarm_value_low: int = block_field(
        offset=72,
        type=UInt16(),
        description="Liquid sensor 2: Low alarm threshold value",
        required=False,
        default=0,
    )
    liquid_2_alarm_clean_value_low: int = block_field(
        offset=74,
        type=UInt16(),
        description="Liquid sensor 2: Low alarm clear threshold",
        required=False,
        default=0,
    )
    liquid_2_alarm_delay_low: int = block_field(
        offset=76,
        type=UInt16(),
        description="Liquid sensor 2: Low alarm delay time",
        required=False,
        default=0,
    )
    liquid_2_alarm_clean_delay_low: int = block_field(
        offset=78,
        type=UInt16(),
        description="Liquid sensor 2: Low alarm clear delay time",
        required=False,
        default=0,
    )

    # ===== Liquid Sensor 3 Extended (80-97) =====
    liquid_3_alarm_enable: int = block_field(
        offset=80,
        type=UInt16(),
        description=(
            "Liquid sensor 3: Alarm enable flags "
            "(bits 0-1: low alarm, bits 2-3: high alarm)"
        ),
        required=False,
        default=0,
    )
    liquid_3_alarm_value_high: int = block_field(
        offset=82,
        type=UInt16(),
        description="Liquid sensor 3: High alarm threshold value",
        required=False,
        default=0,
    )
    liquid_3_alarm_clean_value_high: int = block_field(
        offset=84,
        type=UInt16(),
        description="Liquid sensor 3: High alarm clear threshold",
        required=False,
        default=0,
    )
    liquid_3_alarm_delay_high: int = block_field(
        offset=86,
        type=UInt16(),
        description="Liquid sensor 3: High alarm delay time",
        required=False,
        default=0,
    )
    liquid_3_alarm_clean_delay_high: int = block_field(
        offset=88,
        type=UInt16(),
        description="Liquid sensor 3: High alarm clear delay time",
        required=False,
        default=0,
    )
    liquid_3_alarm_value_low: int = block_field(
        offset=90,
        type=UInt16(),
        description="Liquid sensor 3: Low alarm threshold value",
        required=False,
        default=0,
    )
    liquid_3_alarm_clean_value_low: int = block_field(
        offset=92,
        type=UInt16(),
        description="Liquid sensor 3: Low alarm clear threshold",
        required=False,
        default=0,
    )
    liquid_3_alarm_delay_low: int = block_field(
        offset=94,
        type=UInt16(),
        description="Liquid sensor 3: Low alarm delay time",
        required=False,
        default=0,
    )
    liquid_3_alarm_clean_delay_low: int = block_field(
        offset=96,
        type=UInt16(),
        description="Liquid sensor 3: Low alarm clear delay time",
        required=False,
        default=0,
    )

    # ===== Temperature Sensor 1 (98-107) =====
    temp_1_calibration_offset: int = block_field(
        offset=98,
        type=Int16(),
        description=(
            "Temp sensor 1: Signed calibration offset "
            "[reference: sub-parser tempSensorSetItemParse lines 770-968, "
            "bean: EpadTempSensorSetItem]"
        ),
        required=False,
        default=0,
    )
    temp_1_calibration_ratio: int = block_field(
        offset=100,
        type=UInt16(),
        description="Temp sensor 1: Calibration ratio/multiplier",
        required=False,
        default=0,
    )
    temp_1_temp_unit: int = block_field(
        offset=102,
        type=UInt16(),
        description="Temp sensor 1: Temperature unit (1=Celsius, hardcoded in parser)",
        required=False,
        default=1,
    )
    temp_1_nominal_resistance: int = block_field(
        offset=104,
        type=UInt16(),
        description="Temp sensor 1: Nominal thermistor resistance",
        required=False,
        default=0,
    )
    temp_1_beta: int = block_field(
        offset=106,
        type=UInt16(),
        description="Temp sensor 1: Beta coefficient for thermistor calculations",
        required=False,
        default=0,
    )

    # ===== Temperature Sensor 2 (108-117) =====
    temp_2_calibration_offset: int = block_field(
        offset=108,
        type=Int16(),
        description="Temp sensor 2: Signed calibration offset",
        required=False,
        default=0,
    )
    temp_2_calibration_ratio: int = block_field(
        offset=110,
        type=UInt16(),
        description="Temp sensor 2: Calibration ratio/multiplier",
        required=False,
        default=0,
    )
    temp_2_temp_unit: int = block_field(
        offset=112,
        type=UInt16(),
        description="Temp sensor 2: Temperature unit (1=Celsius)",
        required=False,
        default=1,
    )
    temp_2_nominal_resistance: int = block_field(
        offset=114,
        type=UInt16(),
        description="Temp sensor 2: Nominal thermistor resistance",
        required=False,
        default=0,
    )
    temp_2_beta: int = block_field(
        offset=116,
        type=UInt16(),
        description="Temp sensor 2: Beta coefficient",
        required=False,
        default=0,
    )

    # ===== Temperature Sensor 3 (118-127) =====
    temp_3_calibration_offset: int = block_field(
        offset=118,
        type=Int16(),
        description="Temp sensor 3: Signed calibration offset",
        required=False,
        default=0,
    )
    temp_3_calibration_ratio: int = block_field(
        offset=120,
        type=UInt16(),
        description="Temp sensor 3: Calibration ratio/multiplier",
        required=False,
        default=0,
    )
    temp_3_temp_unit: int = block_field(
        offset=122,
        type=UInt16(),
        description="Temp sensor 3: Temperature unit (1=Celsius)",
        required=False,
        default=1,
    )
    temp_3_nominal_resistance: int = block_field(
        offset=124,
        type=UInt16(),
        description="Temp sensor 3: Nominal thermistor resistance",
        required=False,
        default=0,
    )
    temp_3_beta: int = block_field(
        offset=126,
        type=UInt16(),
        description="Temp sensor 3: Beta coefficient",
        required=False,
        default=0,
    )

    # Note: Offsets 128-149 (22 bytes) are reserved/padding (not referenced in parser)

    # ===== LCD Control (150-151) =====
    lcd_active_time: int = block_field(
        offset=150,
        type=UInt16(),
        description=(
            "LCD backlight active time "
            "[reference: lines 1986-2023, bean: setLcdActiveTime]"
        ),
        required=False,
        default=0,
    )


BLOCK_18300_SCHEMA = EPadSettingsBlock.to_schema()  # type: ignore[attr-defined]

__all__ = ["BLOCK_18300_SCHEMA", "EPadSettingsBlock"]
