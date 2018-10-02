from distutils.core import setup

setup(name='kf-release-maker',
      version='1.0.0',
      description='Kids First software release authoring tool',
      author='Kids First Data Resource Center',
      scripts=['release-maker/release'],
      packages=['release-maker'],
)
