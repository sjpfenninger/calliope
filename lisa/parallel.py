from __future__ import print_function
from __future__ import division

import itertools
import os

import pandas as pd
import yaml

from . import utils


class LisaParallelizer(object):
    """docstring for LisaParallelizer"""
    def __init__(self, config=None):
        super(LisaParallelizer, self).__init__()
        self.config = utils.AttrDict(yaml.load(open(config, 'r')))

    def generate_iterations(self):
        keys = (['override.' + c for c in self.config.iterations_model.keys()]
                + self.config.iterations_run.keys())
        values = (self.config.iterations_model.values()
                  + self.config.iterations_run.values())
        df = pd.DataFrame(list(itertools.product(*values)), columns=keys)
        return df

    def generate_runs(self, target_dir=None):
        c = self.config
        # Create output directory
        if target_dir:
            out_dir = os.path.join(target_dir, c.name)
        else:
            out_dir = c.name
        os.makedirs(out_dir)
        iterations = self.generate_iterations()
        # Save iterations to disk to figure out what all the numbers mean!
        os.makedirs(os.path.join(out_dir, 'Output'))
        iterations.to_csv(os.path.join(out_dir, 'Output', 'iterations.csv'))
        for row in iterations.iterrows():
            # Generate configuration object
            index, item = row
            index_str = '{:0>4d}'.format(index)
            iteration_config = c.run_settings
            for k, v in item.to_dict().iteritems():
                iteration_config.set_key(k, v)
            # Always make sure we are saving outputs from iterations!
            iteration_config.set_key('output.save', True)
            # Set output dir in configuration object (NB: relative path!)
            iteration_config.set_key('output.path', os.path.join('Output',
                                                                 index_str))
            # Write configuration object to YAML file
            settings = 'settings_{}.yaml'.format(index_str)
            with open(os.path.join(out_dir, settings), 'w') as f:
                yaml.dump(iteration_config.as_dict(), f)
            # Write model run script
            run = 'run_{}.py'.format(index_str)
            with open(os.path.join(out_dir, run), 'w') as f:
                f.write('#!/usr/bin/env python\n')
                f.write('import lisa\n')
                f.write('model = lisa.Lisa(config_run=\'{}\')\n'.format(settings))
                f.write('model.run()\n')
            os.chmod(os.path.join(out_dir, run), 0755)
