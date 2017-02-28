import pandas
from nltk.corpus import wordnet as wn
from collections import defaultdict


def get_lemmapos2mfs_offset():
    """
    static function to load dict mapping
    (lemma, pos) -> offset mfs (senserank 1)
    
    :rtype: dict
    :return: (lemma, pos) -> offset mfs (senserank 1)
    """
    lemmapos2mfs_offset = dict()
    
    for synset in wn.all_synsets():
        label = synset.name()
        lemma, pos, senserank = label.rsplit('.', 2)
        
        if pos == 's':
            pos = 'a'
        senserank_int = int(senserank)

        if senserank_int == 1:
            lemmapos2mfs_offset[(lemma, pos)] = synset.offset()

    return lemmapos2mfs_offset

def get_candidates(lemmapos2mfs_offset, ignore_monosemous=True):
    """
    given output get_lemmapos2mfs_offset
    create dictionary mapping 
    (lemma, pos) -> set of candidates (offsets)
    
    :param bool ignore_monosemous: if True, ignore monosemous 
    lemma, pos combinations
    
    :rtype: dict
    :return: mapping (lemma, pos) -> set of candidates (offsets)
    """
    lemmapos2candidates = dict()
    
    for (lemma, pos), offset in lemmapos2mfs_offset.items():
        synsets = wn.synsets(lemma, pos=pos)
        if len(synsets) >= 2:
            candidates = [synset.offset() for synset in synsets]
            lemmapos2candidates[(lemma, pos)] = candidates
    
    return lemmapos2candidates
        

def example_synset_of_relation(attribute):
    """
    print example of one synset for which the attribute is not empty
    
    :param str attribute: any attribute of a wn synset can be used:
    
    'instance_hypernyms', 'hyponyms', 'instance_hyponyms'
    'member_holonyms', 'substance_holonyms', 'part_holonyms', 
    'member_meronyms', 'substance_meronyms', 'part_meronyms',
    'attributes', 'entailments', 'causes', 'also_sees', 'verb_groups', 'similar_tos'
    """
    for synset in wn.all_synsets():
        results = getattr(synset, attribute)()
        if results:
            print
            print(synset, synset.definition())
            print(attribute)
            for result in results:
                print(result, result.definition())
            break


def load_wn_edges(categories, 
                  wanted_pos=None):
    """
    load wordnet edges
    
    :param set categories: 'hyponym_hypernym' and/or 'meronym_holonym'
    and/or 'others'
    :param set|None wanted_pos: if None, all pos will be taken into account,
    else only the pos in the set (n, v, a, r)
    
    :rtype: set
    :return: set of relations (offset, offset)
    """
    bottomup_cat2attributes = {
    'hyponym_hypernym' : {'hyponyms', 'instance_hyponyms'},
    'meronym_holonym' : {'member_meronyms', 'substance_meronyms', 'part_meronyms'},
    #'others' : {'attributes', 'entailments', 'causes', 'also_sees', 'verb_groups',
    #            'similar_tos'}
    }
    topdown_cat2attributes = {
    'hyponym_hypernym' : {'hypernyms', 
                          #'instance_hypernyms'
                         },
    'meronym_holonym' : {'member_holonyms', 'substance_holonyms', 'part_holonyms'},
    #'others' : {'attributes', 'entailments', 'causes', 'also_sees', 'verb_groups',
    #            'similar_tos'}
    }
    directed_edges = set()
    
    # loop through all synsets
    for synset in wn.all_synsets():
        source_offset = synset.offset()
        source_pos = synset.pos()
        if source_pos == 's':
            source_pos = 'a'
        
        # filter on pos if needed
        if wanted_pos is not None:
            if source_pos not in wanted_pos:
                continue
        
        # add relevant edges
        for cat in categories:
        
            for topdown, attributes in [
                                        #(False, bottomup_cat2attributes[cat]),
                                        (True, topdown_cat2attributes[cat])]:
                for attribute in attributes:
                    attr_targets = getattr(synset, attribute)()
                    for attr_target in attr_targets:
                        attr_target_offset = attr_target.offset()
        
                        if topdown:
                            value = (attr_target_offset, source_offset)
                            directed_edges.add(value)

                        #else:
                        #    value = (attr_target_offset, source_offset)

    return directed_edges


def sem_rels_freqs(category2attributes, perc=False):
    """
    given a categorization of which 
    synset attributes belong to which categories (self-made),
    this function computes the frequencies
    
    :param dict category2attributes: e.g. 
    {
    'hyponym_hypernym' : {'hypernyms', 'instance_hypernyms', 'hyponyms', 'instance_hyponyms'},
    'meronym_holonym' : {'member_holonyms', 'substance_holonyms', 'part_holonyms', 
                         'member_meronyms', 'substance_meronyms', 'part_meronyms'},
    'others' : {'attributes', 'entailments', 'causes', 'also_sees', 'verb_groups',
                'similar_tos'}
    }
    :param bool perc: if True, percentages are shown instead of raw frequencies
   
   
    :rtype: pandas.core.frame.DataFrame
    :return: number of semantic relations per category
    """
    category2edges = {pos: defaultdict(set)
                      for pos in {'n', 'v', 'a', 'r', 'all'}}
    
    for synset in wn.all_synsets():
        source_offset = synset.offset()
        source_pos = synset.pos()
        if source_pos == 's':
            source_pos = 'a'
        
        for category, attributes in category2attributes.items():
            for attribute in attributes:
                attr_targets = getattr(synset, attribute)()
                for attr_target in attr_targets:
                    attr_target_offset = attr_target.offset()
                    value = sorted([source_offset, attr_target_offset])
                    value = tuple(value)
                    
                    category2edges[source_pos][category].add(value)
                    category2edges[source_pos]['all_relations'].add(value)
                    category2edges['all'][category].add(value)
                    category2edges['all']['all_relations'].add(value)


    list_of_lists = []
    headers = ['all_relations'] + [category for category in category2attributes]
    
    for pos in ['all', 'n', 'v', 'a', 'r']:
        
        one_row = [pos]
        for category in headers:
            value = len(category2edges[pos][category])
            
            if perc:
                value = 100 * (float(value) / float(len(category2edges['all'][category])))
                value = round(value, 2)
                
            one_row.append(value)
        list_of_lists.append(one_row)
    
    headers.insert(0, 'pos')
    
    df = pandas.DataFrame(list_of_lists, columns=headers)
    return df
                      
                    
                    
                