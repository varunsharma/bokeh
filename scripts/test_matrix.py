from __future__ import print_function

import argparse
import os
import shutil
import subprocess
import textwrap


def get_parser():
    """Create the parser that will be used to add arguments to the script.
    """

    parser = argparse.ArgumentParser(description=textwrap.dedent("""
                    Creates conda environments for a given
                    version of bokeh, installed using pip and
                    conda and including python 2.7 and python 3.4.

                    The --version ('-v') option takes an earlier version of
                    bokeh, for use in creating environments where bokeh will be
                    updated.


                    Ex: ' python test_matrix.py -v 0.7.0'
                    """), formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-v', '--version', action='store', default=False,
                        help='Version of bokeh', required=True)
    # parser.add_argument('')

    return parser


def cleaner(env_path):
    """Checks that an environment path exists and, if so, deletes it.
    """

    if os.path.exists(env_path):
        shutil.rmtree(env_path)


def conda_creator(env_name, pkgs):
    """Create a conda environment of a given name containing a given string of pkgs.
    """

    subprocess.call("conda create --yes -n %s %s" % (env_name, pkgs), shell=True)


def bokeh_installer(env_name, install_string):
    """Activate an environment and run its install string to either install or update bokeh using
    conda or pip.
    """

    if os.name == 'nt':
        command_string = 'activate %s & %s' % (env_name, install_string)
    else:
        command_string = 'source activate %s; %s' % (env_name, install_string)

    result = subprocess.call(command_string, shell=True, executable="/bin/bash")

    return result == 0


PIP_INSTALL = "pip install --pre -i https://pypi.anaconda.org/bokeh/channel/dev/simple bokeh --extra-index-url https://pypi.python.org/simple/"
PIP_UPGRADE = "pip install --upgrade --pre -i https://pypi.anaconda.org/bokeh/channel/dev/simple bokeh --extra-index-url https://pypi.python.org/simple/"

CONDA_INSTALL = "conda install --yes -c bokeh/channel/dev bokeh"
CONDA_UPDATE = "conda update --yes -c bokeh/channel/dev bokeh"

TEST_INSTALL = {
    "2.7": "conda install --yes -c bokeh nose mock ipython scipy pandas numba beautiful-soup",
    "3.4": "conda install --yes -c bokeh nose mock ipython scipy pandas numba beautiful-soup flexx",
    "3.5": "conda install --yes -c bokeh nose mock ipython scipy pandas numba beautifulsoup4 flexx",
}

def conda(pyver, ver=None):
    if ver:
        return {
            "init"    : "python=%s pytest nose mock bokeh=%s" % (pyver, ver),
            "install" : '; '.join([TEST_INSTALL[pyver], CONDA_UPDATE])
        }
    else:
        return {
            "init"    : "python=%s pytest mock" % pyver,
            "install" : '; '.join([TEST_INSTALL[pyver], CONDA_INSTALL])
        }

def pip(pyver, ver=None):
    if ver:
        return {
            "init"    : "python=%s pip pytest nose mock bokeh=%s" % (pyver, ver),
            "install" :  '; '.join([TEST_INSTALL[pyver], PIP_UPGRADE])
        }
    else:
        return {
            "init"    : "python=%s pytest mock pip" % pyver,
            "install" : '; '.join([TEST_INSTALL[pyver], PIP_INSTALL])
        }


if __name__ == '__main__':

    parser = get_parser()
    ops = parser.parse_args()

    ver = ops.version

    envs = {
        "py27_conda_clean"  : conda("2.7"),
        "py27_conda_update" : conda("2.7", ver),
        "py27_pip_clean"    : pip("2.7"),
        "py27_pip_update"   : pip("2.7", ver),

        "py34_conda_clean"  : conda("3.4"),
        "py34_conda_update" : conda("3.4", ver),
        "py34_pip_clean"    : pip("3.4"),
        "py34_pip_update"   : pip("3.4", ver),

        "py35_conda_clean"  : conda("3.5"),
        "py35_conda_update" : conda("3.5", ver),
        "py35_pip_clean"    : pip("3.5"),
        "py35_pip_update"   : pip("3.5", ver),
    }

    # Use this method rather than os.path.expanduser('~/anaconda') to provide
    # miniconda support
    root = subprocess.check_output(['conda', 'info', '--root']).rstrip()

    # Python3 will return a byte string on the above line, so it must be
    # decoded to utf-8 before we can pass it to os.path.join
    root = root.decode()

    for environment in envs:
        successful_install = True
        fails = []
        cleaner(os.path.join(root, "envs", environment))
        print()
        print("CREATING NEW ENV", environment)
        conda_creator(environment, envs[environment]["init"])

        install = bokeh_installer(environment, envs[environment]["install"])
        if not install:
            fails.append(environment)
            successful_install = False

    print()
    print("*********************")
    if successful_install:
        print("All environments have been installed!  See below for their names.\n")
        for environment in envs:
            print(environment)
        print("\nNOTE: All of these environments will be deleted and replaced if you rerun test_matrix.py")
    else:
        print("The following environments have failed to install:\n")
        for install_fail in fails:
            print(install_fail)
    print("*********************")
