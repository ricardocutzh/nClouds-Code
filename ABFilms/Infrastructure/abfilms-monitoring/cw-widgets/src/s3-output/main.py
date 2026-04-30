import boto3

def get_media_titles(s3_client, bucket, prefix):
    """Retrieves top-level subfolder names within a specific prefix."""
    titles = []
    paginator = s3_client.get_paginator('list_objects_v2')
    
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter='/'):
        for cp in page.get('CommonPrefixes', []):
            full_path = cp.get('Prefix')
            title = full_path.replace(prefix, "").strip("/")
            if title:
                titles.append(title)
    return sorted(titles)

def lambda_handler(event, context):
    bucket_name = event.get('bucket', 'your-media-bucket-name')
    s3 = boto3.client('s3')

    try:
        movies = get_media_titles(s3, bucket_name, "Movies/")
        shows = get_media_titles(s3, bucket_name, "Shows/")
    except Exception as e:
        return f"<div style='color:red;'>Error accessing S3: {str(e)}</div>"

    # HTML/CSS Generation
    css = """
    <style>
        .container { font-family: 'Amazon Ember', Arial, sans-serif; padding: 10px; color: #16191f; }
        
        /* Stats Bar Styling */
        .stats-container { display: flex; gap: 20px; margin-bottom: 20px; }
        .stat-card { background: #f1f3f3; padding: 15px; border-radius: 8px; border-left: 5px solid #0073bb; flex: 1; }
        .stat-card h2 { margin: 0; font-size: 24px; color: #0073bb; }
        .stat-card p { margin: 5px 0 0; font-weight: bold; font-size: 14px; }
        
        /* Expandable Section Styling */
        details { background: #ffffff; border: 1px solid #eaeded; border-radius: 8px; margin-bottom: 15px; overflow: hidden; }
        summary { 
            padding: 12px 15px; 
            background: #fafafa; 
            cursor: pointer; 
            font-weight: bold; 
            font-size: 15px; 
            list-style: none; /* Hide default arrow in some browsers */
            display: flex;
            align-items: center;
            border-bottom: 1px solid transparent;
        }
        details[open] summary { border-bottom: 1px solid #eaeded; background: #f2f8fd; }
        summary::-webkit-details-marker { display: none; } /* Hide arrow in Chrome/Safari */
        
        summary::before {
            content: '▶';
            display: inline-block;
            margin-right: 10px;
            font-size: 10px;
            transition: transform 0.2s;
        }
        details[open] summary::before { transform: rotate(90deg); }

        /* Table Styling */
        .content { padding: 0; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        td { padding: 10px 15px; border-bottom: 1px solid #eaeded; }
        tr:last-child td { border-bottom: none; }
        tr:hover { background-color: #fbfbfb; }
        
        .badge { background: #0073bb; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; margin-left: auto; }
    </style>
    """

    def build_section(title, icon, items):
        rows = "".join([f"<tr><td>{item}</td></tr>" for item in items]) if items else "<tr><td>No items found</td></tr>"
        return f"""
        <details>
            <summary>
                {icon} {title}
                <span class="badge">{len(items)}</span>
            </summary>
            <div class="content">
                <table>
                    <tbody>{rows}</tbody>
                </table>
            </div>
        </details>
        """

    # Stats Bar
    stats_html = f"""
    <div class="stats-container">
        <div class="stat-card"><h2>{len(movies)}</h2><p>Movies - Available</p></div>
        <div class="stat-card"><h2>{len(shows)}</h2><p>Shows - Available</p></div>
    </div>
    """

    content_html = f"""
    <div class="container">
        {stats_html}
        {build_section("Movies", "🎬", movies)}
        {build_section("TV Shows", "📺", shows)}
    </div>
    """

    return css + content_html