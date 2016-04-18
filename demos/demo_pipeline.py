#! /usr/bin/env python3
"""
A demo script that ties some of the command line utilities together in a
pipeline

TODO: Replicate this with luigi or joblib
"""

import logging
import json
from os import path, mkdir
from glob import glob
from subprocess import check_call, CalledProcessError

log = logging.getLogger(__name__)


# Settings
data_dir = path.join(path.expanduser("~"), "data/GA-cover")
proc_dir = path.join(data_dir, "processed")

target_var = "Cr_ppm_i_1"
# target_var = "Na_ppm_i_1"
onehot = False
patchsize = 0
whiten = True  # whiten all of the extracted features?
standardise = False  # standardise all of the extracted features?
pca_frac = 0.7

target_file = "geochem_sites.shp"
target_hdf = path.join(proc_dir, "{}_{}.hdf5"
                       .format(path.splitext(target_file)[0], target_var))
cv_file = path.join(data_dir, "soilcrossvalindices.hdf5")
compos_file = "composite"

# algorithm = "bayesreg"
# args = {}

# algorithm = "glm"
# args = {'lenscale': 10., 'lparams': [100.], 'ard': False, 'nbases': 100,
#         'use_sgd': True}

# algorithm = "approxgp"
# args = {'lenscale': 10., 'ard': False, 'nbases': 100}

algorithm = "svr"
args = {'gamma': 1. / 100, 'epsilon': 0.05}

# algorithm = "randomforest"
# args = {'n_estimators': 100}

removedims = []


def main():

    logging.basicConfig(level=logging.INFO)

    # Make processed dir if it does not exist
    if not path.exists(proc_dir):
        mkdir(proc_dir)
        log.info("Made processed dir")

    # Make pointspec and hdf5 for targets
    cmd = ["maketargets", path.join(data_dir, target_file), target_var,
           "--outfile", target_hdf]

    if try_run_checkfile(cmd, target_hdf):
        log.info("Made targets")

    # Extract feats for training
    tifs = glob(path.join(data_dir, "*.tif"))
    if len(tifs) == 0:
        raise PipeLineFailure("No geotiffs found in {}!".format(data_dir))

    ffiles = []
    for tif in tifs:
        name = path.splitext(path.basename(tif))[0]
        cmd = ["extractfeats", name, tif, "--outputdir", proc_dir, "--chunks",
               "1", "--patchsize", str(patchsize)]
        if onehot:
            cmd += ['--onehot']
        cmd += ["--targets", target_hdf]

        msg = "Processing {}.".format(path.basename(tif))
        ffile = path.join(proc_dir, name + "_0.hdf5")
        try_run_checkfile(cmd, ffile, msg)
        ffiles.append(ffile)

    # Compose individual image features into single feature vector
    cmd = ["composefeats", '--impute']
    if standardise:
        cmd += ['--centre', '--standardise']
    if whiten:
        cmd += ['--whiten', '--featurefraction', str(pca_frac)]
    cmd += ['--outputdir', proc_dir, compos_file] + ffiles

    feat_file = path.join(proc_dir, compos_file + "_0.hdf5")
    try_run(cmd)

    # Train the model
    cmd = ["learnmodel", "--outputdir", proc_dir, "--cvindex", cv_file, "0",
           "--algorithm", algorithm, "--algopts", json.dumps(args), feat_file,
           target_hdf]

    log.info("Training model.")
    try_run(cmd)

    # Test the model
    alg_file = path.join(proc_dir, "{}.pk".format(algorithm))
    cmd = ["predict", "--outputdir", proc_dir, "--cvindex", cv_file, "0",
           alg_file, feat_file]

    log.info("Predicting targets.")
    try_run(cmd)

    # Report score
    cmd = ["validatemodel", "--metric", "r2_score", cv_file, "0", target_hdf,
           path.join(proc_dir, "predicted_0.hdf5")]

    try_run(cmd)


class PipeLineFailure(Exception):
    pass


def try_run_checkfile(cmd, checkfile, premsg=None):
    # TODO make this a proper memoize function?

    if not path.exists(checkfile):
        if premsg:
            log.info(premsg)
        try_run(cmd)
        return True

    return False


def try_run(cmd):

    try:
        check_call(cmd)
    except CalledProcessError:
        log.info("\n--------------------\n")
        raise


if __name__ == "__main__":
    main()
