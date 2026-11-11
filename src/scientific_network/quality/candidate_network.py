"""Paired descriptive centrality diagnostics on identical common-node pivots."""

from hashlib import sha256

import networkx as nx

from scientific_network.analysis.analyze import _spearman, _top

METHOD = "identity-common-pivot-centrality-v1"


def paired_rankings(old,new,*,sample_nodes=256,seed=20261101):
    def projection(graph):
        net=nx.Graph()
        net.add_nodes_from(sorted(n.id for n in graph.nodes if n.label=="Researcher"))
        for e in sorted(graph.edges,key=lambda e:e.edge_id):
            if e.relation=="COAUTHORED_WITH":
                strength=e.properties["fractional_weight"]
                if strength<=0:
                    raise ValueError("centrality requires positive fractional weight")
                net.add_edge(e.source_id,e.target_id,strength=strength,distance=1/strength)
        return net
    a,b=projection(old),projection(new)
    common=set(a)&set(b)
    pivots=sorted(common,key=lambda n:(sha256(f"{seed}:{n}".encode()).hexdigest(),n))[:sample_nodes]
    def scores(net):
        between=nx.betweenness_centrality_subset(net,sources=pivots,targets=sorted(net),normalized=True,weight="distance") if pivots else {}
        # Scale subset sum for an approximate all-source score. This is a paired
        # sensitivity diagnostic conditional on common pivots,not an unbiased
        # sample of removed/new nodes or a reproduction of frozen v4 rankings.
        factor=len(net)/len(pivots) if pivots else 0
        return {"degree":dict(net.degree()),"strength":dict(net.degree(weight="strength")),
                "betweenness":{n:float(v)*factor for n,v in between.items()}}
    before,after=scores(a),scores(b)
    result={"method_version":METHOD,"seed":seed,"pivots":pivots,"pivots_count":len(pivots),
            "scope":"researcher collaboration; identical SHA256-ranked common-node pivots; all nodes as targets",
            "distance":"inverse positive fractional coauthorship strength",
            "limitation":"approximate paired diagnostic conditional on common pivots; not frozen-v4 rank reproduction or semantic accuracy",
            "rankings":{}}
    for name in before:
        top_a,top_b=_top(before[name],20),_top(after[name],20)
        ra={n:i+1 for i,(n,v) in enumerate(sorted(before[name].items(),key=lambda x:(-x[1],x[0])))}
        rb={n:i+1 for i,(n,v) in enumerate(sorted(after[name].items(),key=lambda x:(-x[1],x[0])))}
        selected={r["node_id"] for r in top_a+top_b}
        result["rankings"][name]={"before_top20":top_a,"after_top20":top_b,
            "top20_overlap":len({r["node_id"] for r in top_a}&{r["node_id"] for r in top_b}),
            "spearman_common_nodes":_spearman(before[name],after[name]),
            "selected_rank_changes":[{"node_id":n,"before":ra.get(n),"after":rb.get(n)} for n in sorted(selected)]}
    return result,{"before":before,"after":after}
