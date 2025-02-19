import argparse
import re
import json

from flask import Flask, render_template, request
from HoT import HoT
from module_lib import *

app = Flask(__name__)
hg = HoT()


func_map = {
    "stats": lambda x, y: display_stats(x, y),
    "chart": lambda x, y: display_chart(x, y)
}

config = {}

def load_analysis_config(config_file):
    global config
    with open(config_file) as f:
        config = json.load(f)

def node_title(hg: HoT, node_id: int):
    name = hg.get_node_name(node_id)
    if name:
        return name
    else:
        return node_id
    
@app.context_processor
def inject_config_pages():
    return {'config_pages': config.get("pages", [])}

@app.route('/node/<int:node_id>')
def display_node(node_id):
    node_text = hg.get_text(node_id)
    hyperedges = [(hg_id, hg.get_text(hg_id)) for hg_id in hg.get_containing_hyperedges(node_id)]

    hyperedge_links = {}
    for hyperedge_id, hyperedge_text in hyperedges:
        phrase = hyperedge_text.strip()
        if phrase and phrase.lower() not in hyperedge_links: 
            hyperedge_links[hyperedge_text.lower()] = f'<a href="/hyperedge/{hyperedge_id}">{hyperedge_text.lower()}</a>'


    sorted_phrases = sorted(hyperedge_links.keys(), key=len, reverse=True)

    # Replace occurrences of words with hyperlinks
    def replace_match(match):
        word = match.group(0)
        return hyperedge_links.get(word.lower(), word)  # Replace only if in mapping

    pattern = re.compile(r'\b(' + '|'.join(map(re.escape, sorted_phrases)) + r')\b', re.IGNORECASE)
    linked_text = pattern.sub(replace_match, node_text)
    
    return render_template('node.html', node_display_text=node_title(hg, node_id), node_text=linked_text, hyperedges=hyperedges)

@app.route('/hyperedge/<int:hyperedge_id>')
def display_hyperedge(hyperedge_id):
    node_ids = hg.get_hyperedge_members(hyperedge_id)
    hyperedge_text = hg.get_text(hyperedge_id)

    nodes = [(node_id, node_title(hg, node_id)) for node_id in node_ids]
    
    return render_template('hyperedge.html', hyperedge_text=hyperedge_text, nodes=nodes)

@app.route('/', methods=['GET', 'POST'])
def index():
    app.logger.info(f"number of edges: {len(hg.get_hyperedges())}")
    search_query = request.args.get('search', '').strip()
    all_nodes = hg.get_nodes()
    filtered_nodes = []

    if search_query:
        for node_id in all_nodes:
            if search_query.lower() in hg.get_text(node_id).lower():
                filtered_nodes.append((node_id, hg.get_text(node_id)))
    else:
        filtered_nodes = [(node_id, node_title(hg, node_id), hg.get_text(node_id)) for node_id in all_nodes]

    return render_template('index.html', nodes=filtered_nodes, search_query=search_query)

def register_routes(app: Flask):
    for page in config.get("pages", []):
        route = page["route"]
        template = page["template"]
        func = page["func"]

        def view_func(template=template):
            return func_map[func](hg, template)

        app.add_url_rule(route, endpoint=route, view_func=view_func)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("filepath", type=str, help="Path to the file")

    args = parser.parse_args()

    load_analysis_config(args.filepath)

    hg.from_xml(config['data_route'])

    with app.app_context():
        register_routes(app)

    app.run(debug=True)

