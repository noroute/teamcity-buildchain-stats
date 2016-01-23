from tc_buildchain_stats.gatherer import *
import httpretty

@httpretty.activate
def test_total_build_duration_for_chain_returns_times_for_one_build():
    gatherer = BuildChainStatsGatherer("http://foo", "username", "password")

    httpretty.register_uri(httpretty.GET, gatherer.build_chain_path % 5, body='{"build": [{"id": 27}]}')
    httpretty.register_uri(httpretty.GET, gatherer.statistics_path % 27, body='{"property": [{"name": "BuildDuration", "value": 111}]}')

    assert gatherer.total_build_duration_for_chain(5) == 111

@httpretty.activate
def test_total_build_duration_for_chain_returns_times_for_two_builds():
    gatherer = BuildChainStatsGatherer("http://foo", "username", "password")

    httpretty.register_uri(httpretty.GET, gatherer.build_chain_path % 5, body='{"build": [{"id": 27},{"id": 98}]}')
    httpretty.register_uri(httpretty.GET, gatherer.statistics_path % 27, body='{"property": [{"name": "BuildDuration", "value": 111}]}')
    httpretty.register_uri(httpretty.GET, gatherer.statistics_path % 98, body='{"property": [{"name": "BuildDuration", "value": 346}]}')

    assert gatherer.total_build_duration_for_chain(5) == 457

@httpretty.activate
def test_all_successful_build_chain_times_for_one_successful_build_chain():
    gatherer = BuildChainStatsGatherer("http://foo", "username", "password")

    httpretty.register_uri(httpretty.GET, gatherer.builds_of_a_configuration_path  % 'configuration_id', body='{"build": [{"id": 1, "status": "SUCCESS"},{"id": 2, "status": "FAILURE"}]}')

    httpretty.register_uri(httpretty.GET, gatherer.build_chain_path % 1, body='{"build": [{"id": 27},{"id": 98}]}')

    httpretty.register_uri(httpretty.GET, gatherer.statistics_path % 27, body='{"property": [{"name": "BuildDuration", "value": 111}]}')
    httpretty.register_uri(httpretty.GET, gatherer.statistics_path % 98, body='{"property": [{"name": "BuildDuration", "value": 346}]}')

    assert gatherer.all_successful_build_chain_times('configuration_id') == [457]

@httpretty.activate
def test_all_successful_build_chain_times_for_two_successful_build_chains():
    gatherer = BuildChainStatsGatherer("http://foo", "username", "password")

    httpretty.register_uri(httpretty.GET, gatherer.builds_of_a_configuration_path  % 'configuration_id', body='{"build": [{"id": 1, "status": "SUCCESS"},{"id": 2, "status": "SUCCESS"}]}')

    httpretty.register_uri(httpretty.GET, gatherer.build_chain_path % 1, body='{"build": [{"id": 10},{"id": 11}]}')

    httpretty.register_uri(httpretty.GET, gatherer.statistics_path % 10, body='{"property": [{"name": "BuildDuration", "value": 7}]}')
    httpretty.register_uri(httpretty.GET, gatherer.statistics_path % 11, body='{"property": [{"name": "BuildDuration", "value": 19}]}')

    httpretty.register_uri(httpretty.GET, gatherer.build_chain_path % 2, body='{"build": [{"id": 20},{"id": 21}]}')

    httpretty.register_uri(httpretty.GET, gatherer.statistics_path % 20, body='{"property": [{"name": "BuildDuration", "value": 41}]}')
    httpretty.register_uri(httpretty.GET, gatherer.statistics_path % 21, body='{"property": [{"name": "BuildDuration", "value": 89}]}')

    assert gatherer.all_successful_build_chain_times('configuration_id') == [130, 26]

@httpretty.activate
def test_build_times_for_chain_returns_one_BuildStat_with_values():
    gatherer = BuildChainStatsGatherer("http://foo", "username", "password")

    httpretty.register_uri(httpretty.GET, gatherer.build_chain_path % 1, body='{"build": [{"id": 10, "buildTypeId": "configuration_id"}]}')
    httpretty.register_uri(httpretty.GET, gatherer.statistics_path % 10, body='{"property": [{"name": "BuildDuration", "value": 7}]}')

    assert gatherer.build_stats_for_chain(1) == [BuildStat(10, 'configuration_id', 7)]

@httpretty.activate
def test_build_times_for_chain_returns_list_with_two_BuildStats_on_two_step_chain():
    gatherer = BuildChainStatsGatherer("http://foo", "username", "password")

    httpretty.register_uri(httpretty.GET, gatherer.build_chain_path % 1, body='{"build": [{"id": 10, "buildTypeId": "configuration_id"},{"id": 11, "buildTypeId": "another_configuration_id"}]}')
    httpretty.register_uri(httpretty.GET, gatherer.statistics_path % 10, body='{"property": [{"name": "BuildDuration", "value": 7}]}')
    httpretty.register_uri(httpretty.GET, gatherer.statistics_path % 11, body='{"property": [{"name": "BuildDuration", "value": 34}]}')

    assert gatherer.build_stats_for_chain(1) == [BuildStat(10, 'configuration_id', 7), BuildStat(11, 'another_configuration_id', 34)]
