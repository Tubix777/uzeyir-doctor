"""Regression tests for diagnostic honesty and read-only command routing.

All command output is synthetic. Repository and folder fixtures are temporary;
the suite does not inspect or change the host's service or Flatpak state.
"""
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import call, patch

from doctor import core


APP_ID = "org.example.Editor"
RUNTIME = "org.example.Platform/x86_64/1.0"


def finding_named(findings, title):
    return next(item for item in findings if item.title == title)


class ServiceFindingTests(unittest.TestCase):
    def test_failed_or_inaccessible_systemctl_never_reports_healthy(self):
        for user in (False, True):
            for code in (1, 124, 125, 127):
                with self.subTest(user=user, code=code):
                    finding = core.services_finding(
                        core.Result(code, output="", error="Synthetic failure"), user
                    )
                    self.assertEqual(finding.status, "unknown")
                    self.assertEqual(finding.evidence, [])

    def test_nonzero_exit_does_not_trust_partial_service_output(self):
        finding = core.services_finding(
            core.Result(1, "example.service loaded failed failed Synthetic service"), False
        )
        self.assertEqual(finding.status, "unknown")

    def test_successful_empty_list_is_healthy(self):
        finding = core.services_finding(core.Result(0, "\n  \n"), False)
        self.assertEqual(finding.status, "ok")

    def test_failed_plain_service_rows_are_parsed(self):
        result = core.Result(
            0,
            "  example.service loaded failed failed Synthetic service\n"
            "backup@fixture.service loaded failed failed Synthetic backup\n"
            "\n"
            "example.socket loaded failed failed A socket is not a service\n",
        )
        finding = core.services_finding(result, True)
        self.assertEqual(finding.status, "warning")
        self.assertEqual(finding.evidence, ["example.service", "backup@fixture.service"])
        self.assertIn("2", finding.explanation)

    @patch("doctor.core.ssd_health_findings", return_value=[])
    @patch("doctor.core.repository_findings", return_value=[])
    @patch("doctor.core.Path.read_text", return_value='PRETTY_NAME="Synthetic Linux"\n')
    @patch("doctor.core.Path.stat", return_value=SimpleNamespace(st_dev=1))
    @patch("doctor.core.shutil.disk_usage", return_value=SimpleNamespace(total=100, free=50))
    @patch("doctor.core.shutil.which", side_effect=lambda tool: "/synthetic/systemctl" if tool == "systemctl" else None)
    @patch("doctor.core.run", return_value=core.Result(1, error="Synthetic service bus unavailable"))
    def test_scan_keeps_system_and_user_service_bus_failures_unknown(self, run, *_mocks):
        findings = core.scan()
        self.assertEqual(finding_named(findings, "Sistem servisleri").status, "unknown")
        self.assertEqual(finding_named(findings, "Kullanıcı servisleri").status, "unknown")
        run.assert_has_calls([
            call(["systemctl", "--failed", "--type=service", "--no-legend", "--plain", "--no-pager"]),
            call(["systemctl", "--user", "--failed", "--type=service", "--no-legend", "--plain", "--no-pager"]),
        ])
        self.assertEqual(run.call_count, 2)


class DiskFindingTests(unittest.TestCase):
    def test_usage_thresholds_and_full_disk(self):
        for free, expected in ((11, "ok"), (10, "warning"), (4, "warning"),
                               (3, "critical"), (0, "critical")):
            with self.subTest(free=free):
                finding = core.disk_finding(100, free, "Synthetic disk")
                self.assertEqual(finding.status, expected)
                self.assertEqual(bool(finding.steps), expected != "ok")

    def test_unreadable_capacity_is_unknown(self):
        for total in (0, -1):
            with self.subTest(total=total):
                finding = core.disk_finding(total, 0, "Synthetic disk")
                self.assertEqual(finding.status, "unknown")
                self.assertEqual(finding.evidence, [])


class RepositoryFindingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)

    def write_repo(self, name, text):
        path = self.directory / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_missing_directory_does_not_claim_repositories_verified(self):
        findings = core.repository_findings(self.directory / "missing")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].status, "info")

    def test_empty_directory_and_empty_repository_file_have_no_enabled_repos(self):
        self.assertEqual(core.repository_findings(self.directory)[0].status, "warning")
        self.write_repo("empty.repo", "")
        self.assertEqual(core.repository_findings(self.directory)[0].status, "warning")

    def test_malformed_repository_is_reported_by_basename(self):
        self.write_repo("broken.repo", "[unfinished\nenabled=1\n")
        self.write_repo("valid.repo", "[valid]\nenabled=1\n")
        finding = core.repository_findings(self.directory)[0]
        self.assertEqual(finding.status, "warning")
        self.assertEqual(finding.evidence, ["broken.repo"])

    def test_invalid_enabled_value_is_not_counted_as_healthy(self):
        self.write_repo("invalid.repo", "[fixture]\nenabled=perhaps\n")
        finding = core.repository_findings(self.directory)[0]
        self.assertEqual(finding.status, "warning")
        self.assertEqual(finding.evidence, ["invalid.repo"])

    def test_unreadable_repository_is_reported(self):
        self.write_repo("unreadable.repo", "[fixture]\nenabled=1\n")
        with patch.object(Path, "read_text", side_effect=PermissionError):
            finding = core.repository_findings(self.directory)[0]
        self.assertEqual(finding.status, "warning")
        self.assertEqual(finding.evidence, ["unreadable.repo"])

    def test_enabled_default_and_disabled_sections_count_correctly(self):
        self.write_repo(
            "fixture.repo",
            "[main]\nenabled=1\n"
            "[explicit]\nenabled=1\n"
            "[default]\nname=Default enabled repository\n"
            "[disabled]\nenabled=0\n",
        )
        self.write_repo("ignored.txt", "[not-a-repo]\nenabled=1\n")
        finding = core.repository_findings(self.directory)[0]
        self.assertEqual(finding.status, "info")
        self.assertTrue(finding.explanation.startswith("2 "))
        self.assertIn("test edilmedi", finding.explanation)

    def test_main_and_disabled_sections_are_not_enabled_repositories(self):
        self.write_repo("fixture.repo", "[main]\nenabled=1\n[disabled]\nenabled=false\n")
        self.assertEqual(core.repository_findings(self.directory)[0].status, "warning")


class FlatpakValidationTests(unittest.TestCase):
    @patch("doctor.core.run")
    def test_invalid_app_ids_are_rejected_before_any_command(self, run):
        for app_id in ("", "editor", "org.example", "org.example.Editor;echo",
                       "--help", "org.example.Editor\n", "org.example.Editor extra",
                       "org.example-site.Editor"):
            with self.subTest(app_id=app_id):
                run.reset_mock()
                with self.assertRaises(ValueError):
                    core.check_app(app_id, "user")
                run.assert_not_called()

    @patch("doctor.core.run")
    def test_invalid_scopes_are_rejected_before_any_command(self, run):
        for scope in ("", "user extra", "../custom", "custom;echo", "user\n"):
            with self.subTest(scope=scope):
                run.reset_mock()
                with self.assertRaises(ValueError):
                    core.check_app(APP_ID, scope)
                run.assert_not_called()

    @patch("doctor.core.run")
    def test_all_commands_preserve_selected_installation(self, run):
        with tempfile.TemporaryDirectory() as folder:
            resolved_folder = str(Path(folder).resolve())
            for scope, option in (("user", "--user"), ("system", "--system"),
                                  ("fixture_store", "--installation=fixture_store")):
                with self.subTest(scope=scope):
                    run.reset_mock()
                    run.side_effect = [core.Result(0, RUNTIME), core.Result(0),
                                       core.Result(0, "read-only")]
                    findings = core.check_app(APP_ID, scope, folder)
                    self.assertEqual(run.call_args_list, [
                        call(["flatpak", "info", option, "--show-runtime", APP_ID]),
                        call(["flatpak", "info", option, RUNTIME]),
                        call(["flatpak", "info", option,
                              "--file-access=" + resolved_folder, APP_ID]),
                    ])
                    self.assertEqual(finding_named(findings, "Klasöre erişim").status, "info")

    @patch("doctor.core.run")
    def test_flatpak_list_preserves_installations_and_ignores_invalid_rows(self, run):
        run.return_value = core.Result(
            0,
            f"{APP_ID}\tEditor\tuser\n"
            f"{APP_ID}\tEditor\tsystem\n"
            f"{APP_ID}\tEditor\tfixture_store\n"
            "invalid-id\tIgnored\tuser\n"
            f"{APP_ID}\tIgnored\tbad scope\n"
            "incomplete\trow\n",
        )
        self.assertCountEqual(core.list_flatpaks(), [
            (APP_ID, "Editor", "user"),
            (APP_ID, "Editor", "system"),
            (APP_ID, "Editor", "fixture_store"),
        ])

    @patch("doctor.core.run")
    def test_failed_flatpak_list_does_not_trust_partial_output(self, run):
        run.return_value = core.Result(1, f"{APP_ID}\tEditor\tuser\n")
        self.assertEqual(core.list_flatpaks(), [])


class FlatpakAccessTests(unittest.TestCase):
    def test_hidden_access_is_warning_without_claiming_proven_app_failure(self):
        finding = core.access_finding(core.Result(0, "hidden\n"))
        self.assertEqual(finding.status, "warning")
        self.assertEqual(finding.evidence, ["Doğrudan erişim: yok"])
        self.assertIn("kesin değil", finding.certainty)

    def test_read_only_and_read_write_are_distinguished_without_claiming_app_success(self):
        cases = (("read-only", "Yalnız okuma"), ("read-write", "Okuma ve yazma"))
        for output, access in cases:
            with self.subTest(output=output):
                finding = core.access_finding(core.Result(0, output))
                self.assertEqual(finding.status, "info")
                self.assertEqual(finding.evidence, ["Doğrudan erişim: " + access])
                self.assertIn("kanıtlamaz", finding.explanation)

    def test_unrecognized_and_empty_access_are_unknown(self):
        for output in ("", "unexpected", "read", "read-write\nhidden"):
            with self.subTest(output=output):
                finding = core.access_finding(core.Result(0, output))
                self.assertEqual(finding.status, "unknown")
                self.assertEqual(finding.evidence, [])

    def test_failed_access_query_does_not_trust_partial_output(self):
        for code in (1, 124, 127):
            with self.subTest(code=code):
                finding = core.access_finding(core.Result(code, "read-write"))
                self.assertEqual(finding.status, "unknown")


class FlatpakRuntimeTests(unittest.TestCase):
    @patch("doctor.core.run")
    def test_missing_runtime_is_not_claimed_installed(self, run):
        run.side_effect = [core.Result(0, RUNTIME), core.Result(1)]
        findings = core.check_app(APP_ID, "user")
        self.assertEqual(finding_named(findings, "Uygulama kurulumu").status, "ok")
        runtime = finding_named(findings, "Çalışma ortamı")
        self.assertEqual(runtime.status, "unknown")
        self.assertEqual(runtime.evidence, [RUNTIME])
        self.assertNotIn("kurulu", runtime.explanation)

    @patch("doctor.core.run")
    def test_empty_or_malformed_runtime_information_is_not_claimed_installed(self, run):
        for output in ("", "not a runtime", "org.example.Platform/x86_64", RUNTIME + "\nextra"):
            with self.subTest(output=output):
                run.reset_mock()
                run.side_effect = None
                run.return_value = core.Result(0, output)
                findings = core.check_app(APP_ID, "system")
                self.assertEqual(finding_named(findings, "Çalışma ortamı").status, "unknown")
                self.assertEqual(run.call_count, 1)

    @patch("doctor.core.run")
    def test_unreadable_app_info_stops_before_runtime_or_access_queries(self, run):
        run.return_value = core.Result(1, RUNTIME)
        findings = core.check_app(APP_ID, "user", "/synthetic/unused-folder")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].status, "unknown")
        run.assert_called_once_with(["flatpak", "info", "--user", "--show-runtime", APP_ID])


if __name__ == "__main__":
    unittest.main()
