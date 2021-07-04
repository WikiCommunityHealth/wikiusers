from datetime import datetime
from json import dumps, loads
from pathlib import Path
from typing import Tuple, Union
import matplotlib.pyplot as plt

from wikiusers import settings
from wikiusers import logger

from .utils import Batcher, get_today_month_date, get_month_date_from_key, get_diff_in_months, get_no_ghost, get_key_from_date


class MonthlyDropoffOverActivePopulation:
    def __was_user_active(self, user: dict) -> None:
        per_month = user['activity']['per_month']
        for _, year_obj in per_month.items():
            for _, month_obj in year_obj.items():
                if month_obj['events']['total']['total'] >= self.active_per_month_thr:
                    return True

        return False

    def __process_user(self, user: dict) -> None:
        if self.__was_user_active(user):
            last_event: datetime = user['activity']['total']['last_event_timestamp']
            year_month = get_key_from_date(last_event)

            try:
                self.result[year_month] += 1
            except:
                self.result[year_month] = 1

    def __filter_for_threshold(self) -> None:
        today_month_date = get_today_month_date()

        for key in list(self.result.keys()):
            key_month_date = get_month_date_from_key(key)
            if get_diff_in_months(today_month_date, key_month_date) <= self.dropoff_month_threshold:
                self.result.pop(key)

    def __init__(
        self,
        lang: str = settings.DEFAULT_LANGUAGE,
        database: str = settings.DEFAULT_DATABASE,
        batch_size: str = settings.DEFAULT_BATCH_SIZE,
        metrics_path: Union[str, Path] = settings.DEFAULT_METRICS_DIR,
        dropoff_month_threshold: int = settings.DEFAULT_DROPOFF_MONTH_THRESHOLD,
        active_per_month_thr: int = settings.DEFAULT_ACTIVE_PER_MONTH_THRESHOLD
    ):
        self.lang = lang
        self.database = database
        self.batch_size = batch_size
        self.metrics_path = Path(metrics_path)
        self.dropoff_month_threshold = dropoff_month_threshold
        self.active_per_month_thr = active_per_month_thr
        self.path = self.metrics_path.joinpath(self.lang).joinpath(
            f'monthly_dropoff_with_threshold_{self.dropoff_month_threshold}_over_active_population_{self.active_per_month_thr}.json')

        query_filter = {**get_no_ghost()}
        self.batcher = Batcher(self.database, self.lang, self.batch_size, query_filter)
        self.result = {}

    def compute(self) -> None:
        logger.info(f'Start computing', lang=self.lang,
                    scope=f'MONTHLY DROPOFF THR {self.dropoff_month_threshold} OVER ACTIVE POP {self.active_per_month_thr}')
        for i, users_batch in enumerate(self.batcher):
            logger.debug(f'Computing batch {i}', lang=self.lang,
                         scope=f'MONTHLY DROPOFF THR {self.dropoff_month_threshold} OVER ACTIVE POP {self.active_per_month_thr}')
            for user in users_batch:
                self.__process_user(user)
        self.__filter_for_threshold()
        logger.succ(f'Finished computing', lang=self.lang,
                    scope=f'MONTHLY DROPOFF THR {self.dropoff_month_threshold} OVER ACTIVE POP {self.active_per_month_thr}')

    def save_json(self) -> None:
        logger.info(f'Start saving json', lang=self.lang,
                    scope=f'MONTHLY DROPOFF THR {self.dropoff_month_threshold} OVER ACTIVE POP {self.active_per_month_thr}')
        self.path.parent.mkdir(exist_ok=True, parents=True)
        json_text = dumps(self.result, sort_keys=True)
        with open(self.path, 'w') as out_file:
            out_file.write(json_text)
        logger.succ(f'Finished saving json', lang=self.lang,
                    scope=f'MONTHLY DROPOFF THR {self.dropoff_month_threshold} OVER ACTIVE POP {self.active_per_month_thr}')

    @staticmethod
    def show_graph(
        thresholds: list[Tuple[int, int]],
        lang: str = settings.DEFAULT_LANGUAGE,
        metrics_path: Union[str, Path] = settings.DEFAULT_METRICS_DIR
    ) -> None:
        fig, axs = plt.subplots(len(thresholds), 1, figsize=(18,18))

        metrics_path = Path(metrics_path)
        for i, thrs in enumerate(thresholds):
            diethr, actthr, color = thrs

            path = Path(metrics_path).joinpath(lang).joinpath(
                f'monthly_dropoff_with_threshold_{diethr}_over_active_population_{actthr}.json')
            with open(path) as input_file:
                raw_data = loads(input_file.read())
                x_values = [get_month_date_from_key(key) for key in raw_data.keys()]
                y_values = raw_data.values()
                axs[i].set_ylabel('Dropoff count')
                axs[i].plot(x_values, y_values, color=color)
                axs[i].set_title(f'At least a month with {actthr} events, died since {diethr} months')
        
        fig.savefig('result.png', bbox_inches='tight')

    @staticmethod
    def show_graph_perc(
        thresholds: list[Tuple[int, int]],
        lang: str = settings.DEFAULT_LANGUAGE,
        metrics_path: Union[str, Path] = settings.DEFAULT_METRICS_DIR
    ) -> None:
        fig, axs = plt.subplots(len(thresholds), 1, figsize=(18,18))

        metrics_path = Path(metrics_path)
        for i, thrs in enumerate(thresholds):
            diethr, actthr, color = thrs

            path = Path(metrics_path).joinpath(lang).joinpath(
                f'monthly_dropoff_with_threshold_{diethr}_over_active_population_{actthr}.json')
            with open(path) as input_file:
                raw_data = loads(input_file.read())
                x_values = [get_month_date_from_key(key) for key in raw_data.keys()]
                y_values = raw_data.values()
                axs[i].set_ylabel('Dropoff count')
                axs[i].plot(x_values, y_values, color=color)
                axs[i].set_title(f'At least a month with {actthr} events, died since {diethr} months')
                
        
        fig.savefig('result.png', bbox_inches='tight')
