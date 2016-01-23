#!/usr/bin/env python

import requests, json

###################

class BuildChainStatsGatherer():

    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Accept': 'application/json'})
        self.session.auth = (username, password)

        self.rest_base = self.base_url + "/httpAuth/app/rest"
        self.statistics_path = self.rest_base + "/builds/id:%i/statistics/"
        self.builds_of_a_configuration_path = self.rest_base + "/buildTypes/id:%s/builds/"
        self.build_chain_path = self.rest_base + "/builds?locator=snapshotDependency:(to:(id:%i),includeInitial:true),defaultFilter:false"

    def __retrieve_as_json(self, url):
        return self.session.get(url).json()

    def __successful_build_ids_of_configuration(self, configuration_id):
        builds = self.__retrieve_as_json(self.builds_of_a_configuration_path % configuration_id)
        successful_ids = [build[u'id'] for build in builds[u'build'] if (build[u'status'] == u'SUCCESS')]
        return successful_ids

    def __build_ids_of_chain(self, build_chain_id):
        json_form = self.__retrieve_as_json(self.build_chain_path % build_chain_id)
        return [build[u'id'] for build in json_form[u'build']]

    def __build_duration_for_id(self, build_id):
        json_form = self.__retrieve_as_json(self.statistics_path % build_id)
        return [v[u'value'] for v in json_form[u'property'] if (v[u'name'] == u'BuildDuration')][0]

    def total_build_duration_for_chain(self, build_chain_id):
        return sum([int(self.__build_duration_for_id(id)) for id in self.__build_ids_of_chain(build_chain_id)])

    def all_successful_build_chain_times(self, build_configuration_id):
        return [self.total_build_duration_for_chain(build_id) for build_id in self.__successful_build_ids_of_configuration(build_configuration_id)]
