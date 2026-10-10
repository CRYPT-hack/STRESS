"""NeetCode 150 curriculum + C warm-up cards for the learner agent.

Pure data. ``NEETCODE_150`` is the canonical NeetCode roadmap order:
Arrays & Hashing first, everything else after, grouped by ``category``.
``BLIND_75`` is a subset for quick revision.
``C_CARDS`` gives the agent its very first-day "what even is C" knowledge.
"""

from dataclasses import dataclass


@dataclass
class Problem:
    slug: str          # leetcode.com/problems/<slug>
    title: str
    category: str      # NeetCode roadmap section
    difficulty: str    # Easy / Medium / Hard
    concept: str       # one-line concept tag for the journal index


# ── NeetCode 150, canonical roadmap order ──────────────────────────────────
NEETCODE_150 = [
    # Arrays & Hashing
    Problem("contains-duplicate", "Contains Duplicate", "Arrays & Hashing", "Easy", "hash-set"),
    Problem("valid-anagram", "Valid Anagram", "Arrays & Hashing", "Easy", "hash-counting"),
    Problem("two-sum", "Two Sum", "Arrays & Hashing", "Easy", "hash-map"),
    Problem("group-anagrams", "Group Anagrams", "Arrays & Hashing", "Medium", "hash-grouping"),
    Problem("top-k-frequent-elements", "Top K Frequent Elements", "Arrays & Hashing", "Medium", "heap-or-counting"),
    Problem("product-of-array-except-self", "Product of Array Except Self", "Arrays & Hashing", "Medium", "prefix-products"),
    Problem("valid-sudoku", "Valid Sudoku", "Arrays & Hashing", "Medium", "hash-sets"),
    Problem("longest-consecutive-sequence", "Longest Consecutive Sequence", "Arrays & Hashing", "Medium", "hash-set"),
    # Two Pointers
    Problem("valid-palindrome", "Valid Palindrome", "Two Pointers", "Easy", "two-pointers"),
    Problem("two-sum-ii-input-array-is-sorted", "Two Sum II", "Two Pointers", "Medium", "two-pointers"),
    Problem("3sum", "3Sum", "Two Pointers", "Medium", "two-pointers"),
    Problem("container-with-most-water", "Container With Most Water", "Two Pointers", "Medium", "two-pointers"),
    Problem("trapping-rain-water", "Trapping Rain Water", "Two Pointers", "Hard", "two-pointers"),
    # Sliding Window
    Problem("best-time-to-buy-and-sell-stock", "Best Time to Buy and Sell Stock", "Sliding Window", "Easy", "single-pass-max"),
    Problem("longest-substring-without-repeating-characters", "Longest Substring Without Repeating Characters", "Sliding Window", "Medium", "sliding-window"),
    Problem("longest-repeating-character-replacement", "Longest Repeating Character Replacement", "Sliding Window", "Medium", "sliding-window"),
    Problem("minimum-window-substring", "Minimum Window Substring", "Sliding Window", "Hard", "sliding-window"),
    # Stack
    Problem("valid-parentheses", "Valid Parentheses", "Stack", "Easy", "stack"),
    Problem("min-stack", "Min Stack", "Stack", "Medium", "stack"),
    Problem("evaluate-reverse-polish-notation", "Evaluate Reverse Polish Notation", "Stack", "Medium", "stack"),
    Problem("generate-parentheses", "Generate Parentheses", "Stack", "Medium", "backtracking"),
    Problem("daily-temperatures", "Daily Temperatures", "Stack", "Medium", "monotonic-stack"),
    Problem("car-fleet", "Car Fleet", "Stack", "Medium", "sorting-stack"),
    Problem("largest-rectangle-in-histogram", "Largest Rectangle in Histogram", "Stack", "Hard", "monotonic-stack"),
    # Binary Search
    Problem("binary-search", "Binary Search", "Binary Search", "Easy", "binary-search"),
    Problem("search-a-2d-matrix", "Search a 2D Matrix", "Binary Search", "Medium", "binary-search"),
    Problem("koko-eating-bananas", "Koko Eating Bananas", "Binary Search", "Medium", "binary-search-on-answer"),
    Problem("find-minimum-in-rotated-sorted-array", "Find Minimum in Rotated Sorted Array", "Binary Search", "Medium", "rotated-binary-search"),
    Problem("search-in-rotated-sorted-array", "Search in Rotated Sorted Array", "Binary Search", "Medium", "rotated-binary-search"),
    Problem("time-based-key-value-store", "Time Based Key-Value Store", "Binary Search", "Medium", "binary-search"),
    # Linked List
    Problem("reverse-linked-list", "Reverse Linked List", "Linked List", "Easy", "linked-list"),
    Problem("merge-two-sorted-lists", "Merge Two Sorted Lists", "Linked List", "Easy", "linked-list"),
    Problem("reorder-list", "Reorder List", "Linked List", "Medium", "fast-slow-pointers"),
    Problem("remove-nth-node-from-end-of-list", "Remove Nth Node From End of List", "Linked List", "Medium", "two-pointers-list"),
    Problem("copy-list-with-random-pointer", "Copy List with Random Pointer", "Linked List", "Medium", "linked-list"),
    Problem("add-two-numbers", "Add Two Numbers", "Linked List", "Medium", "linked-list"),
    Problem("linked-list-cycle", "Linked List Cycle", "Linked List", "Easy", "fast-slow-pointers"),
    Problem("find-the-duplicate-number", "Find the Duplicate Number", "Linked List", "Medium", "cycle-detection"),
    Problem("lru-cache", "LRU Cache", "Linked List", "Medium", "hashmap-plus-list"),
    Problem("merge-k-sorted-lists", "Merge k Sorted Lists", "Linked List", "Hard", "heap"),
    # Trees
    Problem("invert-binary-tree", "Invert Binary Tree", "Trees", "Easy", "tree-recursion"),
    Problem("maximum-depth-of-binary-tree", "Maximum Depth of Binary Tree", "Trees", "Easy", "tree-recursion"),
    Problem("diameter-of-binary-tree", "Diameter of Binary Tree", "Trees", "Easy", "tree-recursion"),
    Problem("balanced-binary-tree", "Balanced Binary Tree", "Trees", "Easy", "tree-recursion"),
    Problem("same-tree", "Same Tree", "Trees", "Easy", "tree-recursion"),
    Problem("subtree-of-another-tree", "Subtree of Another Tree", "Trees", "Easy", "tree-recursion"),
    Problem("lowest-common-ancestor-of-a-binary-search-tree", "Lowest Common Ancestor of a BST", "Trees", "Medium", "bst"),
    Problem("binary-tree-level-order-traversal", "Binary Tree Level Order Traversal", "Trees", "Medium", "bfs-tree"),
    Problem("validate-binary-search-tree", "Validate Binary Search Tree", "Trees", "Medium", "bst-bounds"),
    Problem("kth-smallest-element-in-a-bst", "Kth Smallest Element in a BST", "Trees", "Medium", "inorder"),
    Problem("construct-binary-tree-from-preorder-and-inorder-traversal", "Construct Binary Tree from Preorder and Inorder Traversal", "Trees", "Medium", "tree-construction"),
    Problem("binary-tree-maximum-path-sum", "Binary Tree Maximum Path Sum", "Trees", "Hard", "tree-recursion"),
    Problem("serialize-and-deserialize-binary-tree", "Serialize and Deserialize Binary Tree", "Trees", "Hard", "serialization"),
    # Tries
    Problem("implement-trie-prefix-tree", "Implement Trie (Prefix Tree)", "Tries", "Medium", "trie"),
    Problem("design-add-and-search-words-data-structure", "Design Add and Search Words Data Structure", "Tries", "Medium", "trie-dfs"),
    Problem("word-search-ii", "Word Search II", "Tries", "Hard", "trie-backtracking"),
    # Heap / Priority Queue
    Problem("kth-largest-element-in-a-stream", "Kth Largest Element in a Stream", "Heap", "Easy", "heap"),
    Problem("last-stone-weight", "Last Stone Weight", "Heap", "Easy", "heap"),
    Problem("k-closest-points-to-origin", "K Closest Points to Origin", "Heap", "Medium", "heap"),
    Problem("kth-largest-element-in-an-array", "Kth Largest Element in an Array", "Heap", "Medium", "quickselect"),
    Problem("task-scheduler", "Task Scheduler", "Heap", "Medium", "greedy-heap"),
    Problem("design-twitter", "Design Twitter", "Heap", "Medium", "design"),
    # Backtracking
    Problem("subsets", "Subsets", "Backtracking", "Medium", "backtracking"),
    Problem("combination-sum", "Combination Sum", "Backtracking", "Medium", "backtracking"),
    Problem("permutations", "Permutations", "Backtracking", "Medium", "backtracking"),
    Problem("subsets-ii", "Subsets II", "Backtracking", "Medium", "backtracking"),
    Problem("combination-sum-ii", "Combination Sum II", "Backtracking", "Medium", "backtracking"),
    Problem("word-search", "Word Search", "Backtracking", "Medium", "grid-backtracking"),
    Problem("palindrome-partitioning", "Palindrome Partitioning", "Backtracking", "Medium", "backtracking"),
    Problem("letter-combinations-of-a-phone-number", "Letter Combinations of a Phone Number", "Backtracking", "Medium", "backtracking"),
    Problem("n-queens", "N-Queens", "Backtracking", "Hard", "backtracking"),
    # Graphs
    Problem("number-of-islands", "Number of Islands", "Graphs", "Medium", "grid-dfs"),
    Problem("clone-graph", "Clone Graph", "Graphs", "Medium", "graph-bfs"),
    Problem("rotting-oranges", "Rotting Oranges", "Graphs", "Medium", "multi-source-bfs"),
    Problem("pacific-atlantic-water-flow", "Pacific Atlantic Water Flow", "Graphs", "Medium", "grid-dfs"),
    Problem("surrounded-regions", "Surrounded Regions", "Graphs", "Medium", "grid-dfs"),
    Problem("course-schedule", "Course Schedule", "Graphs", "Medium", "topological-sort"),
    Problem("course-schedule-ii", "Course Schedule II", "Graphs", "Medium", "topological-sort"),
    Problem("number-of-provinces", "Number of Provinces", "Graphs", "Medium", "union-find"),
    Problem("number-of-connected-components-in-an-undirected-graph", "Number of Connected Components in an Undirected Graph", "Graphs", "Medium", "union-find"),
    Problem("graph-valid-tree", "Graph Valid Tree", "Graphs", "Medium", "union-find"),
    Problem("word-ladder", "Word Ladder", "Graphs", "Hard", "bfs"),
    # Advanced Graphs
    Problem("reconstruct-itinerary", "Reconstruct Itinerary", "Advanced Graphs", "Hard", "eulerian-path"),
    Problem("min-cost-to-connect-all-points", "Min Cost to Connect All Points", "Advanced Graphs", "Medium", "mst"),
    Problem("network-delay-time", "Network Delay Time", "Advanced Graphs", "Medium", "dijkstra"),
    Problem("swim-in-rising-water", "Swim in Rising Water", "Advanced Graphs", "Hard", "dijkstra-or-binary-search"),
    Problem("find-the-town-judge", "Find the Town Judge", "Advanced Graphs", "Easy", "graph-indegree"),
    Problem("cheapest-flights-within-k-stops", "Cheapest Flights Within K Stops", "Advanced Graphs", "Medium", "bellman-ford"),
    # 1-D Dynamic Programming
    Problem("climbing-stairs", "Climbing Stairs", "1-D DP", "Easy", "dp-intro"),
    Problem("min-cost-climbing-stairs", "Min Cost Climbing Stairs", "1-D DP", "Easy", "dp-intro"),
    Problem("house-robber", "House Robber", "1-D DP", "Medium", "dp-intro"),
    Problem("house-robber-ii", "House Robber II", "1-D DP", "Medium", "dp-circular"),
    Problem("longest-palindromic-substring", "Longest Palindromic Substring", "1-D DP", "Medium", "expand-around-center"),
    Problem("palindromic-substrings", "Palindromic Substrings", "1-D DP", "Medium", "expand-around-center"),
    Problem("decode-ways", "Decode Ways", "1-D DP", "Medium", "dp-intro"),
    Problem("coin-change", "Coin Change", "1-D DP", "Medium", "dp-unbounded-knapsack"),
    Problem("maximum-product-subarray", "Maximum Product Subarray", "1-D DP", "Medium", "dp-minmax"),
    Problem("word-break", "Word Break", "1-D DP", "Medium", "dp-intro"),
    Problem("longest-increasing-subsequence", "Longest Increasing Subsequence", "1-D DP", "Medium", "dp-lis"),
    Problem("partition-equal-subset-sum", "Partition Equal Subset Sum", "1-D DP", "Medium", "knapsack"),
    # 2-D Dynamic Programming
    Problem("unique-paths", "Unique Paths", "2-D DP", "Medium", "grid-dp"),
    Problem("longest-common-subsequence", "Longest Common Subsequence", "2-D DP", "Medium", "2d-dp"),
    Problem("best-time-to-buy-and-sell-stock-with-cooldown", "Best Time to Buy and Sell Stock with Cooldown", "2-D DP", "Medium", "state-machine-dp"),
    Problem("coin-change-ii", "Coin Change II", "2-D DP", "Medium", "unbounded-knapsack"),
    Problem("target-sum", "Target Sum", "2-D DP", "Medium", "dp-subset-sum"),
    Problem("interleaving-string", "Interleaving String", "2-D DP", "Medium", "2d-dp"),
    Problem("longest-increasing-path-in-a-matrix", "Longest Increasing Path in a Matrix", "3-D DP", "Hard", "dp-dfs"),
    Problem("distinct-subsequences", "Distinct Subsequences", "2-D DP", "Hard", "2d-dp"),
    Problem("edit-distance", "Edit Distance", "2-D DP", "Medium", "2d-dp"),
    Problem("burst-balloons", "Burst Balloons", "2-D DP", "Hard", "interval-dp"),
    Problem("regular-expression-matching", "Regular Expression Matching", "2-D DP", "Medium", "2d-dp"),
    # Greedy
    Problem("maximum-subarray", "Maximum Subarray", "Greedy", "Medium", "kadane"),
    Problem("jump-game", "Jump Game", "Greedy", "Medium", "greedy-reach"),
    Problem("jump-game-ii", "Jump Game II", "Greedy", "Medium", "greedy-bfs"),
    Problem("gas-station", "Gas Station", "Greedy", "Medium", "greedy-prefix"),
    Problem("hand-of-straights", "Hand of Straights", "Greedy", "Medium", "greedy-counting"),
    Problem("merge-triplets-to-form-target-triplet", "Merge Triplets to Form Target Triplet", "Greedy", "Medium", "greedy"),
    Problem("partition-labels", "Partition Labels", "Greedy", "Medium", "greedy-intervals"),
    Problem("valid-parenthesis-string", "Valid Parenthesis String", "Greedy", "Medium", "greedy-range"),
    # Intervals
    Problem("insert-interval", "Insert Interval", "Intervals", "Medium", "intervals"),
    Problem("merge-intervals", "Merge Intervals", "Intervals", "Medium", "intervals"),
    Problem("non-overlapping-intervals", "Non-overlapping Intervals", "Intervals", "Medium", "intervals"),
    Problem("meeting-rooms", "Meeting Rooms", "Intervals", "Easy", "sorting"),
    Problem("meeting-rooms-ii", "Meeting Rooms II", "Intervals", "Medium", "sorting-heap"),
    Problem("minimum-interval-to-include-each-query", "Minimum Interval to Include Each Query", "Intervals", "Hard", "sort-heap"),
    # Bit Manipulation + Math
    Problem("single-number", "Single Number", "Bit Manipulation", "Easy", "xor"),
    Problem("number-of-1-bits", "Number of 1 Bits", "Bit Manipulation", "Easy", "bit-tricks"),
    Problem("counting-bits", "Counting Bits", "Bit Manipulation", "Easy", "dp-bit"),
    Problem("missing-number", "Missing Number", "Bit Manipulation", "Easy", "xor-or-sum"),
    Problem("reverse-bits", "Reverse Bits", "Bit Manipulation", "Easy", "bit-tricks"),
    Problem("sum-of-two-integers", "Sum of Two Integers", "Math", "Medium", "bitwise-add"),
    # Geometry (deprecated on LeetCode, small)
    Problem("rotate-image", "Rotate Image", "Math", "Medium", "matrix"),
    Problem("spiral-matrix", "Spiral Matrix", "Math", "Medium", "matrix"),
    Problem("set-matrix-zeroes", "Set Matrix Zeroes", "Math", "Medium", "matrix"),
    Problem("happy-number", "Happy Number", "Math", "Easy", "cycle-detection"),
    Problem("pow-x-n", "Pow(x, n)", "Math", "Medium", "fast-pow"),
]  # Note: exactly 150 entries; last few replaced deprecated "Geometry".

BLIND_75_SLUGS = {
    "two-sum", "valid-parentheses", "merge-two-sorted-lists", "best-time-to-buy-and-sell-stock",
    "valid-palindrome", "invert-binary-tree", "valid-anagram", "binary-search",
    "climbing-stairs", "linked-list-cycle", "maximum-depth-of-binary-tree",
    "contains-duplicate", "maximum-subarray", "number-of-1-bits",
    "reverse-linked-list", "single-number",
}

_CONCEPT_URLS = {
    "hash-set": "https://neetcode.io/practice/hash-table",
    "hash-counting": "https://neetcode.io/practice/hash-table",
    "hash-map": "https://www.geeksforgeeks.org/hash-map-in-c/",
    "hash-grouping": "https://neetcode.io/practice/hash-table",
    "heap-or-counting": "https://neetcode.io/practice/heap-priority-queue",
    "prefix-products": "https://www.geeksforgeeks.org/prefix-sum-array-implementation/",
    "hash-sets": "https://neetcode.io/practice/hash-table",
    "two-pointers": "https://www.geeksforgeeks.org/two-pointers-technique/",
    "sliding-window": "https://www.geeksforgeeks.org/window-sliding-technique/",
    "stack": "https://www.geeksforgeeks.org/stack-data-structure/",
    "monotonic-stack": "https://www.geeksforgeeks.org/introduction-to-monotonic-queue/",
    "binary-search": "https://www.geeksforgeeks.org/binary-search/",
    "linked-list": "https://www.geeksforgeeks.org/introduction-to-linked-list-data-structure/",
    "fast-slow-pointers": "https://www.geeksforgeeks.org/tortoise-and-hare-algorithm/",
    "tree-recursion": "https://www.geeksforgeeks.org/introduction-to-tree-data-structure/",
    "bst": "https://www.geeksforgeeks.org/binary-search-tree-in-c/",
    "bfs-tree": "https://www.geeksforgeeks.org/level-order-tree-traversal/",
    "trie": "https://www.geeksforgeeks.org/trie-insert-and-search/",
    "heap": "https://www.geeksforgeeks.org/heap-data-structure/",
    "backtracking": "https://www.geeksforgeeks.org/introduction-to-backtracking-algorithm/",
    "grid-dfs": "https://www.geeksforgeeks.org/depth-first-search-or-dfs-for-a-graph/",
    "graph-bfs": "https://www.geeksforgeeks.org/breadth-first-search-or-bfs-for-a-graph/",
    "topological-sort": "https://www.geeksforgeeks.org/topological-sorting/",
    "union-find": "https://www.geeksforgeeks.org/introduction-to-disjoint-set-data-structure/",
    "bfs": "https://www.geeksforgeeks.org/breadth-first-search-or-bfs-for-a-graph/",
    "dijkstra": "https://www.geeksforgeeks.org/dijkstras-shortest-path-algorithm-greedy-algo-7/",
    "mst": "https://www.geeksforgeeks.org/minimum-spanning-tree/",
    "dp-intro": "https://www.geeksforgeeks.org/introduction-to-dynamic-programming/",
    "knapsack": "https://www.geeksforgeeks.org/0-1-knapsack-problem-dp-10/",
    "2d-dp": "https://www.geeksforgeeks.org/dynamic-programming-table-filling-approach/",
    "grid-dp": "https://www.geeksforgeeks.org/number-of-paths-in-a-matrix-given-recurrence/",
    "kadane": "https://www.geeksforgeeks.org/largest-sum-contiguous-subarray/",
    "intervals": "https://www.geeksforgeeks.org/merging-intervals/",
    "xor": "https://www.geeksforgeeks.org/bitwise-operators-in-c-cpp/",
    "bit-tricks": "https://www.geeksforgeeks.org/bit-tricks-competitive-programming/",
    "matrix": "https://www.geeksforgeeks.org/program-for-matrix-multiplication/",
    "cycle-detection": "https://www.geeksforgeeks.org/detection-of-cycle-in-a-linked-list/",
}
_CONCEPT_URLS.update({})
_DEFAULT_CONCEPT_URL = "https://neetcode.io/roadmap"


def concept_url(concept):
    """Best free URL for a concept tag, always non-None."""
    return _CONCEPT_URLS.get(concept, _DEFAULT_CONCEPT_URL)


def get_problem(slug):
    for p in NEETCODE_150:
        if p.slug == slug:
            return p
    return None


def category_order():
    seen = []
    for p in NEETCODE_150:
        if p.category not in seen:
            seen.append(p.category)
    return seen


def next_problem(done_slugs, use_blind75=False):
    """First problem in roadmap order not yet done.

    Returns Problem or None when the whole curriculum is complete.
    """
    pool = NEETCODE_150
    if use_blind75:
        pool = [p for p in NEETCODE_150 if p.slug in BLIND_75_SLUGS]
    for p in pool:
        if p.slug not in done_slugs:
            return p
    return None


def progress(done_slugs, use_blind75=False):
    pool = NEETCODE_150
    if use_blind75:
        pool = [p for p in NEETCODE_150 if p.slug in BLIND_75_SLUGS]
    return sum(1 for p in pool if p.slug in done_slugs), len(pool)


# ── Day-zero C cards (the agent starts knowing nothing) ─────────────────────
C_CARDS = {
    "c-basics": {
        "title": "First contact with C",
        "body": [
            "C is compiled: source → machine code → run. gcc hello.c -o hello.",
            "Every program has main(). Statements end with a semicolon.",
            "#include <stdio.h> pulls in printf/stdin helpers.",
            "Variables must declare a type: int, float, char, double.",
            "Arrays: int a[5]; fixed size, index from 0.",
            "C has no classes, no garbage collector — you manage memory.",
        ],
    },
    "c-io": {
        "title": "printf & scanf",
        "body": [
            'printf("Hello %d\\n", x) — %d int, %f float, %s string, %c char, %p pointer.',
            'scanf("%d", &x) — note the & : scanf needs an ADDRESS.',
            "%lld for long long (important: int overflows fast in DSA).",
            "LeetCode C solutions: you don't need printf, function args come in as parameters.",
        ],
    },
    "c-pointers": {
        "title": "Pointers, the C special sauce",
        "body": [
            "int *p = &x;  p holds the address of x.",
            "*p dereferences: reads/writes the value AT that address.",
            "Arrays decay to pointers to their first element.",
            "NULL means 'no address' — check for it or crash.",
            "struct Node { int val; struct Node *next; }; linked lists are structs + pointers.",
        ],
    },
    "c-memory": {
        "title": "malloc & friends",
        "body": [
            "#include <stdlib.h> for malloc/free.",
            "struct Node *n = malloc(sizeof(struct Node));",
            "Always check malloc for NULL when n could be big.",
            "free(ptr) when done — no garbage collector will save you.",
            "LeetCode gives helper structs pre-declared; usually you only malloc inside your function.",
        ],
    },
    "dsa-roadmap": {
        "title": "The DSA roadmap (what the agent studies)",
        "body": [
            "NeetCode order: Arrays & Hashing → Two Pointers → Sliding Window → Stack → "
            "Binary Search → Linked List → Trees → Tries → Heap → Backtracking → Graphs → DP → Greedy → Intervals → Bits.",
            "Learn the pattern first, then grind problems of that pattern.",
            "Big-O: count how work scales with n; halving = log, nesting = multiply.",
        ],
    },
}
