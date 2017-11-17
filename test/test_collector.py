# Copyright 2017 Luca Toscano
#                Filippo Giunchedi
#                Wikimedia Foundation
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

from collections import defaultdict
from druid_exporter.collector import DruidCollector


class TestDruidCollector(unittest.TestCase):

    def setUp(self):
        self.collector = DruidCollector(['coordinator', 'historical', 'broker'])
        self.metrics_without_labels = [
            'druid_historical_segment_scan_pending',
            'druid_historical_max_segment_bytes',
            'druid_coordinator_segment_overshadowed_count',
            'druid_broker_query_cache_numentries_count',
            'druid_broker_query_cache_sizebytes_count',
            'druid_broker_query_cache_hits_count',
            'druid_broker_query_cache_misses_count',
            'druid_broker_query_cache_evictions_count',
            'druid_broker_query_cache_timeouts_count',
            'druid_broker_query_cache_errors_count',
            'druid_historical_query_cache_numentries_count',
            'druid_historical_query_cache_sizebytes_count',
            'druid_historical_query_cache_hits_count',
            'druid_historical_query_cache_misses_count',
            'druid_historical_query_cache_evictions_count',
            'druid_historical_query_cache_timeouts_count',
            'druid_historical_query_cache_errors_count',
            'druid_exporter_datapoints_registered_count',
        ]

    def test_store_histogram(self):
        """Check that multiple datapoints modify the self.histograms data-structure
           in the expected way.
        """
        datapoint = {'feed': 'metrics', 'service': 'druid/historical', 'dataSource': 'test',
                     'metric': 'query/time', 'value': 42}
        self.collector.register_datapoint(datapoint)
        expected_struct = {
            'query/time': {
                'historical':
                    {'test': {'10': 0, '100': 1, '500': 1, '1000': 1, '10000': 1, 'inf': 1, 'sum': 42.0}}}}
        expected_result = defaultdict(lambda: {}, expected_struct)
        self.assertEqual(self.collector.histograms, expected_result)

        datapoint = {'feed': 'metrics', 'service': 'druid/historical', 'dataSource': 'test',
                     'metric': 'query/time', 'value': 5}
        self.collector.register_datapoint(datapoint)
        for bucket in expected_struct['query/time']['historical']['test']:
            if bucket != 'sum':
                expected_struct['query/time']['historical']['test'][bucket] += 1
            else:
                expected_struct['query/time']['historical']['test'][bucket] += 5
        self.assertEqual(self.collector.histograms, expected_result)

        datapoint = {'feed': 'metrics', 'service': 'druid/historical', 'dataSource': 'test2',
                     'metric': 'query/time', 'value': 5}
        self.collector.register_datapoint(datapoint)
        expected_result['query/time']['historical']['test2'] = {'10': 1, '100': 1, '500': 1, '1000': 1,
                                                                '10000': 1, 'inf': 1, 'sum': 5.0}
        self.assertEqual(self.collector.histograms, expected_result)

        datapoint = {'feed': 'metrics', 'service': 'druid/broker', 'dataSource': 'test',
                     'metric': 'query/time', 'value': 42}
        self.collector.register_datapoint(datapoint)
        expected_result['query/time']['broker'] = {
            'test': {'10': 0, '100': 1, '500': 1, '1000': 1,  '10000': 1, 'inf': 1, 'sum': 42.0}}
        self.assertEqual(self.collector.histograms, expected_result)

        datapoint = {'feed': 'metrics', 'service': 'druid/broker', 'dataSource': 'test',
                     'metric': 'query/time', 'value': 600}
        self.collector.register_datapoint(datapoint)
        for bucket in expected_struct['query/time']['broker']['test']:
            if bucket == 'sum':
                expected_struct['query/time']['broker']['test'][bucket] += 600
            elif 600 <= float(bucket):
                expected_struct['query/time']['broker']['test'][bucket] += 1
        self.assertEqual(self.collector.histograms, expected_result)

        datapoint = {'feed': 'metrics', 'service': 'druid/broker', 'dataSource': 'test2',
                     'metric': 'query/time', 'value': 5}
        self.collector.register_datapoint(datapoint)
        expected_result['query/time']['broker']['test2'] = {'10': 1, '100': 1, '500': 1, '1000': 1,
                                                            '10000': 1, 'inf': 1, 'sum': 5.0}
        self.assertEqual(self.collector.histograms, expected_result)

    def test_store_counter(self):
        """Check that multiple datapoints modify the self.counters data-structure
           in the expected way.
        """
        # First datapoint should add the missing layout to the data structure
        datapoint = {'feed': 'metrics', 'service': 'druid/historical', 'dataSource': 'test',
                     'metric': 'segment/used', 'tier': '_default_tier', 'value': 42}
        self.collector.register_datapoint(datapoint)
        expected_struct = {'segment/used': {'historical': {'_default_tier': {'test': 42.0}}}}
        expected_result = defaultdict(lambda: {}, expected_struct)
        self.assertEqual(self.collector.counters, expected_result)

        # Second datapoint for the same daemon but different metric should create
        # the missing layout without touching the rest.
        datapoint = {'feed': 'metrics', 'service': 'druid/historical', 'dataSource': 'test',
                     'metric': 'query/cache/total/evictions', 'value': 142}
        self.collector.register_datapoint(datapoint)
        expected_result['query/cache/total/evictions'] = {'historical': 142.0}
        self.assertEqual(self.collector.counters, expected_result)

        # Third datapoint for the same metric as used in the first test, should
        # add a key to the already existent dictionary.
        datapoint = {'feed': 'metrics', 'service': 'druid/historical', 'dataSource': 'test2',
                     'metric': 'segment/used', 'tier': '_default_tier', 'value': 543}
        self.collector.register_datapoint(datapoint)
        expected_result['segment/used']['historical']['_default_tier']['test2'] = 543.0
        self.assertEqual(self.collector.counters, expected_result)

        # Fourth datapoint for an already seen metric but differen broker
        datapoint = {'feed': 'metrics', 'service': 'druid/broker', 'dataSource': 'test',
                     'metric': 'segment/used', 'tier': '_default_tier', 'value': 111}
        self.collector.register_datapoint(datapoint)
        expected_result['segment/used']['broker'] = {'_default_tier': {'test': 111.0}}
        self.assertEqual(self.collector.counters, expected_result)

        # Fifth datapoint should override a pre-existent value
        datapoint = {'feed': 'metrics', 'service': 'druid/historical', 'dataSource': 'test',
                     'metric': 'segment/used', 'tier': '_default_tier', 'value': 11}
        self.collector.register_datapoint(datapoint)
        expected_result['segment/used']['historical']['_default_tier']['test'] = 11.0
        self.assertEqual(self.collector.counters, expected_result)

    def test_metrics_without_datapoints(self):
        """Whenever a Prometheus metric needs to be rendered, it may happen that
           no datapoints have been registered yet. In case that the metric do not
           have any label associated with it, 'nan' will be returned, otherwise
           the metric will not be rendered.
        """
        druid_metric_names = []
        for metric in self.collector.collect():
            if not metric.samples[0][0].startswith("druid_") or \
                    "scrape" in metric.samples[0][0]:
                continue
            self.assertEqual(len(metric.samples), 1)
            druid_metric_names.append(metric.samples[0][0])

        self.assertEqual(set(druid_metric_names), set(self.metrics_without_labels))

    def test_add_one_datapoint_for_each_metric(self):
        """Add one datapoint for each metric and make sure that they render correctly
           when running collect()
        """
        datapoints = [
            {"feed": "metrics",
             "timestamp": "2017-11-14T16:25:01.395Z",
             "service": "druid/broker",
             "host": "druid1001.eqiad.wmnet:8082",
             "metric": "query/time",
             "value": 10,
             "context": "{\"queryId\":\"b09649a1-a440-463f-8b7e-6b476cc22d45\",\"timeout\":40000}",
             "dataSource": "NavigationTiming",
             "duration": "PT94670899200S", "hasFilters": "false",
             "id": "b09649a1-a440-463f-8b7e-6b476cc22d45",
             "interval": ["0000-01-01T00:00:00.000Z/3000-01-01T00:00:00.000Z"],
             "remoteAddress": "10.64.53.26", "success": "true",
             "type": "timeBoundary", "version": "0.9.2"},

            {"feed": "metrics",
             "timestamp": "2017-11-14T16:25:01.395Z",
             "service": "druid/historical",
             "host": "druid1001.eqiad.wmnet:8082",
             "metric": "query/time",
             "value": 1,
             "context": "{\"queryId\":\"b09649a1-a440-463f-8b7e-6b476cc22d45\",\"timeout\":40000}",
             "dataSource": "NavigationTiming",
             "duration": "PT94670899200S", "hasFilters": "false",
             "id": "b09649a1-a440-463f-8b7e-6b476cc22d45",
             "interval": ["0000-01-01T00:00:00.000Z/3000-01-01T00:00:00.000Z"],
             "remoteAddress": "10.64.53.26", "success": "true",
             "type": "timeBoundary", "version": "0.9.2"},

            {"feed": "metrics", "timestamp": "2017-11-14T13:11:55.581Z",
             "service": "druid/broker", "host": "druid1001.eqiad.wmnet:8083",
             "metric": "query/bytes", "value": 1015,
             "context": "{\"bySegment\":true,\"finalize\":false,\"populateCache\":false,\
                          \"priority\":0,\"queryId\":\"d96c4b73-8e9b-4a43-821d-f194b4e134d7\",\
                          \"timeout\":40000}",
             "dataSource": "webrequest", "duration": "PT3600S",
             "hasFilters": "false", "id": "d96c4b73-8e9b-4a43-821d-f194b4e134d7",
             "interval": ["2017-11-14T11:00:00.000Z/2017-11-14T12:00:00.000Z"],
             "remoteAddress": "10.64.5.101", "type": "segmentMetadata",
             "version": "0.9.2"},

            {"feed": "metrics", "timestamp": "2017-11-14T13:11:55.581Z",
             "service": "druid/historical", "host": "druid1001.eqiad.wmnet:8083",
             "metric": "query/bytes", "value": 1015,
             "context": "{\"bySegment\":true,\"finalize\":false,\"populateCache\":false,\
                         \"priority\":0,\"queryId\":\"d96c4b73-8e9b-4a43-821d-f194b4e134d7\"\
                         ,\"timeout\":40000}",
             "dataSource": "webrequest", "duration": "PT3600S", "hasFilters": "false",
             "id": "d96c4b73-8e9b-4a43-821d-f194b4e134d7",
             "interval": ["2017-11-14T11:00:00.000Z/2017-11-14T12:00:00.000Z"],
             "remoteAddress": "10.64.5.101", "type": "segmentMetadata",
             "version": "0.9.2"},

            {"feed": "metrics", "timestamp": "2017-11-14T16:25:19.437Z",
             "service": "druid/broker", "host": "druid1001.eqiad.wmnet:8082",
             "metric": "query/node/time", "value": 15,
             "dataSource": "banner_activity_minutely",
             "duration": "PT3600S", "hasFilters": "false",
             "id": "39fbcfd5-d616-4313-9df0-5f2deb46ccb9",
             "interval": ["2017-11-14T16:00:00.000Z/2017-11-14T17:00:00.000Z"],
             "server": "druid1003.eqiad.wmnet:8103", "type": "timeBoundary",
             "version": "0.9.2"},

            {"feed": "metrics", "timestamp": "2017-11-14T16:25:19.437Z",
             "service": "druid/historical", "host": "druid1001.eqiad.wmnet:8082",
             "metric": "query/node/time", "value": 135,
             "dataSource": "banner_activity_minutely",
             "duration": "PT3600S", "hasFilters": "false",
             "id": "39fbcfd5-d616-4313-9df0-5f2deb46ccb9",
             "interval": ["2017-11-14T16:00:00.000Z/2017-11-14T17:00:00.000Z"],
             "server": "druid1003.eqiad.wmnet:8103", "type": "timeBoundary",
             "version": "0.9.2"},

            {"feed": "metrics", "timestamp": "2017-11-14T16:25:39.217Z",
             "service": "druid/broker", "host": "druid1001.eqiad.wmnet:8082",
             "metric": "query/cache/total/numEntries", "value": 5350},

            {"feed": "metrics", "timestamp": "2017-11-14T16:25:39.217Z",
             "service": "druid/historical", "host": "druid1001.eqiad.wmnet:8082",
             "metric": "query/cache/total/numEntries", "value": 5351},

            {"feed": "metrics", "timestamp": "2017-11-14T16:25:39.217Z",
             "service": "druid/broker", "host": "druid1001.eqiad.wmnet:8082",
             "metric": "query/cache/total/sizeBytes", "value": 23951932},

            {"feed": "metrics", "timestamp": "2017-11-14T16:25:39.217Z",
             "service": "druid/historical", "host": "druid1001.eqiad.wmnet:8082",
             "metric": "query/cache/total/sizeBytes", "value": 2391931},

            {"feed": "metrics",
             "timestamp": "2017-11-14T16:25:39.217Z", "service": "druid/broker",
             "host": "druid1001.eqiad.wmnet:8082",
             "metric": "query/cache/total/hits", "value": 358547},

            {"feed": "metrics",
             "timestamp": "2017-11-14T16:25:39.217Z", "service": "druid/historical",
             "host": "druid1001.eqiad.wmnet:8082",
             "metric": "query/cache/total/hits", "value": 358548},

            {"feed": "metrics", "timestamp": "2017-11-14T13:08:20.820Z",
             "service": "druid/broker", "host": "druid1001.eqiad.wmnet:8082",
             "metric": "query/cache/total/misses", "value": 188},

            {"feed": "metrics", "timestamp": "2017-11-14T13:08:20.820Z",
             "service": "druid/historical", "host": "druid1001.eqiad.wmnet:8083",
             "metric": "query/cache/total/misses", "value": 1887},

            {"feed": "metrics", "timestamp": "2017-11-14T13:08:20.820Z",
             "service": "druid/broker", "host": "druid1001.eqiad.wmnet:8083",
             "metric": "query/cache/total/evictions", "value": 0},

            {"feed": "metrics", "timestamp": "2017-11-14T13:08:20.820Z",
             "service": "druid/historical", "host": "druid1001.eqiad.wmnet:8083",
             "metric": "query/cache/total/evictions", "value": 0},

            {"feed": "metrics", "timestamp": "2017-11-14T16:25:39.217Z",
             "service": "druid/broker", "host": "druid1001.eqiad.wmnet:8082",
             "metric": "query/cache/total/timeouts", "value": 0},

            {"feed": "metrics", "timestamp": "2017-11-14T16:25:39.217Z",
             "service": "druid/historical", "host": "druid1001.eqiad.wmnet:8082",
             "metric": "query/cache/total/timeouts", "value": 0},

            {"feed": "metrics", "timestamp": "2017-11-14T16:25:39.217Z",
             "service": "druid/broker", "host": "druid1001.eqiad.wmnet:8082",
             "metric": "query/cache/total/errors", "value": 0},

            {"feed": "metrics", "timestamp": "2017-11-14T16:25:39.217Z",
             "service": "druid/historical", "host": "druid1001.eqiad.wmnet:8082",
             "metric": "query/cache/total/errors", "value": 0},

            {"feed": "metrics", "timestamp": "2017-11-14T13:07:20.823Z",
             "service": "druid/historical", "host": "druid1001.eqiad.wmnet:8083",
             "metric": "segment/count", "value": 41, "dataSource": "netflow",
             "priority": "0", "tier": "_default_tier"},

            {"feed": "metrics", "timestamp": "2017-11-14T12:14:53.697Z",
             "service": "druid/coordinator", "host": "druid1001.eqiad.wmnet: 8081",
             "metric": "segment/count", "value": 56, "dataSource": "netflow"},

            {"feed": "metrics", "timestamp": "2017-11-14T13:08:20.820Z",
             "service": "druid/historical", "host": "druid1001.eqiad.wmnet:8083",
             "metric": "segment/max", "value": 2748779069440},

            {"feed": "metrics", "timestamp": "2017-11-14T13:08:20.819Z",
             "service": "druid/historical", "host": "druid1001.eqiad.wmnet:8083",
             "metric": "segment/scan/pending", "value": 0},

            {"feed": "metrics", "timestamp": "2017-11-14T16:15:15.577Z",
             "service": "druid/coordinator",
             "host": "druid1001.eqiad.wmnet:8081", "metric": "segment/assigned/count",
             "value": 0.0, "tier": "_default_tier"},

            {"feed": "metrics",
             "timestamp": "2017-11-14T16:19:46.564Z",
             "service": "druid/coordinator", "host": "druid1001.eqiad.wmnet:8081",
             "metric": "segment/moved/count", "value": 0.0,
             "tier": "_default_tier"},

            {"feed": "metrics",
             "timestamp": "2017-11-14T16:19:46.564Z",
             "service": "druid/coordinator", "host": "druid1001.eqiad.wmnet:8081",
             "metric": "segment/dropped/count",
             "value": 0.0, "tier": "_default_tier"},

            {"feed": "metrics",
             "timestamp": "2017-11-14T16:19:46.564Z",
             "service": "druid/coordinator", "host": "druid1001.eqiad.wmnet:8081",
             "metric": "segment/deleted/count",
             "value": 0.0, "tier": "_default_tier"},

            {"feed": "metrics",
             "timestamp": "2017-11-14T16:19:46.564Z",
             "service": "druid/coordinator",
             "host": "druid1001.eqiad.wmnet:8081", "metric": "segment/unneeded/count",
             "value": 0.0, "tier": "_default_tier"},

            {"feed": "metrics",
             "timestamp": "2017-11-14T16:19:46.564Z",
             "service": "druid/coordinator", "host": "druid1001.eqiad.wmnet:8081",
             "metric": "segment/overShadowed/count", "value": 0.0},

            {"feed": "metrics",
             "timestamp": "2017-11-14T16:25:47.866Z",
             "service": "druid/coordinator", "host": "druid1001.eqiad.wmnet:8081",
             "metric": "segment/loadQueue/failed",
             "value": 0, "server": "druid1003.eqiad.wmnet:8083"},

            {"feed": "metrics",
             "timestamp": "2017-11-14T16:25:47.866Z",
             "service": "druid/coordinator",
             "host": "druid1001.eqiad.wmnet:8081",
             "metric": "segment/loadQueue/count",
             "value": 0, "server": "druid1003.eqiad.wmnet:8083"},

            {"feed": "metrics",
             "timestamp": "2017-11-14T16:25:47.866Z",
             "service": "druid/coordinator",
             "host": "druid1001.eqiad.wmnet:8081",
             "metric": "segment/dropQueue/count",
             "value": 0, "server": "druid1003.eqiad.wmnet:8083"},

            {"feed": "metrics",
             "timestamp": "2017-11-14T16:27:18.196Z",
             "service": "druid/coordinator",
             "host": "druid1001.eqiad.wmnet:8081",
             "metric": "segment/size", "value": 12351349,
             "dataSource": "unique_devices_per_project_family_daily"},

            {"feed": "metrics",
             "timestamp": "2017-11-14T16:27:18.189Z",
             "service": "druid/coordinator",
             "host": "druid1001.eqiad.wmnet:8081",
             "metric": "segment/unavailable/count",
             "value": 0, "dataSource": "unique_devices_per_domain_monthly"},

            {"feed": "metrics",
             "timestamp": "2017-11-14T16:27:48.310Z",
             "service": "druid/coordinator",
             "host": "druid1001.eqiad.wmnet:8081",
             "metric": "segment/underReplicated/count", "value": 0,
             "dataSource": "unique_devices_per_project_family_monthly",
             "tier": "_default_tier"}
        ]

        # The following datapoint registration batch should not generate
        # any exception (breaking the test).
        for datapoint in datapoints:
            self.collector.register_datapoint(datapoint)

        collected_metrics = 0
        for metric in self.collector.collect():
            # Metrics should not be returned if no sample is associated
            # (not even a 'nan')
            self.assertNotEqual(metric.samples, [])
            if metric.samples and metric.samples[0][0].startswith('druid_'):
                collected_metrics += 1

        # Number of metrics pushed using register_datapoint plus the ones
        # generated by the exporter for bookeeping,
        # like druid_exporter_datapoints_registered_count
        expected_druid_metrics_len = len(datapoints) + 1
        self.assertEqual(collected_metrics, expected_druid_metrics_len)

    def test_register_datapoints_count(self):
        datapoints = [

            {"feed": "metrics", "timestamp": "2017-11-14T16:25:39.217Z",
             "service": "druid/broker", "host": "druid1001.eqiad.wmnet:8082",
             "metric": "query/cache/total/numEntries", "value": 5350},

            {"feed": "metrics", "timestamp": "2017-11-14T16:25:39.217Z",
             "service": "druid/broker", "host": "druid1001.eqiad.wmnet:8082",
             "metric": "query/cache/total/sizeBytes", "value": 23951931},

            {"feed": "metrics",
             "timestamp": "2017-11-14T16:25:39.217Z", "service": "druid/broker",
             "host": "druid1001.eqiad.wmnet:8082",
             "metric": "query/cache/total/hits", "value": 358547},
        ]

        for datapoint in datapoints:
            self.collector.register_datapoint(datapoint)

        self.assertEqual(self.collector.datapoints_registered, 3)