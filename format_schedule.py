import pandas as pd
import yaml
import ics
from typing import Tuple


class FormatSchedule(object):
    def __init__(self, file_, start=None):
        self.file_ = file_
        self.df, self.meta = self.read_yaml(file_)
        self.start = start
        self.name = self.meta['templateName']

    @staticmethod
    def read_yaml(file_: str) -> Tuple[pd.DataFrame, dict]:
        with open(file_, 'r') as fh:
            yml = yaml.safe_load(fh)

            # Clean up data
            df = pd.DataFrame(yml['schedule'])
            week_del = 'week'
            day_del = 'day'
            df.columns = [int(w) for w in
                          df.columns.str.replace(week_del, '').str.strip()]
            df.columns.name = week_del
            total = df.loc['total'].copy()
            df = df.drop('total')
            df.index = [int(d) for d in
                        df.index.str.replace(day_del, '').str.strip()]
            df.loc['total'] = total
            df.index.name = day_del

        return df, yml['meta']

    @staticmethod
    def make_events(dates, names, descriptions) -> ics.Calendar:
        cal = ics.Calendar()
        for date, name, desc in zip(dates, names, descriptions):
            e = ics.Event(name=name, begin=date, description=desc)
            e.make_all_day()
            cal.events.add(e)
        return cal

    @classmethod
    def make_weekly_events(cls, df: pd.DataFrame,
                           start: str,
                           title: str) -> ics.Calendar:
        n_weeks = len(df.T)
        dates = pd.date_range(start, periods=n_weeks, freq='W-Mon')
        names = [title.replace('M', '.').replace('km', '.') + str(week)
                 for week in df.columns]
        descriptions = [df[week].to_csv() for week in df.columns]
        return cls.make_events(dates, names, descriptions)

    @classmethod
    def make_daily_events(cls,
                          df: pd.DataFrame,
                          start: str,
                          title: str) -> ics.Calendar:
        if 'total' in df.index:
            df = df.drop('total')
        n_days = len(df.T) * 7
        dates = pd.date_range(start, periods=n_days, freq='D')
        names = [f'{title.replace("M", ".")}{week}.{day}'
                 for week in df.columns
                 for day in df.index]
        descriptions = [df.loc[day, week]
                        for week in df.columns
                        for day in df.index]
        return cls.make_events(dates, names, descriptions)

    @property
    def weekly(self) -> ics.Calendar:
        """
        :return: ical object with weekly events based on saved parameters
        """
        return self.make_weekly_events(
            self.df, start=self.start, title=self.name
        )

    @property
    def daily(self) -> ics.Calendar:
        """
        :return: ical object with daily events based on saved parameters
        """
        return self.make_daily_events(
            self.df, start=self.start, title=self.name
        )

    def save_weekly(self, file_) -> None:
        """
        Save ical object at specified location using saved parameters
        :param file_: file location to be saved
        :return: None
        """
        with open(file_, 'w') as fh:
            fh.writelines(self.weekly)
        return None

    def save_daily(self, file_) -> None:
        """
        Save ical object at specified location using saved parameters
        :param file_: file location to be saved
        :return: None
        """
        with open(file_, 'w') as fh:
            fh.writelines(self.daily)
        return None

    def __repr__(self):
        return f'{self.__class__.__name__}({self.file_})'
