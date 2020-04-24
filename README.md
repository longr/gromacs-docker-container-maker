# gromacs-docker-container-maker
Builds the containers that contribute to gromacs/gromacs on Docker Hub, as built by gromacs-docker repository

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
