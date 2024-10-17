"""
Setup module adapted from setuptools code. See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages

setup(
	name='MultiNBS',
	version='0.0.0',
	description='Python package to perform integrated network based stratification of somatic mutation and gene expression profiles as described in [insert citation].',
	url='https://github.com/kenliou45/multiNBS',
	author='Kenny Liou',
	author_email='kliou@ini.usc.edu',
	license='MIT',
	classifiers=[
		'Development Status :: 1 - Beta',
		'Intended Audience :: Science/Research',
		'Topic :: Software Development :: Build Tools',
		'License :: OSI Approved :: MIT License',
		'Programming Language :: Python :: 3.10'
	],
	packages=find_packages(exclude=['os', 'random', 'time']),
	install_requires=[
        'lifelines>=0.9.1',
        'networkx>=2.0',
        'numpy>=1.11.0',
        'matplotlib>=1.5.1',
        'pandas>=0.19.0',
        'scipy>=0.17.0',
        'scikit-learn>=0.17.1',
        'seaborn>=0.7.1']
)
