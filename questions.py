"""Question bank and study cards for STRESS.

Pure data, no logic. To add your own questions, append ``mcq(...)`` or
``openq(...)`` calls to the bottom of the BANK section. Every question
needs a short explanation -- future-you reads them after failing.
"""

from dataclasses import dataclass, field
from typing import List, Optional

SUBJECTS = ["ML", "DSA", "LA"]
SUBJECT_NAMES = {
    "ML": "Machine Learning",
    "DSA": "Data Structures & Algorithms",
    "LA": "Linear Algebra",
}


@dataclass
class Question:
    subject: str
    q: str
    options: Optional[List[str]]          # None => open (typed) answer
    answer: int                            # index into options, -1 when open
    open_answers: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)  # all must appear in reply
    explanation: str = ""
    difficulty: int = 2                    # 1..3
    qid: str = ""


BANK: List[Question] = []


def mcq(subject, q, options, correct, explanation="", difficulty=2):
    BANK.append(Question(subject=subject, q=q, options=options, answer=correct,
                         explanation=explanation, difficulty=difficulty))


def openq(subject, q, answers, keywords=None, explanation="", difficulty=2):
    BANK.append(Question(subject=subject, q=q, options=None, answer=-1,
                         open_answers=answers, keywords=keywords or [],
                         explanation=explanation, difficulty=difficulty))


# ─────────────────────────────── Machine Learning ────────────────────────────

mcq("ML",
    "Training error is low but validation error is high. What is happening?",
    ["Underfitting", "Overfitting", "Perfect generalization", "Vanishing gradients"],
    1,
    "The model memorized training-set noise. Fix with regularization, more data, "
    "dropout or early stopping.",
    1)

mcq("ML",
    "Which regularization term drives some weights to exactly zero, "
    "effectively performing feature selection?",
    ["L1 (Lasso)", "L2 (Ridge)", "Dropout", "Batch normalization"],
    0,
    "L1 penalizes |w|, whose gradient is constant, pushing small weights to 0.",
    1)

mcq("ML",
    "L2 (Ridge) regularization primarily...",
    ["Drives weights to exactly zero",
     "Shrinks all weights smoothly toward zero",
     "Doubles the weights",
     "Only affects the bias term"],
    1,
    "L2 penalizes w squared, so weights shrink smoothly but rarely hit exactly 0.",
    1)

mcq("ML",
    "A learning rate that is too large causes...",
    ["Smooth, guaranteed convergence",
     "Oscillation or divergence",
     "Automatic feature selection",
     "Underfitting"],
    1,
    "Too-large steps overshoot the minimum; the loss bounces or explodes.",
    1)

mcq("ML",
    "Which update rule describes gradient descent?",
    ["w ← w − η·∇L(w)", "w ← w + η·∇L(w)", "w ← η·∇L(w)", "w ← w − ∇L(w)/η²"],
    0,
    "Step against the gradient (downhill), scaled by the learning rate η.",
    1)

mcq("ML",
    "Precision is defined as:",
    ["TP / (TP + FP)", "TP / (TP + FN)", "TN / (TN + FP)", "(TP + TN) / all"],
    0,
    "Precision: of everything flagged positive, how much was truly positive.",
    1)

mcq("ML",
    "Recall is defined as:",
    ["TP / (TP + FP)", "TP / (TP + FN)", "TN / (TN + FP)", "(TP + TN) / all"],
    1,
    "Recall: of everything truly positive, how much did we catch?",
    1)

mcq("ML",
    "The F1 score is the ___ of precision and recall.",
    ["Arithmetic mean", "Harmonic mean", "Geometric mean", "Maximum"],
    1,
    "Harmonic mean punishes imbalance: F1 = 2PR/(P+R).",
    1)

mcq("ML",
    "What is the purpose of a validation set?",
    ["Tuning hyperparameters / model selection without touching test data",
     "Increasing training data size",
     "Making the model train faster",
     "Storing labels"],
    0,
    "Validation drives choices (lr, layers, ...); test stays untouched until the end.",
    1)

mcq("ML",
    "K-fold cross-validation mainly...",
    ["Reduces the variance of the performance estimate",
     "Eliminates the need for a test set",
     "Guarantees no overfitting",
     "Reduces model bias to zero"],
    0,
    "Averaging over k splits makes the estimate less dependent on one lucky split.",
    2)

mcq("ML",
    "k-NN is called a 'lazy learner' because...",
    ["It stores data and defers all computation until query time",
     "It trains very slowly",
     "It needs no distance metric",
     "It requires a GPU"],
    0,
    "No training phase; prediction scans stored points using a distance metric.",
    1)

mcq("ML",
    "Naive Bayes assumes features are...",
    ["Conditionally independent given the class",
     "Mutually exclusive",
     "Always Gaussian",
     "Uncorrelated with the label"],
    0,
    "'Naive' = P(x1..xn | y) factorizes into P(xi | y).",
    1)

mcq("ML",
    "A support vector machine finds...",
    ["A maximum-margin separating hyperplane",
     "The cluster centroids",
     "A sorted array of support vectors",
     "A probability density estimate"],
    0,
    "The decision boundary that maximizes the margin to the closest points.",
    1)

mcq("ML",
    "The kernel trick is used to...",
    ["Compute inner products in a high-dimensional feature space without "
     "explicitly mapping into it",
     "Add noise to improve generalization",
     "Sort support vectors by alpha",
     "Replace gradients with Hessians"],
    0,
    "K(x, z) = <φ(x), φ(z)> — the margin math only needs inner products.",
    2)

mcq("ML",
    "Random forests reduce variance by...",
    ["Bagging many de-correlated decision trees and averaging",
     "Boosting the residuals of a single tree",
     "Pruning one very deep tree",
     "Stacking neural networks"],
    0,
    "Averaging noisy-but-unbiased trees cancels their individual errors.",
    1)

mcq("ML",
    "ReLU is defined as:",
    ["max(0, x)", "1/(1+e^(−x))", "tanh(x)", "ln(1+e^x)"],
    0,
    "Cheap, non-saturating for x>0; dead for x<0.",
    1)

mcq("ML",
    "Softmax converts a score vector into...",
    ["A probability distribution that sums to 1",
     "A zero-mean vector",
     "A sorted vector",
     "A unit-norm vector"],
    0,
    "exp(xi)/Σexp(xj) — positive components summing to one.",
    1)

mcq("ML",
    "Which loss pairs naturally with softmax classification?",
    ["Cross-entropy", "Mean squared error", "Hinge loss on probabilities",
     "Cosine similarity"],
    0,
    "Cross-entropy's gradient is (p − y): clean and stable with softmax.",
    1)

mcq("ML",
    "Backpropagation computes gradients using...",
    ["The chain rule applied backwards through the network",
     "Matrix inversion of the Hessian",
     "Monte Carlo sampling",
     "Numerical differentiation with ε = 1"],
    0,
    "Reuse of intermediate results makes it cost roughly one forward pass.",
    1)

mcq("ML",
    "High bias in a model typically manifests as...",
    ["Underfitting: high error on both train and test",
     "Overfitting: low train error, high test error",
     "Low error everywhere",
     "High variance only"],
    0,
    "Bias = systematic error from too simple a model; variance = sensitivity to data.",
    1)

mcq("ML",
    "Why scale features before gradient descent or k-NN?",
    ["So features with large ranges don't dominate distances and gradients",
     "Because scaling adds new features",
     "Because it removes outliers",
     "Because decision trees require it"],
    0,
    "One huge-range feature dwarfs the others in distance metrics and slows GD.",
    1)

mcq("ML",
    "Dropout during training...",
    ["Randomly zeroes activations each forward pass",
     "Randomly removes labels",
     "Doubles the learning rate",
     "Normalizes batch statistics"],
    0,
    "Forces redundant representations — an ensemble effect at inference time.",
    1)

mcq("ML",
    "Stochastic gradient descent differs from batch gradient descent because it...",
    ["Uses small random subsets per update — noisier but far cheaper",
     "Uses the full dataset per update",
     "Uses second-order derivatives",
     "Has no learning rate"],
    0,
    "Mini-batch noise also helps escape shallow local minima.",
    1)

mcq("ML",
    "In self-attention, the attention weights are softmax of:",
    ["QKᵀ/√d", "Q + K + V", "softmax(QV)Kᵀ", "QᵀK + V"],
    0,
    "Queries against keys, scaled by √d to keep softmax gradients healthy.",
    3)

mcq("ML",
    "PCA projects data onto...",
    ["The eigenvectors of the covariance matrix with the largest eigenvalues",
     "Random orthogonal directions",
     "The class means",
     "The last principal component"],
    0,
    "Top eigenvectors = directions of maximum variance (linear algebra pays off).",
    2)

mcq("ML",
    "Which is NOT a remedy for overfitting?",
    ["Adding more training data", "Dropout / regularization",
     "Training longer on the same data", "Data augmentation"],
    2,
    "More epochs on the same data usually deepens overfitting.",
    1)

openq("ML",
      "Write the formula for precision using TP and FP.",
      ["tp/(tp+fp)"],
      keywords=["tp", "fp"],
      explanation="precision = TP / (TP + FP).",
      difficulty=1)

openq("ML",
      "One word: a model performs well on training data but poorly on unseen data.",
      ["overfitting"],
      keywords=["overfit"],
      explanation="Overfitting — memorized noise, learned little.",
      difficulty=1)

# ───────────────────── Data Structures & Algorithms ──────────────────────────

mcq("DSA",
    "The precondition for binary search on an array is that it is:",
    ["Sorted", "Made of unique elements", "All positive", "A heap"],
    0,
    "Each comparison halves the search space — only meaningful if order is known.",
    1)

mcq("DSA",
    "Average-case lookup in a hash map is:",
    ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
    0,
    "Hash to a bucket, then (usually) O(1) work inside it.",
    1)

mcq("DSA",
    "Worst-case lookup in a hash map with heavy collisions is:",
    ["O(n)", "O(1)", "O(log n)", "O(n²)"],
    0,
    "Everything in one bucket degenerates into a linear scan.",
    2)

mcq("DSA",
    "Inserting at the head of a singly linked list costs:",
    ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
    0,
    "Rewire one pointer: new.next = head; head = new.",
    1)

mcq("DSA",
    "Accessing the i-th element of a linked list costs:",
    ["O(n)", "O(1)", "O(log n)", "O(√n)"],
    0,
    "No random access — walk from the head.",
    1)

mcq("DSA",
    "Which structure is FIFO?",
    ["Queue", "Stack", "Heap", "Trie"],
    0,
    "First in, first out — enqueue at the tail, dequeue at the head.",
    1)

mcq("DSA",
    "BFS naturally uses which auxiliary structure?",
    ["A queue", "A stack", "A priority queue", "A hash map"],
    0,
    "The queue preserves the layer-by-layer frontier.",
    1)

mcq("DSA",
    "DFS may be implemented with:",
    ["A stack or recursion", "A queue only", "A heap only",
     "A doubly linked list only"],
    0,
    "Recursion implicitly uses the call stack.",
    1)

mcq("DSA",
    "Shortest paths (fewest edges) in an unweighted graph are found by:",
    ["BFS", "DFS", "Dijkstra's algorithm", "Kruskal's algorithm"],
    0,
    "All equal edge weights => BFS explores by increasing distance.",
    1)

mcq("DSA",
    "Quicksort's worst-case time is:",
    ["O(n²)", "O(n log n)", "O(n)", "O(log n)"],
    0,
    "Terrible pivots (sorted input, first element) split 0 : n−1 every time.",
    1)

mcq("DSA",
    "Merge sort's worst-case time and extra space are:",
    ["O(n log n) time, O(n) extra space", "O(n²) time, O(1) space",
     "O(n log n) time, O(1) space", "O(n) time, O(n) space"],
    0,
    "Guaranteed halving + linear merge; needs the auxiliary array.",
    1)

mcq("DSA",
    "Extracting the max from a binary max-heap costs:",
    ["O(log n)", "O(1)", "O(n)", "O(n log n)"],
    0,
    "Swap root with last leaf, pop, then sift the new root down the height.",
    1)

mcq("DSA",
    "Peeking at the max of a binary max-heap costs:",
    ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
    0,
    "The max sits at the root.",
    1)

mcq("DSA",
    "In-order traversal of a binary search tree yields:",
    ["Sorted order", "Level order", "Reverse-sorted order", "Heap order"],
    0,
    "left subtree < node < right subtree, visited in exactly that order.",
    1)

mcq("DSA",
    "Lookup in a balanced BST (AVL, red-black) costs:",
    ["O(log n)", "O(1)", "O(n)", "O(n log n)"],
    0,
    "Balance keeps the height logarithmic.",
    1)

mcq("DSA",
    "The space cost of a graph adjacency matrix is:",
    ["O(V²)", "O(V+E)", "O(E)", "O(V)"],
    0,
    "A V×V cell for every possible edge, present or not.",
    1)

mcq("DSA",
    "The space cost of an adjacency list is:",
    ["O(V+E)", "O(V²)", "O(V)", "O(E²)"],
    0,
    "One bucket per vertex plus one entry per actual edge.",
    1)

mcq("DSA",
    "The time complexity of DFS over a graph stored as adjacency lists is:",
    ["O(V+E)", "O(V²)", "O(E log V)", "O(V)"],
    0,
    "Each vertex entered once, each edge followed once (twice if undirected).",
    1)

mcq("DSA",
    "The two properties a problem must have for dynamic programming are:",
    ["Overlapping subproblems and optimal substructure",
     "Greedy choice property and exchange argument",
     "Sorted input and hashing",
     "Recursion and labels"],
    0,
    "Reuse solutions to repeated subproblems; build optima from subproblem optima.",
    2)

mcq("DSA",
    "Memoization is...",
    ["Caching results of subproblems during top-down recursion",
     "Building a table bottom-up",
     "Sorting subproblems by cost",
     "Dividing the problem without overlap"],
    0,
    "Same recursion, but each subproblem is solved once.",
    1)

mcq("DSA",
    "Detecting a cycle in a linked list using O(1) extra space:",
    ["Floyd's tortoise-and-hare two pointers",
     "Hash set of visited nodes",
     "Sorting the list",
     "Reversing the list"],
    0,
    "Fast pointer laps the slow one iff a cycle exists.",
    2)

mcq("DSA",
    "Dijkstra's algorithm requires:",
    ["Non-negative edge weights", "A directed acyclic graph",
     "An undirected graph", "Distinct edge weights"],
    0,
    "Negative edges break the 'settled means final' invariant.",
    2)

mcq("DSA",
    "Searching a word of length L in a trie costs:",
    ["O(L)", "O(L log n)", "O(1)", "O(n·L)"],
    0,
    "One hop per character, independent of how many words are stored.",
    2)

mcq("DSA",
    "The amortized cost of appending to a dynamic (resizable) array is:",
    ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
    0,
    "Rare O(n) resizes average out over many cheap appends.",
    2)

mcq("DSA",
    "Deleting a node whose pointer you already hold in a doubly linked list costs:",
    ["O(1)", "O(n)", "O(log n)", "O(n log n)"],
    0,
    "prev and next pointers are right there — rewire three links.",
    1)

mcq("DSA",
    "Greedy algorithms...",
    ["Make the locally optimal choice at each step — no general global guarantee",
     "Always find the global optimum",
     "Require memoization",
     "Only work on trees"],
    0,
    "Optimal only with a proven exchange argument (e.g. Huffman, interval scheduling).",
    2)

mcq("DSA",
    "Which of these sorting algorithms is stable?",
    ["Merge sort", "Quick sort", "Heap sort", "Selection sort"],
    0,
    "Stable = equal keys keep their relative order; merge never swaps equals.",
    2)

openq("DSA",
      "In Big-O, what is the average-case time complexity of binary search?",
      ["ologn", "logn"],
      explanation="O(log n) — the search space halves each step.",
      difficulty=1)

openq("DSA",
      "In Big-O, what is the worst-case time complexity of quicksort?",
      ["on^2", "n^2"],
      explanation="O(n²) — when pivots split 0 : n−1 repeatedly.",
      difficulty=1)

# ─────────────────────────────── Linear Algebra ──────────────────────────────

mcq("LA",
    "If A is m×n and B is n×p, then AB has shape:",
    ["m×p", "n×n", "p×m", "Undefined unless m = p"],
    0,
    "Inner dimensions must match (n = n) and cancel; outer ones survive.",
    1)

mcq("LA",
    "Matrix multiplication is generally...",
    ["Not commutative: AB ≠ BA", "Commutative: AB = BA always",
     "Only defined for diagonal matrices", "Only defined for symmetric matrices"],
    0,
    "Order matters — direction of the linear maps matters.",
    1)

mcq("LA",
    "(AB)ᵀ equals:",
    ["BᵀAᵀ", "AᵀBᵀ", "AB", "(BA)ᵀ"],
    0,
    "Transpose reverses the order — a classic trap.",
    2)

mcq("LA",
    "A·Iₙ equals:",
    ["A", "I", "A²", "0"],
    0,
    "The identity is the multiplicative neutral element.",
    1)

mcq("LA",
    "A square matrix is invertible if and only if:",
    ["det(A) ≠ 0", "det(A) = 0", "trace(A) > 0", "A is symmetric"],
    0,
    "Nonzero determinant = full rank = no collapsed dimensions.",
    1)

mcq("LA",
    "The determinant of [[a, b], [c, d]] is:",
    ["ad − bc", "ad + bc", "ab − cd", "ac − bd"],
    0,
    "Main diagonal product minus anti-diagonal product.",
    1)

mcq("LA",
    "A 'singular' matrix is one that...",
    ["Has determinant 0 and no inverse", "Is symmetric",
     "Is diagonal", "Has full rank"],
    0,
    "Singular = crushes some direction to zero = not invertible.",
    1)

mcq("LA",
    "The eigenvalue equation is:",
    ["Av = λv", "Av = λvᵀ", "vA = λI", "A = λv²"],
    0,
    "An eigenvector only gets scaled, not rotated, by A.",
    1)

mcq("LA",
    "The trace of a matrix is:",
    ["The sum of the diagonal entries", "The sum of all entries",
     "The determinant", "The largest entry"],
    0,
    "Also the sum of eigenvalues (with multiplicity).",
    1)

mcq("LA",
    "The rank of a matrix is...",
    ["The number of linearly independent columns",
     "The number of rows",
     "The number of nonzero entries",
     "The size of the largest entry"],
    0,
    "= dimension of the column space = dimension of the row space.",
    1)

mcq("LA",
    "Two vectors are orthogonal if and only if their dot product is:",
    ["0", "1", "−1", "The product of their norms"],
    0,
    "cos 90° = 0 kills the geometric formula a·b = ‖a‖‖b‖cos θ.",
    1)

mcq("LA",
    "The Euclidean norm ‖(x, y)‖ equals:",
    ["√(x² + y²)", "x + y", "|x| + |y|", "xy"],
    0,
    "Pythagoras; |x|+|y| is the taxicab norm instead.",
    1)

mcq("LA",
    "A symmetric matrix satisfies:",
    ["A = Aᵀ", "A = −Aᵀ", "A² = I", "AAᵀ = 0"],
    0,
    "Mirror image across the main diagonal.",
    1)

mcq("LA",
    "The span of a set of vectors is...",
    ["The set of all their linear combinations",
     "The length of the longest vector",
     "The angle between the vectors",
     "The number of vectors"],
    0,
    "All points reachable as c₁v₁ + c₂v₂ + ...",
    1)

mcq("LA",
    "A basis of a vector space is a set that is...",
    ["Linearly independent and spanning",
     "Maximal in size only",
     "Orthogonal only",
     "Counted by the trace"],
    0,
    "Every vector = exactly one combination of basis elements.",
    1)

mcq("LA",
    "Geometrically, a·b equals:",
    ["‖a‖‖b‖cos θ", "‖a‖‖b‖sin θ", "‖a‖ + ‖b‖", "The area of the parallelogram"],
    0,
    "Projection of one onto the other, scaled by length.",
    1)

mcq("LA",
    "The columns of a square matrix are linearly dependent iff:",
    ["det(A) = 0", "det(A) = 1", "trace(A) = 0", "rank(A) = n"],
    0,
    "Dependency means a direction collapses — zero determinant.",
    2)

mcq("LA",
    "The cross product a × b...",
    ["Returns a vector orthogonal to both inputs (3-D)",
     "Returns a scalar",
     "Works only for 2-D vectors",
     "Equals the dot product"],
    0,
    "Its magnitude is the parallelogram area; right-hand rule gives direction.",
    2)

mcq("LA",
    "Diagonalizing A = PDP⁻¹ requires...",
    ["A full set of linearly independent eigenvectors",
     "A symmetric matrix only",
     "det(A) = 0",
     "A triangular matrix"],
    0,
    "Columns of P are eigenvectors; defective matrices can't be diagonalized.",
    3)

mcq("LA",
    "A real symmetric matrix has eigenvalues that are...",
    ["All real", "All imaginary", "All zero", "Complex conjugate pairs"],
    0,
    "Symmetry forces λ = λ̄ — one reason it's everyone's favorite matrix.",
    2)

mcq("LA",
    "An orthogonal matrix Q satisfies:",
    ["QᵀQ = I", "Q = Qᵀ", "Q² = Q", "det(Q) = 0"],
    0,
    "Columns are orthonormal; the transpose is the inverse.",
    2)

mcq("LA",
    "Multiplication by an orthogonal matrix preserves:",
    ["Lengths (and angles)", "Only orientation", "The trace", "The determinant = 0"],
    0,
    "A rigid rotation/reflection: ‖Qx‖ = ‖x‖.",
    2)

mcq("LA",
    "A symmetric matrix A is positive definite when...",
    ["xᵀAx > 0 for every nonzero x (equivalently: all eigenvalues positive)",
     "Every entry of A is positive",
     "det(A) > 0 alone",
     "A is strictly upper triangular"],
    0,
    "Entry positivity is neither necessary nor sufficient; the quadratic form decides.",
    3)

mcq("LA",
    "det(AB) equals:",
    ["det(A)·det(B)", "det(A) + det(B)", "det(A) − det(B)", "1"],
    0,
    "Determinants multiply — so det(A⁻¹) = 1/det(A).",
    1)

mcq("LA",
    "The rank–nullity theorem for an m×n matrix A says:",
    ["rank(A) + nullity(A) = n", "rank(A) + nullity(A) = m",
     "rank(A) · nullity(A) = n", "rank(A) + nullity(A) = 0"],
    0,
    "Columns split between independent ones and free ones: n total.",
    2)

mcq("LA",
    "If λ is an eigenvalue of A, then A − 5I has eigenvalue:",
    ["λ − 5", "λ + 5", "5λ", "λ/5"],
    0,
    "(A − 5I)v = Av − 5v = (λ − 5)v — shifting the matrix shifts the spectrum.",
    2)

mcq("LA",
    "A is 3×3 with eigenvalues 2, 3, 5. det(A) = ?",
    ["30", "10", "2", "0"],
    0,
    "Determinant = product of eigenvalues.",
    2)

openq("LA",
      "Compute det([[3, 4], [2, 5]]).",
      ["7"],
      explanation="3·5 − 4·2 = 15 − 8 = 7.",
      difficulty=1)

openq("LA",
      "What is the dot product of (1, 2, 3) and (4, 5, 6)?",
      ["32"],
      explanation="1·4 + 2·5 + 3·6 = 4 + 10 + 18 = 32.",
      difficulty=1)

openq("LA",
      "What is the rank of the 4×4 identity matrix? (a number)",
      ["4"],
      explanation="Four independent columns — full rank.",
      difficulty=1)

# Stable ids used by the daily "no repeats" tracker.
for _i, _q in enumerate(BANK):
    _q.qid = f"{_q.subject}-{_i:03d}"


# ─────────────────────────────── Study cards ─────────────────────────────────

CARDS = {
    "gradient-descent": {
        "title": "Gradient Descent",
        "body": [
            "L(w) measures how wrong the model is on data.",
            "∇L points uphill — step the other way: w ← w − η·∇L.",
            "η too small = slow; too large = oscillation/divergence.",
            "Batch GD uses all data, SGD one sample, mini-batch the compromise.",
            "Feature scaling keeps the loss bowl round so GD converges fast.",
        ],
    },
    "bias-variance": {
        "title": "Bias vs Variance",
        "body": [
            "Bias: systematic error from too simple a model (underfitting).",
            "Variance: sensitivity to the particular training set (overfitting).",
            "High train error + high test error → bias problem.",
            "Low train error + high test error → variance problem.",
            "Fixes for variance: more data, regularization, dropout, early stopping.",
            "Fixes for bias: bigger model, better features, less regularization.",
        ],
    },
    "regularization": {
        "title": "Regularization",
        "body": [
            "Penalize model complexity so it can't memorize noise.",
            "L1 (Lasso): penalizes |w| → sparsity, feature selection.",
            "L2 (Ridge): penalizes w² → smooth shrinkage, small weights.",
            "Dropout: randomly zero activations during training.",
            "Early stopping: halt when validation loss starts rising.",
        ],
    },
    "metrics": {
        "title": "Classification Metrics",
        "body": [
            "Precision = TP/(TP+FP): flagged items that were right.",
            "Recall = TP/(TP+FN): true items that were caught.",
            "F1 = 2PR/(P+R): harmonic mean, punishes imbalance.",
            "Accuracy lies under class imbalance (99% negatives → predict 'no').",
            "ROC-AUC: ranking quality across thresholds.",
        ],
    },
    "attention": {
        "title": "Self-Attention (Transformers)",
        "body": [
            "Every token emits a Query, Key and Value vector.",
            "Attention(Q,K,V) = softmax(QKᵀ/√d)·V.",
            "QKᵀ scores how much each token cares about each other token.",
            "√d scaling keeps softmax gradients healthy.",
            "Multi-head: several attention patterns in parallel, then merged.",
        ],
    },
    "big-o": {
        "title": "Big-O Survival Kit",
        "body": [
            "Drop constants and lower-order terms: 3n² + n → O(n²).",
            "Hash map get/put: O(1) average, O(n) worst (collisions).",
            "Sorting comparison-based: O(n log n) floor (merge, heap, good quick).",
            "Balanced BST / heap ops: O(log n).",
            "Graph with adjacency lists: O(V+E) for BFS/DFS.",
            "Nested loops over n → multiply: O(n²). Halving → log.",
        ],
    },
    "bfs-dfs": {
        "title": "BFS & DFS",
        "body": [
            "BFS uses a queue; explores layer by layer.",
            "DFS uses a stack (or recursion); dives deep, backtracks.",
            "Unweighted shortest path → BFS. Weighted → Dijkstra (needs w ≥ 0).",
            "Cycle detection: DFS + colors (visiting/visited), or tortoise-hare on lists.",
            "Topological sort = DFS finish order reversed (DAGs).",
        ],
    },
    "dynamic-programming": {
        "title": "Dynamic Programming",
        "body": [
            "Needs: overlapping subproblems + optimal substructure.",
            "Top-down = recursion + memoization.",
            "Bottom-up = table, fill in dependency order.",
            "State design is 90% of the problem: what does dp[i][j] mean?",
            "Classics: knapsack, LIS, edit distance, coin change, grid paths.",
            "Space often compressible to one row (or two variables).",
        ],
    },
    "hash-tables": {
        "title": "Hash Tables",
        "body": [
            "key → hash → bucket index; store (key, value) in the bucket.",
            "Average O(1) get/put; worst O(n) when hashes collide badly.",
            "Collisions: chaining vs open addressing (linear/quadratic probing).",
            "Load factor triggers resize & rehash (amortized O(1) insert).",
            "The 'two-sum in O(n)' trick everyone keeps reusing.",
        ],
    },
    "two-pointers": {
        "title": "Two Pointers & Sliding Window",
        "body": [
            "Sorted array pair-sum: left/right ends, move inward. O(n).",
            "Fast/slow pointers: linked-list cycles, dedup in place.",
            "Sliding window: expand right, shrink left while invalid.",
            "Works when the invariant is monotone — 'add right never hurts'.",
            "Classic results: longest substring without repeats, min window.",
        ],
    },
    "matrix-multiplication": {
        "title": "Matrix Multiplication",
        "body": [
            "(m×n)·(n×p) = m×p — inner dimensions must match.",
            "Entry (i,j) = row i of A dotted with column j of B.",
            "AB ≠ BA in general — order encodes map composition.",
            "(AB)ᵀ = BᵀAᵀ — order flips.",
            "Row i of AB = row i of A times B (linear combination of rows).",
        ],
    },
    "eigenvalues": {
        "title": "Eigenvalues & Eigenvectors",
        "body": [
            "Av = λv: v keeps its direction, only scaled by λ.",
            "Find λ from det(A − λI) = 0, then v from (A − λI)v = 0.",
            "det(A) = product of λ's; trace(A) = sum of λ's.",
            "Diagonalization A = PDP⁻¹ needs n independent eigenvectors.",
            "Symmetric matrices: real λ's, orthonormal eigenbasis.",
            "PCA = projecting onto top eigenvectors of the covariance matrix.",
        ],
    },
    "orthogonality": {
        "title": "Orthogonality",
        "body": [
            "u ⊥ v ⇔ u·v = 0.",
            "Orthonormal basis: directions at right angles, length 1.",
            "Orthogonal matrix Q: QᵀQ = I, so Q⁻¹ = Qᵀ; preserves lengths.",
            "Projection onto unit vector u: (x·u)u.",
            "Least squares: residual must be orthogonal to the column space.",
        ],
    },
    "vector-spaces": {
        "title": "Vector Spaces, Span, Basis, Rank",
        "body": [
            "Span: everything reachable by linear combinations.",
            "Basis: independent + spanning; size = dimension.",
            "Column space of A: all possible Ax outputs.",
            "Null space: all x with Ax = 0.",
            "rank + nullity = number of columns.",
            "Rank = independent columns = independent rows (yes, equal).",
        ],
    },
}
