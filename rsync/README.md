# Rsync Real-Time Output Python Script

This project provides a Python script to run `rsync` commands with real-time, line-by-line output updates for each source-destination pair. Each pair's progress is displayed and updated on its own line.

**Note:** The script itself uses only Python standard library modules. Any additional libraries listed in the dependencies are required for testing and development only, not for running the main script.

## Usage

1. Install requirements (recommended):

   ```bash
   pip install .
   # or, for development (installs dev dependencies too):
   pip install -e .
   ```

   This will install all dependencies specified in `pyproject.toml`.

   Alternatively, you can use [pipx](https://pypa.github.io/pipx/) or [poetry](https://python-poetry.org/) if you prefer.

2. Run the script with one or more `--src_dst` arguments (each as `src,dst`):

   ```bash
   python rsync.py --src_dst /path/to/source1,/path/to/dest1 --src_dst /path/to/source2,/path/to/dest2 [other rsync args]
   ```

   - You must provide at least one `--src_dst` argument.
   - You can repeat `--src_dst` as many times as needed for multiple pairs.
   - Any additional arguments are passed directly to `rsync`.

3. Example:

   ```bash
   python rsync.py --info=delete0 --src_dst ./src1,./dst1 --src_dst ./src2,./dst2 --info=progress2
   ```

   This will run two rsync jobs in parallel, each with real-time output, and pass `--info=delete0 --info=progress2` to each.

## Features

- Real-time, line-by-line output for each source-destination pair.
- Supports any valid rsync arguments after the `--src_dst` pairs.
- Logging to `rsync.log` with rotation.
- Async implementation for efficient parallel execution.

## Requirements

- Python 3.8+
- `rsync` installed and available in your system PATH
- **No third-party Python libraries are required to run the script itself.**
- Python packages: `pytest`, `pytest-asyncio` (for testing only)

## Testing

Run all tests with:

```bash
pytest
```

### What is tested?

- Argument parsing for single, multiple, extra, missing, and invalid `--src_dst` pairs
- Real-time output: tests capture and assert that the output contains the correct prefixes and file names for each rsync job, both for single and multiple sources
- Async error handling for invalid sources
