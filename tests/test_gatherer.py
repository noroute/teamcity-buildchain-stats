from tc_buildchain_stats.gatherer import *
import httpretty, re, pytest

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

def test_total_build_duration_for_chain_returns_times_for_one_build(http_mock, stats_gatherer):
    httpretty.register_uri(httpretty.GET, stats_gatherer.build_chain_path % 5, body='{"build": [{"id": 27}]}')
    httpretty.register_uri(httpretty.GET, stats_gatherer.statistics_path % 27, body='{"property": [{"name": "BuildDuration", "value": 111}]}')

    assert stats_gatherer.total_build_duration_for_chain(5) == 111

def test_total_build_duration_for_chain_returns_times_for_two_builds(http_mock, stats_gatherer):
    httpretty.register_uri(httpretty.GET, stats_gatherer.build_chain_path % 5, body='{"build": [{"id": 27},{"id": 98}]}')
    httpretty.register_uri(httpretty.GET, stats_gatherer.statistics_path % 27, body='{"property": [{"name": "BuildDuration", "value": 111}]}')
    httpretty.register_uri(httpretty.GET, stats_gatherer.statistics_path % 98, body='{"property": [{"name": "BuildDuration", "value": 346}]}')

    assert stats_gatherer.total_build_duration_for_chain(5) == 457

def test_all_successful_build_chain_stats_for_one_successful_build_chain(http_mock, stats_gatherer):
    httpretty.register_uri(httpretty.GET, stats_gatherer.builds_of_a_configuration_path  % 'configuration_id', body='{"build": [{"id": 1, "status": "SUCCESS"},{"id": 2, "status": "FAILURE"}]}')

    httpretty.register_uri(httpretty.GET, stats_gatherer.build_chain_path % 1, body='{"build": [{"id": 11, "buildTypeId": "build_configuration11"},{"id": 12, "buildTypeId": "build_configuration12"}]}')

    httpretty.register_uri(httpretty.GET, stats_gatherer.builds_path % 11, body='{"id": 11, "startDate": "%s"}' % date_fixture)
    httpretty.register_uri(httpretty.GET, stats_gatherer.statistics_path % 11, body='{"property": [{"name": "BuildDuration", "value": 111}]}')
    httpretty.register_uri(httpretty.GET, stats_gatherer.builds_path % 12, body='{"id": 12, "startDate": "%s"}' % date_fixture)
    httpretty.register_uri(httpretty.GET, stats_gatherer.statistics_path % 12, body='{"property": [{"name": "BuildDuration", "value": 346}]}')

    assert stats_gatherer.all_successful_build_chain_stats('configuration_id') == [BuildChain(1,[BuildStat(11, 'build_configuration11', 111, datetime_fixture), BuildStat(12, 'build_configuration12', 346, datetime_fixture)])]

@httpretty.activate
def test_all_successful_build_chain_stats_for_two_successful_build_chains():
    stats_gatherer = BuildChainStatsGatherer("http://foo", "username", "password")
    httpretty.register_uri(httpretty.GET, stats_gatherer.builds_of_a_configuration_path  % 'configuration_id', body='{"build": [{"id": 1, "status": "SUCCESS"},{"id": 2, "status": "SUCCESS"}]}')

    build_chain_id_in_request = lambda q : re.search("snapshotDependency:\(to:\(id:(\d+)\)", str(q['locator'])).group(1)
    def build_chain_path_callback(request, uri, headers):
        build_chain_id = int(build_chain_id_in_request(request.querystring))
        return (200, headers, '{"build": [{"id": %(id)i1, "buildTypeId": "build_configuration%(id)i1"},{"id": %(id)i2, "buildTypeId": "build_configuration%(id)i2"}]}' % {'id' : build_chain_id})

    httpretty.register_uri(httpretty.GET, stats_gatherer.build_chain_path % 1, body=build_chain_path_callback)

    httpretty.register_uri(httpretty.GET, stats_gatherer.builds_path % 11, body='{"id": 11, "startDate": "%s"}' % date_fixture)
    httpretty.register_uri(httpretty.GET, stats_gatherer.statistics_path % 11, body='{"property": [{"name": "BuildDuration", "value": 11}]}')
    httpretty.register_uri(httpretty.GET, stats_gatherer.builds_path % 12, body='{"id": 12, "startDate": "%s"}' % date_fixture)
    httpretty.register_uri(httpretty.GET, stats_gatherer.statistics_path % 12, body='{"property": [{"name": "BuildDuration", "value": 12}]}')
    httpretty.register_uri(httpretty.GET, stats_gatherer.builds_path % 21, body='{"id": 21, "startDate": "%s"}' % date_fixture)
    httpretty.register_uri(httpretty.GET, stats_gatherer.statistics_path % 21, body='{"property": [{"name": "BuildDuration", "value": 21}]}')
    httpretty.register_uri(httpretty.GET, stats_gatherer.builds_path % 22, body='{"id": 22, "startDate": "%s"}' % date_fixture)
    httpretty.register_uri(httpretty.GET, stats_gatherer.statistics_path % 22, body='{"property": [{"name": "BuildDuration", "value": 22}]}')

    assert stats_gatherer.all_successful_build_chain_stats('configuration_id') == [BuildChain(1,[BuildStat(11, 'build_configuration11', 11, datetime_fixture), BuildStat(12, 'build_configuration12', 12, datetime_fixture)]),BuildChain(2,[BuildStat(21, 'build_configuration21', 21, datetime_fixture), BuildStat(22, 'build_configuration22', 22, datetime_fixture)])]

def test_build_times_for_chain_returns_one_BuildStat_with_values(http_mock, stats_gatherer):
    httpretty.register_uri(httpretty.GET, stats_gatherer.build_chain_path % 1, body='{"build": [{"id": 10, "buildTypeId": "configuration_id"}]}')
    httpretty.register_uri(httpretty.GET, stats_gatherer.builds_path % 10, body='{"id": 10, "startDate": "%s"}' % date_fixture)
    httpretty.register_uri(httpretty.GET, stats_gatherer.statistics_path % 10, body='{"property": [{"name": "BuildDuration", "value": 7}]}')

    assert stats_gatherer.build_stats_for_chain(1) == [BuildStat(10, 'configuration_id', 7, datetime_fixture)]

def test_build_times_for_chain_returns_list_with_two_BuildStats_on_two_step_chain(http_mock, stats_gatherer):
    httpretty.register_uri(httpretty.GET, stats_gatherer.build_chain_path % 1, body='{"build": [{"id": 10, "buildTypeId": "configuration_id"},{"id": 11, "buildTypeId": "another_configuration_id"}]}')
    httpretty.register_uri(httpretty.GET, stats_gatherer.builds_path % 10, body='{"id": 10, "startDate": "%s"}' % date_fixture)
    httpretty.register_uri(httpretty.GET, stats_gatherer.statistics_path % 10, body='{"property": [{"name": "BuildDuration", "value": 7}]}')
    httpretty.register_uri(httpretty.GET, stats_gatherer.builds_path % 11, body='{"id": 11, "startDate": "%s"}' % date_fixture)
    httpretty.register_uri(httpretty.GET, stats_gatherer.statistics_path % 11, body='{"property": [{"name": "BuildDuration", "value": 34}]}')

    assert stats_gatherer.build_stats_for_chain(1) == [BuildStat(10, 'configuration_id', 7, datetime_fixture), BuildStat(11, 'another_configuration_id', 34, datetime_fixture)]
