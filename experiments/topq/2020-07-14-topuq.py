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

#SUITE = ['agricola-opt18-strips', 'airport', 'barman-opt11-strips', 'barman-opt14-strips', 'blocks', 'childsnack-opt14-strips', 'data-network-opt18-strips', 'depot', 'driverlog', 'elevators-opt08-strips', 'elevators-opt11-strips', 'floortile-opt11-strips', 'floortile-opt14-strips', 'freecell', 'ged-opt14-strips', 'grid', 'gripper', 'hiking-opt14-strips', 'logistics00', 'logistics98', 'miconic', 'movie', 'mprime', 'mystery', 'nomystery-opt11-strips', 'openstacks-opt08-strips', 'openstacks-opt11-strips', 'openstacks-opt14-strips', 'openstacks-strips', 'organic-synthesis-opt18-strips', 'organic-synthesis-split-opt18-strips', 'parcprinter-08-strips', 'parcprinter-opt11-strips', 'parking-opt11-strips', 'parking-opt14-strips', 'pegsol-08-strips', 'pegsol-opt11-strips', 'petri-net-alignment-opt18-strips', 'pipesworld-notankage', 'pipesworld-tankage', 'psr-small', 'rovers', 'satellite', 'scanalyzer-08-strips', 'scanalyzer-opt11-strips', 'snake-opt18-strips', 'sokoban-opt08-strips', 'sokoban-opt11-strips', 'spider-opt18-strips', 'storage', 'termes-opt18-strips', 'tetris-opt14-strips', 'tidybot-opt11-strips', 'tidybot-opt14-strips', 'tpp', 'transport-opt08-strips', 'transport-opt11-strips', 'transport-opt14-strips', 'trucks-strips', 'visitall-opt11-strips', 'visitall-opt14-strips', 'woodworking-opt08-strips', 'woodworking-opt11-strips', 'zenotravel']


#SUITE = ['gripper']
#SUITE = ['zenotravel:p01.pddl', 'zenotravel:p06.pddl']
#SUITE = ['zenotravel:p01.pddl', 'zenotravel:p06.pddl', 'logistics00:probLOGISTICS-4-0.pddl']

#SUITE = ['organic-synthesis-split-opt18-strips:p01.pddl']

import optimal_costs

SUITE = optimal_costs.suite()

ATTRIBUTES = ['coverage', 'found_plans', 'total_time', 'num_iterations', 'plan_files', 'all_plan_costs', 'min_plan_cost', 'max_plan_cost', 'actual_cost_bound']


config_name = 'topuq-sym' 
config_date = '2020-07-14'
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

def add_exp(exp_q):
    for task in suites.build_suite(BENCHMARKS_DIR, SUITE):
        run = exp.add_run()
        # Create symbolic links and aliases. This is optional. We
        # could also use absolute paths in add_command().
        run.add_resource('domain', task.domain_file, symlink=True)
        run.add_resource('problem', task.problem_file, symlink=True)
        # We could also use exp.add_resource().
        run.add_command(
            'run-planner',
            [planner_name, '{domain}', '{problem}',  '--search', "symq-bd(plan_selection=unordered(num_plans=10000),quality=%s)" % exp_q],
            time_limit=1740,
            memory_limit=2048, soft_stdout_limit=None, hard_stdout_limit=None)
        # AbsoluteReport needs the following properties:
        # 'domain', 'problem', 'algorithm', 'coverage'.
        run.set_property('domain', task.domain)
        run.set_property('problem', task.problem)
        run.set_property('algorithm', "topq-%s" % exp_q )
        run.set_property('q', exp_q)
        run.set_property('domain_file', task.domain_file)
        run.set_property('problem_file', task.problem_file)
        # Every run has to have a unique id in the form of a list.
        # The algorithm name is only really needed when there are
        # multiple algorithms.
        run.set_property('id', [config_name, task.domain, task.problem])

for q in [1.0, 1.05, 1.1, 1.2]:
    add_exp(q)


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
