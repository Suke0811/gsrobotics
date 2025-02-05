from setuptools import setup

setup(
    name='gelsight',
    version='2.0',
    packages=['gelsight'],
    license='',
    author='gelsight',
    author_email='info@gelsight.com',
    install_requires=[
        'numpy', 'numba', 'open3d', 'opencv_python_headless', 'scipy', 'torch',
        'opencv-contrib-python'
    ],
    description='A toolkit to interface with Gelsight tactile devices'
)
