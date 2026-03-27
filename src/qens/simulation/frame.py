from __future__ import annotations

import numpy as np

from qens.core.types import PauliString, PauliOp
from qens.core.circuit import Circuit, Gate
from qens.utils.pauli_algebra import pauli_string_multiply


class PauliFrameSimulator:
    """Pauli frame simulator for Clifford circuits.

    Tracks Pauli errors through a Clifford circuit efficiently.
    Instead of simulating full quantum states, only tracks how Pauli errors
    propagate through gates. This is O(n) per gate instead of O(2^n).

    Supports: H, X, Z, CX (CNOT), CZ, M (measurement), R (reset).
    """

    def __init__(self, num_qubits: int) -> None:
        self._num_qubits = num_qubits
        self._frame = np.zeros(num_qubits, dtype=np.uint8)

    @property
    def frame(self) -> PauliString:
        return self._frame.copy()

    def reset(self) -> None:
        self._frame[:] = 0

    def apply_error(self, error: PauliString) -> None:
        """Compose an error onto the current Pauli frame."""
        self._frame, _ = pauli_string_multiply(self._frame, error)

    def propagate_gate(self, gate: Gate) -> None:
        """Propagate the Pauli frame through a Clifford gate.

        Conjugation rules:
        - H: X <-> Z, Y -> -Y (phase doesn't matter for Pauli frame)
        - CX: XI -> XX, IX -> IX, ZI -> ZI, IZ -> ZZ
        - CZ: XI -> XZ, IX -> ZX, ZI -> ZI, IZ -> IZ
        """
        if gate.name == "H":
            q = gate.qubits[0]
            p = self._frame[q]
            if p == PauliOp.X:
                self._frame[q] = PauliOp.Z
            elif p == PauliOp.Z:
                self._frame[q] = PauliOp.X
            # Y -> Y (up to phase, which we don't track)

        elif gate.name == "CX":
            ctrl, tgt = gate.qubits
            pc, pt = self._frame[ctrl], self._frame[tgt]

            # Propagation: CX conjugation on Pauli tensor products
            # X_c -> X_c X_t, Z_t -> Z_c Z_t
            if pc == PauliOp.X:
                # X on control propagates to target
                self._frame[tgt] ^= PauliOp.X
            elif pc == PauliOp.Y:
                # Y = iXZ: X propagates, Z stays
                self._frame[tgt] ^= PauliOp.X

            if pt == PauliOp.Z:
                # Z on target propagates to control
                self._frame[ctrl] ^= PauliOp.Z
            elif pt == PauliOp.Y:
                # Y = iXZ: Z propagates back
                self._frame[ctrl] ^= PauliOp.Z

        elif gate.name == "CZ":
            q0, q1 = gate.qubits
            p0, p1 = self._frame[q0], self._frame[q1]

            # CZ: X_0 -> X_0 Z_1, X_1 -> Z_0 X_1
            if p0 in (PauliOp.X, PauliOp.Y):
                self._frame[q1] ^= PauliOp.Z
            if p1 in (PauliOp.X, PauliOp.Y):
                self._frame[q0] ^= PauliOp.Z

        elif gate.name in ("X", "Z", "M", "R"):
            pass  # These don't change the Pauli frame tracking

    def propagate_circuit(self, circuit: Circuit) -> None:
        """Propagate the frame through an entire circuit."""
        for moment in circuit.moments:
            for gate in moment.gates:
                self.propagate_gate(gate)

    def measure(self, qubit: int) -> int:
        """Read out the Pauli frame value on a qubit.

        Returns 1 if there's an X or Y error (bit flip), 0 otherwise.
        """
        p = self._frame[qubit]
        return 1 if p in (PauliOp.X, PauliOp.Y) else 0
