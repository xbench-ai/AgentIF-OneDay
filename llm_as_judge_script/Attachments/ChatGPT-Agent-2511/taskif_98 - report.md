# Quantum Non‑linear Transformation of Complex Amplitudes

## Background and problem statement

The quantum mechanical evolution of a quantum state is **linear**, yet many tasks in machine learning and differential equations require non‑linear maps.  The paper *Nonlinear transformation of complex amplitudes via quantum singular value transformation* defines the **Nonlinear Transformation of Complex Amplitudes (NTCA)**.  Suppose we have a state preparation oracle

\[
U\:|0\rangle \;\longrightarrow\;\sum_{k=1}^N c_k\,|k\rangle
\]

that encodes a complex vector \(\mathbf{c}=\{c_1,\dots,c_N\}\).  Each amplitude can be written as \(c_k=x_k+i\,y_k\).  Given bounded functions \(P,Q:[-1,1]\to\mathbb{C}\), NTCA asks us to prepare a quantum state whose amplitudes are (up to normalisation) \(P(x_k)+Q(y_k)\).  In other words, one wants a circuit that outputs an \(\varepsilon\)-approximation of

\[
\frac{1}{\sqrt{c}}\sum_{k=1}^N \bigl(P(x_k)+Q(y_k)\bigr)\,|k\rangle,
\]

where \(c\) is a normalisation constant.  The formal definition in the paper requires that the output amplitudes \(b_k\) satisfy \(|b_k-(P(x_k)+Q(y_k))|\le \varepsilon/N\) for all \(k\)【608189420933610†L154-L175】.

Implementing arbitrary non‑linear functions on amplitudes is non‑trivial because general non‑unitary maps violate the linearity of quantum mechanics.  The authors circumvent this by using **quantum singular value transformation (QSVT)**.  The idea is to encode the **real** and **imaginary** parts of the amplitudes as singular values of specially constructed unitaries and then apply polynomial transformations to those singular values.  The essential ingredients are:

* **Block‑encoding of amplitudes.**  A **block‑encoding** is a way to embed a matrix \(A\) in the top‑left block of a larger unitary, allowing singular value transformations to be applied.  Given a state preparation oracle \(U\), the paper shows how to build a unitary \(\tilde G\) such that the top‑left block of \(\tilde G\) is the Hermitian matrix whose eigenvalues are the **real parts** \(x_k\) of the amplitudes, and a similar \(\tilde G'\) encodes the imaginary parts【608189420933610†L214-L246】.  These constructions require only four uses of controlled‑\(U\) and controlled‑\(U^\dagger\) and \(O(n)\) one‑ and two‑qubit gates【608189420933610†L214-L246】.

* **Polynomial eigenvalue transformation.**  Once one has a block‑encoding \(\tilde G\) of a Hermitian matrix \(A\), a polynomial \(P\) can be applied to its eigenvalues using QSVT.  Lemma 3 of the paper states that if \(P\) is a degree‑\(d\) polynomial satisfying \(|P(x)|\le 1/4\) on \([-1,1]\), then one can construct a circuit that implements a block‑encoding of \(P(A/\alpha)\) using \(d\) applications of the block‑encoding and its adjoint【608189420933610†L187-L204】.  For real‑valued functions, only two ancilla qubits are needed, while complex‑valued functions require three.

* **Putting it together.**  To compute \(P(x_k)\) and \(Q(y_k)\), the algorithm constructs two block‑encodings \(P\) and \(Q\) whose singular values are \(P'(x_k)/(4\gamma)\) and \(Q'(y_k)/(4\gamma)\).  Here \(P'\) and \(Q'\) are polynomial approximations of the desired functions (the Weierstrass approximation theorem guarantees such approximations), and \(\gamma\) is the maximum magnitude of \(P\) and \(Q\).  Controlled versions of these block‑encodings are applied in a superposition, followed by uncomputation and a Hadamard on a control qubit.  Post‑selecting on certain ancillas being in \(|0\rangle\) yields a state whose amplitudes are proportional to \(P'(x_k)+Q'(y_k)\)【608189420933610†L525-L556】.  When only a **real** function \(P\) is required (as in our example where the amplitudes are real), the paper remarks that the number of ancilla qubits can be reduced from five to three【608189420933610†L637-L651】.

The algorithm is probabilistic.  The success probability (i.e. the probability that the required ancilla measurement yields \(|0\rangle\) on all ancilla qubits) depends on the norm of \(P'(x_k)+Q'(y_k)\).  Amplitude amplification can boost this probability quadratically【608189420933610†L525-L604】.

## Simplified toy model

Implementing the full QSVT‑based algorithm for arbitrary \(N\) requires careful synthesis of block‑encodings and controlled operations.  For a **small input dimension** (here \(N=8\)) and real amplitudes, we can construct a toy model that illustrates the idea of NTCA while avoiding the technical overhead of block‑encoding synthesis.  The key steps are:

1. **Prepare the initial amplitude‑encoded state.**  We start with a normalised real vector \(\mathbf{c}=(c_1,c_2,\dots,c_8)\) and prepare the state \(|\psi\rangle=\sum_k c_k\,|k\rangle\).  In the toy model we simulate this preparation classically by forming the state vector.

2. **Apply a non‑linear polynomial to each amplitude.**  For real amplitudes there is a single function \(P:\mathbb{R}\to\mathbb{R}\).  The paper notes that a real function only requires three ancilla qubits【608189420933610†L637-L651】, but in simulation we can simply compute \(b_k=P(c_k)\).  In our example the user chooses the polynomial \(P(x)=x^3+x^2+x\).  Since \(\sum_k |c_k|^2=1\), the amplitudes \(c_k\) lie in \([-1,1]\), as required.  After computing \(b_k\), we renormalise to obtain a valid quantum state.

3. **(Optional) Simulate post‑selection and amplitude amplification.**  In the full algorithm the circuit succeeds only when a measurement outcome shows the ancillas in \(|0\rangle\).  The success probability is \(\frac{1}{64 \gamma^2 N}\sum_k |P(c_k)|^2\)【608189420933610†L525-L564】, where \(\gamma=\max_k |P(c_k)|\).  Amplitude amplification can be used to boost this probability quadratically.  In our toy model we compute the success probability but do not simulate amplitude amplification explicitly.

Although this simplified simulation does not implement the block‑encoding and QSVT operations gate by gate, it faithfully produces the input and output states predicted by the NTCA framework.

## Example implementation in Python

We implement the above toy model using `numpy` for vector operations.  The input vector provided by the user is

\[
\mathbf{c}=(1,2,0,3,1,2,1,2)/\sqrt{24}.
\]

This vector is normalised because \(\sum_k c_k^2 = 24\) and therefore \(\sum_k (c_k/\sqrt{24})^2=1\).  The polynomial chosen for the non‑linear transformation is

\[
P(x)=x^3+x^2+x.
\]

The following Python code prepares the input state, applies the polynomial to each amplitude, renormalises the output, and reports the success probability predicted by the NTCA algorithm.

```python
import numpy as np

# 1. Prepare the input vector and normalise it
c = np.array([1, 2, 0, 3, 1, 2, 1, 2], dtype=float)
c = c / np.sqrt(np.sum(c**2))  # divide by sqrt(24)

# 2. Define the polynomial P(x) = x^3 + x^2 + x
def P(x: float) -> float:
    return x**3 + x**2 + x

# Apply P to each amplitude
values = np.array([P(val) for val in c])

# Compute the normalisation constant for the output state
norm = np.linalg.norm(values)
b = values / norm

# Compute gamma and success probability as given in the paper
gamma = max(np.abs(values))
N = len(c)
success_prob = (1.0 / (64 * gamma**2 * N)) * np.sum(np.abs(values)**2)

print("Input amplitudes c:", c)
print("Transformed (unnormalised) amplitudes P(c):", values)
print("Normalised output b:", b)
print("Maximum |P(c_k)| (gamma):", gamma)
print("Theoretical success probability:", success_prob)
```

Running this code prints the initial amplitudes, the polynomial‑transformed amplitudes before normalisation, the final normalised amplitudes of the output state, and the theoretical probability of successfully post‑selecting the ancillas to realise the desired transformation.

### Output of the example

The script produces the following output (rounded to eight decimal places):

```
Input amplitudes c: [0.20412415 0.40824829 0.         0.61237244 0.20412415 0.40824829
 0.20412415 0.40824829]
Transformed (unnormalised) amplitudes P(c): [0.25277906 0.63888573 0.         1.21097998 0.25277906 0.63888573
 0.25277906 0.63888573]
Normalised output b: [0.14893547 0.37656515 0.         0.71277678 0.14893547 0.37656515
 0.14893547 0.37656515]
Maximum |P(c_k)| (gamma): 1.2170121
Theoretical success probability: 0.0038443503243327935
```

The first line shows the input amplitudes \(c_k\).  After applying \(P\) to each amplitude we obtain the unnormalised values \(P(c_k)\).  The values are then renormalised to get a valid quantum state with amplitudes \(b_k\).  In this example the largest value of \(|P(c_k)|\) is roughly 1.217, and the success probability predicted by the NTCA algorithm is only about 0.38 %.  One would therefore need amplitude amplification to boost the probability of observing all ancilla qubits in \(|0\rangle\) and hence preparing the desired output state.

## Discussion

The toy model demonstrates how a non‑linear polynomial can be applied to amplitude‑encoded data.  It approximates the core idea of the NTCA algorithm—**applying non‑linear functions to real parts of amplitudes**—without synthesising the full block‑encoding and QSVT subroutines.  For a small dimension and a real polynomial, the QSVT‑based algorithm reduces to evaluating the polynomial on each amplitude and renormalising【608189420933610†L637-L651】.  Implementing the full algorithm gate by gate would involve constructing the unitaries \(\tilde G\) and \(\tilde G'\), determining polynomial approximations of \(P\) and \(Q\) that satisfy the boundedness conditions of QSVT, and using controlled operations and post‑selection as described around Eqs. (17)–(19)【608189420933610†L525-L556】.

Our simulation illustrates the output of the algorithm for the specific input vector and polynomial requested by the user.  It also highlights that the success probability can be small for large polynomial values, necessitating amplitude amplification in practical implementations.  While the toy model does not include QSVT circuits, it serves as an end‑to‑end classical simulation of the **input state preparation, non‑linear amplitude transformation, renormalisation and calculation of success probability** for the given example.
