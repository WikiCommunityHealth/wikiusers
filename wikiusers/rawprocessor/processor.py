from pathlib import Path
from typing import Optional, Tuple
from joblib import Parallel, delayed

from wikiusers import logger
from wikiusers.settings import DEFAULT_DATASETS_DIR, DEFAULT_N_PROCESSES, DEFAULT_LANGUAGE, DEFAULT_PARALLELIZE, DEFAULT_SYNC_DATA, DEFAULT_DATABASE
from wikiusers.dataloader import WhdtLoader
from wikiusers.rawprocessor.utils import Analyzer


class RawProcessor:

    def __init_loader(self) -> None:
        self.loader = WhdtLoader(self.datasets_dir, self.lang)
        if self.sync_data:
            self.loader.sync_wikies()

    def __get_tsv_month_and_year(self, tsv_file_name: str) -> Tuple[Optional[int], Optional[int]]:
        try:
            month = int(tsv_file_name.split('.')[::-1][1].split('-')[1])
        except:
            month = None

        try:
            year = int(tsv_file_name.split('.')[::-1][1])
        except:
            year = None

        return month, year

    def __init__(
        self,
        sync_data: bool = DEFAULT_SYNC_DATA,
        datasets_dir: Path = DEFAULT_DATASETS_DIR,
        lang: str = DEFAULT_LANGUAGE,
        parallelize: bool = DEFAULT_PARALLELIZE,
        n_processes: int = DEFAULT_N_PROCESSES,
        database: str = DEFAULT_DATABASE
    ):
        self.sync_data = sync_data
        self.datasets_dir = datasets_dir
        self.lang = lang
        self.parallelize = parallelize
        self.n_processes = n_processes
        self.database = database

        self.__init_loader()

    def _process_file(self, path: Path) -> None:
        logger.info(f'Starting processing {path}', lang=self.lang, scope='ANALYZER')
        month, year = self.__get_tsv_month_and_year(path.name())
        analyzer = Analyzer(path, month, year, self.lang, self.database)
        analyzer.analyze()
        logger.succ(f'Finished processing {path}', lang=self.lang, scope='ANALYZER')

    def process(self) -> None:
        datasets_paths = self.loader.get_tsv_files(self.lang)

        if self.parallelize:
            Parallel(n_jobs=self.n_processes)(
                delayed(self._process_file)(path)
                for path in datasets_paths
            )
        else:
            for path in datasets_paths:
                self._process_file(path)