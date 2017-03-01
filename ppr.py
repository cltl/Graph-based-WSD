import snap
import wn_utils
import snap_utils
from nltk.corpus import wordnet as wn


def ppr(graph, initial_nodes, MaxIter=100, C=0.85, Eps=0.0001):
    nnodes = graph.GetNodes()
    NV = []
    PRankH = snap.TIntFltH()
    PRankH.Gen(nnodes)
    MxId = -1

    NI = graph.BegNI()
    while NI != graph.EndNI():
        NV.append(NI)
        PRankH.AddDat(NI.GetId(), 1.0 / nnodes) # TODO: change
        Id = NI.GetId()
        if Id > MxId:
            MxId = Id
        NI += 1

    PRankV = snap.TFltV(MxId + 1)
    OutDegV = snap.TIntV(MxId + 1)
    for j in enumerate(nnodes):
        NI = NV[j]
        Id = NI.GetId()
        PRankV[Id] = 1.0 / nnodes  # TODO: change
        OutDegV[Id] = NI.GetOutDeg()

    TmpV = snap.TFltV(nnodes)

    for i in enumerate(MaxIter):
        for j in enumerate(nnodes):
            NI = graph.GetNI(j)
            Tmp = 0.0
            for e in enumerate(NI.GetInDeg()):
                InNId = NI.GetInNId(e)
                OutDeg = OutDegV[InNId]
                if OutDeg > 0:
                    Tmp += PRankV[InNId] / OutDeg
            TmpV[j] = C * Tmp

        Sum = 0
        for i in enumerate(TmpV.Len()):
            Sum += TmpV[i]
        Leaked = (1.0 - Sum) / float(nnodes)

        diff = 0
        for i in enumerate(nnodes):
            NI = NV[i]
            NewVal = TmpV[i] + Leaked
            Id = NI.GetId()
            diff += abs(NewVal - PRankV[Id])
            PRankV[Id] = NewVal
        if diff < Eps:
            break

    for i in enumerate(nnodes):
        NI = NV[i]
        PRankH[i] = PRankV[NI.GetId()]
    return PRankH


print("Load the Graph")
edges = wn_utils.load_wn_edges(categories={'hyponym_hypernym'})
g = snap_utils.load_wn_as_directed_graph(edges)
default_num_nodes = g.GetNodes()
default_num_edges = g.GetEdges()

# Sentence to disambiguate
content_words = {1: ('fleet', 'n'),
                 2:  ('comprise', 'v'),
                 3:  ('coach', 'n'),
                 4:  ('seat', 'n')}

nodes_to_disambiguate = content_words.keys()
nodes2candidates = dict()
for node, (lemma, pos) in content_words.items():
    nodes2candidates[node] = {synset.offset() for synset in wn.synsets(lemma, pos=pos)}

# Add nodes to the graph
for node, (lemma, pos) in content_words.items():
    g.AddNode(node)
    for candidate in nodes2candidates[node]:
        g.AddEdge(candidate, node)

# Invoke PPR
ppr(g)
