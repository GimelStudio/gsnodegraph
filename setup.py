from setuptools import setup


setup(
  name = 'gsnodegraph',
  packages = ['gsnodegraph',
              'gsnodegraph.graph',
              'gsnodegraph.graph.utils',
              'gsnodegraph.node',
              'gsnodegraph.assets'],
  version = '0.5.5',
  license = 'Apache 2.0',
  description = 'Powerful node graph widget for wxPython GUIs',
  long_description_content_type="text/markdown",
  author = 'Noah Rahm and contributors',
  author_email = 'correctsyntax@yahoo.com',
  url = 'https://github.com/GimelStudio/gsnodegraph',
  keywords = ['nodegraph', 'nodes', 'graph', 'node-based', 'widget'],
  install_requires = [
      'wxpython==4.2.0'
    ],
  classifiers = [
    'Development Status :: 2 - Pre-Alpha',
    'Intended Audience :: Developers',
    'Operating System :: OS Independent',
    'Topic :: Desktop Environment',
    'Topic :: Multimedia :: Graphics :: Editors',
    'License :: OSI Approved :: Apache Software License',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
  ],
)
