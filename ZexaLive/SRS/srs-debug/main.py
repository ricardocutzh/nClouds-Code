import sys
import json
import secrets
import requests
import os
import time
import boto3
from flask import Flask, request, jsonify, render_template_string
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

app = Flask(__name__)

# --- CONFIGURATION ---
SRS_API_URL = "http://srs:1985/api/v1"
HLS_BASE_PATH = "/tmp/hls"

# AWS Configuration from Environment Variables
S3_BUCKET = os.environ.get('S3_BUCKET')
s3_client = boto3.client(
    's3',
    region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
)

# In-Memory Database
data_store = {
    "live": {"room1": "default-key-123"}
}

class HlsSyncHandler(FileSystemEventHandler):
    """
    Watches /tmp/hls and syncs any new or modified file to S3.
    """
    def on_modified(self, event):
        if not event.is_directory:
            self.sync_to_s3(event.src_path)

    def on_created(self, event):
        if not event.is_directory:
            self.sync_to_s3(event.src_path)

    def sync_to_s3(self, local_path):
        # We only care about .ts and .m3u8 files
        if not local_path.endswith(('.ts', '.m3u8')):
            return

        # Calculate S3 Key: /tmp/hls/app/stream/file.ts -> app/stream/file.ts
        relative_path = os.path.relpath(local_path, HLS_BASE_PATH)
        
        try:
            # Set specific metadata based on file type
            extra_args = {}
            if local_path.endswith('.m3u8'):
                extra_args = {
                    'ContentType': 'application/vnd.apple.mpegurl',
                    'CacheControl': 'no-cache, no-store, must-revalidate'
                }
            elif local_path.endswith('.ts'):
                extra_args = {'ContentType': 'video/MP2T'}

            # Small delay to ensure SRS has finished writing the file
            time.sleep(0.5) 
            
            s3_client.upload_file(local_path, S3_BUCKET, relative_path, ExtraArgs=extra_args)
            print(f"☁️  S3 SYNC: {relative_path}", file=sys.stderr)
        except Exception as e:
            print(f"❌ S3 Sync Error ({relative_path}): {str(e)}", file=sys.stderr)

def start_watcher():
    """Initializes the background thread for file watching"""
    # Ensure directory exists before watching
    if not os.path.exists(HLS_BASE_PATH):
        os.makedirs(HLS_BASE_PATH, exist_ok=True)
        
    observer = Observer()
    observer.schedule(HlsSyncHandler(), HLS_BASE_PATH, recursive=True)
    observer.start()
    print(f"👀 Watcher started on {HLS_BASE_PATH}", file=sys.stderr)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# --- UNIFIED DASHBOARD UI (Tailwind CSS) ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>SRS Central Hub</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-gray-100 p-6 font-sans">
    <div class="max-w-7xl mx-auto">
        <header class="flex justify-between items-center mb-8 bg-gray-800 p-6 rounded-2xl border border-gray-700 shadow-2xl">
            <div>
                <h1 class="text-2xl font-bold text-blue-500 tracking-tighter uppercase">SRS Central Hub</h1>
                <p class="text-[10px] text-gray-500 font-mono">Status: Connected to SRS Engine</p>
            </div>
            <div class="flex gap-8">
                <div class="text-center">
                    <p class="text-gray-500 text-[10px] uppercase mb-1">CPU Load</p>
                    <p id="stat-cpu" class="font-mono text-blue-400 font-bold text-xl">--</p>
                </div>
                <div class="text-center">
                    <p class="text-gray-500 text-[10px] uppercase mb-1">Memory</p>
                    <p id="stat-mem" class="font-mono text-green-400 font-bold text-xl">--</p>
                </div>
                <div class="text-center">
                    <p class="text-gray-500 text-[10px] uppercase mb-1">Live Feeds</p>
                    <p id="stat-streams" class="font-mono text-purple-400 font-bold text-xl">0</p>
                </div>
            </div>
        </header>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <div class="lg:col-span-5 space-y-6">
                <div class="bg-gray-800 p-6 rounded-2xl border border-gray-700 shadow-xl">
                    <h2 class="text-lg font-bold mb-4 text-blue-300 flex items-center">
                        <span class="mr-2">📁</span> Create Application Path
                    </h2>
                    <div class="flex gap-2">
                        <input type="text" id="newAppName" placeholder="App Name (e.g. nClouds)" 
                               class="bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 w-full text-sm focus:border-blue-500 outline-none transition-all">
                        <button type="button" onclick="createApp()" 
                                class="bg-blue-600 hover:bg-blue-500 px-6 py-2 rounded-lg text-sm font-bold transition-all">Create</button>
                    </div>
                </div>

                <div id="managementContainer" class="space-y-4">
                    </div>
            </div>

            <div class="lg:col-span-7">
                <div class="bg-gray-800 rounded-2xl border border-gray-700 shadow-xl overflow-hidden">
                    <div class="p-4 bg-gray-700/30 border-b border-gray-700 flex justify-between items-center">
                        <h2 class="text-lg font-bold">Real-time Traffic</h2>
                        <span class="flex items-center text-[10px] font-bold text-red-500 uppercase tracking-widest">
                            <span class="animate-ping inline-flex h-2 w-2 rounded-full bg-red-400 opacity-75 mr-2"></span>
                            Live Monitoring
                        </span>
                    </div>
                    <div class="overflow-x-auto">
                        <table class="w-full text-left">
                            <thead class="bg-gray-900/50 text-gray-500 text-[10px] uppercase tracking-widest">
                                <tr>
                                    <th class="p-4">Stream Path</th>
                                    <th class="p-4">Resolution</th>
                                    <th class="p-4">Bitrate</th>
                                    <th class="p-4 text-right">Viewers</th>
                                </tr>
                            </thead>
                            <tbody id="monitoringList" class="divide-y divide-gray-700">
                                <tr><td colspan="4" class="p-10 text-center text-gray-600 italic text-sm">Waiting for incoming streams...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // --- 1. MONITORING POLLING ---
        async function pollStats() {
            try {
                // Fetch System Health
                const statsRes = await fetch('/proxy/summaries');
                const stats = await statsRes.json();
                if(stats.data && stats.data.self) {
                    document.getElementById('stat-cpu').innerText = stats.data.self.cpu_percent.toFixed(1) + '%';
                    document.getElementById('stat-mem').innerText = (stats.data.self.mem_kbyte/1024).toFixed(0) + 'MB';
                }

                // Fetch Active Streams
                const streamRes = await fetch('/proxy/streams');
                const streamData = await streamRes.json();
                renderMonitoring(streamData.streams || []);
            } catch(e) { console.error("SRS Stats fetch failed"); }
        }

        function renderMonitoring(streams) {
            document.getElementById('stat-streams').innerText = streams.length;
            const list = document.getElementById('monitoringList');
            if(streams.length === 0) {
                list.innerHTML = '<tr><td colspan="4" class="p-10 text-center text-gray-600 italic text-sm">No active streams in the pipeline.</td></tr>';
                return;
            }
            list.innerHTML = streams.map(s => `
                <tr class="hover:bg-gray-700/20 transition-all">
                    <td class="p-4 border-b border-gray-700/50">
                        <div class="font-bold text-blue-400 text-sm">/${s.app}/${s.name}</div>
                        <div class="text-[9px] text-gray-500 font-mono uppercase tracking-tighter">ID: ${s.id}</div>
                    </td>
                    <td class="p-4 border-b border-gray-700/50">
                        <span class="bg-gray-900 px-2 py-1 rounded text-[10px] border border-gray-700">
                            ${s.video ? s.video.width+'x'+s.video.height : 'AUDIO ONLY'}
                        </span>
                    </td>
                    <td class="p-4 border-b border-gray-700/50 text-green-400 font-mono text-xs font-bold">
                        ${s.kbps.recv_30s} <span class="text-[10px] text-gray-600 uppercase">kbps</span>
                    </td>
                    <td class="p-4 border-b border-gray-700/50 text-right font-black text-sm">
                        ${s.clients}
                    </td>
                </tr>
            `).join('');
        }

        // --- 2. MANAGEMENT UI ---
        async function refreshManagement() {
            try {
                const res = await fetch('/api/data');
                const store = await res.json();
                renderManagement(store);
            } catch(e) { console.error("Management fetch failed"); }
        }

        function renderManagement(store) {
            const container = document.getElementById('managementContainer');
            container.innerHTML = '';
            Object.entries(store).forEach(([appName, rooms]) => {
                const card = document.createElement('div');
                card.className = "bg-gray-800 rounded-2xl border border-gray-700 overflow-hidden shadow-lg border-l-4 border-l-blue-500";
                card.innerHTML = `
                    <div class="p-4 bg-gray-700/20 flex justify-between items-center border-b border-gray-700">
                        <span class="text-sm font-black text-blue-400 uppercase tracking-tighter">APP PATH: /${appName}</span>
                        <button type="button" onclick="deleteApp('${appName}')" class="text-red-500 hover:text-red-400 text-[10px] font-bold">DELETE APP</button>
                    </div>
                    <div class="p-4 space-y-4">
                        <div class="flex gap-2">
                            <input type="text" id="room-input-${appName}" placeholder="New Room Name" 
                                   class="bg-gray-900 border border-gray-700 rounded-lg px-3 py-1 text-xs w-full outline-none focus:border-blue-500">
                            <button type="button" onclick="addRoom('${appName}')" 
                                    class="bg-green-600 hover:bg-green-500 px-4 rounded-lg text-[10px] font-bold uppercase transition-all">Add</button>
                        </div>
                        <div class="space-y-2">
                            ${Object.entries(rooms).map(([room, key]) => `
                                <div class="bg-gray-900 p-3 rounded-lg border border-gray-700 group relative">
                                    <div class="flex justify-between items-center mb-1">
                                        <span class="font-bold text-xs text-gray-200">${room}</span>
                                        <button type="button" onclick="deleteRoom('${appName}','${room}')" class="text-gray-600 hover:text-red-500 transition-colors">
                                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="6 18L18 6M6 6l12 12"></path></svg>
                                        </button>
                                    </div>
                                    <div class="mt-2 space-y-1">
                                        <p class="text-[9px] text-gray-500 uppercase tracking-widest font-bold">OBS Stream Key:</p>
                                        <code class="block text-[10px] bg-black/50 p-2 rounded text-green-400 break-all border border-green-900/30 font-mono">
                                            ${room}?key=${key}
                                        </code>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
                container.appendChild(card);
            });
        }

        // --- 3. CRUD ACTIONS (NO REFRESH) ---
        async function createApp() {
            const input = document.getElementById('newAppName');
            const name = input.value.trim();
            if(!name) return;
            await fetch('/api/apps', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ name })
            });
            input.value = '';
            refreshManagement();
        }

        async function addRoom(app) {
            const input = document.getElementById(`room-input-${app}`);
            const name = input.value.trim();
            if(!name) return;
            await fetch(`/api/apps/${app}/rooms`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ name })
            });
            input.value = '';
            refreshManagement();
        }

        async function deleteApp(n) { if(confirm(`Delete App /${n}?`)) { await fetch(`/api/apps/${n}`, {method:'DELETE'}); refreshManagement(); } }
        async function deleteRoom(a, r) { await fetch(`/api/apps/${a}/rooms/${r}`, {method:'DELETE'}); refreshManagement(); }

        // Intervals
        setInterval(pollStats, 2000);   // Frequent stats
        
        // Initial Loads
        refreshManagement();
        pollStats();
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML)

# --- 1. SRS API PROXY ---
@app.route('/proxy/<endpoint>')
def srs_proxy(endpoint):
    try:
        r = requests.get(f"{SRS_API_URL}/{endpoint}")
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- 2. MANAGEMENT API (Keep your existing routes) ---
@app.route('/api/data')
def get_data(): return jsonify(data_store)

@app.route('/api/apps', methods=['POST'])
def create_app():
    name = request.json.get('name')
    if name and name not in data_store: data_store[name] = {}
    return "OK", 200

@app.route('/api/apps/<name>', methods=['DELETE'])
def delete_app(name):
    data_store.pop(name, None)
    return "OK", 200

@app.route('/api/apps/<app_name>/rooms', methods=['POST'])
def create_room(app_name):
    room_name = request.json.get('name')
    if app_name in data_store and room_name:
        data_store[app_name][room_name] = secrets.token_hex(6)
    return "OK", 200

@app.route('/api/apps/<app_name>/rooms/<room_name>', methods=['DELETE'])
def delete_room(app_name, room_name):
    if app_name in data_store: data_store[app_name].pop(room_name, None)
    return "OK", 200

# --- 3. SRS AUTHENTICATION & VOD FINALIZATION ---
@app.route('/on_publish', methods=['POST'])
def on_publish():
    payload = request.json
    req_app, req_room, param = payload.get('app'), payload.get('stream'), payload.get('param', '')
    provided_key = param.split('key=')[1].split('&')[0] if 'key=' in param else None

    if req_app in data_store and req_room in data_store[req_app]:
        if data_store[req_app][req_room] == provided_key:
            print(f"✅ GRANTED: {req_app}/{req_room}", file=sys.stderr)
            return "0", 200
    
    print(f"❌ DENIED: {req_app}/{req_room}", file=sys.stderr)
    return "1", 403

@app.route('/on_unpublish', methods=['POST'])
def on_unpublish():
    """Finalizes the HLS playlist and uploads the VOD manifest to S3"""
    payload = request.json
    app_name = payload.get('app')
    stream_name = payload.get('stream')
    
    local_m3u8 = f"{HLS_BASE_PATH}/{app_name}/{stream_name}/index.m3u8"
    s3_key = f"{app_name}/{stream_name}/index.m3u8"

    print(f"⏹️ OFFLINE: {app_name}/{stream_name}. Finalizing VOD...", file=sys.stderr)

    # 1. Wait briefly for SRS to flush the last segment to disk
    time.sleep(5)

    if os.path.exists(local_m3u8):
        try:
            # 2. Append VOD tags locally
            with open(local_m3u8, 'r') as f:
                content = f.read()
            
            if "#EXT-X-ENDLIST" not in content:
                with open(local_m3u8, 'a') as f:
                    f.write("\n#EXT-X-PLAYLIST-TYPE:VOD\n")
                    f.write("#EXT-X-ENDLIST\n")
                print(f"📝 Appended VOD tags to {local_m3u8}", file=sys.stderr)

            # 3. Upload the finalized manifest to S3
            # We set Cache-Control to ensure browsers/CloudFront don't cache the old "live" version
            s3_client.upload_file(
                local_m3u8, S3_BUCKET, s3_key,
                ExtraArgs={'ContentType': 'application/vnd.apple.mpegurl', 'CacheControl': 'no-cache, no-store, must-revalidate'}
            )
            print(f"🚀 Finalized VOD uploaded to S3: s3://{S3_BUCKET}/{s3_key}", file=sys.stderr)

        except Exception as e:
            print(f"❌ Error finalizing VOD: {str(e)}", file=sys.stderr)
    else:
        print(f"⚠️ Warning: {local_m3u8} not found. Skipping VOD finalization.", file=sys.stderr)

    return "0", 200

# --- SRS HLS SYNC HOOK ---
@app.route('/on_hls', methods=['POST'])
def on_hls():
    """
    Called by SRS every time a new HLS segment (.ts) is created.
    Syncs the new segment and the updated m3u8 to S3.
    """
    payload = request.json
    
    # 1. Parse useful information from the payload
    app_name = payload.get('app')
    stream_name = payload.get('stream')
    ts_relative_path = payload.get('url')      # e.g., "live/livestream/segment-0.ts"
    m3u8_relative_path = payload.get('m3u8_url') # e.g., "live/livestream/index.m3u8"
    
    # 2. Define local full paths (Mapped to your shared volume /tmp/hls)
    # SRS sends 'file' and 'm3u8' paths relative to its own CWD. 
    # We use the app/stream structure to find them in our mount.
    local_ts_path = f"{HLS_BASE_PATH}/{ts_relative_path}"
    local_m3u8_path = f"{HLS_BASE_PATH}/{m3u8_relative_path}"

    print(f"📦 NEW SEGMENT: {ts_relative_path} (Seq: {payload.get('seq_no')})", file=sys.stderr)

    try:
        # 3. Upload the .ts Segment
        if os.path.exists(local_ts_path):
            s3_client.upload_file(
                local_ts_path, S3_BUCKET, ts_relative_path,
                ExtraArgs={'ContentType': 'video/MP2T'}
            )
        
        # 4. Upload the updated .m3u8 Playlist
        # We use Cache-Control: no-cache so the player always gets the latest live window
        if os.path.exists(local_m3u8_path):
            s3_client.upload_file(
                local_m3u8_path, S3_BUCKET, m3u8_relative_path,
                ExtraArgs={
                    'ContentType': 'application/vnd.apple.mpegurl',
                    'CacheControl': 'no-cache, no-store, must-revalidate'
                }
            )
            
        return "0", 200

    except Exception as e:
        print(f"❌ S3 Sync Error: {str(e)}", file=sys.stderr)
        return "1", 500

if __name__ == '__main__':
    watcher_thread = threading.Thread(target=start_watcher, daemon=True)
    watcher_thread.start()
    app.run(host='0.0.0.0', port=3001)