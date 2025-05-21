from setuptools import setup, find_packages

setup(
    name="hardware-inventory-viz",
    version="1.0.0",
    description="Hardware Inventory Visualization Tool",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "PyYAML>=6.0",
        "lxml>=4.9.3",
        "Pillow>=10.0.0",
    ],
    entry_points={
        'console_scripts': [
            'parse-csv=parse_csv_to_diagrams:main',
            'generate-svg=generate_interactive_svg:main',
        ],
    },
    python_requires='>=3.6',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
