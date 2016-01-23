teamcity-buildchain-stats
=========================

![Build Status](https://travis-ci.org/noroute/teamcity-buildchain-stats.svg?branch=master)

`teamcity-buildchain-stats` is a Python 2.6/2.7 library that provides
access to [TeamCity](https://www.jetbrains.com/teamcity/) 8 and 9
build chain runtime statistics.

Build chains have been a building block for TeamCity for a while now
but there is no built-in way to gather runtime statistics for whole
build chains.

`teamcity-buildchain-stats` uses the REST interface provided by
TeamCity to retrieve runtime statistics.

**WARNING**: The library is in an early alpha stage and interfaces are
undocumented and may change at will. I hope to be able to provide a
1.0 version with API stability, soon.
