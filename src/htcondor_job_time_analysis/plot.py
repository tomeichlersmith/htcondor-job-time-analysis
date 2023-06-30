"""module for creating common job timing plots"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def plotter(func):
    """decorator to register a function as a plotter

    Instead of figuring out the python nonsense necessary to check
    the following, we instead assume the user satisfies these criteria:

    1. The function has a name unique to this module
    2. The function takes a single argument: the pandas dataframe of job timing data
    3. The function does /not/ savefig or plt.show. Either the user does that
        in their jupyter notebook or the script does that, both of which can
        access the figure with plt.gcf()
    """
    plotter.__registry__[func.__name__] = func
    return func


plotter.__registry__ = dict()


@plotter
def execute_vs_transfer(df: pd.DataFrame):
    """Plot execute time vs transfer time and calculate effective number of cores for this group of jobs"""
    # definitions for the axes
    left, width = 0.1, 0.65
    bottom, height = 0.1, 0.65
    spacing = 0.005

    rect_scatter = [left, bottom, width, height]
    rect_histx = [left, bottom + height + spacing, width, 0.2]
    rect_histy = [left + width + spacing, bottom, 0.2, height]

    # start with a rectangular Figure
    plt.figure(figsize=(10, 8))

    ax_scatter = plt.axes(rect_scatter)
    ax_scatter.tick_params(direction='in', top=True, right=True)
    ax_histx = plt.axes(rect_histx)
    ax_histx.tick_params(direction='in', labelbottom=False)
    ax_histy = plt.axes(rect_histy)
    ax_histy.tick_params(direction='in', labelleft=False)
    ax_text = plt.axes([left+width+spacing, bottom+height+spacing, 0.2, 0.2])
    ax_text.axis('off')

    cluster_time = (df['TransferOutFinished'].max() - df['QDate'].min())/60
    mean_job_time = df['JobTime'].mean()
    tot_execute = df['ExecuteTime'].sum()
    df['TransferFrac'] = df['TransferTime']/df['ExecuteTime']
    lines = [
        f'Total Submit to Complete: {cluster_time:.2f} min',
        f'Num Jobs: {len(df.index)}',
        f'Mean Job Time (including transfer): {mean_job_time:.2f} s',
        f'Total Execute: {tot_execute} s',
        f'Eff N cores: {tot_execute/(cluster_time*60):.2f}'
    ]
    ax_text.text(0.01, 0.01, '\n'.join(lines), verticalalignment='bottom', horizontalalignment='left')

    # the scatter plot
    ax_scatter.scatter(df['ExecuteTime'], df['TransferTime'])

    # separate so we can get scatter limits for histogram
    ax_histy.hist(
        df['TransferTime'],
        bins=50,
        range=ax_scatter.get_ylim(),
        orientation='horizontal', histtype='step'
    )
    ax_scatter.set_xlabel('Execution Time [s]')
    ax_scatter.set_ylabel('Transfer Time [s]')

    worst_transfer = df['TransferFrac'].max()
    mean_transfer = df['TransferFrac'].mean()
    ax_scatter.axline(
        (0, 0),
        slope=worst_transfer,
        label=f'Worst Transfer ({worst_transfer*100:.2f}%)',
        color='black'
    )
    ax_scatter.axline(
        (0, 0),
        slope=mean_transfer,
        label=f'Mean Transfer ({mean_transfer*100:.2f}%)',
        color='gray'
    )

    ax_scatter.legend()

    ax_histx.hist(
        df['ExecuteTime'],
        range=ax_scatter.get_xlim(),
        bins=50,
        histtype='step'
    )
    ax_histx.set_xlim(ax_scatter.get_xlim())
    ax_histx.set_ylabel('Jobs')
    ax_histx.set_yscale('log')
    ax_histy.set_ylim(ax_scatter.get_ylim())
    ax_histy.set_xscale('log')
    ax_histy.set_xlabel('Jobs')


@plotter
def transfer_hist(df: pd.DataFrame):
    """histogram the different transfer time samples"""
    for k in ['TransferIn', 'TransferInQueueTime', 'TransferOut', 'TransferOutQueueTime']:
        plt.hist(
            df[k],
            bins=[-1]+np.logspace(0, 6, 50),
            label=k, histtype='step',
            # density=True,
            ls='--' if 'Queue' in k else '-',
            color='tab:blue' if 'In' in k else 'tab:red',
            lw=2
        )
    plt.yscale('log')
    plt.xscale('log')
    plt.ylabel('Jobs')  # / Bin Width')
    plt.xlabel('Time [s]')
    plt.legend(
        ncol=2,
        loc='lower center',
        bbox_to_anchor=(0.5, 1.)
    )


@plotter
def transfer_by_index(df: pd.DataFrame):
    """plot the transfer queue time by job index"""
    sl = df.sort_values(['ClusterId', 'ProcId']).reset_index()
    plt.scatter(
        sl.index, sl['TransferInQueueTime'],
        alpha=0.1, marker='s',
        label='In Queue'
    )
    plt.scatter(
        sl.index, sl['TransferOutQueueTime'],
        alpha=0.1,
        label='Out Queue'
    )
    plt.ylabel('Time [s]')
    plt.xlabel('Job Index (sort by ClusterID then ProcId)')
    plt.legend()


def main():
    """main function to run if this module is called as a script"""

    plot_options = list(plotter.__registry__.keys())

    import argparse
    import pathlib
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'input_file',
        type=pathlib.Path,
        help='input CSV data table of job time data'
    )
    parser.add_argument(
        'plot',
        type=str,
        nargs='+',
        help=f'name of plot to make, options: {plot_options} or "all" to make them all'
    )
    parser.add_argument(
        '--out-dir',
        type=pathlib.Path,
        help='output directory to store plots (default is current directory)',
        default=pathlib.Path.cwd()
    )

    clargs = parser.parse_args()

    # deduce and clean clarg plot selection
    selected_plots = clargs.plot
    for name in selected_plots:
        if name not in plot_options and name != 'all':
            raise ValueError(f'Plot "{name}" is not one of the options.')
    if 'all' in selected_plots:
        selected_plots = plot_options

    df = pd.read_csv(clargs.input_file)

    def save_and_close(name):
        plt.savefig(
            str(clargs.out_dir / name)+'.pdf',
            bbox_inches='tight'
        )
        plt.close()

    for name in selected_plots:
        plotter.__registry__[name](df)
        save_and_close(name)


if __name__ == '__main__':
    main()
