from flask import Flask, request, jsonify
import json
import datetime

app = Flask(__name__)

@app.route('/', defaults={'path': ''}, methods=['POST', 'GET'])
@app.route('/<path:path>', methods=['POST', 'GET'])
def catch_all(path):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"\n{'='*60}")
    print(f"[{now}] REQUEST RECEIVED")
    print(f"Path:   /{path}")
    print(f"Method: {request.method}")
    print(f"{'-'*60}")
    
    # Print Headers
    print("HEADERS:")
    for header, value in request.headers.items():
        print(f"  {header}: {value}")
    
    # Print Body (Payload)
    print("\nPAYLOAD:")
    if request.is_json:
        print(json.dumps(request.json, indent=4))
    else:
        print(request.get_data(as_text=True) or "Empty Body")
    print(f"{'='*60}\n")

    # SRS expects a '0' string or 200 OK to consider the hook "successful"
    return "0", 200

if __name__ == '__main__':
    # Listen on port 3001
    app.run(host='0.0.0.0', port=3001)