"""Free-resource reader for the learner agent.

The agent never free-surfs: it consults a hard-coded registry of free,
legitimate learning sites, picks pages relevant to its current problem,
and extracts the readable text for the brain to digest. No scraping of
premium content, no random web crawling.
"""

import re

LEETCODE_URL = "https://leetcode.com/problems/{slug}/description/"
NEETCODE_URL = "https://neetcode.io/problems/{slug}"
Translatef = "https://wu-english.translate.goog/?_x_tr_sl=auto&_x_tr_tl=en"
GOOGLE_TRANSLATE = "https://translate.google.com"


# Curated free-resource registry: generic pages per topic.
FREE_PAGES = {
    "arrays": [
        "https://www.geeksforgeeks.org/introduction-to-arrays/",
        "https://www.freecodecamp.org/news/data-structures-101-arrays-a-guide-for-beginners-8f3ff6d5b1e/",
    ],
    "pointers": [
        "https://www.geeksforgeeks.org/pointers-in-c-and-cpp/",
        "https://beej.us/guide/bgc/html/split/pointers.html",
    ],
    "linked-list": [
        "https://www.geeksforgeeks.org/introduction-to-linked-list-data-structure/",
        "https://www.freecodecamp.org/news/how-linked-lists-work/",
    ],
    "hash": [
        "https://www.geeksforgeeks.org/hashing-in-data-structure/",
        "https://www.freecodecamp.org/news/hash-tables-explained/",
    ],
    "two-pointers": [
        "https://www.geeksforgeeks.org/two-pointers-technique/",
    ],
    "sliding-window": [
        "https://www.geeksforgeeks.org/window-sliding-technique/",
    ],
    "stack": [
        "https://www.geeksforgeeks.org/stack-data-structure/",
    ],
    "binary-search": [
        "https://www.geeksforgeeks.org/binary-search/",
    ],
    "trees": [
        "https://www.geeksforgeeks.org/introduction-to-tree-data-structure/",
        "https://www.geeksforgeeks.org/binary-search-tree-in-c/",
    ],
    "tries": [
        "https://www.geeksforgeeks.org/trie-insert-and-search/",
    ],
    "heap": [
        "https://www.geeksforgeeks.org/heap-data-structure/",
    ],
    "backtracking": [
        "https://www.geeksforgeeks.org/introduction-to-backtracking-algorithm/",
        "https://algodaily.com/lessons/backtracking-algorithms",
    ],
    "graphs": [
        "https://www.geeksforgeeks.org/introduction-and-basic-terminology-of-graph/",
        "https://www.geeksforgeeks.org/breadth-first-search-or-bfs-for-a-graph/",
        "https://www.geeksforgeeks.org/depth-first-search-or-dfs-for-a-graph/",
    ],
    "dp": [
        "https://www.geeksforgeeks.org/introduction-to-dynamic-programming/",
        "https://www.freecodecamp.org/news/an-introduction-to-dynamic-programming-89cd6b3b4b1/",
    ],
    "greedy": [
        "https://www.geeksforgeeks.org/greedy-algorithms/",
    ],
    "intervals": [
        "https://www.geeksforgeeks.org/merging-intervals/",
    ],
    "bit-manipulation": [
        "https://www.geeksforgeeks.org/bitwise-operators-in-c-cpp/",
    ],
    "big-o": [
        "https://www.freecodecamp.org/news/big-o-notation-explained-free-course/",
    ],
    "c-language": [
        "https://www.geeksforgeeks.org/c-programming-language-tutorial/",
        "https://beej.us/guide/bgc/html/split/index.html",
        "https://en.cppreference.com/w/c",
    ],
}

CATEGORIES_TO_KEYS = {
    "Arrays & Hashing": ("hash", "arrays", "big-o"),
    "Two Pointers": ("two-pointers", "arrays"),
    "Sliding Window": ("sliding-window", "arrays"),
    "Stack": ("stack",),
    "Binary Search": ("binary-search",),
    "Linked List": ("linked-list", "pointers"),
    "Trees": ("trees",),
    "Tries": ("tries", "trees"),
    "Heap": ("heap",),
    "Backtracking": ("backtracking",),
    "Graphs": ("graphs",),
    "Advanced Graphs": ("graphs",),
    "1-D DP": ("dp",),
    "2-D DP": ("dp",),
    "Greedy": ("greedy",),
    "Intervals": ("intervals",),
    "Bit Manipulation": ("bit-manipulation",),
    "Math": ("arrays",),
}

# The same key mapped from the "concept" tag on curriculum problems.
CONCEPT_KEYS = {
    "hash-set": "hash", "hash-counting": "hash", "hash-map": "hash",
    "hash-grouping": "hash", "heap-or-counting": "heap", "hash-sets": "hash",
    "prefix-products": "arrays",
    "two-pointers": "two-pointers", "single-pass-max": "arrays",
    "sliding-window": "sliding-window",
    "stack": "stack", "monotonic-stack": "stack", "backtracking": "backtracking",
    "sorting-stack": "stack", "sort-heap": "heap",
    "binary-search": "binary-search", "binary-search-on-answer": "binary-search",
    "rotated-binary-search": "binary-search",
    "linked-list": "linked-list", "fast-slow-pointers": "linked-list",
    "two-pointers-list": "linked-list", "cycle-detection": "linked-list",
    "hashmap-plus-list": "linked-list", "heap": "heap", "quickselect": "arrays",
    "greedy-heap": "heap", "design": "hash",
    "tree-recursion": "trees", "bst": "trees", "bst-bounds": "trees",
    "inorder": "trees", "tree-construction": "trees",
    "bfs-tree": "trees", "serialization": "trees",
    "trie": "tries", "trie-dfs": "tries", "trie-backtracking": "tries",
    "grid-backtracking": "backtracking",
    "grid-dfs": "graphs", "graph-bfs": "graphs", "multi-source-bfs": "graphs",
    "topological-sort": "graphs", "union-find": "graphs", "bfs": "graphs",
    "eulerian-path": "graphs", "mst": "graphs", "dijkstra": "graphs",
    "dijkstra-or-binary-search": "graphs", "graph-indegree": "graphs",
    "bellman-ford": "graphs", "topological-sort-2": "graphs",
    "dp-intro": "dp", "dp-circular": "dp", "expand-around-center": "dp",
    "dp-unbounded-knapsack": "dp", "dp-minmax": "dp", "dp-lis": "dp",
    "knapsack": "dp", "grid-dp": "dp", "2d-dp": "dp",
    "state-machine-dp": "dp", "unbounded-knapsack": "dp", "dp-subset-sum": "dp",
    "dp-dfs": "dp", "interval-dp": "dp",
    "kadane": "greedy", "greedy-reach": "greedy", "greedy-bfs": "greedy",
    "greedy-prefix": "greedy", "greedy-counting": "greedy", "greedy": "greedy",
    "greedy-intervals": "greedy", "greedy-range": "greedy",
    "intervals": "intervals", "sorting": "arrays", "sorting-heap": "heap",
    "xor": "bit-manipulation", "bit-tricks": "bit-manipulation", "dp-bit": "dp",
    "xor-or-sum": "bit-manipulation", "bitwise-add": "bit-manipulation",
    "matrix": "arrays", "fast-pow": "arrays", "dp-lis-2": "dp",
}


def pages_for(problem):
    """Curated URLs relevant to `problem` (category + concept)."""
    keys = list(CATEGORIES_TO_KEYS.get(problem.category, ()))
    ck = CONCEPT_KEYS.get(problem.concept)
    if ck and ck not in keys:
        keys.insert(0, ck)
    urls = []
    for k in keys:
        for u in FREE_PAGES.get(k, []):
            if u not in urls:
                urls.append(u)
    return urls[:4]  # don't drown the little brain


def readable_text(html):
    """Very small, dependency-free HTML → text.

    Keeps <p>, <li>, headings; strips scripts/styles/nav noise. Good enough
    for GfG/freeCodeCamp article pages whose main content is plain paragraphs.
    """
    if not html:
        return ""
    # drop script/style blocks wholesale
    html = re.sub(r"(?is)<(script|style|svg|head|footer|nav)[^>]*>.*?</\1>", " ", html)
    # block-ish elements become newlines
    html = re.sub(r"(?i)</?(p|li|h[1-6]|pre|div|table|tr)[^>]*>", "\n", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    entities = {
        "&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"',
        "&#39;": "'", "&nbsp;": " ", "&rsquo;": "'", "&mdash;": "—",
    }
    for k, v in entities.items():
        text = text.replace(k, v)
    lines = []
    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if len(line) >= 15:  # skip menu crumbs / tiny fragments
            lines.append(line)
    # de-noise: GfG and friends repeat the title in every paragraph sometimes;
    # keep at most the first 400 lines.
    return "\n".join(lines[:400])


def url_for_slug(slug, neetcode=False):
    if neetcode:
        return NEETCODE_URL.format(slug=slug)
    return LEETCODE_URL.format(slug=slug)
