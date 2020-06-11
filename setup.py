from setuptools import setup

setup(
    name='xform',
    version='0.0.1',
    description='Tornado get query string or form data utils.',
    author='Maco',
    author_email='macohong@hotmail.com',
    license='MIT',
    url='https://github.com/marcohong/xform',
    keywords=['tornado form xform'],
    packages=['xform'],
    install_requires=['tornado>6.0.0'],
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        "Programming Language :: Python :: Implementation :: CPython",
        'Operating System :: OS Independent',
        'Framework :: AsyncIO',
    ]
)
