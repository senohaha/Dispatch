from zope.interface import Interface


class IPoller(Interface):
    """A component that polls for projects that need to run"""

    def poll():
        """Called periodically to poll for projects"""

    def next():
        """Return the next message.

        It should return a Deferred which will get fired when there is a new
        project that needs to run, or already fired if there was a project
        waiting to run already.

        The message is a dict containing (at least):
        * the name of the project to be run in the '_project' key
        * the name of the spider to be run in the '_spider' key
        * a unique identifier for this run in the `_job` key
        This message will be passed later to IEnvironment.get_environment().
        """

    def update_projects():
        """Called when projects may have changed, to refresh the available
        projects"""


