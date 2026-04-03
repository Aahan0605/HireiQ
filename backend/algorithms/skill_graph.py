"""
Graph + BFS — Skill Gap Analysis.

Finds missing skills and shortest learning path from current to target skills.
Uses directed graph where edges represent prerequisites.

Time: O(V + E) where V=skills, E=prerequisites
Space: O(V + E)
"""

from collections import defaultdict, deque


def build_skill_graph():
    """
    Build skill prerequisite graph (edges = prerequisites).
    Time: O(1), Space: O(V + E)
    """
    graph = defaultdict(list)

    # Skill prerequisites: skill -> [prerequisite_skills]
    graph["Python"] = []
    graph["Statistics"] = ["Python"]
    graph["ML"] = ["Python", "Statistics"]
    graph["Deep Learning"] = ["ML", "Linear Algebra"]
    graph["Linear Algebra"] = []
    graph["SQL"] = []
    graph["Data Engineering"] = ["Python", "SQL"]
    graph["Spark"] = ["Data Engineering", "SQL"]
    graph["Kubernetes"] = ["Docker"]
    graph["Docker"] = []

    return graph


def find_learning_path(current_skills, target_skills, graph):
    """
    BFS to find shortest path from current to missing target skills.

    Args:
        current_skills: List of skills candidate already has
        target_skills: List of skills needed for target job
        graph: Skill graph (defaultdict)

    Returns: Dict with missing_skills and learning_path
    Time: O(V + E), Space: O(V)
    """
    missing = set(target_skills) - set(current_skills)

    if not missing:
        return {"missing_skills": [], "learning_path": []}

    queue = deque()
    visited = set(current_skills)
    parent = {}

    # BFS from all current skills
    for skill in current_skills:
        queue.append(skill)

    while queue:
        skill = queue.popleft()

        # Find skills that have this skill as prerequisite
        for next_skill, prereqs in graph.items():
            if skill in prereqs and next_skill not in visited:
                visited.add(next_skill)
                parent[next_skill] = skill
                queue.append(next_skill)

    # Build learning path for first missing skill found
    path = []
    for target in missing:
        if target in visited:
            path = []
            curr = target
            while curr in parent:
                path.append(parent[curr])
                curr = parent[curr]
            path.reverse()
            path.append(target)
            break

    return {
        "missing_skills": list(missing),
        "learning_path": path,
    }


if __name__ == "__main__":
    graph = build_skill_graph()

    current = ["Python", "SQL"]
    target = ["ML", "Kubernetes"]

    result = find_learning_path(current, target, graph)

    print(f"Current Skills: {current}")
    print(f"Target Skills: {target}")
    print(f"Missing: {result['missing_skills']}")
    print(f"Learning Path: {result['learning_path']}")
