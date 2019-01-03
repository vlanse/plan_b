from datetime import date
from typing import List


class Worker:

    def __init__(self, name: str, efficiency: float = 0.5, works_since: date = None):
        self._name = name
        self._efficiency = efficiency
        self._works_since = works_since

    @property
    def name(self) -> str:
        return self._name

    def efficiency(self, *_) -> float:
        return self._efficiency


class TBHWorker(Worker):

    TBH_WORKER_MAX_EFFICIENCY = 0.7
    TBH_WORKER_START_EFFICIENCY = 0.4

    def __init__(self, name: str, works_since: date):
        super().__init__(name, works_since=works_since)

    def efficiency(self, current_date: date = None) -> float:
        """
        calculate TBH worker efficiency based on experience (the more he works, the more is his efficiency)
        """
        return self.TBH_WORKER_START_EFFICIENCY + min(
            self.TBH_WORKER_MAX_EFFICIENCY - self.TBH_WORKER_START_EFFICIENCY,
            0.0015 * (current_date - self._works_since).days
        )


def make_worker(name, efficiency: float = 0.5, works_since: date = None) -> Worker:
    if 'TBH' in name:
        return TBHWorker(name, works_since=works_since)
    else:
        return Worker(name, efficiency=efficiency, works_since=works_since)


class Team:

    def __init__(self, name: str, members: List[Worker] = None):
        self.name = name
        self.members = members if members else []

    @staticmethod
    def is_dev():
        return False

    @staticmethod
    def is_qa():
        return False


class DevTeam(Team):

    def __init__(self, name: str, members: List[Worker] = None):
        super().__init__(name, members)

    @staticmethod
    def is_dev():
        return True


class QATeam(Team):

    def __init__(self, name: str, members: List[Worker] = None):
        super().__init__(name, members)

    @staticmethod
    def is_qa():
        return True


def make_team(name: str, workers: List[Worker] = None):
    if 'qa' in name.lower():
        return QATeam(name, workers)
    return DevTeam(name, workers)


def match_team_by_worker_name(worker_name: str, teams: List[Team]) -> Team:
    for team in teams:
        for worker in team.members:
            surname = worker.name.split('.')[-1].lower()
            if surname == worker_name.split('.')[-1].lower():
                return team
            if surname in worker_name:
                # workaround for cases when name is ipetrov instead of ivan.petrov
                return team
