import os
import re

from setuptools import find_packages, setup

regexp = re.compile(r'.*__version__ = [\'\"](.*?)[\'\"]', re.S)

base_package = 'htcondor_job_time_analysis'
base_path = os.path.dirname(__file__)

init_file = os.path.join(base_path, 'src', 'htcondor_job_time_analysis', '__init__.py')
with open(init_file, 'r') as f:
    module_content = f.read()

    match = regexp.match(module_content)
    if match:
        version = match.group(1)
    else:
        raise RuntimeError(
            'Cannot find __version__ in {}'.format(init_file))

with open('README.md', 'r') as f:
    readme = f.read()

def parse_requirements(filename):
    ''' Load requirements from a pip requirements file '''
    with open(filename, 'r') as fd:
        lines = []
        for line in fd:
            line.strip()
            if line and not line.startswith("#"):
                lines.append(line)
    return lines

requirements = parse_requirements('requirements.txt')


if __name__ == '__main__':
    setup(
        name='htcondor_job_time_analysis',
        description='analyze job times submitted via htcondor',
        long_description=readme,
        license='MIT license',
        url='https://github.com/tomeichlersmith/htcondor_job_time_analysis',
        version=version,
        author='Tom Eichlersmith',
        author_email='eichl008@umn.edu',
        maintainer='Tom Eichlersmith',
        maintainer_email='eichl008@umn.edu',
        install_requires=requirements,
        keywords=['htcondor_job_time_analysis'],
        package_dir={'': 'src'},
        packages=find_packages('src'),
        entry_points={
            'console_scripts': [
                'hjta-pull = htcondor_job_time_analysis.pull:main',
                'hjta-plot = htcondor_job_time_analysis.plot:main'
            ],
        },
        zip_safe=False,
        classifiers=['Development Status :: 3 - Alpha',
                     'Intended Audience :: Developers',
                     'Programming Language :: Python :: 3.6',
                     'Programming Language :: Python :: 3.7',
                     'Programming Language :: Python :: 3.8']
    )
