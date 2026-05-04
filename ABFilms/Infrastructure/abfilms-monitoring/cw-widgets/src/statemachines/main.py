import boto3
import json
from datetime import datetime, timezone

def format_date(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S') if dt else "—"

def get_filtered_executions(client, arn, status, start_dt, end_dt):
    """Fetches executions and filters them by the dashboard timeframe."""
    executions_in_window = []
    
    # We fetch a larger batch (e.g., 100) to ensure we find enough 
    # within the specific timeframe, then filter down to the 10 most recent.
    try:
        paginator = client.get_paginator('list_executions')
        for page in paginator.paginate(stateMachineArn=arn, statusFilter=status):
            for exe in page.get('executions', []):
                exe_start = exe['startDate']
                
                # Check if the execution started within the dashboard window
                if start_dt <= exe_start <= end_dt:
                    executions_in_window.append(exe)
                
                # Since executions are returned newest-first, if we are older 
                # than the start_dt, we can stop looking in this page/status.
                if exe_start < start_dt:
                    break
            
            # Stop if we have enough or if we've passed the window
            if len(executions_in_window) >= 10 or (page.get('executions') and page['executions'][-1]['startDate'] < start_dt):
                break
                
        return executions_in_window[:10]
    except Exception as e:
        print(f"Error fetching {status}: {str(e)}")
        return []

def lambda_handler(event, context):
    # 1. Extract context and parameters
    state_machine_arn = event.get('stateMachineArn', '')
    widget_context = event.get('widgetContext', {})
    time_range = widget_context.get('timeRange', {})
    
    # 2. Parse the dashboard timeframe (Unix ms to datetime)
    # Default to last 24h if for some reason context is missing
    start_ms = time_range.get('start', (datetime.now().timestamp() - 86400) * 1000)
    end_ms = time_range.get('end', datetime.now().timestamp() * 1000)
    
    start_dt = datetime.fromtimestamp(start_ms / 1000.0, tz=timezone.utc)
    end_dt = datetime.fromtimestamp(end_ms / 1000.0, tz=timezone.utc)

    client = boto3.client('stepfunctions')
    statuses = ['RUNNING', 'SUCCEEDED', 'FAILED', 'ABORTED']
    
    # 3. Get filtered data
    data = {status: get_filtered_executions(client, state_machine_arn, status, start_dt, end_dt) for status in statuses}

    # UI/CSS (Same as before, simplified for brevity)
    css = """
    <style>
        .container { font-family: 'Amazon Ember', Arial, sans-serif; padding: 15px; color: #16191f; }
        .time-info { font-size: 12px; color: #687078; margin-bottom: 10px; font-style: italic; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .card { background: white; border: 1px solid #eaeded; border-radius: 8px; overflow: hidden; margin-bottom:10px; }
        .card-header { padding: 10px 15px; font-weight: bold; font-size: 14px; display: flex; justify-content: space-between; }
        .RUNNING { background: #f2f8fd; border-top: 4px solid #0073bb; color: #0073bb; }
        .SUCCEEDED { background: #f1faff; border-top: 4px solid #1d8102; color: #1d8102; }
        .FAILED { background: #fff5f5; border-top: 4px solid #d13212; color: #d13212; }
        .ABORTED { background: #fbfbfb; border-top: 4px solid #687078; color: #687078; }
        table { width: 100%; border-collapse: collapse; font-size: 11px; }
        th { text-align: left; padding: 8px; background: #fafafa; border-bottom: 1px solid #eaeded; }
        td { padding: 8px; border-bottom: 1px solid #f2f2f2; vertical-align: top; }
        .arn { font-family: monospace; font-size: 9px; color: #545b64; }
    </style>
    """

    header_html = f"""
    <div class='container'>
        <h3>State Machine: {state_machine_arn.split(':')[-1]}</h3>
        <p class='time-info'>Showing executions between {format_date(start_dt)} and {format_date(end_dt)}</p>
        <div class='grid'>
    """

    body_html = ""
    for status in statuses:
        executions = data[status]
        body_html += f"""
        <div class="card">
            <div class="card-header {status}"><span>{status}</span> <span>({len(executions)})</span></div>
            {"<table><thead><tr><th>Date</th><th>Execution ID</th></tr></thead><tbody>" if executions else "<div style='padding:15px; color:#999;'>No matches in range</div>"}
        """
        for exe in executions:
            name = exe['executionArn'].split(':')[-1]
            body_html += f"<tr><td>{format_date(exe['startDate'])}</td><td class='arn'>{name}</td></tr>"
        
        body_html += "</tbody></table></div>" if executions else "</div>"

    return css + header_html + body_html + "</div></div>"