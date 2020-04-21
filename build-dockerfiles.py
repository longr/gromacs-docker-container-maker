#!/usr/bin/env python

"""Generates a set of docker images each containing a single build configuration
of GROMACS. These are combined via the Docker builder pattern into the
multi-configuration container on Docker Hub gromacs/gromacs. It examines the
environment at run time and dispatches to the correct build configuration.

The images are prepared according to a selection of build
configuration targets that cover a broad scope of different possible
run-time environmeents. Each combination is described as an entry in
the build_configs dictionary, with the script analysing the logic and
adding build stages as needed.

Based on the example script provided by the NVidia HPCCM repository
from https://github.com/NVIDIA/hpc-container-maker and ideas from the
similar script used within the main GROMACS repository for building
containers used for CI testing.

Authors:
    * Mark Abraham <mark.j.abraham@gmail.com>

Usage::

    $ python3 build-dockerfiles.py --help
    $ python3 build-dockerfiles.py --format docker > Dockerfile && docker build .
    $ python3 build-dockerfiles.py | docker build -

"""

import argparse
import collections
import typing
from distutils.version import StrictVersion

import hpccm
import hpccm.config
from hpccm.building_blocks.base import bb_base

try:
    import utility
except ImportError:
    raise RuntimeError(
        'This module assumes availability of supporting modules in the same directory. Add the directory to '
        'PYTHONPATH or invoke Python from within the module directory so module location can be resolved.')

# Basic packages for all final images.
_common_packages = ['build-essential',
                    'ca-certificates',
                    'git',
                    'gnupg',
                    'libhwloc-dev',
                    'libx11-dev',
                    'ninja-build',
                    'wget']

# Parse command line arguments
parser = argparse.ArgumentParser(description='GROMACS Dockerfile creation script', parents=[utility.parser])

parser.add_argument('--format', type=str, default='docker',
                    choices=['docker', 'singularity'],
                    help='Container specification format (default: docker)')
parser.add_argument('--version', type=str, default='2020.1',
                    choices=['2020.1'],
                    help='Version of GROMACS to build')
parser.add_argument('--simd', type=str, default='auto',
                    choices=['AUTO', 'SSE2', 'AVX_256', 'AVX2_256', 'AVX_512'],
                    help='SIMD flavour of GROMACS to build')

def base_image_tag(args) -> str:
    # Check if we use CUDA images or plain linux images
    if args.cuda is not None:
        cuda_version_tag = 'nvidia/cuda:' + args.cuda + '-devel'
        if args.centos is not None:
            cuda_version_tag += '-centos' + args.centos
        elif args.ubuntu is not None:
            cuda_version_tag += '-ubuntu' + args.ubuntu
        else:
            raise RuntimeError('Logic error: no Linux distribution selected.')

        base_image_tag = cuda_version_tag
    else:
        if args.centos is not None:
            base_image_tag = 'centos:centos' + args.centos
        elif args.ubuntu is not None:
            base_image_tag = 'ubuntu:' + args.ubuntu
        else:
            raise RuntimeError('Logic error: no Linux distribution selected.')
    return base_image_tag


def get_compiler(args):
    compiler = hpccm.building_blocks.gnu(extra_repository=True,
                                         version=args.gcc,
                                         fortran=False)
    return compiler

def get_mpi(args, compiler):
    # If needed, add MPI to the image
    if args.mpi is not None:
        if args.mpi == 'openmpi':
            use_cuda = False
            if args.cuda is not None:
                use_cuda = True

            if hasattr(compiler, 'toolchain'):
                return hpccm.building_blocks.openmpi(toolchain=compiler.toolchain, cuda=use_cuda, infiniband=False)
            else:
                raise RuntimeError('compiler is not an HPCCM compiler building block!')

        elif args.mpi == 'impi':
            raise RuntimeError('Intel MPI recipe not implemented yet.')
        else:
            raise RuntimeError('Requested unknown MPI implementation.')
    else:
        return None

def get_cmake(args):
    return hpccm.building_blocks.packages(
        apt_keys=['https://apt.kitware.com/keys/kitware-archive-latest.asc'],
        apt_repositories=['deb [arch=amd64] https://apt.kitware.com/ubuntu/ bionic main'],
        ospackages=['cmake']
        )

def build_gmx(args):
    build_dir='build'
    cmake_command = [
        f'cmake -S . -B {build_dir}',
        '-D CMAKE_BUILD_TYPE=Release',
        '-D CUDA_TOOLKIT_ROOT_DIR=/usr/local/cuda',
        f'-D GMX_SIMD={args.simd}',
        '-D GMX_BUILD_OWN_FFTW=ON',
        '-D GMX_GPU=ON',
        '-D GMX_MPI=OFF',
        f'-D CMAKE_INSTALL_PREFIX=/gromacs/bin.{args.simd}',
        #'-D GMX_PREFER_STATIC_LIBS=ON',
        #'-D MPIEXEC_PREFLAGS=--allow-run-as-root'
        '-D GMX_OPENMP=ON',]
    gmx = hpccm.building_blocks.generic_build(
        build=[f'mkdir -p {build_dir}',
               ' '.join(cmake_command),
               f'cmake -S . -B {build_dir}',
               f'cmake --build {build_dir} --target all -- -j2'],
        install=[f'cmake --install {build_dir}'],
        url=f'ftp://ftp.gromacs.org/pub/gromacs/gromacs-{args.version}.tar.gz'
    )
    return gmx

def build_stages(args) -> typing.Iterable[hpccm.Stage]:
    """Define and sequence the stages for the recipe corresponding to *args*."""

    # A Dockerfile or Singularity recipe can have multiple build stages.
    # The main build stage can copy files from previous stages, though only
    # the last stage is included in the tagged output image. This means that
    # large or expensive sets of build instructions can be isolated in
    # local/temporary images, but all of the stages need to be output by this
    # script, and need to occur in the correct order, so we create a sequence
    # object early in this function.
    stages = collections.OrderedDict()

    # Building blocks are chunks of container-builder instructions that can be
    # copied to any build stage with the addition operator.
    building_blocks = collections.OrderedDict()

    os_packages = _common_packages
    building_blocks['ospackages'] = hpccm.building_blocks.packages(ospackages=os_packages)
    
    # These are the most expensive and most reusable layers, so we put them first.
    building_blocks['compiler'] = get_compiler(args)
    building_blocks['mpi'] = get_mpi(args, building_blocks['compiler'])
    building_blocks['cmake'] = get_cmake(args)
#    building_blocks['configure_gmx'] = configure_gmx(args, building_blocks['compiler'])
    building_blocks['build_gmx'] = build_gmx(args)

    # Create the stage from which the targeted image will be tagged.
    stages['main'] = hpccm.Stage()

    stages['main'] += hpccm.primitives.baseimage(image=base_image_tag(args))
    for bb in building_blocks.values():
        if bb is not None:
            stages['main'] += bb

    # Note that the list of stages should be sorted in dependency order.
    for build_stage in stages.values():
        if build_stage is not None:
            yield build_stage


if __name__ == '__main__':
    args = parser.parse_args()

    # Set container specification output format
    hpccm.config.set_container_format(args.format)

    container_recipe = build_stages(args)

    # Output container specification
    for stage in container_recipe:
        print(stage)
