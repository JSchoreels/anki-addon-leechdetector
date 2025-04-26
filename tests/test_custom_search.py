import unittest
import re

from leechdetector.browse_custom_search import RE_CUSTOMSEARCH, RE_CUSTOMSEARCH_GROUP_TYPE, RE_CUSTOMSEARCH_GROUP_ARGS


class CustomSearch(unittest.TestCase):
    test_string = [
        "leeches:all(dropcount=2, dropratio=0.2)",
        "leeches:active(dropcount=2, dropratio=0.2)",
        "leeches:recovering(dropcount=2, dropratio=0.2)",
        "leeches:recovering(dropcount=2, dropratio=0.2)",
        "leeches:recovered(dropcount=2, dropratio=0.2)",
        "leeches:recovered(dropcount=2, dropratio=0.2)",
        "leeches:active(dropcount=2, dropratio=0.200)",
        "leeches:active(dropcount=2, dropratio=0.2)",
        "leeches:active(dropcount=2, dropratio=0.2)",
        "leeches:active(dropcount=2, dropratio=0.20)"
    ]

    def test_regex_matching_leechestype(self):
        self.assertListEqual(
            list1=self.get_group_from_search(self.test_string, RE_CUSTOMSEARCH, RE_CUSTOMSEARCH_GROUP_TYPE),
            list2=['all', 'active', 'recovering', 'recovering', 'recovered', 'recovered', 'active', 'active', 'active',
                   'active']
        )

    def test_regex_matching_args_raw(self):
        self.assertListEqual(
            list1=self.get_group_from_search(self.test_string, RE_CUSTOMSEARCH, RE_CUSTOMSEARCH_GROUP_ARGS),
            list2=['dropcount=2, dropratio=0.2',
                   'dropcount=2, dropratio=0.2',
                   'dropcount=2, dropratio=0.2',
                   'dropcount=2, dropratio=0.2',
                   'dropcount=2, dropratio=0.2',
                   'dropcount=2, dropratio=0.2',
                   'dropcount=2, dropratio=0.200',
                   'dropcount=2, dropratio=0.2',
                   'dropcount=2, dropratio=0.2',
                   'dropcount=2, dropratio=0.20']
        )

    def get_group_from_search(self, to_match_list, pattern, group):
        return [re.search(pattern, to_match).group(group) for to_match in to_match_list]
