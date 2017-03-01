


def compute_mfs_pr_rank(mfs_offset, candidates,
                        offset2pagerank):
    """
    compute rank of mfs according to pagerank
    
    :param int mfs_offset: the offset of the mfs
    :param set candidates: set of offsets
    :param dict offset2pagerank: dict mapping offset -> pagerank
    
    :rtype: int
    :return: rank of mfs according to pagerank
    """
    mfs_pr_rank = 'rest'

    info = []
    for offset in candidates:
        if offset in offset2pagerank:
            pr_value = offset2pagerank[offset]
        else:
            pr_value = 0
        info.append((pr_value, offset))
        
    for pr_rank, (pr_value, offset) in enumerate(sorted(info, reverse=True), 1):
        if mfs_offset == offset:
            mfs_pr_rank = pr_rank
    
    return mfs_pr_rank