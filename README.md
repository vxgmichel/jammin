jammin
======

An ssh server for competitive programming

**work in progress**


Installation
------------

```shell
# Using pip (requires pip3 and setuptools)
$ pip install -e .

# Using pipenv
$ pipenv install

# Using pipenv developer mode
$ pipenv install --dev
```

Example usage
-------------

Running the server:

```shell
# Regular run
$ jammin example/standard-sum/runner.py example/standard-sum/solver.py
Serving TCP interface on port 8000...
Serving SSH interface on port 8022...

# Using pipenv
$ pipenv run jammin example/standard-sum/runner.py example/standard-sum/solver.py
Serving TCP interface on port 8000...
Serving SSH interface on port 8022...
```

Connecting to the console:

```shell
# Using ssh
$ ssh <server-host> -p 8022

# Using tcp (rlwrap + netcat)
$ rlwrap nc localhost 8000
<press enter once>
```

Getting an authentification token:

```shell
# Using ssh
$ TOKEN=`ssh <server-host> -p8022 claim <username>`
$ echo $TOKEN
89c59d8b7c

# Using tcp
$ TOKEN=`echo claim <username> | nc <server-host> 8000`
$ echo $TOKEN
6be4bd1bce
```

Automated submission using ssh:

```shell
# Using the provided helper
$ misc/sshsubmit.sh <server-host> 8022 $TOKEN example/standard-sum/fastsolver.py
[...] # Input and output data displayed on stderr
..........
[01:06:10] [00.003] 10 / 10

# Using a pipe-line of standard tools
$ ssh <server-host> -p8022 request $TOKEN | # Send request command
  tee data.in.tmp |                         # Save input data
  example/standard-sum/fastsolver.py |      # Run the solver
  tee data.out.tmp |                        # Save output data
  ssh <server-host> -p8022 submit $TOKEN    # Send submit command
..........
[01:06:20] [00.003] 10 / 10
```

Automated submission using tcp:

```shell
# Using the provided helper
$ misc/submit.sh <server-host> 8000 $TOKEN example/standard-sum/fastsolver.py
[...] # Input and output data displayed on stderr
..........
[01:06:30] [00.003] 10 / 10

# Using a pipe-line of standard tools
$ echo request $TOKEN |                 # Craft request command
  nc <server-host> 8000 |               # Send request command
  tee data.in.tmp |                     # Save input data
  example/standard-sum/fastsolver.py |  # Run the solver
  tee data.out.tmp |                    # Save output data
  { echo submit $TOKEN; cat; } |        # Craft submit command
  nc <server-host> 8000                 # Send submit command
..........
[01:06:40] [00.003] 10 / 10
```

Web console
-----------

```shell
# Add ssh server key to known hosts
$ ssh-keyscan -t rsa -p 8022 localhost >> ~/.ssh/known_hosts

# Using ttyd
$ ttyd -p 8080 -B ssh localhost -p 8022

# Make it available on default http port
$ sudo iptables -t nat -I OUTPUT -p tcp -d 127.0.0.1 --dport 80 -j REDIRECT --to-ports 8080
```
