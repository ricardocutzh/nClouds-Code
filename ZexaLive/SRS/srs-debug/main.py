import sys
import json
import secrets
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# --- CONFIGURATION ---
# Internal SRS API URL (Uses the service name from docker-compose)
SRS_API_URL = "http://srs:1985/api/v1"

# In-Memory Database structure: { "app_name": { "room_name": "key" } }
data_store = {
    "live": {"room1": "default-key-123"}
}

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
    """Serves the Unified Dashboard UI"""
    return render_template_string(DASHBOARD_HTML)

# --- 1. SRS API PROXY ---
@app.route('/proxy/<endpoint>')
def srs_proxy(endpoint):
    """Bypasses CORS by fetching SRS data server-side"""
    try:
        r = requests.get(f"{SRS_API_URL}/{endpoint}")
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- 2. MANAGEMENT API ---
@app.route('/api/data')
def get_data(): 
    return jsonify(data_store)

@app.route('/api/apps', methods=['POST'])
def create_app():
    name = request.json.get('name')
    if name and name not in data_store:
        data_store[name] = {}
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
    if app_name in data_store:
        data_store[app_name].pop(room_name, None)
    return "OK", 200

# --- 3. SRS AUTHENTICATION HOOKS ---
@app.route('/on_publish', methods=['POST'])
def on_publish():
    """Called by SRS to authorize a stream"""
    payload = request.json
    
    # Debug: Print full payload to console
    print(f"\\n--- AUTH ATTEMPT ---", file=sys.stderr)
    print(json.dumps(payload, indent=2), file=sys.stderr)

    req_app = payload.get('app')
    req_room = payload.get('stream')
    param = payload.get('param', '')

    # Extract key from param string (?key=...)
    provided_key = None
    if 'key=' in param:
        provided_key = param.split('key=')[1].split('&')[0]

    # Evaluation
    if req_app in data_store and req_room in data_store[req_app]:
        if data_store[req_app][req_room] == provided_key:
            print(f"✅ GRANTED: {req_app}/{req_room}", file=sys.stderr)
            return "0", 200
    
    print(f"❌ DENIED: {req_app}/{req_room} (Key: {provided_key})", file=sys.stderr)
    return "1", 403

@app.route('/on_unpublish', methods=['POST'])
def on_unpublish():
    """Called by SRS when a stream ends"""
    print(f"⏹️ OFFLINE: {request.json.get('app')}/{request.json.get('stream')}", file=sys.stderr)
    return "0", 200

if __name__ == '__main__':
    # Internal port remains 3001
    app.run(host='0.0.0.0', port=3001)