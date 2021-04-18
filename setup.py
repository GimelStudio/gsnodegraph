from setuptools import setup


setup(
  name = 'gsnodegraph',   
  packages = ['gsnodegraph'],   
  version = '0.1.2',
  license='Apache 2.0',   
  description = 'Powerful nodegraph widget for wxpython GUIs',
  long_description_content_type="text/markdown",
  author = 'Correct Syntax, Noah Rahm', 
  author_email = 'correctsyntax@yahoo.com',     
  url = 'https://github.com/Correct-Syntax/gsnodegraph', 
  keywords = ['nodegraph', 'nodes', 'graph', 'node-based'], 
  install_requires=[           
          'wxpython==4.1.1'
      ],
  classifiers=[
    'Development Status :: 2 - Pre-Alpha',
    'Intended Audience :: Developers',
    'Operating System :: OS Independent',
    'Topic :: Desktop Environment',
    'Topic :: Multimedia :: Graphics :: Editors',
    'License :: OSI Approved :: Apache Software License', 
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
  ],
)

