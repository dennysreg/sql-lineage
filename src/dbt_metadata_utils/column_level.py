"""Utils to get column-level lineage graph of SQL query; WIP."""
import json
import random
from hashlib import md5
from typing import Dict, List, Optional, Tuple, Union

import networkx as nx

from matplotlib import pyplot as plt


def find_col(
    query: Dict, col_name: str
) -> Optional[Tuple[Dict, Union[str, List[Union[str, Dict]]]]]:
    """Get matching colum from query

    Arguments:
        query: moz-sql-parser query with 'select' key and 'from' key
        col_name: col we want to get lineage info from

    Returns:
        lineage info of column.
    """
    final_select = query["select"]
    if type(final_select) == list:
        matching_cols = [
            col for col in query["select"] if col.get("name", col["value"]) == col_name
        ]
        if len(matching_cols):
            return (matching_cols[0], query["from"])
    elif type(final_select) == dict:
        # handle '*'
        if "*" in str(final_select):
            return ({"value": col_name}, query["from"])
    return None


def slice_ctes(query: Dict, cte_name: str):
    return {w["name"]: w["value"] for w in query["with"]}.get(cte_name)


class LineagePoint:
    def __init__(self, x, y, display_name=None):
        self.x: Dict = x
        self.y: Union[str, Dict, List[Union[str, Dict]]] = y
        self.display_name = display_name

    @property
    def col_name(self):
        # if there is a rename, get the renamed value
        return self.x.get("name", self.x["value"])

    @property
    def ancestor_col_name(self):
        if type(self.x["value"]) == str:
            # not an aggregate
            # print('~'*31)
            # print(self.x["value"])
            # print('~'*31)
            return self.x["value"]
        else:
            # print('/'*31)
            # print(self.x['value'].values())
            token = next(iter(self.x["value"].values()))
            # if there is an aggregation, get the ancestor column
            # the key could be anything
            # TODO: handle complex aggregations, e.g. for idf_entities.idf
            # if isinstance(token, list):
            #     tokens = flatten(token)
            #     tok = {md5(json.dumps(k).encode("utf-8")).hexdigest(): v for k,v in tokens.items()}
            #     # print('tokens')
            #     # print(tokens,tok)
            #     return next(iter(tok.values()))
            # print('\\'*31)
            return token

    @staticmethod
    def get_table_name(tbl):
        if type(tbl) == list:
            # more than 1 table
            return md5(json.dumps(tbl).encode("utf-8")).hexdigest()
        elif type(tbl) == str:
            return tbl
        elif type(tbl) == dict:
            # TODO: check when JOIN + rename
            # TODO: check for left, inner and right JOIN
            return tbl.get("join") or tbl.get("value")

    @property
    def table_name(self):
        return self.display_name or self.get_table_name(self.y)

    def __repr__(self):
        # Important: ancestor_col_name instead of col_name because col_name might be a rename
        return f"{self.table_name}.{self.ancestor_col_name}"

from functools import reduce


def _reducer(items, key, val, pref):
    if isinstance(val, dict):
        return {**items, **flatten(val, pref = f'{pref}{key}')}
    elif isinstance(val, list):        
        return {**items, **flatten(dict(enumerate(val)), pref = f'{pref}{key}')}
    elif isinstance(val, str):        
        return {**items, f'{pref}{key}': val}
    else:
        return {**items}


def flatten(d, pref=''):
    if isinstance(d, list):
        d = dict(enumerate(d))
    return(
        reduce(
            lambda new_d, kv: _reducer(new_d, *kv, pref), 
            d.items(), 
            {}
        )
    )


def process_lineage_point(lp: LineagePoint, query: Dict) -> Optional[List[LineagePoint]]:
    # Handle cases where the column is computed with custom logic
    if type(lp.ancestor_col_name) != str:
        print('AQUIII!')
        #return None
        cols = flatten(lp.ancestor_col_name).values()
        new_lp = [ LineagePoint(*({'value': col}, query['from'])) for col in cols]
        return new_lp
        

    if type(lp.y) == list:
        # flatten joins by considering each part of join as potential provenance for column
        new_lps = [LineagePoint(lp.x, tbl) for tbl in lp.y]
        return new_lps
    else:
        # TODO: use name_for_upstream instead of name_for_downstream, e.g. for kg_coaches.coach_id
        q = slice_ctes(query, lp.table_name)
        if not q:
            # no CTE with the table_name was found
            return []
        found_col = find_col(query=q, col_name=lp.ancestor_col_name)
        if not found_col:
            #  CTE isn't related to column
            # remove dead branch
            return None
        new_lp = LineagePoint(*found_col)
        return [new_lp]


def draw_multi_graph(G: nx.Graph):
    return nx.drawing.nx_pydot.to_pydot(G)



def draw_graph(G: nx.Graph) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(15, 7))
    

    if len(G):
        pos = nx.spring_layout(G)
        
        # nodes
        nx.draw_networkx_nodes(G, pos,
                               node_size=100,
                               node_color="orange")

        #edges        
        nx.draw_networkx_edges(
            G, pos,
            width=1,alpha=0.9,edge_color='black',
            arrowsize=20,
            ax=ax)
        #edge-labels
        formatted_edge_labels = {(u, v): d for u, v, d in G.edges(data=True)}
        nx.draw_networkx_edge_labels(G,pos,edge_labels=formatted_edge_labels,font_color='red')

        # labels
        nodenames = {n:'\n'.join(n.split('.')) for n in G.nodes()}

        nx.draw_networkx_labels(
            G,pos,font_size=8,font_family='sans-serif'
            ,verticalalignment='bottom'
            ,labels=nodenames
        )
    plt.axis('off')
    plt.tight_layout()
    plt.subplots_adjust(left=0.1)

    return fig
