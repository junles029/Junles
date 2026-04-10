from __future__ import annotations

from typing import Dict, List, Tuple



def _escape(text: str) -> str:
    return text.replace('"', "'").replace('[', '(').replace(']', ')').strip()



def build_graph(title: str, summary: Dict[str, object]) -> Tuple[Dict[str, object], str]:
    nodes: List[Dict[str, str]] = []
    edges: List[Dict[str, str]] = []

    def add_node(node_id: str, label: str, kind: str) -> None:
        nodes.append({'id': node_id, 'label': label, 'kind': kind})

    def add_edge(source: str, target: str, relation: str) -> None:
        edges.append({'source': source, 'target': target, 'relation': relation})

    add_node('video', title, 'video')

    abstract = str(summary.get('executive_summary', '')).strip()
    if abstract:
        add_node('abstract', abstract, 'summary')
        add_edge('video', 'abstract', '概览')

    for idx, point in enumerate(summary.get('key_points', []), start=1):
        node_id = f'kp{idx}'
        add_node(node_id, str(point), 'key_point')
        add_edge('video', node_id, '要点')

    for idx, action in enumerate(summary.get('action_items', []), start=1):
        node_id = f'act{idx}'
        add_node(node_id, str(action), 'action_item')
        add_edge('video', node_id, '行动项')

    for idx, tag in enumerate(summary.get('tags', []), start=1):
        node_id = f'tag{idx}'
        add_node(node_id, str(tag), 'tag')
        add_edge('video', node_id, '标签')

    mermaid_lines = ['graph TD']
    for node in nodes:
        mermaid_lines.append(f'    {node["id"]}["{_escape(node["label"])}"]')
    for edge in edges:
        mermaid_lines.append(f'    {edge["source"]} -->|{_escape(edge["relation"])}| {edge["target"]}')

    graph = {'nodes': nodes, 'edges': edges}
    return graph, '\n'.join(mermaid_lines) + '\n'
