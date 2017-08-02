=======
SageWui
=======

SageWui is a major refactor/rewrite of the [Sage Notebook](https://github.com/sagemath/sagenb) (Sagenb).

We intend a smooth transition from Sagenb to SageWui to get _something
completely different_.

Status
======

* SageWui is independent from Sage, so that it can be launched from
  an independent python interpreter. A SageMath installation and the `sage`
  command in the default path is required, though.
* SageWui runs on python 2 and 3.
* `smtpsend` is now a global module.
* Sagewui startup procedure differs from Sagenb one.
  - No need for intermediate startup code files.
  - Standalone command interface.
  - Debug mode added.
* Sage server interface totally isolated.
  - Implemented in the subpackage `sage_server`. It can be reused in other
    projects.
  - No need for intermediate code files. Code is passed directly to the
    Sage server.
  - Sage initialization left to the `sage_server` interface.
  - Input is parsed with `ast`. Bugs in Sagenb related to incorrect parsing
    fixed
* New flask json session mechanism adopted.
* A lot of reformatting, bug fixing and simplification of code done, with
  respect to Sagenb.

Install
=======

Only for testing purposes.

The instructions below are valid for a modern Linux host. A working
`python` >= 3.4 and <3.6 installation with `venv` module
(`sudo apt-get install python3-venv` on Ubuntu based dists) is supposed to be
available.

Previously to the instructions below, install a recent version of
[SageMath](http://sagemath.org). Make `sage` command available in your PATH.


Standalone mode
---------------

1. In the command line, set a variable with your installation dir

   ```bash
   export INSTALLDIR="/some/dir/you/can/write/to"
   ```

1. Create a python3 virtual environment

   ```bash
   python3 -m venv "$INSTALLDIR/python"
   ```

1. Clone SageWui

   ```bash
   git clone https://github.com/damahou/sagewui $INSTALLDIR/sagewui
   cd "$INSTALLDIR/sagewui"
   git branch release origin/release
   git checkout release
   ```

1. Activate the python virtual environment

   ```bash
   . "$INSTALLDIR/python/bin/activate"
   ```

1. Populate de virtual environment

   ```bash
   pip install twisted flask flask-autoindex flask-babel flask-themes2 future pexpect docutils jsmin pyopenssl service_identity appdirs
   ```

1. SageWui related stuff

   ```bash
   cp -a "$INSTALLDIR/sagewui/sagewui" "$INSTALLDIR/sagewui/smtpsend.py" "$INSTALLDIR"/python/lib/python*/site-packages
   ln -s "$INSTALLDIR"/python/lib/python*/site-packages/sagewui/run.py "$INSTALLDIR/python/bin/sagewui"
   ```

1. Test the installation

   ```bash
   sagewui
   ```

To run sagewui from a fresh command line shell write

```bash
cd /path/where/you/installed/sagewui
. python/bin/activate
sagewui
```

Standalone development mode
---------------------------

1. In the command line, set a variable with your installation dir

   ```bash
   export INSTALLDIR="/some/dir/you/can/write/to"
   ```

1. Create a python3 virtual environment

   ```bash
   python3 -m venv "$INSTALLDIR/python"
   ```

1. Clone SageWui

   ```bash
   git clone https://github.com/damahou/sagewui "$INSTALLDIR/sagewui"
   ```

1. Activate the python virtual environment

   ```bash
   . "$INSTALLDIR/python/bin/activate"
   ```

1. Populate de virtual environment

   ```bash
   pip install twisted flask flask-autoindex flask-babel flask-themes2 future pexpect docutils jsmin pyopenssl service_identity appdirs
   ```

1. SageWui related stuff

   ```bash
   ln -s "$INSTALLDIR/sagewui/sagewui" "$INSTALLDIR/sagewui/smtpsend.py" "$INSTALLDIR"/python/lib/python*/site-packages
   ln -s "$INSTALLDIR"/python/lib/python*/site-packages/sagewui/run.py "$INSTALLDIR/python/bin/sagewui"
   ```

1. Test the installation

   ```bash
   sagewui
   ```

1. Run sagewui from a fresh command line shell in debug mode

    ```bash
    cd /path/where/you/installed/sagewui
    . python/bin/activate
    sagewui --debug
    ```

1. Edit code in $INSTALLDIR/sagewui. every time you change python code, the
   application is reloaded.

Server mode
-----------

This instructions are based on https://wiki.sagemath.org/SageServer.

A `ssh` server must be running.

1. Change the following shell variables as needed

   ```bash
   export sageservername="sageserver"
   export sageusername="sage"
   export sageusergroupname="sageusers"
   export INSTALLDIR="/directory/where/sagewui/will/be/installed"
   export pythondir="$INSTALLDIR/python"
   export sagewuidir="$INSTALLDIR/sagewui"
   export sageserverdir="$INSTALLDIR/$sageservername"
   export sageuserdir="$INSTALLDIR/$sageusergroupname"

   ```

1. Create a python3 virtual environment

   ```bash
   python3 -m venv "$pythondir"
   ```

1. Clone SageWui

   ```bash
   git clone https://github.com/damahou/sagewui "$sagewuidir"
   cd "$sagewuidir"
   git branch release origin/release
   git checkout release
   ```

1. Activate the python virtual environment

   ```bash
   . $pythondir/bin/activate"
   ```

1. Populate de virtual environment

   ```bash
   pip install twisted flask flask-autoindex flask-babel flask-themes2 future pexpect docutils jsmin pyopenssl service_identity appdirs
   ```

1. SageWui related stuff

   ```bash
   cp -a "$sagewuidir/sagewui" "$sagewuidir/smtpsend.py" "$pythondir"/lib/python*/site-packages
   ln -s "$pythondir"/lib/python*/site-packages/sagewui/run.py "$pythondir/bin/sagewui"
   ```

1. Test the installation and set the SageWui admin password

   ```bash
   sagewui --secure
   ```
1. Create users

   ```bash
    sudo mkdir -p "$sageserverdir" "$sageuserdir"
    sudo addgroup --gid 1010 "$sageservername"
    sudo addgroup --gid 1011 "$sageusergroupname"
    sudo adduser --disabled-password "$sageservername"\
           --ingroup "$sageservername"\
           --home "$sageserverdir/$sageservername"\
           --geco ",,,"
   for i in $(seq 0 9); do
       sudo adduser --disabled-password\
               --ingroup "$sageusergroupname"\
               --home "$sageuserdir/$sageusername$i"\
               --geco ",,," sage$i;
   done
   ```

1. Secure users login

   ```bash
   sudo echo "- : (sageusers) : ALL EXCEPT localhost" >> /etc/security/access.conf
   sudo echo "- : sageserver : ALL" >> /etc/security/access.conf
   ```

1. `ssh` configuration

   ```bash
   sudo -u "$sageservername" -i ssh-keygen -b 4096
   dir="$sageuserdir/$sageusername"
   for i in $(seq 0 9); do
        sudo mkdir -p "$dir$i"/.ssh
        sudo cat "$sageserverdir/$sageservername/.ssh/id_rsa.pub" \
            > "$dir$i/.ssh/authorized_keys"
        sudo chown -R "$sageusername$i:$sageusergroupname" "$dir$i"
        sudo chmod -R 700 "$dir$i"
   done

   sudo find "$sageuserdir" -type f -exec chmod u-x {} \;
   sudo chmod 700 "$sageserverdir/$sageservername"
   sudo chmod 750 "$sageserverdir" "$sageuserdir"
   sudo chgrp "$sageservername" "$sageserverdir"
   sudo chgrp "$sageusergroupname" "$sageuserdir"
   sudo echo "umask 077" >> "$sageserverdir/$sageservername/.profile"
   sudo dir="$sageuserdir/$sageusername"
   for i in $(seq 0 9); do
       sudo echo "umask 077" >> "$dir$i/.profile"
   done
   ```

1. Set localhost identity for sageserver user ssh config.  Answer yes to all

   ```bash
   sudo -u "$sageservername" ssh "${sageusername}0@localhost" echo Done
   ```

1. Test all the ssh connections

   ```bash
   for i in $(seq 0 9); do
       sudo -u "$sageservername" ssh "$sageusername$i@localhost" echo Success
   done
   ```

1. Prepare the sagewui service

   ```bash
       cp "$sagewuidir/util/sagewui-server" /etc/init.d
   ```

1. Edit the shell variables in `/etc/init.d/sagewui-server` to set the host
   and port wanted.

1. Configure the sagewui service

   ```bash
   update-rc.d sagewui-server defaults 92 08
   update-rc.d sagewui-server enable
   ```

1. Test the service

   ```bash
   service sagewui-server start
   ```
   Open your browser and navigate accordingly with the host and port selected.
   Note that SageWui runs in secure mode, so `https://` must be used.

TODO
=====

* Break SageWui in more packages (WebApp, sage_server interface,
  model, controller, ...) useful to develop other independent software.
* Objects must be processed by the client for displaying. No more html
  representation of objects must be generated by the server. Establish
  a clear web server API, so that different web clients could be
  implemented.
* `interact` code refactor.
* Improve maintainability.
* Improve security, both in the WebApp and in the sage_server interactions.
* Improve scalability.
* ...


Notes
=====

* The dependencies for `sagewui` are: `twisted`, `flask`, `flask-autoindex`,
  `flask-babel`, `flask-themes2`, `future`, `smtpsend`, `pexpect`, `docutils`,
  `jsmin`, `pyopenssl`, `service_identity`, `appdirs`.
  All of them, but `smtpsend`
  which is in the source tree, are installable from pipy in an virtual
  python environment.

* Backward compatibility is not a goal, but at this moment this version
  can be used as a replacement of the current Sage Notebook.

* Some Notebook features could be removed.

* Removed features:

    * `send_mail` disabled under py3. Twisted.mail port needed.

    * Openid authentication.
