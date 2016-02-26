#!/usr/bin/env python

"""A TeamCity >= 9.1 build chain runtime stats gatherer"""

import requests, json
import dateutil.parser
from collections import namedtuple

###################

__BuildStat = namedtuple("BuildStat", "build_id build_configuration_id duration start_date")
__BuildChain = namedtuple("BuildChain", "build_chain_id build_stats")
__BuildCycleTime = namedtuple("BuildCycleTime", "build_id build_configuration start_date cycle_time")

class BuildStat(__BuildStat):
    """DTO for a build step:
   stat.build_id
   stat.build_configuration_id # traditionally called buildTypeId in TeamCity
   stat.duration               # from the BuildDuration field in the REST interface
   stat.start_date             # start of build
    """
    pass

class BuildChain(__BuildChain):
    """DTO for a build chain:
   chain.build_chain_id
   stat.build_stats # list of BuildStats that belongs to the chain
    """
    pass

class BuildCycleTime(__BuildCycleTime):
    """DTO for build cycle times (difference between queue time and finish):
    bct.build_id
    bct.build_configuration
    bct.start_date # start of build
    bct.cycle_time # difference between queue time and finish in seconds
    """
    pass

def as_date(json_dict, field_name):
    return dateutil.parser.parse(json_dict[field_name])

class BuildChainStatsGatherer():

    """A BuildChainStatsGatherer connects to a TeamCity instance as a user that's
    able to read build statistics in the respective project and retrieves runtime
    statistics for whole build chains.

    The REST API used is the one described in https://confluence.jetbrains.com/display/TCD9/REST+API#RESTAPI-Snapshotdependencies

    Example:
       gatherer = BuildChainGatherer("https://my.teamcity.instance", "guest", "guest")

       stats = gatherer.build_stats_for_chain(12345)
       total_time = gatherer.total_build_duration_for_chain(12345)
    """

    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Accept': 'application/json'})
        self.session.auth = (username, password)

        self.rest_base = self.base_url + "/httpAuth/app/rest"
        self.statistics_path = self.rest_base + "/builds/id:%i/statistics/"
        self.builds_path = self.rest_base + "/builds/id:%i"
        self.builds_of_a_configuration_path = self.rest_base + "/buildTypes/id:%s/builds/"
        self.build_chain_path = self.rest_base + "/builds?locator=snapshotDependency:(to:(id:%i),includeInitial:true),defaultFilter:false"

    def __retrieve_as_json(self, url):
        return self.session.get(url).json()

    def __successful_build_chain_ids_of_configuration(self, configuration_id):
        builds = self.__retrieve_as_json(self.builds_of_a_configuration_path % configuration_id)
        return [
            build[u'id']
            for build in builds[u'build'] if (build[u'status'] == u'SUCCESS')
        ]

    def __build_ids_of_chain(self, build_chain_id):
        json_form = self.__retrieve_as_json(self.build_chain_path % build_chain_id)
        return [
            build[u'id']
            for build in json_form[u'build']
        ]

    def __build_duration_for_id(self, build_id):
        json_form = self.__retrieve_as_json(self.statistics_path % build_id)
        return self.__get_statistics_property_values(json_form, 'BuildDuration')[0]

    def __build_start_date_for_id(self, build_id):
        json_form = self.__retrieve_as_json(self.builds_path % build_id)
        return as_date(json_form, u'startDate')

    def __get_statistics_property_values(self, json_form, property_name):
        return [
            v[u'value']
            for v in json_form[u'property'] if (v[u'name'] == property_name)
        ]

    def total_build_duration_for_chain(self, build_chain_id):
        """Returns the total duration for one specific build chain run"""
        return sum([
            int(self.__build_duration_for_id(id))
            for id in self.__build_ids_of_chain(build_chain_id)
        ])

    def all_successful_build_chain_stats(self, build_configuration_id):
        return [
            BuildChain(
                build_chain_id,
                self.build_stats_for_chain(build_chain_id)
            ) for build_chain_id in self.__successful_build_chain_ids_of_configuration(build_configuration_id)
        ]

    def all_successful_build_chain_ids(self, build_configuration_id):
        """Returns the buildIds of all successful build chains for the given build configuration"""
        return [
            build_chain_id
            for build_chain_id in self.__successful_build_chain_ids_of_configuration(build_configuration_id)
        ]

    def build_cycle_time(self, build_id):
        """Returns a BuildCycleTime object for the given build"""
        json_form = self.__retrieve_as_json(self.builds_path % build_id)
        return BuildCycleTime(
            build_id,
            json_form[u'buildTypeId'],
            as_date(json_form, u'startDate'),
            (as_date(json_form, u'finishDate') - as_date(json_form, u'queuedDate')).seconds * 1000
        )

    def build_stats_for_chain(self, build_chain_id):
        """Returns a list of Build tuples for all elements in the build chain.

        This method allows insight into the runtime of each configuratio inside the build chain.
        """
        json_form = self.__retrieve_as_json(self.build_chain_path % build_chain_id)
        builds = [{'build_id': build[u'id'], 'configuration_id': build[u'buildTypeId']} for build in json_form[u'build']]

        return [
            BuildStat(
                build['build_id'],
                build['configuration_id'],
                self.__build_duration_for_id(build['build_id']),
                self.__build_start_date_for_id(build['build_id']))
            for build in builds
        ]
