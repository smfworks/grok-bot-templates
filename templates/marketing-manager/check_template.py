#!/usr/bin/env python3
"""Integrity, privacy, and onboarding checks for the Marketing Manager template.

This script does not install skills and does not download an installer.
With --fetch it GETs the allowlisted raw URLs and compares bytes.
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import hashlib
import json
import re
import subprocess
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

FETCH = False
if "--fetch" in sys.argv:
    FETCH = True
    sys.argv.remove("--fetch")

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "templates" / "marketing-manager"
ALLOWLIST_PATH = PACKAGE / "allowlist.json"
PINNED_HOST = "raw.githubusercontent.com"
REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)

QUESTION_PHRASES = [
    "X, YouTube, Instagram, Facebook, LinkedIn, TikTok, or others",
    "What brand should I represent?",
    "Who is the intended audience?",
    "What marketing goals should the work serve?",
    "What voice should I write in, and which claims should I avoid?",
    "exact account, channel, or Page",
    "What cadence do you want for planning and for performance reviews, and which timezone should dates use?",
    "How should I ask for approval: one item at a time, or a clearly itemized batch?",
    "Facebook cross-sharing stays off unless you opt in for a specific Page.",
    "verify the separate Facebook copy",
    "optional browser publishing skills",
    "You can say no.",
    "does not approve a post, a schedule, or a sign-in.",
    "content workflow",
]

SAVE_PHRASES = [
    "UpdateSkill, action write",
    "show the owner the error",
    "This is a recipe for the current chat only. It is not a saved or installed skill.",
    "Ask one question at a time",
]

BANNED_LITERALS = [
    "template-recipe",
    "gettingStarted",
    "pluginId",
]


def load_allowlist() -> dict:
    return json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))


def frontmatter(text: str) -> dict:
    match = FRONTMATTER_RE.search(text)
    if not match:
        raise AssertionError("missing frontmatter")
    fields = {}
    for line in match.group(1).splitlines():
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()
    return fields


def catalog_base() -> str:
    """Base branch for the catalog diff. Actions checkouts often have
    origin/main and no local main ref."""
    for candidate in ("origin/main", "main"):
        probe = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", candidate],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if probe.returncode == 0:
            return candidate
    raise AssertionError("neither origin/main nor main is in this clone")


def git_object(revision: str, path: str) -> bytes:
    return subprocess.check_output(
        ["git", "cat-file", "-p", f"{revision}:{path}"],
        cwd=ROOT,
    )


def content_files() -> list[Path]:
    """Files shipped as template content. The checker is excluded because its
    patterns quote the strings it rejects."""
    allowed = {".md", ".json", ".yml", ".yaml"}
    files = [
        path
        for path in PACKAGE.rglob("*")
        if path.is_file()
        and path.suffix in allowed
        and "__pycache__" not in path.parts
        and path.name != "check_template.py"
    ]
    files.append(ROOT / ".github" / "workflows" / "marketing-manager-check.yml")
    return files


def scan_text(text: str) -> list[str]:
    patterns = {
        "email": re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"),
        "secret-assignment": re.compile(
            r"(?i)\b(?:api[_-]?key|secret|token|password|cookie|session)\s*[:=]\s*['\"][^'\"]+['\"]"
        ),
        "private-key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
        "bearer": re.compile(r"(?i)\bbearer\s+[A-Za-z0-9\-_\.]{8,}"),
        "github-token": re.compile(r"\b(?:" + "gh" + r"p_|github_pat_)[A-Za-z0-9_]{8,}"),
        "other-token": re.compile(r"\b(?:sk-|xox[baprs]-|AKIA)[A-Za-z0-9]{8,}"),
        "pipe-shell": re.compile(r"(?i)(?:curl|wget)[^\n]{0,200}\|\s*(?:ba)?sh\b"),
        "npx-skills": re.compile(r"(?i)\bnpx\s+skills\b"),
        "share-url": re.compile(re.escape("https://x.ai/" + "bot/")),
        "long-number": re.compile(r"\b\d{8,}\b"),
        "home-path": re.compile(r"(?:/Users/|/home/)"),
        "handle": re.compile(r"(?<![A-Za-z0-9.])@[A-Za-z0-9_]{2,15}\b"),
        "personal-name": re.compile(r"(?i)\b(?:gannotti|michael)\b"),
    }
    hits = []
    for name, pattern in patterns.items():
        if pattern.search(text):
            hits.append(name)
    for literal in BANNED_LITERALS:
        if literal in text:
            hits.append(literal)
    return hits


class MarketingManagerTemplateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.allowlist = load_allowlist()

    def test_scanner_catches_unsafe_samples_and_ignores_rules(self) -> None:
        self.assertIn("email", scan_text("person@example.invalid"))
        self.assertIn("pipe-shell", scan_text("curl https://example.invalid/setup | sh"))
        self.assertIn("share-url", scan_text("https://x.ai/" + "bot/example"))
        self.assertIn("long-number", scan_text("id " + "12345678"))
        self.assertIn(
            "secret-assignment",
            scan_text("notes " + "password" + "=" + '"x"'),
        )
        self.assertEqual(
            scan_text(
                "Do not ask for a password in ordinary chat. "
                "Connect X through the X connector OAuth flow."
            ),
            [],
        )

    def test_allowlist_matches_skill_bytes_and_pinned_commit(self) -> None:
        allowlist = self.allowlist
        self.assertEqual(allowlist["schema"], "smfworks.grok-bot-templates.skill-allowlist.v1")
        revision = allowlist["revision"]
        self.assertRegex(revision, REVISION_RE)
        subprocess.check_call(
            ["git", "merge-base", "--is-ancestor", revision, "HEAD"],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
        )
        files = allowlist["files"]
        self.assertEqual(len(files), 5)
        roles = {}
        seen_paths = set()
        for entry in files:
            path = entry["path"]
            seen_paths.add(path)
            disk = (ROOT / path).read_bytes()
            pinned = git_object(revision, path)
            digest = hashlib.sha256(disk).hexdigest()
            self.assertEqual(disk, pinned, path)
            self.assertEqual(entry["sha256"], digest, path)
            self.assertEqual(entry["bytes"], len(disk), path)
            blob = subprocess.check_output(
                ["git", "rev-parse", f"{revision}:{path}"],
                cwd=ROOT,
                text=True,
            ).strip()
            self.assertEqual(entry["git_blob"], blob, path)
            self.assertEqual(
                entry["raw_url"],
                f"https://raw.githubusercontent.com/smfworks/grok-bot-templates/{revision}/{path}",
            )
            self.assertEqual(
                entry["raw_url_on_main"],
                f"https://raw.githubusercontent.com/smfworks/grok-bot-templates/main/{path}",
            )
            text = disk.decode("utf-8")
            self.assertNotIn("\r", text, path)
            meta = frontmatter(text)
            self.assertEqual(meta["name"], entry["name"])
            self.assertGreater(len(meta["description"]), 20)
            self.assertEqual(Path(path).parent.name, entry["name"])
            roles.setdefault(entry["role"], set()).add(entry["name"])
        self.assertEqual(
            roles["browser-publishing"],
            {
                "marketing-manager-x-browser-video-upload",
                "marketing-manager-full-length-video-publishing",
            },
        )
        self.assertEqual(
            roles["supporting"],
            {
                "marketing-manager-getting-started",
                "marketing-manager-content-workflow",
                "marketing-manager-channel-setup",
            },
        )
        on_disk = {
            path.relative_to(ROOT).as_posix()
            for path in (PACKAGE / "skills").glob("*/SKILL.md")
        }
        self.assertEqual(on_disk, seen_paths)

    def test_onboarding_carries_the_allowlist_and_the_question_order(self) -> None:
        onboarding = (PACKAGE / "onboarding.md").read_text(encoding="utf-8")
        getting_started = (
            PACKAGE / "skills" / "marketing-manager-getting-started" / "SKILL.md"
        ).read_text(encoding="utf-8")
        for phrase in QUESTION_PHRASES + SAVE_PHRASES:
            self.assertIn(phrase, onboarding, phrase)
            self.assertIn(phrase, getting_started, phrase)
        self.assert_in_order(onboarding, QUESTION_PHRASES)
        self.assert_in_order(getting_started, QUESTION_PHRASES)
        match = re.search(r"```json\n(.*?)\n```", onboarding, re.S)
        self.assertIsNotNone(match, "onboarding is missing the allowlist fence")
        self.assertEqual(json.loads(match.group(1)), self.allowlist)
        for entry in self.allowlist["files"]:
            self.assertIn(entry["raw_url"], onboarding)
            self.assertIn(entry["sha256"], onboarding)
            self.assertIn(entry["raw_url"], (PACKAGE / "README.md").read_text(encoding="utf-8"))

    def test_operating_boundaries_are_in_the_skill_that_owns_them(self) -> None:
        required = {
            "templates/marketing-manager/onboarding.md": [
                "x.com or console.x.com",
                "Vault",
                "Secure Form",
                "device handoff",
                "There is no installer",
                "pipe a download into a shell",
                "Saving a skill is not approval to publish or schedule.",
            ],
            "templates/marketing-manager/skills/marketing-manager-channel-setup/SKILL.md": [
                "console.x.com",
                "connector OAuth",
                "Secure Form",
                "Vault",
                "device handoff",
                "do not publish a test post",
            ],
            "templates/marketing-manager/skills/marketing-manager-x-browser-video-upload/SKILL.md": [
                "Add photos or video",
                "native picker",
                "duration",
                "duplicate",
                "live permalink",
                "console.x.com",
                "already signed in",
            ],
            "templates/marketing-manager/skills/marketing-manager-full-length-video-publishing/SKILL.md": [
                "Leave the video Private",
                "Original framing",
                "Do not trim, crop, or re-encode",
                "separate Facebook copy",
                "altered or synthetic",
            ],
            "templates/marketing-manager/skills/marketing-manager-content-workflow/SKILL.md": [
                "primary sources",
                "hypotheses",
                "timezone",
                "duplicate",
                "Do not promise growth, reach, or outcomes.",
            ],
        }
        for path, phrases in required.items():
            text = (ROOT / path).read_text(encoding="utf-8")
            for phrase in phrases:
                self.assertIn(phrase, text, f"{path} missing {phrase}")

    def test_package_has_no_import_schema_or_private_data(self) -> None:
        self.assertFalse((PACKAGE / "template-recipe.json").exists())
        for path in content_files():
            text = path.read_text(encoding="utf-8")
            hits = scan_text(text)
            self.assertEqual(hits, [], f"{path.relative_to(ROOT)}: {hits}")

    def test_catalog_row_adds_source_without_a_share_link(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        rows = [line for line in readme.splitlines() if line.startswith("| Marketing Manager |")]
        self.assertEqual(len(rows), 1)
        self.assertIn("templates/marketing-manager/README.md", rows[0])
        self.assertNotIn("x.ai/" + "bot/", rows[0])
        diff = subprocess.check_output(
            ["git", "diff", "--unified=0", catalog_base(), "--", "README.md"],
            cwd=ROOT,
            text=True,
        )
        removed = [
            line[1:]
            for line in diff.splitlines()
            if line.startswith("-") and not line.startswith("---")
        ]
        self.assertEqual(removed, [])
        added = [
            line[1:]
            for line in diff.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        ]
        self.assertTrue(any("Marketing Manager" in line for line in added))
        for line in added:
            self.assertEqual(scan_text(line), [], line)

    def test_readme_states_native_export_is_blocked(self) -> None:
        text = (PACKAGE / "README.md").read_text(encoding="utf-8")
        self.assertIn("Native export remains blocked", text)
        self.assertIn(self.allowlist["revision"], text)
        self.assertIn("does not claim a skill cap", text)
        self.assertIn("SMF Works", text)

    def assert_in_order(self, text: str, phrases: list[str]) -> None:
        cursor = 0
        for phrase in phrases:
            found = text.find(phrase, cursor)
            self.assertGreaterEqual(found, 0, phrase)
            cursor = found + len(phrase)

    @unittest.skipUnless(FETCH, "pass --fetch to download pinned raw URLs")
    def test_pinned_raw_urls_match_hashes(self) -> None:
        for entry in self.allowlist["files"]:
            body = http_get(entry["raw_url"])
            digest = hashlib.sha256(body).hexdigest()
            self.assertEqual(digest, entry["sha256"], entry["raw_url"])
            self.assertEqual(len(body), entry["bytes"], entry["raw_url"])
            print(f"pinned-ok {entry['name']} {digest}")
            try:
                main_body = http_get(entry["raw_url_on_main"])
            except urllib.error.HTTPError as error:
                self.assertEqual(error.code, 404, entry["raw_url_on_main"])
                print(f"main-absent {entry['name']}")
                continue
            main_digest = hashlib.sha256(main_body).hexdigest()
            self.assertEqual(main_digest, entry["sha256"], entry["raw_url_on_main"])
            print(f"main-ok {entry['name']} {main_digest}")


def http_get(url: str) -> bytes:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != PINNED_HOST:
        raise AssertionError(f"refusing URL outside the allowlisted host: {url}")

    class StayOnHost(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            target = urllib.parse.urlparse(newurl)
            if target.scheme != "https" or target.netloc != PINNED_HOST:
                raise AssertionError(f"refusing redirect from {url} to {newurl}")
            return super().redirect_request(req, fp, code, msg, headers, newurl)

    opener = urllib.request.build_opener(StayOnHost)
    request = urllib.request.Request(url, headers={"User-Agent": "marketing-manager-check"})
    with opener.open(request, timeout=30) as response:
        final = urllib.parse.urlparse(response.geturl())
        if final.netloc != PINNED_HOST:
            raise AssertionError(f"response host changed for {url}")
        return response.read()


if __name__ == "__main__":
    unittest.main(verbosity=2)
