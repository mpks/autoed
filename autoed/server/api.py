from fastapi import APIRouter
from pydantic import BaseModel

from autoed.autoed import AutoedDaemon, kill_process_and_children

router = APIRouter(prefix='/api/v1')

autoed_daemon = AutoedDaemon()


class Watcher(BaseModel):
    path: str
    pid: int


@router.get('/watchers')
def get_watchers() -> list[Watcher]:
    return [
        {'path': d, 'pid': autoed_daemon.pids[d]}
        for d in autoed_daemon.directories.values()
    ]


class PID(BaseModel):
    pid: int


@router.get('/watchers/{path:path}/pid')
def get_watcher_pid(path: str) -> PID:
    return autoed_daemon.pids[path]


class WatcherSetup(BaseModel):
    path: str
    inotify: bool = False
    sleep_time: float = 30
    log_dir: str = ''
    slurm: bool = False


@router.post('/watcher')
def start_watcher(watcher_setup: WatcherSetup):
    autoed_daemon.watch(
        dirname=watcher_setup.path,
        use_inotify=watcher_setup.inotify,
        sleep_time=watcher_setup.sleep_time,
        log_dir=watcher_setup.log_dir,
        no_slurm=not watcher_setup.slurm,
    )


@router.delete('/watchers/{pid}')
def stop_watcher(pid: int):
    if pid in autoed_daemon.pids.values():
        kill_process_and_children(pid)
