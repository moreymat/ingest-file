import logging
from followthemoney import model
from servicelayer.worker import Worker
from servicelayer.jobs import JobStage as Stage, Task

from ingestors.manager import Manager

log = logging.getLogger(__name__)


class IngestWorker(Worker):
    """A long running task runner that uses Redis as a task queue"""

    def dispatch_next(self, task, entities):
        next_stage = task.context.get('next_stage')
        if next_stage is None:
            return
        stage = task.job.get_stage(next_stage)
        log.info("Sending %s entities to: %s", len(entities), next_stage)
        for entity_id in entities:
            stage.queue({'entity_id': entity_id}, task.context)

    def handle(self, task):
        manager = Manager(task.stage, task.context)
        entity = model.get_proxy(task.payload)
        log.debug("Ingest: %r", entity)
        manager.ingest_entity(entity)
        manager.close()
        self.dispatch_next(task, manager.emitted)
