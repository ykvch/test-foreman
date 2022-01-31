Test Foreman
===
Orchestrate parallel test runs on multiple workers

A pytest plugin to have multiple pytest processes (aka nodes, workers) split
test set into parts and run those parts in parallel.

> NOTE: nose version is also available

Goals:
---
* auto-balancing
* distributed
* automatic splitting
* dynamic node attaching/detaching
* re-run ability
* simplicity
* control server via CLI (done via `nc <foreman-host> -p <port>`)

Flow and architecture:
---
* Start foreman server (separate process with command `foreman`).
* Start multiple nodes (pytest processes) with exact same parameters
  (same set of tests, same `--foreman-addr` value).
* Before running each test a node (pytest process) informs a foreman server
  its intention with `take <test-name>` request.
* A foreman (server keeps track of every `take` request previously made to it.
* A foreman server allows taking only tests that were NOT taken previously by
  some other node.
* This way earch node skips over to next test if current one has been taken.


Flow example:
---
1. Run server to coordinate pytest nodes:
  ```
  foreman -i localhost -p 12345
  ```
1. Run multiple pytest instances with the same command line:
  ```
  pytest --with-foreman --foreman-addr localhost:12345 path/to/test_*.py
  ...repeat command in multiple consoles
  ```
1. Observe the pyetst runners share and balance the workload.
1. Wait all pytest processes get complete.
1. Connect to foreman to see what's up:
  ```
  nc localhost -p 12345
  ls
  ...node names and their taken tests printed here
  ```
1. Stop the foreman server:
  ```
  nc localhost -p 12345
  thank you
  ...server stops, connection dropped
  ```