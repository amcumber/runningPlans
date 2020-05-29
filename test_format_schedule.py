import format_schedule
import unittest
import os
import datetime
import pandas as pd

TEST_FILE_STR = """meta:
  info: Test INFO
  abbreviations:
    CU: Cool Down
    M: mile
    WU: Warm Up
    ar: active recovery
    e: easy
    mix: mix between easy and steady
  source: Test Source
  templateName: TEST_100M
  raceDay: 2.6
schedule:
  week 01:
    day 1: 4-6M e, core
    day 2: 15m WU, PYRAMID HILL (2,4,6,4,2) w equal recovery, 15m CD
    day 3: 6M e
    day 4: Rest -or- ar 35m
    day 5: 5-7M, core
    day 6: 10-12M
    day 7: 7-9M
    total: 45 M
  week 02:
    day 1: Rest
    day 2: 5M, core
    day 3: 15m WU, RLADDER (10,8,6,3,2,1) w 1/2t recovery, 15CD
    day 4: Rest, ar 40min
    day 5: 6-8M e, core
    day 6: 12-14M
    day 7: 10-12M
    total: 49 M
"""

MODULE_NAME = 'runningPlans'


class TestFormatSchedule(unittest.TestCase):
    def setUp(self) -> None:
        self.root = os.path.join(
            os.path.abspath(__file__).split(MODULE_NAME)[0],
            MODULE_NAME
        )

        self.debug_dir = os.path.join(self.root, 'debug')
        if not os.path.exists(self.debug_dir):
            os.mkdir(self.debug_dir)
        self.file = os.path.join(self.debug_dir, 'run_template.yaml')
        with open(self.file, 'w') as fh:
            fh.write(TEST_FILE_STR)
        self.fs = format_schedule.FormatSchedule(
            self.file, start=datetime.datetime.now()
        )

    def tearDown(self) -> None:
        if os.path.exists(self.file):
            os.remove(self.file)
        if os.path.exists(self.debug_dir):
            files = [os.path.join(self.debug_dir, file)
                     for file in os.listdir(self.debug_dir)]
            for file in files:
                if os.path.exists(file):
                    os.remove(file)
            os.rmdir(self.debug_dir)

    def test_init(self):
        self.assertEqual(len(self.fs.df), 8)
        self.assertEqual(len(self.fs.df.columns), 2)
        self.assertEqual(self.fs.df.iloc[3, 1], 'Rest, ar 40min')

    def test_read_yaml(self):
        df, meta = format_schedule.FormatSchedule.read_yaml(self.file)
        self.assertEqual(meta['info'], 'Test INFO')
        self.assertEqual(len(df), 8)
        self.assertEqual(len(df.columns), 2)
        self.assertEqual(df.iloc[2, 0], '6M e')

    def test_make_events(self):
        dates = pd.date_range(self.fs.start, periods=2, freq='W-MON')
        names = ['a', 'b']
        descriptions = ['desc1', 'desc2']
        cal = format_schedule.FormatSchedule.make_events(
            dates, names, descriptions
        )
        self.assertEqual(len(cal.events), 2)
        self.assertEqual(
            cal.events.pop().description.strip('1').strip('2'), 'desc'
        )

    def test_make_weekly_events(self):
        cal = format_schedule.FormatSchedule.make_weekly_events(
            self.fs.df, self.fs.start, self.fs.name
        )
        self.assertEqual(len(cal.events), 2)

    def test_make_daily_events(self):
        cal = format_schedule.FormatSchedule.make_daily_events(
            self.fs.df, self.fs.start, self.fs.name
        )
        self.assertEqual(len(cal.events), 14)

    def test_weekly(self):
        cal = self.fs.weekly
        self.assertEqual(len(cal.events), 2)

    def test_daily(self):
        cal = self.fs.daily
        self.assertEqual(len(cal.events), 14)

    def test_save_weekly(self):
        fn = 'debug/test.ics'
        self.fs.save_weekly(fn)
        with open(fn, 'r') as fh:
            cal = fh.readlines()
        self.assertGreater(len(cal), 0)

    def test_save_daily(self):
        fn = 'debug/test.ics'
        self.fs.save_daily(fn)
        with open(fn, 'r') as fh:
            cal = fh.readlines()
        self.assertGreater(len(cal), 0)


if __name__ == '__main__':
    unittest.main()
