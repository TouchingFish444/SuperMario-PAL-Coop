"""Build and publish the current Windows ready-to-play package on GitHub."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from app.netplay import PAL_RELEASE_TAG, ROOT
from tools.build_windows import READY_TO_PLAY_NAME, build


def run(*command: str) -> str:
    result = subprocess.run(command, cwd=ROOT, capture_output=True, encoding="utf-8", check=True)
    return result.stdout.strip()


def release_info(repo: str) -> dict | None:
    try:
        return json.loads(run(
            "gh", "release", "view", PAL_RELEASE_TAG, "--repo", repo,
            "--json", "databaseId,isDraft,targetCommitish,url",
        ))
    except subprocess.CalledProcessError as error:
        if error.stderr.strip().lower() == "release not found":
            return None
        raise


def release_asset(repo: str, release_id: int) -> dict | None:
    assets = json.loads(run("gh", "api", f"repos/{repo}/releases/{release_id}/assets"))
    return next((asset for asset in assets if asset["name"] == f"{READY_TO_PLAY_NAME}.zip"), None)


def check_existing_tag(repo: str, commit: str) -> None:
    try:
        tagged = run("gh", "api", f"repos/{repo}/commits/{PAL_RELEASE_TAG}", "--jq", ".sha")
    except subprocess.CalledProcessError as error:
        if "(HTTP 404)" in error.stderr or "(HTTP 422)" in error.stderr:
            return
        raise
    if tagged != commit:
        raise ValueError(f"标签 {PAL_RELEASE_TAG} 已指向另一个提交")


def publish(repo: str, notes: Path) -> str:
    if not notes.is_file():
        raise ValueError(f"找不到版本说明：{notes}")
    if run("git", "status", "--porcelain"):
        raise ValueError("请先提交本次发行的源码和文档")
    commit = run("git", "rev-parse", "HEAD")
    repository = json.loads(run("gh", "api", f"repos/{repo}"))
    branch = repository["default_branch"]
    if run("gh", "api", f"repos/{repo}/commits/{branch}", "--jq", ".sha") != commit:
        raise ValueError(f"请先把当前提交推送到 GitHub 的 {branch} 分支")
    check_existing_tag(repo, commit)

    release = release_info(repo)
    if release is not None and release["targetCommitish"] != commit:
        raise ValueError(f"{PAL_RELEASE_TAG} 已对应另一个提交，请使用新的版本号")

    asset = release_asset(repo, release["databaseId"]) if release is not None else None
    upload_needed = asset is None
    archive = ROOT / "dist" / f"{READY_TO_PLAY_NAME}.zip"
    if upload_needed:
        (archive,) = build(include_rom=True)
        if release is None:
            run(
                "gh", "release", "create", PAL_RELEASE_TAG, "--repo", repo, "--draft",
                "--target", commit, "--title", f"PAL {PAL_RELEASE_TAG} Windows 即玩版",
                "--notes-file", str(notes),
            )
            release = release_info(repo)
            if release is None:
                raise RuntimeError("GitHub 尚未返回 Release 草稿")

        subprocess.run(
            ["gh", "release", "upload", PAL_RELEASE_TAG, str(archive), "--repo", repo],
            cwd=ROOT, check=True,
        )
        asset = release_asset(repo, release["databaseId"])

    if asset is None or asset["state"] != "uploaded":
        raise RuntimeError("GitHub 上的附件尚未上传完成")
    if upload_needed or release["isDraft"]:
        digest = sha256()
        with archive.open("rb") as content:
            for chunk in iter(lambda: content.read(1024 * 1024), b""):
                digest.update(chunk)
        if (asset["size"] != archive.stat().st_size
                or asset.get("digest") != f"sha256:{digest.hexdigest()}"):
            raise RuntimeError("GitHub 上的附件与本机即玩包校验值不一致")

    if release["isDraft"]:
        run("gh", "release", "edit", PAL_RELEASE_TAG, "--repo", repo, "--draft=false", "--latest")
        release = release_info(repo)
        if release is None or release["isDraft"]:
            raise RuntimeError("GitHub 尚未确认 Release 已发布")
    return release["url"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="GitHub 仓库，格式为 OWNER/REPO")
    args = parser.parse_args()
    try:
        print(publish(args.repo, ROOT / "docs" / "releases" / f"{PAL_RELEASE_TAG}.md"))
    except subprocess.CalledProcessError as error:
        parser.exit(1, f"{error.stderr.strip() if error.stderr else error}\n")
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
