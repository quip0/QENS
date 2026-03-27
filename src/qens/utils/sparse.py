from __future__ import annotations

import numpy as np
import numpy.typing as npt


class GF2Matrix:
    """Sparse binary matrix over GF(2).

    Stores rows as sets of column indices where the entry is 1.
    Efficient for the sparse parity-check matrices common in QEC.
    """

    def __init__(self, num_rows: int, num_cols: int) -> None:
        self.num_rows = num_rows
        self.num_cols = num_cols
        self._rows: list[set[int]] = [set() for _ in range(num_rows)]

    @classmethod
    def from_dense(cls, matrix: npt.NDArray[np.uint8]) -> GF2Matrix:
        """Create from a dense numpy array (mod 2)."""
        m, n = matrix.shape
        gf2 = cls(m, n)
        for i in range(m):
            for j in range(n):
                if matrix[i, j] % 2 == 1:
                    gf2._rows[i].add(j)
        return gf2

    def to_dense(self) -> npt.NDArray[np.uint8]:
        """Convert to a dense numpy array."""
        result = np.zeros((self.num_rows, self.num_cols), dtype=np.uint8)
        for i, row in enumerate(self._rows):
            for j in row:
                result[i, j] = 1
        return result

    def set(self, row: int, col: int, value: int) -> None:
        """Set entry at (row, col) to value (mod 2)."""
        if value % 2 == 1:
            self._rows[row].add(col)
        else:
            self._rows[row].discard(col)

    def get(self, row: int, col: int) -> int:
        """Get entry at (row, col)."""
        return 1 if col in self._rows[row] else 0

    def dot_vec(self, vec: npt.NDArray[np.uint8]) -> npt.NDArray[np.uint8]:
        """Multiply this matrix by a binary vector (mod 2).

        Args:
            vec: Binary vector of length num_cols.

        Returns:
            Binary vector of length num_rows.
        """
        result = np.zeros(self.num_rows, dtype=np.uint8)
        for i, row in enumerate(self._rows):
            total = 0
            for j in row:
                total += int(vec[j])
            result[i] = total % 2
        return result

    def row_reduce(self) -> tuple[GF2Matrix, list[int]]:
        """Row-reduce to echelon form over GF(2).

        Returns:
            (reduced_matrix, pivot_columns).
        """
        mat = GF2Matrix(self.num_rows, self.num_cols)
        for i in range(self.num_rows):
            mat._rows[i] = set(self._rows[i])

        pivots: list[int] = []
        current_row = 0

        for col in range(mat.num_cols):
            # Find pivot row
            pivot = None
            for row in range(current_row, mat.num_rows):
                if col in mat._rows[row]:
                    pivot = row
                    break

            if pivot is None:
                continue

            # Swap rows
            mat._rows[current_row], mat._rows[pivot] = (
                mat._rows[pivot],
                mat._rows[current_row],
            )

            # Eliminate column in other rows
            for row in range(mat.num_rows):
                if row != current_row and col in mat._rows[row]:
                    mat._rows[row] = mat._rows[row] ^ mat._rows[current_row]

            pivots.append(col)
            current_row += 1

        return mat, pivots

    def kernel(self) -> list[npt.NDArray[np.uint8]]:
        """Compute the kernel (null space) over GF(2).

        Returns:
            List of binary vectors in the kernel.
        """
        reduced, pivots = self.row_reduce()
        pivot_set = set(pivots)
        free_cols = [c for c in range(self.num_cols) if c not in pivot_set]

        # Map pivot column -> row index
        pivot_to_row = {col: row for row, col in enumerate(pivots)}

        kernel_vecs: list[npt.NDArray[np.uint8]] = []
        for fc in free_cols:
            vec = np.zeros(self.num_cols, dtype=np.uint8)
            vec[fc] = 1
            for pc in pivots:
                if fc in reduced._rows[pivot_to_row[pc]]:
                    vec[pc] = 1
            kernel_vecs.append(vec)

        return kernel_vecs

    def __repr__(self) -> str:
        return f"GF2Matrix({self.num_rows}x{self.num_cols})"
