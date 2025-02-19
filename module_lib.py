from HoT import HoT
from flask import Flask, render_template
import json

def _node_title(hg: HoT, node_id: int):
    name = hg.get_node_name(node_id)
    if name:
        return name
    else:
        return node_id

def display_stats(g: HoT, temp):
    return render_template(temp, num_nodes=len(g.get_nodes()), num_hyperedges=len(g.get_hyperedges()))

def display_chart(g: HoT, temp):
    hyperedges = [
            {"id": he_id, "name": g.get_text(he_id), "size": len(g.get_hyperedge_members(he_id))}
            for he_id in g.get_hyperedges()
        ]
    top_hyperedges = sorted(hyperedges, key=lambda x: x["size"], reverse=True)[:50]
    j_he = json.dumps(top_hyperedges)
    return render_template(temp, hyperedges=j_he)