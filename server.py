from flask import Flask, request, jsonify, send_file
import subprocess, pathlib

app = Flask(name)
ROOT = pathlib.Path.home() / "local_agent_data"
ROOT.mkdir(exist_ok=True)

@app.route("/run", methods=["POST"])
def run():
data = request.json or {}
cmd = data.get("cmd","")
workdir = data.get("workdir", str(ROOT))
for f in ["rm -rf","shutdown","reboot","su","dd","mkfs"]:
if f in cmd:
return jsonify({"error":"forbidden"}),400
proc = subprocess.run(cmd, shell=True, cwd=workdir, capture_output=True, text=True, timeout=30)
return jsonify({"returncode":proc.returncode,"stdout":proc.stdout,"stderr":proc.stderr})

@app.route("/ls")
def ls():
p = (ROOT / request.args.get("path","")).resolve()
if not str(p).startswith(str(ROOT.resolve())):
return jsonify({"entries":[]})
entries = [{"name":e.name,"is_dir":e.is_dir()} for e in p.iterdir()] if p.exists() else []
return jsonify({"entries":entries})

if name == "__main__":
app.run(host="127.0.0.1", port=8080)
