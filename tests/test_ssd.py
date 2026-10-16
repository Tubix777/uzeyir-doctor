"""Synthetic SSD snapshots and mocked D-Bus calls; no hardware is queried."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from doctor import hardware


NOW = 2_000_000
MODEL = "Fixture NVMe SSD"
FIXTURE_PATH = "/org/freedesktop/UDisks2/drives/fixture_nvme"


def properties(**overrides):
    values = {"SmartUpdated": NOW - 30, "SmartCriticalWarning": []}
    values.update(overrides)
    return values


class NvmeParserTests(unittest.TestCase):
    def parse(self, attributes=None, props=None):
        return hardware.parse_nvme_health(MODEL, attributes, properties() if props is None else props, now=NOW)

    def test_new_drive_percent_used_zero_means_estimated_remaining_100(self):
        finding = self.parse({"percent_used": 0})
        self.assertEqual(finding.metric, 100)
        self.assertEqual(finding.metric_label, "Tahmini kalan ömür")
        self.assertEqual(finding.status, "info")
        self.assertIn("garantisi", finding.explanation)

    def test_normal_endurance_is_complement_of_percent_used(self):
        finding = self.parse({"percent_used": 27})
        self.assertEqual(finding.metric, 73)
        self.assertEqual(finding.status, "info")

    def test_exhausted_and_exceeded_estimate_never_claim_drive_failure(self):
        for used in (100, 125, 255):
            with self.subTest(used=used):
                finding = self.parse({"percent_used": used})
                self.assertEqual(finding.metric, 0)
                self.assertEqual(finding.status, "warning")
                self.assertIn("tek başına SSD arızası anlamına gelmez", finding.explanation)

    def test_invalid_percentages_do_not_generate_a_number(self):
        for used in (-1, 256, True, False, 30.0, "30", None, float("nan")):
            with self.subTest(used=used):
                finding = self.parse({"percent_used": used})
                self.assertIsNone(finding.metric)
                self.assertEqual(finding.status, "unknown")

    def test_missing_and_unreadable_attributes_have_no_fake_percentage(self):
        for attributes in (None, {}, {"avail_spare": 100}, "unexpected"):
            with self.subTest(attributes=attributes):
                finding = self.parse(attributes)
                self.assertIsNone(finding.metric)
                self.assertEqual(finding.status, "unknown")

    def test_never_updated_data_ignores_unmeaningful_percentage_and_warnings(self):
        finding = self.parse({"percent_used": 0}, properties(SmartUpdated=0, SmartCriticalWarning=["readonly"]))
        self.assertIsNone(finding.metric)
        self.assertEqual(finding.status, "unknown")
        self.assertIn("kayıt zamanı", finding.explanation)

    def test_invalid_or_future_update_timestamp_is_unknown(self):
        for timestamp in (None, -1, True, "2000000", NOW + 1):
            with self.subTest(timestamp=timestamp):
                finding = self.parse({"percent_used": 10}, properties(SmartUpdated=timestamp))
                self.assertIsNone(finding.metric)
                self.assertEqual(finding.status, "unknown")

    def test_stale_data_does_not_present_a_current_percentage(self):
        finding = self.parse({"percent_used": 0}, properties(SmartUpdated=NOW - hardware.SMART_MAX_AGE_SECONDS - 1))
        self.assertIsNone(finding.metric)
        self.assertEqual(finding.status, "unknown")
        self.assertIn("24 saatten eski", finding.explanation)

    def test_exact_cache_age_boundary_remains_usable(self):
        finding = self.parse({"percent_used": 20}, properties(SmartUpdated=NOW - hardware.SMART_MAX_AGE_SECONDS))
        self.assertEqual(finding.metric, 80)

    def test_critical_warning_overrides_high_remaining_endurance(self):
        for warning in hardware.WARNING_LABELS:
            with self.subTest(warning=warning):
                finding = self.parse({"percent_used": 0}, properties(SmartCriticalWarning=[warning]))
                self.assertEqual(finding.metric, 100)
                self.assertEqual(finding.status, "critical")
                self.assertTrue(finding.steps)

    def test_warning_is_retained_if_percentage_cannot_be_read(self):
        finding = self.parse(None, properties(SmartCriticalWarning=["degraded"]))
        self.assertIsNone(finding.metric)
        self.assertEqual(finding.status, "critical")

    def test_stale_warning_is_explicitly_a_previous_record(self):
        finding = self.parse({"percent_used": 5}, properties(
            SmartUpdated=NOW - hardware.SMART_MAX_AGE_SECONDS - 60,
            SmartCriticalWarning=["readonly"],
        ))
        self.assertIsNone(finding.metric)
        self.assertEqual(finding.status, "critical")
        self.assertIn("Önceki kayıtta", finding.explanation)

    def test_unknown_warning_codes_are_not_echoed(self):
        finding = self.parse({"percent_used": 0}, properties(SmartCriticalWarning=["synthetic_unrecognized_value"]))
        self.assertEqual(finding.status, "critical")
        self.assertNotIn("synthetic_unrecognized_value", repr(finding))

    def test_missing_or_invalid_warning_property_is_not_a_health_claim(self):
        for props in ({"SmartUpdated": NOW - 30}, properties(SmartCriticalWarning="readonly"),
                      properties(SmartCriticalWarning=[1])):
            with self.subTest(props=props):
                finding = self.parse({"percent_used": 20}, props)
                self.assertEqual(finding.metric, 80)
                self.assertEqual(finding.status, "unknown")

    def test_model_fallback_never_uses_an_identifier(self):
        for model in (None, "", [], " \n "):
            with self.subTest(model=model):
                finding = hardware.parse_nvme_health(model, {"percent_used": 20}, properties(), now=NOW)
                self.assertEqual(finding.title, "SSD · Model bilinmiyor")


class SyntheticDbusError(Exception):
    pass


class FakeVariant:
    def __init__(self, signature, value):
        self.signature = signature
        self.value = value

    def unpack(self):
        return self.value


class DbusReaderTests(unittest.TestCase):
    def setUp(self):
        self.bus = Mock()
        self.gio = SimpleNamespace(
            BusType=SimpleNamespace(SYSTEM="system"),
            DBusCallFlags=SimpleNamespace(NO_AUTO_START="no-auto-start"),
            bus_get_sync=Mock(return_value=self.bus),
        )
        self.glib = SimpleNamespace(
            Variant=FakeVariant,
            VariantType=SimpleNamespace(new=lambda signature: signature),
            Error=SyntheticDbusError,
        )

    def read(self):
        with patch.object(hardware, "_load_dbus", return_value=(self.gio, self.glib)), \
             patch.object(hardware.time, "time", return_value=NOW):
            return hardware.read_ssd_health()

    def nvme_objects(self, props=None):
        return {FIXTURE_PATH: {
            hardware.DRIVE_INTERFACE: {"Model": MODEL, "Serial": "REDACTION_FIXTURE", "RotationRate": 0},
            hardware.NVME_INTERFACE: properties() if props is None else props,
        }}

    def set_replies(self, objects, attributes=None):
        self.bus.call_sync.side_effect = [FakeVariant("managed", (objects,))]
        if attributes is not None:
            self.bus.call_sync.side_effect = [FakeVariant("managed", (objects,)),
                                               FakeVariant("attributes", (attributes,))]

    def test_read_uses_only_cached_read_methods_and_disables_interactive_auth(self):
        self.set_replies(self.nvme_objects(), {"percent_used": 19})
        finding = self.read()[0]
        self.assertEqual(finding.metric, 81)
        calls = self.bus.call_sync.call_args_list
        self.assertEqual([item.args[3] for item in calls], ["GetManagedObjects", "SmartGetAttributes"])
        for item in calls:
            self.assertEqual(item.args[6], self.gio.DBusCallFlags.NO_AUTO_START)
            self.assertGreaterEqual(item.args[7], 3000)
            self.assertLessEqual(item.args[7], 5000)
        options = calls[1].args[4].unpack()[0]
        self.assertTrue(options["auth.no_user_interaction"].unpack())
        self.assertNotIn("REDACTION_FIXTURE", repr(finding))
        self.assertNotIn(FIXTURE_PATH, repr(finding))

    def test_missing_gio_returns_unknown(self):
        with patch.object(hardware, "_load_dbus", return_value=None):
            finding = hardware.read_ssd_health()[0]
        self.assertEqual(finding.status, "unknown")
        self.assertIsNone(finding.metric)

    def test_service_absent_or_access_denied_returns_sanitized_unknown(self):
        self.bus.call_sync.side_effect = SyntheticDbusError("synthetic-private-detail")
        finding = self.read()[0]
        self.assertEqual(finding.status, "unknown")
        self.assertIsNone(finding.metric)
        self.assertNotIn("synthetic-private-detail", repr(finding))

    def test_system_bus_unavailable_returns_unknown(self):
        self.gio.bus_get_sync.side_effect = SyntheticDbusError("synthetic-private-detail")
        finding = self.read()[0]
        self.assertEqual(finding.status, "unknown")
        self.assertIsNone(finding.metric)

    def test_attributes_access_denied_does_not_create_a_percentage(self):
        self.bus.call_sync.side_effect = [FakeVariant("managed", (self.nvme_objects(),)),
                                           SyntheticDbusError("synthetic-private-detail")]
        finding = self.read()[0]
        self.assertEqual(finding.status, "unknown")
        self.assertIsNone(finding.metric)
        self.assertNotIn("synthetic-private-detail", repr(finding))

    def test_attributes_access_denied_retains_a_known_critical_warning(self):
        objects = self.nvme_objects(properties(SmartCriticalWarning=["temperature"]))
        self.bus.call_sync.side_effect = [FakeVariant("managed", (objects,)), SyntheticDbusError()]
        finding = self.read()[0]
        self.assertEqual(finding.status, "critical")
        self.assertIsNone(finding.metric)

    def test_never_updated_and_stale_data_do_not_request_attributes_or_refresh(self):
        for updated in (0, NOW - hardware.SMART_MAX_AGE_SECONDS - 1):
            with self.subTest(updated=updated):
                self.bus.reset_mock()
                self.set_replies(self.nvme_objects(properties(SmartUpdated=updated)))
                finding = self.read()[0]
                self.assertIsNone(finding.metric)
                self.assertEqual(self.bus.call_sync.call_count, 1)

    def test_ata_ssd_is_identified_without_vendor_percentage_guess(self):
        objects = {"/org/freedesktop/UDisks2/drives/fixture_ata": {
            hardware.DRIVE_INTERFACE: {"Model": "Fixture SATA SSD", "RotationRate": 0},
            hardware.ATA_INTERFACE: {"SmartSupported": True},
        }}
        self.set_replies(objects)
        finding = self.read()[0]
        self.assertEqual(finding.title, "SSD · Fixture SATA SSD")
        self.assertEqual(finding.status, "unknown")
        self.assertIsNone(finding.metric)
        self.assertIn("üreticiye özgü", finding.explanation)
        self.assertEqual(self.bus.call_sync.call_count, 1)

    def test_unsupported_solid_state_device_remains_unknown(self):
        objects = {"/org/freedesktop/UDisks2/drives/fixture_other": {
            hardware.DRIVE_INTERFACE: {"Model": "Fixture device", "RotationRate": 0},
        }}
        self.set_replies(objects)
        finding = self.read()[0]
        self.assertEqual(finding.status, "unknown")
        self.assertIsNone(finding.metric)

    def test_spinning_or_optical_drive_is_not_presented_as_an_ssd(self):
        for properties_ in ({"Model": "Fixture HDD", "RotationRate": 7200},
                            {"Model": "Fixture optical", "RotationRate": 0, "Optical": True}):
            with self.subTest(properties=properties_):
                self.bus.reset_mock()
                self.set_replies({"/org/freedesktop/UDisks2/drives/fixture_other": {
                    hardware.DRIVE_INTERFACE: properties_, hardware.ATA_INTERFACE: {},
                }})
                finding = self.read()[0]
                self.assertEqual(finding.title, "SSD sağlığı")
                self.assertEqual(finding.status, "unknown")
                self.assertIsNone(finding.metric)

    def test_empty_or_unexpected_object_result_does_not_invent_a_disk(self):
        for output in ({}, "unexpected"):
            with self.subTest(output=output):
                self.bus.call_sync.return_value = FakeVariant("managed", (output,))
                self.bus.call_sync.side_effect = None
                finding = self.read()[0]
                self.assertEqual(finding.status, "unknown")
                self.assertIsNone(finding.metric)


if __name__ == "__main__":
    unittest.main()
