from __future__ import annotations



from qens.core.types import PauliString, Syndrome
from qens.codes.base import QECCode
from qens.noise.base import ErrorModel
from qens.decoders.base import Decoder
from qens.simulation.result import SimulationResult
from qens.utils.random import get_rng


class NoisySampler:
    """Monte Carlo sampler for noisy QEC circuits.

    Runs the Pauli frame simulation loop:
    1. For each shot, sample errors from the noise model
    2. Propagate errors through the syndrome circuit
    3. Extract syndromes
    4. Optionally decode and check for logical errors
    """

    def __init__(self, seed: int | None = None) -> None:
        self._rng = get_rng(seed)

    def sample_errors(
        self,
        code: QECCode,
        noise_model: ErrorModel,
        shots: int,
    ) -> SimulationResult:
        """Sample errors and compute syndromes without decoding.

        This is the core sampling loop. For each shot:
        1. Sample a random Pauli error from the noise model
        2. Compute the syndrome using the code's check matrix
        """
        nd = code.num_data_qubits
        all_qubits = list(range(nd))
        syndromes: list[Syndrome] = []
        errors: list[PauliString] = []

        for _ in range(shots):
            noise_model.reset()
            error = noise_model.sample_errors(nd, all_qubits, self._rng)
            syndrome = code.compute_syndrome(error)
            syndromes.append(syndrome)
            errors.append(error)

        return SimulationResult(syndromes=syndromes, errors=errors)

    def run(
        self,
        code: QECCode,
        noise_model: ErrorModel,
        decoder: Decoder,
        shots: int,
    ) -> SimulationResult:
        """Full simulation: sample errors, decode, check for logical errors.

        For each shot:
        1. Sample a random Pauli error
        2. Compute the syndrome
        3. Decode the syndrome to get a correction
        4. Check if error + correction is a logical error
        """
        from qens.utils.pauli_algebra import pauli_string_multiply

        nd = code.num_data_qubits
        all_qubits = list(range(nd))

        syndromes: list[Syndrome] = []
        errors: list[PauliString] = []
        corrections: list[PauliString] = []
        logical_errors: list[bool] = []

        for _ in range(shots):
            noise_model.reset()
            error = noise_model.sample_errors(nd, all_qubits, self._rng)
            syndrome = code.compute_syndrome(error)

            result = decoder.decode(syndrome)

            # Residual = error * correction
            residual, _ = pauli_string_multiply(error, result.correction)
            is_logical = code.is_logical_error(residual)

            syndromes.append(syndrome)
            errors.append(error)
            corrections.append(result.correction)
            logical_errors.append(is_logical)

        return SimulationResult(
            syndromes=syndromes,
            errors=errors,
            corrections=corrections,
            logical_errors=logical_errors,
        )
