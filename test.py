import ppr
from nltk.corpus import wordnet as wn

print("Loading the graph ...")
g = ppr.Graph('cache.edges')
print("Done. Nodes:", g.GetNNodes(), "Edges:", g.GetNEdges())

# Disambiguating some words
content_words = {1 : ('fleet', 'n'),
                 2:  ('comprise', 'v'),
                 3:  ('coach', 'n'),
                 4:  ('seat', 'n')}
nodes_to_disambiguate = content_words.keys()
nodes2candidates = dict()
for node, (lemma, pos) in content_words.items():
    nodes2candidates[node] = {synset.offset() for synset in wn.synsets(lemma, pos=pos)}

# Add the nodes and edges to the graph
print("Adding the nodes and edges to the graph ...")
added_nodes = []
for node, (lemma, pos) in content_words.items():
    added_nodes.append(node)
    g.AddNode(node)
    for candidate in nodes2candidates[node]:
        g.AddEdge(node, candidate)
print("Done. Nodes:", g.GetNNodes(), "Edges:", g.GetNEdges())

res = g.PPR(added_nodes, C=0.85, eps=0.0001, maxiter=30)
res.sort(key=lambda x: x[1], reverse=True)
for node, candidates in nodes2candidates.items():
    print("Node", node, "?")
    cands = set()
    for c in candidates:
        cands.add(c)
    for r in res:
        if r[0] in cands:
            print("   Candidate", r[0], "%0.7f" % r[1])
