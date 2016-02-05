from tc_buildchain_stats.gatherer import *
import httpretty, re, pytest
from collections import namedtuple

date_fixture = "20160127T160502+0100"
datetime_fixture = dateutil.parser.parse(date_fixture)

# Need a pytest fixture to enable httpretty since @httpretty.activate cannot deal with test method arguments
@pytest.yield_fixture
def http_mock():
    httpretty.enable()
    yield
    httpretty.disable()

@pytest.fixture
def stats_gatherer():
    return BuildChainStatsGatherer("http://foo", "username", "password")

def given_a_build_chain(chain_id, builds):
    builds_list = ",".join(['{"id": %i, "buildTypeId": "%s"}' % (build.build_id,build.build_configuration_id) for build in builds])
    httpretty.register_uri(httpretty.GET, stats_gatherer().build_chain_path % chain_id, body='{"build": [%s]}' % builds_list)

    for build in builds:
        httpretty.register_uri(httpretty.GET, stats_gatherer().builds_path % build.build_id, body='{"id": %i, "startDate": "%s"}' % (build.build_id, build.start_date))
        httpretty.register_uri(httpretty.GET, stats_gatherer().statistics_path % build.build_id, body='{"property": [{"name": "BuildDuration", "value": %i }]}' % build.duration)

def test_total_build_duration_for_chain_returns_times_for_one_build(http_mock, stats_gatherer):
    given_a_build_chain(5, [BuildStat(1, None, 111, None)])

    assert stats_gatherer.total_build_duration_for_chain(5) == 111

def test_total_build_duration_for_chain_returns_times_for_two_builds(http_mock, stats_gatherer):
    given_a_build_chain(5,[BuildStat(1, None, 111, None),
                                BuildStat(2, None, 346, None)])

    assert stats_gatherer.total_build_duration_for_chain(5) == 457

def test_all_successful_build_chain_stats_for_one_successful_build_chain(http_mock, stats_gatherer):
    httpretty.register_uri(httpretty.GET, stats_gatherer.builds_of_a_configuration_path  % 'configuration_id', body='{"build": [{"id": 1, "status": "SUCCESS"},{"id": 2, "status": "FAILURE"}]}')

    given_a_build_chain(1,[BuildStat(1, "build_configuration1", 111, date_fixture),
                                BuildStat(2, "build_configuration2", 346, date_fixture)])

    assert stats_gatherer.all_successful_build_chain_stats('configuration_id') == [BuildChain(1,[BuildStat(1, 'build_configuration1', 111, datetime_fixture), BuildStat(2, 'build_configuration2', 346, datetime_fixture)])]

@httpretty.activate
def test_all_successful_build_chain_stats_for_two_successful_build_chains():
    stats_gatherer = BuildChainStatsGatherer("http://foo", "username", "password")
    httpretty.register_uri(httpretty.GET, stats_gatherer.builds_of_a_configuration_path  % 'configuration_id', body='{"build": [{"id": 1, "status": "SUCCESS"},{"id": 2, "status": "SUCCESS"}]}')

    build_chain_id_in_request = lambda q : re.search("snapshotDependency:\(to:\(id:(\d+)\)", str(q['locator'])).group(1)
    def build_chain_path_callback(request, uri, headers):
        build_chain_id = int(build_chain_id_in_request(request.querystring))
        return (200, headers, '{"build": [{"id": %(id)i1, "buildTypeId": "build_configuration%(id)i1"},{"id": %(id)i2, "buildTypeId": "build_configuration%(id)i2"}]}' % {'id' : build_chain_id})

    given_a_build_chain(1,[BuildStat(11, "build_configuration11", 11, date_fixture),
                                BuildStat(12, "build_configuration12", 12, date_fixture)])
    given_a_build_chain(2,[BuildStat(21, "build_configuration21", 21, date_fixture),
                                BuildStat(22, "build_configuration22", 22, date_fixture)])

    httpretty.register_uri(httpretty.GET, stats_gatherer.build_chain_path % 1, body=build_chain_path_callback)

    assert stats_gatherer.all_successful_build_chain_stats('configuration_id') == [BuildChain(1,[BuildStat(11, 'build_configuration11', 11, datetime_fixture), BuildStat(12, 'build_configuration12', 12, datetime_fixture)]),BuildChain(2,[BuildStat(21, 'build_configuration21', 21, datetime_fixture), BuildStat(22, 'build_configuration22', 22, datetime_fixture)])]

def test_build_times_for_chain_returns_one_BuildStat_with_values(http_mock, stats_gatherer):
    given_a_build_chain(1, [BuildStat(10, "configuration_id", 7, date_fixture)])

    assert stats_gatherer.build_stats_for_chain(1) == [BuildStat(10, 'configuration_id', 7, datetime_fixture)]

def test_build_times_for_chain_returns_list_with_two_BuildStats_on_two_step_chain(http_mock, stats_gatherer):
    given_a_build_chain(1, [BuildStat(10, "configuration_id", 7, date_fixture),
                                 BuildStat(11, "another_configuration_id", 34, date_fixture)])

    assert stats_gatherer.build_stats_for_chain(1) == [BuildStat(10, 'configuration_id', 7, datetime_fixture), BuildStat(11, 'another_configuration_id', 34, datetime_fixture)]
