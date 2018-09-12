from transitions import Machine
import datetime
import inspect

class JobStateMachine(object):
    """Load and manage Job state from serialized record"""
    states = ['created', 'running', 'failed', 'finished','validating',
    'validated', 'rejected', 'finalized', 'retired']
    transitions = [
        {'trigger': 'run', 'source': ['created', 'running'], 'dest': 'running'},
        {'trigger': 'fail', 'source': '*', 'dest': 'failed'},
        {'trigger': 'finish', 'source': ['running', 'finished'], 'dest': 'finished'},
        {'trigger': 'validate', 'source': 'finished', 'dest': 'validating'},
        {'trigger': 'validated', 'source': 'validating', 'dest': 'validated'},
        {'trigger': 'reject', 'source': 'validating', 'dest': 'rejected'},
        {'trigger': 'finalize', 'source': 'validated', 'dest': 'finalized'},
        {'trigger': 'retire', 'source': [
            'failed', 'finished', 'validating', 'validated', 'validated', 'finalized'], 'dest': 'retired'}
    ]

    def __init__(self, jobdef={}, state='created'):

        self.data = {}
        ts = current_time()
        for k in jobdef:
            self.data[k] = jobdef.get(k, None)
        if 'history' not in self.data:
            self.data['history'] = [{'CREATED': ts}]
        self.data['status'] = 'CREATED'
        self.data['last_event'] = 'CREATE'

        self.machine = Machine(
            model=self, states=JobStateMachine.states,
            transitions=JobStateMachine.transitions,
            initial=state,
            auto_transitions=False,
            after_state_change='update_history')

    def handle(self, event_name, opts={}):
        eventfn = event_name.lower()
        eventname = event_name.upper()
        vars(self)[eventfn](opts, event=eventname)
        return self

    def history(self):
        return self.data.get('history', [])

    def update_history(self, opts, event_name):
        ts = current_time()
        history_entry = {}
        history_entry[str(self.state).upper()] = ts
        self.data['history'].append(history_entry)
        self.data['status']: self.state
        self.data['last_event'] = event_name

def current_time():
    return datetime.datetime.utcnow()
