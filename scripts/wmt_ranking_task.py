#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Project: Appraise evaluation system
 Author: Matt Post <post@cs.jhu.edu>

This script takes a set of parallel files (source, reference, and system translations) and writes
out the XML file used to setup the corresponding Appraise tasks for WMT reranking. It supports many
options, such as limiting the maximum length of a source sentence (-maxlen, default 30), inserting
controls (-controls file) with a certain probability (-control_prob, default 1.0, meaning every HIT
will have a control), and so on.

"""

import os
import sys
import math
import random
import hashlib
import argparse
from ranking_task import RankingTask,Control
from xml.sax.saxutils import escape

PARSER = argparse.ArgumentParser(description="Build evaluation task input file.")
PARSER.add_argument("source", type=file, help="source language file")
PARSER.add_argument("reference", type=file, nargs="?", help="reference language file")
PARSER.add_argument("system", metavar="system", nargs="*", type=file, help="parallel files to compare")
PARSER.add_argument("-block",type=str,default="-1", help="Block id for this set of HITs")
PARSER.add_argument("-id", type=str, default="none", help="ID name to use for the system name")
PARSER.add_argument("-source", type=str, default="spa", dest="sourceLang", help="the source language")
PARSER.add_argument("-target", type=str, default="eng", dest="targetLang", help="the target language")
PARSER.add_argument("-numhits", type=int, default=100, help="number of HITs in the batch")
PARSER.add_argument("-tasksperhit", type=int, default=3, help="number of HITs in the batch")
PARSER.add_argument("-systemspertask", type=int, default=5, help="number of systems to rerank")
PARSER.add_argument("-redundancy", type=int, default=10, help="number of redundant HITs in the batch")
PARSER.add_argument('-maxlen', type=int, default=30, help='maximum source sentence length')
PARSER.add_argument('-min-index', dest='min_index', type=int, default=0, help='Minimum index from which to start sampling sentences')
PARSER.add_argument('-seed', type=int, default=None, help='random seed')
PARSER.add_argument('-no-sequential', dest='sequential', default=True, action='store_false', help='whether sentences within a HIT should be sequential')
PARSER.add_argument('-controls', type=str, default=None, dest="controlFile", help='file containing controls to use (implies -no-sequential)')
PARSER.add_argument('-control_prob', type=float, default=1.0, dest="control_prob", help='probability of inserting a control into a HIT')
PARSER.add_argument('-save', type=str, default=None, dest="saveDir", help='directory to save reduced corpora to')

def random_from_range(range_max, num_draws, tuple_size = 3, sequential = True, min_index=0):
    """Returns a set of tuples (of size `size') of numbers, representing sentences to use in constructing a HIT. `range_max' is the number of sentences, `num_draws' is the number of HITs to create, `tuple_size' is the number of sentences in each HIT, and `sequential' indicates that we should draw sentences in block groups."""
    
    """Returns a set of 'num' unique integers from the range (0, max-1)."""

    blocks = []
    if sequential is True:
        block_grid = []
        block_idx = -1
        indices = range(min_index, range_max)
        for i,index in enumerate(indices):
            if i % tuple_size == 0 or len(block_grid) == 0:
                block_idx += 1
                block_grid.append([index])
            else:
                block_grid[block_idx].append(index)
        # Stupid special case: make sure that each block has three
        # sentences due to hardcoding in the wmt14 app. So just
        # pick a random sentence to fill out the last item in
        # the block
        if len(block_grid[-1]) != 3:
            random.shuffle(indices)
            while len(block_grid[-1]) != 3:
                block_grid[-1].append(indices.pop())
        
        indices = range(len(block_grid))
        # Randomize the order in which raters see the blocks,
        # but do not randomize the blocks themselves since Appraise
        # expects 3 sentences per block. Otherwise we can't guarantee
        # a clean partitioning into blocks of 3
        random.shuffle(indices)
        blocks = [tuple(block_grid[i]) for i in indices[0:num_draws]]
    else:
        sentences = range(min_index, range_max)
        random.shuffle(sentences)
        sys.stderr.write(str(num_draws) + ' ' + str(len(sentences)))
        blocks = [tuple([sentences.pop(random.randint(0, len(sentences) - 1)) for x in range(tuple_size) if len(sentences) > 0]) for x in range(num_draws)]

    return blocks

if __name__ == "__main__":
    args = PARSER.parse_args()

    # SANITY CHECKING AND DEPENDENT VARIABLE SETTING

    if args.seed is not None:
        random.seed(args.seed)

    num_unique_hits = args.numhits - args.redundancy

    controls = []
    if args.controlFile is not None:
        args.sequential = False

        controls = Control.load(args.controlFile)
#        print 'Read %d controls, keeping %d best' % (len(controls), args.numhits - args.redundancy)
        controls = controls[:args.numhits-args.redundancy]

        if len(controls) < num_unique_hits:
            sys.stderr.write('* WARNING: not enough controls (%d < %d)\n' % (len(controls), num_unique_hits))

    # BEGIN 

    source = []
    for line in args.source:
        source.append(line.strip())
    
    reference = []
    if args.reference:
        for line in args.reference:
            reference.append(line.strip())

    if len(reference) != len(source):
        sys.stderr.write('* FATAL: reference length (%d) != source length (%d)\n' % (len(source), len(reference)))
        sys.exit(1)

    systems = []
    system_names = []
    if len(args.system):
        for i, system in enumerate(args.system):
            systems.append([])
            system_name = os.path.basename(system.name)
            system_names.append(system_name)
            for line in system:
                systems[i].append(line.strip())

            if len(systems[i]) != len(source):
                sys.stderr.write('* FATAL: system %s length (%d) != source length (%d)\n' % (system_name, len(source), len(reference)))
                sys.exit(1)

    system_hashes = [hashlib.sha1(x).hexdigest() for x in system_names]

    # Make a list of all eligible sentences
    eligible = []
    for i in range(len(source)):
        if len(source[i].split()) <= args.maxlen:
            eligible.append(i)

    def dump_system(system_file, lines):
        outfile = os.path.join(args.saveDir, os.path.basename(system_file))
        if not os.path.exists(outfile):
            sys.stderr.write('DUMPING TO %s\n' % (outfile))
            out = open(outfile, 'w')
            for line in lines:
                out.write('%s\n' % (line))
            out.close()

    # Save corpora if requested and not already existing
    if args.saveDir is not None:
        if not os.path.exists(args.saveDir):
            os.makedirs(args.saveDir)
        dump_system(args.source.name, source)
        dump_system(args.reference.name, reference)
        for i,system in enumerate(args.system):
            dump_system(system.name, systems[i])
        dump_system('line_numbers', [x + 1 for x in eligible])

    random_blocks = random_from_range(len(eligible), args.numhits - args.redundancy, tuple_size = args.tasksperhit, sequential = args.sequential, min_index = args.min_index)
    hits = []
    for sentnos_tuple in random_blocks:

        # Randomize the selection of systems
        system_indexes = range(len(systems))
        random.shuffle(system_indexes)
        sampled_indexes = []
        for index in system_indexes:
            if len(sampled_indexes) == args.systemspertask:
                break
            add_id = True
            for sent_id in sentnos_tuple:
                if len(systems[index][eligible[sent_id]].strip()) == 0:
                    sys.stderr.write('Filtering sys %d id %d\n' % (index, sent_id))
                    add_id = False
                    break
            if add_id:
                sampled_indexes.append(index)
        assert len(sampled_indexes) == args.systemspertask
        system_indexes = sampled_indexes
        tasks = [RankingTask(eligible[id] + 1, escape(source[eligible[id]]), escape(reference[eligible[id]]), [system_names[sysid] for sysid in system_indexes], [escape(systems[sysid][eligible[id]]) for sysid in system_indexes]) for id in sentnos_tuple]

        # Randomly decided whether to randomly replace one of the tasks with a random control.  That
        # is, we roll a dice to see whether to insert a control (determined by
        # args.control_prob). If so, we randomly choose which HIT to replace, and then randomly
        # choose one of the remaining controls to put there.
        if len(controls):
            if random.random() < args.control_prob:
                tasks[random.randint(0, len(tasks)-1)] = controls.pop(random.randint(0,len(controls)-1))

        # sentnos_str = ",".join([`x.id` for x in tasks])
        sentnos_str = args.block
        hit = '  <hit block-id="%s" source-language="%s" target-language="%s">' % (sentnos_str, args.sourceLang, args.targetLang)
        for task in tasks:
            hit += task.xml()
        hit += '\n  </hit>'

        hits.append(hit)

    # Now create redundant HITs
    if args.redundancy > 0:
        numbers = random_from_range(len(hits), args.redundancy, tuple_size = 1, sequential = False)

        hits += [hits[x[0]] for x in numbers]

    print '<hits>'
    for hit in hits:
        print hit
    print '</hits>'
    sys.stderr.write('Wrote %d HITs%s' % (len(hits), os.linesep))
