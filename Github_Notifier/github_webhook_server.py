from flask import Flask, request, abort
import hmac
import hashlib
import json
import subprocess
import os

from creds import GITHUB_WEBHOOK_SECRET

app = Flask(__name__)

def verify_signature(secret, request):
    signature = request.headers.get('X-Hub-Signature-256')
    if signature is None:
        return False
    sha_name, signature = signature.split('=')
    if sha_name != 'sha256':
        return False
    mac = hmac.new(secret.encode(), msg=request.data, digestmod=hashlib.sha256)
    return hmac.compare_digest(mac.hexdigest(), signature)

def show_vbs_notification(title: str, message: str):
    try:
        # Replace double quotes to avoid parsing errors
        title = title.replace('"', "'")
        message = message.replace('"', "'")

        vbs_path = os.path.join(os.path.dirname(__file__), "notify.vbs")
        if not os.path.isfile(vbs_path):
            print(f"notify.vbs not found at {vbs_path}")
            return

        subprocess.Popen(["wscript", vbs_path, title, message], shell=False)
    except Exception as e:
        print(f"Failed to launch VBS notification: {e}")

@app.route('/github-webhook', methods=['POST'])
def github_webhook():
    if not verify_signature(GITHUB_WEBHOOK_SECRET, request):
        abort(403)

    event = request.headers.get('X-GitHub-Event', 'ping')
    if event == 'ping':
        return json.dumps({'msg': 'pong'})

    if event != 'push':
        return '', 204  # We only handle push events

    payload = request.json
    repo_name = payload.get('repository', {}).get('full_name', 'unknown repo')
    pusher = payload.get('pusher', {}).get('name', 'unknown pusher')
    ref = payload.get('ref', '')
    branch = ref.split('/')[-1] if ref else 'unknown branch'
    commits = payload.get('commits', [])

    commit_msgs = "\n".join([f"- {c.get('message', '').strip()}" for c in commits])

    title = f"GitHub: {repo_name} ({branch})"
    message = f"Pusher: {pusher}\nCommits:\n{commit_msgs}"

    show_vbs_notification(title, message)
    return '', 200
