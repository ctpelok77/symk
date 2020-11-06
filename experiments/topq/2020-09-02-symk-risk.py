#! /usr/bin/env python

import os, sys
import subprocess

from lab.experiment import Experiment

# In the future, these modules should live in a separate
# "planning" or "solver" package.
from downward import suites
from lab.environments import LocalEnvironment, GridEnvironment
from lab.reports import Attribute, arithmetic_mean, geometric_mean
from downward.reports.absolute import AbsoluteReport
from downward.reports.compare import ComparativeReport
from lab import tools


BENCHMARKS_DIR = os.environ["DOWNWARD_BENCHMARKS"]


class OracleGridEngineEnvironment(GridEnvironment):
    """Abstract base class for grid environments using OGE."""
    # Must be overridden in derived classes.
    DEFAULT_QUEUE = None

    # Can be overridden in derived classes.
    JOB_HEADER_TEMPLATE_FILE = 'oge-job-header'
    RUN_JOB_BODY_TEMPLATE_FILE = 'oge-run-job-body'
    STEP_JOB_BODY_TEMPLATE_FILE = 'oge-step-job-body'
    DEFAULT_PRIORITY = 0
    HOST_RESTRICTIONS = {}
    DEFAULT_HOST_RESTRICTION = ""

    def __init__(self, queue=None, priority=None, host_restriction=None, **kwargs):
        """
        *queue* must be a valid queue name on the grid.

        *priority* must be in the range [-1023, 0] where 0 is the
        highest priority. If you're a superuser the value can be in the
        range [-1023, 1024].

        See :py:class:`~lab.environments.GridEnvironment` for inherited
        parameters.

        """
        GridEnvironment.__init__(self, **kwargs)

        if queue is None:
            queue = self.DEFAULT_QUEUE
        if priority is None:
            priority = self.DEFAULT_PRIORITY
        if host_restriction is None:
            host_restriction = self.DEFAULT_HOST_RESTRICTION

        self.queue = queue
        self.priority = priority
        assert self.priority in xrange(-1023, 1024 + 1)
        self.host_spec = self._get_host_spec(host_restriction)

    # TODO: Don't forget to remove the run-dispatcher file once we get rid
    #       of OracleGridEngineEnvironment.
    def _write_run_dispatcher(self):
        dispatcher_content = tools.fill_template(
            'run-dispatcher.py',
            task_order=self._get_task_order())
        self.exp.add_new_file(
            '', 'run-dispatcher.py', dispatcher_content, permissions=0o755)

    def write_main_script(self):
        # The main script is written by the run_steps() method.
        self._write_run_dispatcher()

    def _get_job_params(self, step, is_last):
        job_params = GridEnvironment._get_job_params(self, step, is_last)
        job_params['priority'] = self.priority
        job_params['queue'] = self.queue
        job_params['host_spec'] = self.host_spec
        job_params['notification'] = '#$ -m n'
        job_params['errfile'] = 'driver.err'

        if is_last and self.email:
            if is_run_step(step):
                logging.warning(
                    "The cluster sends mails per run, not per step."
                    " Since the last of the submitted steps would send"
                    " too many mails, we disable the notification."
                    " We recommend submitting the 'run' step together"
                    " with the 'fetch' step.")
            else:
                job_params['notification'] = '#$ -M %s\n#$ -m e' % self.email

        return job_params

    def _get_host_spec(self, host_restriction):
        if not host_restriction:
            return '## (not used)'
        else:
            hosts = self.HOST_RESTRICTIONS[host_restriction]
            return '#$ -l hostname="%s"' % '|'.join(hosts)

    def _submit_job(self, job_name, job_file, job_dir, dependency=None):
        submit = ['qsub']
        if dependency:
            submit.extend(['-hold_jid', dependency])
        submit.append(job_file)
        tools.run_command(submit, cwd=job_dir)
        return job_name

def get_script():
    """Get file name of main script."""
    return os.path.abspath(sys.argv[0])


def get_script_dir():
    """Get directory of main script.

    Usually a relative directory (depends on how it was called by the user.)"""
    return os.path.dirname(get_script())


def get_base_dir():
    """Assume that this script always lives in the base dir of the infrastructure."""
    return os.path.abspath(get_script_dir())

def get_path_level_up(path):
    return os.path.dirname(path)

def get_planner_dir():
    return get_path_level_up(get_path_level_up(get_base_dir()))

## Suite for optimal

BENCHMARKS_DIR = '/storage/US1J6721/risk-pddl'
SUITE = ['power_and_utilities_generated', 'covid_generated_pddl']
SUITE = ['covid_082720', 'p_and_u_082720']
ATTRIBUTES = ['coverage', 'found_plans', 'total_time', 'num_iterations', 'plan_files', 'all_plan_costs', 'min_plan_cost', 'max_plan_cost', 'actual_cost_bound']


config_name = 'topk-sym' 
config_date = '2020-09-02'
report_name = '%s-%s' % (config_name,config_date)


planner_name = os.path.join(get_planner_dir(), 'fast-downward.py')
   
ENV = OracleGridEngineEnvironment(queue='all.q')

# Create a new experiment.
exp = Experiment(environment=ENV)
# Add built-in parsers.
#exp.add_parser(exp.LAB_STATIC_PROPERTIES_PARSER)
#exp.add_parser(exp.LAB_DRIVER_PARSER)
#exp.add_parser(exp.EXITCODE_PARSER)
#exp.add_parser(exp.TRANSLATOR_PARSER)
#exp.add_parser(exp.SINGLE_SEARCH_PARSER)
#exp.add_parser(exp.PLANNER_PARSER)

# Add custom parser.
#exp.add_parser('topq-iterative-parser.py')
exp.add_parser('parser.py')

def add_exp():
    for task in suites.build_suite(BENCHMARKS_DIR, SUITE):
        run = exp.add_run()
        # Create symbolic links and aliases. This is optional. We
        # could also use absolute paths in add_command().
        run.add_resource('domain', task.domain_file, symlink=True)
        run.add_resource('problem', task.problem_file, symlink=True)
        # We could also use exp.add_resource().
        run.add_command(
            'run-planner',
            [planner_name, '{domain}', '{problem}',  '--search', "symq-bd(plan_selection=top_k(num_plans=1000),quality=infinity)"],
            time_limit=1800,
            memory_limit=2048, soft_stdout_limit=None, hard_stdout_limit=None)
        # AbsoluteReport needs the following properties:
        # 'domain', 'problem', 'algorithm', 'coverage'.
        run.set_property('domain', task.domain)
        run.set_property('problem', task.problem)
        run.set_property('algorithm', "topk-sym"  )
        run.set_property('domain_file', task.domain_file)
        run.set_property('problem_file', task.problem_file)
        # Every run has to have a unique id in the form of a list.
        # The algorithm name is only really needed when there are
        # multiple algorithms.
        run.set_property('id', [config_name, task.domain, task.problem])

add_exp()

# Add step that writes experiment files to disk.
exp.add_step('build', exp.build)

# Add step that executes all runs.
exp.add_step('start', exp.start_runs)

# Add step that collects properties from run directories and
# writes them to *-eval/properties.
exp.add_fetcher(name='fetch')

exp.add_parse_again_step()

# Make a report.
exp.add_report(
    AbsoluteReport(attributes=ATTRIBUTES),
    outfile='%s.html' % report_name)

# Parse the commandline and run the specified steps.
exp.run_steps()
