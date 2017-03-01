import snap
import utils


def load_wn_as_directed_graph(edges):
    """
    load WordNet as directed graph (snap.PUNGraph in snappy)
    
    :param set edges: set of edges (offset, offset)
    
    :rtype: snap.PNGraph
    :return: wordnet loaded as directed graph using snap
    """
    with open('cache.edges', 'w') as outfile:
        for source_offset, target_offset in edges:
            outfile.write('%s\t%s\n' % (source_offset, target_offset))
    
    g = snap.LoadEdgeList(snap.PNGraph, 'input/cache.edges', 0, 1, '\t')
    
    return g


def distr_mfs_pr_rank(edges,
                      lemmapos2mfs_offset,
                      the_candidates):
    """
    compute distribution of what the rank of the mfs sense is
    according to pagerank
    
    :param set edges: output wn_utils.load_wn_edges
    :param dict lemmapos2mfs_offset: output wn_utils.get_lemmapos2mfs_offset
    :param dict the_candidates: output wn_utils.get_candidates
    
    :rtype: tuple
    :return: (all pagerank ranks of the mfs, num_nodes)
    """
    # load graph
    g = load_wn_as_undirected_graph(edges)
    num_nodes = g.GetNodes()
    
    # compute pagerank
    PRankH = snap.TIntFltH()
    snap.GetPageRank(g, PRankH)
    offset2pagerank = dict()
    for item in PRankH:
        offset2pagerank[item] = PRankH[item]
    
    # compute mfs_pr_rank
    mfs_pr_rank_values = []
    for lemma, pos in the_candidates:

        mfs_offset = lemmapos2mfs_offset[(lemma, pos)]
        candidates = the_candidates[(lemma, pos)]

        mfs_pr_rank = utils.compute_mfs_pr_rank(mfs_offset, candidates,
                                                offset2pagerank)
        mfs_pr_rank_values.append(mfs_pr_rank)
    
    return mfs_pr_rank_values, num_nodes