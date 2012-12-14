#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" core.py

Main passage times classes/functions
"""
__author__ = 'Scott Burns <scott.s.burns@vanderbilt.edu>'
__copyright__ = 'Copyright 2012 Vanderbilt University. All Rights Reserved'

import numpy as np

from .metadata import BASE, FAR, MANIP, MANIP_TYPE, NEAR, TOTWORDS


class PassageTimeRunner(object):
    def __init__(self, label, group, data, version):
        self.id = label
        self.grp = group
        self.data = data
        self.ver = version

    def get(self, p):
        try:
            # row = _get_row(d, sub)
            # self.data is row
            bad = True if self.data['passages_discontinued'] else False
            key = '%s_time' % p
            t = self.data[key]
        except (IndexError, KeyError) as e:
            print e
            raise ValueError
        return t, bad

    def get_wpm(self, pass_name, sec):
        return round(TOTWORDS[self.ver][pass_name] / (sec / 60), 3)

    def process(self):
        results = {}
        if not self.grp:
            return self.data
        # Start baseline
        base_t = []
        for base_p in BASE[self.grp]:
            t, bad = self.get(base_p)
            results['%s_baseline_sec' % base_p] = t
            base_t.append(t)
        for manip_p in MANIP[self.grp]:
            manip_t = MANIP_TYPE[manip_p]
            t, bad = self.get(manip_p)
            results['%s_%s_sec' % (manip_p, manip_t)] = t
        # get NEAR/FAR
        nf_loop = zip(('near', 'far'), (NEAR, FAR))
        for nft, nfd in nf_loop:
            nf_p = nfd[self.grp]
            t, bad = self.get(nf_p)
            results['%s_%s_sec' % (nf_p, nft)] = t

        # DO WPM
        for sec_k, sec_v in [(k, v) for k, v in results.items() if '_sec' in k]:
            try:
                results[sec_k.replace('_sec', '_wpm')] = self.get_wpm(sec_k, sec_v)
            except TypeError:
                # probably a weird passage time
                results[sec_k.replace('_sec', '_wpm')] = ''

        # DO STATS
        if not self.data['passages_discontinued']:
            # numplify
            base_t = np.array(base_t)
            results['baseline_mean_sec'] = np.mean(base_t)
            results['baseline_mean_stdev'] = np.std(base_t)
            # add vocab, cohesion, decode, syntax
            for man in ('vocab_wpm', 'cohesion_wpm', 'decode_wpm', 'syntax_wpm'):
                gk = filter(lambda x: man in x, results.keys())[0]
                m = man.replace('_wpm', '')
                results[m] = results[gk]
            # do baseline wpm
            base_wpm_arr = np.array([v for k, v in results.items() if 'baseline_wpm' in k])
            results['baseline_wpm_raw'] = np.mean(base_wpm_arr)
            results['baseline_wpm_stdev'] = np.std(base_wpm_arr)
        self.results = results
        self.format_for_redcap()

    def format_for_redcap(self):

        # Change mustangs* to must*
        for k in self.results.keys():
            if 'mustang' in k:
                v = self.results.pop(k)
                self.results[k.replace('mustang', 'must')] = v
        # group in RC Passages Survey is 1-10, 0-9 in RC redcap
        self.results['group'] = str(self.grp - 1)
        # Format
        for k, v in self.results.items():
            str_v = str(v)
            if is_int(str_v):
                self.results[k] = '%d' % int(v)
            elif is_number(str_v):
                self.results[k] = '%0.3f' % round(float(v), 3)
            else:
                self.results[k] = str_v


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
