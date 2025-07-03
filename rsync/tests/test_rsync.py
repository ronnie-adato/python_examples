import io
import sys
import pytest
from ..rsync import parse_args, run_rsync, setup_logger
import asyncio


@pytest.fixture(autouse=True)
def setup_logging_fixture():
    setup_logger()


def test_parse_args_single_pair(monkeypatch):
    test_args = ["prog", "--src_dst", "src1,dst1"]
    monkeypatch.setattr("sys.argv", test_args)
    args, extra = parse_args()
    assert args.src_dst == [["src1", "dst1"]]
    assert extra == []


def test_parse_args_multiple_pairs(monkeypatch):
    test_args = ["prog", "--src_dst", "src1,dst1", "--src_dst", "src2,dst2"]
    monkeypatch.setattr("sys.argv", test_args)
    args, extra = parse_args()
    assert args.src_dst == [["src1", "dst1"], ["src2", "dst2"]]
    assert extra == []


def test_parse_args_with_extra(monkeypatch):
    test_args = ["prog", "--src_dst", "src1,dst1", "--info=progress2", "--info=delete0"]
    monkeypatch.setattr("sys.argv", test_args)
    args, extra = parse_args()
    assert args.src_dst == [["src1", "dst1"]]
    assert extra == ["--info=progress2", "--info=delete0"]


def test_parse_args_missing_src_dst(monkeypatch):
    test_args = ["prog"]
    monkeypatch.setattr("sys.argv", test_args)
    with pytest.raises(SystemExit):
        parse_args()


def test_parse_args_invalid_pair(monkeypatch):
    test_args = ["prog", "--src_dst", "src1only"]
    monkeypatch.setattr("sys.argv", test_args)
    with pytest.raises(ValueError):
        parse_args()


@pytest.mark.asyncio
async def test_run_rsync_invalid_src():
    # This test checks that run_rsync handles a non-existent source gracefully
    # It should not raise, but rsync will output an error
    src = "/nonexistent/source"
    dst = "/tmp"
    # We pass a dummy extra_args to avoid using sys.argv
    await run_rsync(src, dst, idx=0, extra_args=["-avh", "--bwlimit=100", "--dry-run"])


@pytest.mark.asyncio
async def test_run_rsync_output(tmp_path, capfd):
    # Create a dummy source file
    src_file = tmp_path / "src.txt"
    src_file.write_text("hello world\n")
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()

    await run_rsync(str(src_file), str(dst_dir), idx=0, extra_args=["-avh", "--bwlimit=100", "--dry-run"])

    out, _ = capfd.readouterr()
    # Check that the output contains the expected prefix and file name
    assert "[src1] " in out
    assert "src.txt" in out


@pytest.mark.asyncio
async def test_run_rsync_multiple_outputs(tmp_path, capfd):
    # Create multiple dummy source files
    src1 = tmp_path / "a.txt"
    src2 = tmp_path / "b.txt"
    src1.write_text("a\n")
    src2.write_text("b\n")
    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()

    await asyncio.gather(
        run_rsync(str(src1), str(dst_dir), idx=0, extra_args=["-avh", "--bwlimit=100", "--dry-run"]),
        run_rsync(str(src2), str(dst_dir), idx=1, extra_args=["-avh", "--bwlimit=100", "--dry-run"]),
    ) # type: ignore
    out, _ = capfd.readouterr()
    assert "[src1] " in out
    assert "[src2] " in out
    assert "a.txt" in out
    assert "b.txt" in out
