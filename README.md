# gromacs-docker-container-maker


## What does this repository contain?

This repository holds the Dockerfiles and scripts needed to builds
the containers that contribute to gromacs/gromacs on Docker Hub, as built by gromacs-docker repository.

### How does it work?

This is the 2nd of 3 repositories requried to build the [gromacs/gromacs container on Docker Hub](https://hub.docker.com/r/gromacs/gromacs/).  The three stages are:

1. [fftw-docker](https://github.com/bioexcel/fftw-docker/), which builds the containerised fftw used by gromacs.
2. [gromacs-docker-container-maker](https://github.com/bioexcel/gromacs-docker-container-maker, the repository we are in, which builds the individual gromacs containers.
3. [gromacs-docker](https://github.com/bioexcel/gromacs-docker), which combines all the containers together.

## Layout and functions

This repository consists of 4 main files:

* `build-all-dockerfiles.sh` - This controls which build configurations are built by calling the `build-dockerfiles.py` once for each of the different configurations.
* `build-dockerfiles.sh` - This controls how each individual container is made.  This should be modified if you wish to change how the configurations are built, or which GROMACS version is used. If this is changed, `build-all-dockerfiles.sh` should be ran again.
* `utility.py`- ?Not clear on usage?
* `gmx-<gromacs_version>-cuda-<cuda_version>-<simd_type>` - There is one directory for each different gromacs versiona and simd type. Each contains the docker file needed to build it.

## Updating

Future updates will include things like new GROMACS versions, changes
to build configurations, and changes to which build configurations are
available.
The build-all-dockerfiles.sh file controls which build
configurations are built, but calling the build-dockerfiles.py file
repeatedly for the different configurations.
Edit the latter to change how configurations are built (and see
below), or the GROMACS version that is built. If you have
edited the latter, then run build-all-dockerfiles.sh after
doing so.

Make a new git branch and push it to
https://github.com/bioexcel/gromacs-docker-container-maker.
The Docker Hub repository
https://hub.docker.com/repository/docker/gromacs/gmx-configurations is
configured to build several configurations from this project. This must be
extended manually when new build configurations are added.

Test the configurations manually (for now, later we can have some
automated testing of the basics).

Once a matching set of configurations has been built, make a merge
request into master branch of https://github.com/bioexcel/gromacs-docker-container-maker.

Once that is accepted, make matching changes to https://github.com/bioexcel/gromacs-docker
so that it pulls the new containers when it is rebuild (or just trigger the
rebuild from https://hub.docker.com/repository/docker/gromacs/gromacs/builds
if no changes are needed).

## Maintainer

Mark Abraham (mabraham on github)
