"""Pull job timing data from HTCondor Schedd History

HTCondor cleans up its old history on a periodic basis, so this pull should be done
close enough in time to the job submission and completion date that the history of it
has not been removed
"""

import htcondor
import classad
import pandas as pd
import numpy as np
import socket
import os


def __clusters_expand(*args):
    """expand the provided arguments into a list of full-definition clusters

    In HTCondor a cluster of jobs is uniquely defined by which scheduler it
    was submitted from and its cluster ID number. We expand the provided list
    into a new list of 2-tuples which contains this information. Any item in
    the list that is only an integer (assumed to be a cluster ID) is given the
    current host as the scheduler to pull from.

    Attributes
    ----------
    __schedd_lut__ : Dict[str, classad]
        look up table from hostname to full definition of a scheduler

    Parameters
    ----------
    args: List[str]
        list of clusters to expand. A cluster is defined as <cluster_id>[:<scheduler>]

    Returns
    -------
    List[Tuple[int,str]]
        list of fully-defined clusters, each entry is a (cluster_id, scheduler) pair
    """
    # first expand argument into what we want
    clusters = []
    for arg in args:
        if not isinstance(arg, (str, int)):
            raise TypeError('Provided cluster definition {arg} is not a str or an int')
        clusterid, schedname = None, None
        if isinstance(arg, int) or arg.isdigit():
            clusterid = int(arg)
            schedname = socket.gethostname()
        else:
            params = arg.split(':')
            if len(params) != 2 or not params[0].isdigit():
                raise ValueError(f'Cluster {arg} is not of the form <cluster_id>:<submitter>')
            clusterid = int(params[0])
            schedname = params[1]
        if schedname not in __clusters_expand.__schedd_lut__:
            # if schedname only matches a unique machine name, then
            # assume user is using some alias and use that schedd
            matches = [m for m in __clusters_expand.__schedd_lut__ if schedname in m]
            if len(matches) == 0:
                raise ValueError(f'{schedname} not recognized as having a scheduler')
            if len(matches) > 1:
                raise ValueError(f'{schedname} matches more than on scheduler {matches}. Be more precise!')
            schedname = matches[0]
        clusters.append((clusterid, __clusters_expand.__schedd_lut__[schedname]))
    return clusters


__clusters_expand.__schedd_lut__ = {
    fulldef['Machine']: fulldef
    for fulldef in htcondor.Collector().locateAll(htcondor.DaemonTypes.Schedd)
}


def acquire_timing(*args):
    """Acquire timing data from jobs matching the input clusters

    The input cluster arguments are one of two forms.

    1. <cluster_id> : use the Schedd from the current machine and
        get timing for that cluster ID number
    2. (<cluster_id>, <machine_name>): get timing from cluster ID
        on the Schedd from <machine_name>

    After acquiring the raw timing data from the condor schedd,
    we add a few more columns to the data frame with variables of interest.

    - 'JobTime' : difference between output transfer complete and job start
        (not perfectly equal to total job time but within a few seconds)
    - 'Transfer{In,Out}' : time [s] spent actually copying data in/out
    - 'FracTransfer{In,Out}' : fraction of job time spent copying data in/out
    - 'Trasnfer{In,Out}QueueTime' : time [s] job spent in queue to copy data in/out
    """
    clusters = __clusters_expand(*args)

    items_of_interest = {
        'ClusterId': [],
        'ProcId': [],
        'ExitCode': [],
        'QDate': [],
        'TransferInputSizeMB': [],
        'JobStartDate': [],
        'TransferInQueued': [],
        'TransferInStarted': [],
        'TransferInFinished': [],
        'TransferOutQueued': [],
        'TransferOutStarted': [],
        'TransferOutFinished': [],
        'BytesSent': [],
    }

    for cluster_id, submitter in clusters:
        schedd = htcondor.Schedd(submitter)
        for h in schedd.history(
            (classad.Attribute('ClusterId') == cluster_id),
            list(items_of_interest.keys())
        ):
            for k in items_of_interest:
                items_of_interest[k].append(h.get(k))

    df = pd.DataFrame(items_of_interest)
    df['JobTime'] = df['TransferOutFinished']-df['JobStartDate']
    for d in ['In', 'Out']:
        df[f'Transfer{d}'] = df[f'Transfer{d}Finished'] - df[f'Transfer{d}Started']
        df[f'Transfer{d}QueueTime'] = (df[f'Transfer{d}Started']-df[f'Transfer{d}Queued']).fillna(0)
    df['TransferTime'] = df['TransferIn']+df['TransferOut']+df['TransferInQueueTime']+df['TransferOutQueueTime']
    df['ExecuteTime'] = df['TransferOutStarted']-df['TransferInFinished']
    return df


def main():
    """main pull function, run if this module is run as script"""

    import argparse
    import pathlib

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'output_file',
        type=pathlib.Path,
        help='output file to write data to'
    )
    parser.add_argument(
        'cluster',
        type=str,
        nargs='+',
        help='cluster of jobs to pull data for in the format: '
        '<cluster_id>[:<submitting-node>] where the default submitting node '
        'is the current host '+socket.gethostname()+'. The submitting node '
        'can be provided by its shortened name if the shortened name only '
        'matches one option.'
    )

    clargs = parser.parse_args()

    df = acquire_timing(*(clargs.cluster))
    df.to_csv(clargs.output_file)


if __name__ == '__main__':
    main()
