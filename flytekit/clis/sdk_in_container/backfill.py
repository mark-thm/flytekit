import typing
from datetime import datetime, timedelta

import click

from flytekit.clis.sdk_in_container.helpers import get_and_save_remote_with_click_context
from flytekit.clis.sdk_in_container.run import DateTimeType, DurationParamType

_backfill_help = """
Backfill command generates, registers a new workflow based on the input launchplan, that can be used to run an
automated backfill. The workflow can be managed using the Flyte UI and can be canceled, relaunched, recovered and
is implicitly cached. 
"""


def resolve_backfill_window(
    from_date: datetime = None,
    to_date: datetime = None,
    window: timedelta = None,
) -> typing.Tuple[datetime, datetime]:
    """
    Resolves the from_date -> to_date
    """
    if from_date and to_date and window:
        raise click.BadParameter("Cannot use from-date, to-date and duration. Use any two")
    if not (from_date or to_date):
        raise click.BadParameter(
            "One of following pairs are required -> (from-date, to-date) | (from-date, duration) | (to-date, duration)"
        )
    if from_date and to_date:
        pass
    elif not window:
        raise click.BadParameter("One of start-date and end-date are needed with duration")
    elif from_date:
        to_date = from_date + window
    else:
        from_date = to_date - window
    return from_date, to_date


@click.command("backfill", help=_backfill_help)
@click.option(
    "-p",
    "--project",
    required=False,
    type=str,
    default="flytesnacks",
    help="Project to register and run this workflow in",
)
@click.option(
    "-d",
    "--domain",
    required=False,
    type=str,
    default="development",
    help="Domain to register and run this workflow in",
)
@click.option(
    "-v",
    "--version",
    required=False,
    type=str,
    default=None,
    help="Version for the registered workflow. If not specified it is auto-derived using the start and end date",
)
@click.option(
    "-n",
    "--execution-name",
    required=False,
    type=str,
    default=None,
    help="Create a named execution for the backfill. This can prevent launching multiple executions.",
)
@click.option(
    "--dry-run",
    required=False,
    type=bool,
    is_flag=True,
    default=False,
    show_default=True,
    help="Just generate the workflow - do not register or execute",
)
@click.option(
    "--parallel/--serial",
    required=False,
    type=bool,
    is_flag=True,
    default=False,
    show_default=True,
    help="All backfill can be run in parallel - with max-parallelism",
)
@click.option(
    "--no-execute",
    required=False,
    type=bool,
    is_flag=True,
    default=False,
    show_default=True,
    help="Generate the workflow and register, do not execute",
)
@click.option(
    "--from-date",
    required=False,
    type=DateTimeType(),
    default=None,
    help="Date from which the backfill should begin. Start date is inclusive.",
)
@click.option(
    "--to-date",
    required=False,
    type=DateTimeType(),
    default=None,
    help="Date to which the backfill should run_until. End date is inclusive",
)
@click.option(
    "--backfill-window",
    required=False,
    type=DurationParamType(),
    default=None,
    help="Timedelta for number of days, minutes hours after the from-date or before the to-date to compute the"
    " backfills between. This is needed with from-date / to-date. Optional if both from-date and to-date are provided",
)
@click.argument(
    "launchplan",
    required=True,
    type=str,
    # help="Name of launchplan to be backfilled.",
)
@click.argument(
    "launchplan-version",
    required=False,
    type=str,
    default=None,
    # help="Version of the launchplan to be backfilled, if not specified, the latest version "
    #      "(by registration time) will be used",
)
@click.pass_context
def backfill(
    ctx: click.Context,
    project: str,
    domain: str,
    from_date: datetime,
    to_date: datetime,
    backfill_window: timedelta,
    launchplan: str,
    launchplan_version: str,
    dry_run: bool,
    no_execute: bool,
    parallel: bool,
    execution_name: str,
    version: str,
):
    from_date, to_date = resolve_backfill_window(from_date, to_date, backfill_window)
    remote = get_and_save_remote_with_click_context(ctx, project, domain)
    entity = remote.launch_backfill(
        project=project,
        domain=domain,
        from_date=from_date,
        to_date=to_date,
        launchplan=launchplan,
        launchplan_version=launchplan_version,
        execution_name=execution_name,
        version=version,
        dry_run=dry_run,
        no_execute=no_execute,
        parallel=parallel,
        output=click.secho,
    )
    if entity:
        console_url = remote.generate_console_url(entity)
        if no_execute:
            click.secho(f"\n No Execution mode: Workflow registered at {console_url}", fg="green")
        else:
            click.secho(f"\n Execution can be seen at {console_url} to see execution in the console.", fg="green")
