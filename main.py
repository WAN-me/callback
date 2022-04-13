#!/usr/bin/python3
import sbeaver
import requests
import os
from cfg import *

server = sbeaver.Server('0.0.0.0', 4050, False)

def send_msg(text):
   url_req = "https://api.telegram.org/bot" + tgTOKEN + "/sendMessage" + "?chat_id=" + tgchat_id + "&text=" + text 
   results = requests.get(url_req)
   print(results.json())

@server.sbind('/jira')
def jira(request):
    print(request.data)
    event = request.data.get('webhookEvent')
    print(event)

    issue = request.data['issue']
    task =f"""task: {issue['key']}\n
{issue['fields']['summary']}
тип задачи: {issue['fields'].get('issuetype',{}).get('name')}
проект: {issue['fields']['project']['name']}
исполнитель: {issue['fields'].get('assignee',{}).get('displayName')}
URL: https://wan-me.atlassian.net/browse/{issue['key']}"""
    if event == "comment_created":
        comment = request.data['comment']
        send_msg(f"{task}\n\n{comment['updateAuthor']['displayName']} оставил коментарий:\n{comment['body']}")
    elif event == "comment_deleted":
        comment = request.data['comment']
        send_msg(f"{task}\n\n{comment['updateAuthor']['displayName']} удилил коментарий:\n{comment['body']}")
    else:
        send_msg(f"{task}\n\nнеобработанное событие:\n{event}")
    return 200, request.dict
 
def do(r):
    print(r.dict)
    r.data.pop('secret')
    r.data.pop('event_id')
    requests.post(f'https://api.vk.com/method/messages.send?access_token={vkTOKEN}&v=5.131', {"random_id": 0, "peer_id": vkchat_id, 'message': str(r.data)})

@server.sbind('/vk')
def vk(request: sbeaver.Request):
    if request.data.get('secret') == secret:
        do(request)
        return 200, 'ok'
    print(request.__dict__)
    return 200, request.dict

@server.sbind('/github')
def github(request: sbeaver.Request):
    if request.headers.get("X-GitHub-Event") == 'push':
        repo = request.data['repository']['full_name']
        commits = '\n'.join([x['message'] for x in request.data['commits']])
        sender = request.data['sender']['login']
        send_msg(f'{sender} пушнул в {repo}:\n{commits}')
        if repo.split('/')[1] == "api":
            try:
                send_msg('Стерт тестов для api')
                os.system('sh root/apitest.sh &')
            except:
                pass
        return 200, 'ok'
    return 200, request.dict

server.start()