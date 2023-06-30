# htcondor-job-time-analysis

analyze job times submitted via htcondor


Quickstart
==========

htcondor-job-time-analysis is **not** available on PyPI and so it should be installed using the `git` support of `pip`.

```
# do this in a venv
python3 -m venv venv
. venv/bin/activate
# upgrade pip to avoid warnings
pip install --upgrade
# upgrade setuptools to avoid warnings
pip install --upgrade setuptools
# install this
pip install git+https://github.com/tomeichlersmith/htcondor-job-time-analysis@v0.0.2
```

Then you can start pulling job information from HTCondor and making plots from it.
```
hjta-pull my-job-times.csv <batch id> <batch id2> ...
hjta-plot my-job-times.csv all
```

### Development
If you wish to help develop this package, make sure to install the style checker and auto-formatter.
```
pip install -e .[dev]
```
