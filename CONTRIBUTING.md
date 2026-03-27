# Contributing to QENS

Welcome to QENS, a Python SDK for Quantum Error and Noise Simulation. We appreciate your interest in contributing. Whether you are reporting a bug, suggesting a feature, or submitting code, this guide will help you get started.

We follow standard open-source practices and expect all contributors to engage respectfully and constructively. Please treat others as you would like to be treated.

---

## How to Contribute

### Report Bugs

Open a [GitHub issue](https://github.com/quip0/QENS/issues) with:
- A clear, descriptive title.
- Steps to reproduce the problem.
- Expected vs. actual behavior.
- Your Python version and QENS version (`python --version`, `pip show qens`).

### Suggest Features

Open a [GitHub issue](https://github.com/quip0/QENS/issues) with:
- A description of the feature and why it would be useful.
- Any relevant references (papers, other libraries, etc.).

### Submit Pull Requests

See the full process below.

---

## Development Setup

```bash
git clone https://github.com/quip0/QENS.git
cd QENS
pip install -e ".[dev]"
pytest  # Verify everything passes
```

This installs QENS in editable mode along with all development dependencies (pytest, ruff, matplotlib, etc.).

---

## Code Standards

- **Python 3.11+** is required.
- **Type annotations** on all public APIs (function signatures, class attributes, return types).
- **Ruff** for linting, with a line-length limit of 88 characters.
- **Pure Python + NumPy only.** No compiled extensions, no Cython, no C bindings. This keeps the SDK portable and easy to install.
- **Follow existing patterns.** New subsystems should use the ABC + Registry architecture. Look at any existing module (e.g., `qens.noise`, `qens.codes`) for reference.

---

## Testing

All tests are run with pytest.

### Test Organization

Test files mirror the source tree:

```
tests/
  test_core/
    test_types.py
    test_circuit.py
    test_noise_channel.py
    test_registry.py
  test_noise/
    test_bit_flip.py
    test_depolarizing.py
    ...
  test_codes/
    test_repetition.py
    test_surface.py
    ...
  test_decoders/
    test_lookup_table.py
    test_mwpm.py
    ...
  test_simulation/
    test_noisy_sampler.py
    test_threshold.py
    ...
  test_viz/
    test_draw_circuit.py
    test_plot_threshold.py
    ...
```

### Test Guidelines

- **Noise models:** Use statistical tests with at least 10,000 samples and 3-sigma tolerance bands.
- **QEC codes:** Verify stabilizer properties, syndrome computation, and check matrix dimensions.
- **Decoders:** Test against known syndrome-to-correction mappings.
- **Visualizations:** Smoke tests only -- create the figure and close it immediately. Do not compare pixel output.

### Running Tests

```bash
# Run the full test suite (194 tests, <1 second)
pytest

# Run a specific test file
pytest tests/test_noise/test_bit_flip.py

# Run with verbose output
pytest -v

# Lint the source
ruff check src/qens/
```

---

## Pull Request Process

1. **Fork** the repository and create a feature branch from `main`.
2. **Write your code** and corresponding tests.
3. **Run the test suite** (`pytest`) and the linter (`ruff check src/qens/`). All checks must pass.
4. **Open a pull request** against `main` with a clear description of what you changed and why.
5. A maintainer will review your PR. Address any feedback and push updates to your branch.

---

## Adding New Components

QENS is designed to be extended. Here is how to add each type of component:

### New Error Model

1. Create a new file in `src/qens/noise/` (e.g., `my_error.py`).
2. Subclass `ErrorModel` and implement the required methods.
3. Register it in `src/qens/noise/__init__.py` using `noise_registry.register(...)`.
4. Add tests in `tests/test_noise/test_my_error.py`.

### New QEC Code

1. Create a new file in `src/qens/codes/` (e.g., `my_code.py`).
2. Subclass `QECCode` and implement all abstract properties and methods.
3. Register it in `src/qens/codes/__init__.py` using `code_registry.register(...)`.
4. Add tests in `tests/test_codes/test_my_code.py`.

### New Decoder

1. Create a new file in `src/qens/decoders/` (e.g., `my_decoder.py`).
2. Subclass `Decoder` and implement `decode()`.
3. Register it in `src/qens/decoders/__init__.py` using `decoder_registry.register(...)`.
4. Add tests in `tests/test_decoders/test_my_decoder.py`.

### New Visualizer

1. Create a new file in `src/qens/viz/` (e.g., `my_viz.py`).
2. Subclass `Visualizer` and implement `draw()`.
3. Register it in `src/qens/viz/__init__.py` using `viz_registry.register(...)`.
4. Add smoke tests in `tests/test_viz/test_my_viz.py`.

See the [Extension Guide](docs/extending.md) for detailed examples.

---

## Commit Messages

- Use the imperative mood: "Add feature" not "Added feature" or "Adds feature".
- Keep the first line under 72 characters.
- Optionally add a blank line followed by a more detailed explanation.

Examples:

```
Add thermal relaxation error model

Implements T1/T2 relaxation as a probabilistic Pauli channel.
Includes statistical tests with 10k samples.
```

```
Fix syndrome computation for surface code with even distance
```

---

## Questions?

If you have questions about contributing, open an issue on GitHub and we will be happy to help.
