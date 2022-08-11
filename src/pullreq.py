# encoding: utf-8
import os
import sys
import argparse
from workflow import Workflow3, ICON_WARNING, ICON_INFO, PasswordNotFound
from workflow.background import run_in_background, is_running
import mureq
import os
import base64

ORG_NAME = os.getenv('ORG_NAME')
USER_NAME = os.getenv('USER_NAME')
USER_TOKEN = os.getenv('USER_TOKEN')

log = None

ORG_NAME = os.getenv('ORG_NAME')

def get_pullreqs():
    
    userTokenBase64 = base64.b64encode('{}:{}'.format(USER_NAME, USER_TOKEN).encode('ascii')).decode('ascii')
    response = mureq.get('https://dev.azure.com/'+ORG_NAME+'/_apis/git/pullrequests?api-version=6.0', headers=({'Authorization': 'Basic '+userTokenBase64}))

    # throw an error if request failed
    # Workflow will catch this and show it to the user
    response.raise_for_status()

    # Parse the JSON returned and extract the pullreqs
    return response.json()["value"]

def search_for_pullreq(pullreq):
    """Generate a string search key for a pullreq"""
    elements = [str(pullreq['pullRequestId']), pullreq['title'], pullreq["repository"]["name"], pullreq["createdBy"]["displayName"]]
    return u' '.join(elements)


def main(wf):
    query = wf.args[0]
    pullreqs = get_pullreqs()

    # If script was passed a query, use it to filter pullreqs
    if query and pullreqs:
        pullreqs = wf.filter(query, pullreqs, key=search_for_pullreq, min_score=20)

    if not pullreqs:  # we have no data to show, so show a warning and stop
        wf.add_item('No Pull Requests found', icon=ICON_WARNING)
        wf.send_feedback()
        return 0

    # Loop through the returned posts and add an item for each to
    # the list of results for Alfred
    for pullreq in pullreqs:
        wf.add_item(title="{} - {}".format(pullreq["pullRequestId"], pullreq["title"]),
                    subtitle="{} ({})".format(pullreq["repository"]["name"], pullreq["createdBy"]["displayName"]),
                    arg="https://dev.azure.com/{}/{}/_git/{}/pullrequest/{}".format(ORG_NAME, pullreq['repository']['project']['name'], pullreq['repository']['name'], pullreq["pullRequestId"]),
                    valid=True,
                    icon=None,
                    uid=pullreq['pullRequestId'])

    # Send the results to Alfred as XML
    wf.send_feedback()

if __name__ == u"__main__":
    wf = Workflow3()
    log = wf.logger
    sys.exit(wf.run(main))