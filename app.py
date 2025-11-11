"""
Flask Web Application for Web Scraping Tool
Provides a modern web-based UI for the web scraping functionality.
"""

from flask import Flask, render_template, request, jsonify, send_file
from web_scraper import (
    search_text_by_keyword,
    search_image_by_keyword,
    search_link_by_keyword,
    scrape_card_results,
    scrape_result_list,
    ai_scrape_topic,
    ai_scrape_result_list,
    list_all_images
)
import json
import os
from datetime import datetime

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # Support UTF-8 characters

# Create downloads directory if it doesn't exist
downloads_dir = os.path.join(os.path.dirname(__file__), 'downloads')
os.makedirs(downloads_dir, exist_ok=True)


@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')


@app.route('/api/scrape', methods=['POST'])
def scrape():
    """API endpoint for scraping."""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        scrape_type = data.get('type', '')
        options = data.get('options', {})
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Add https:// if not present
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url
        
        result = None
        message = ''
        
        if scrape_type == 'text':
            method = options.get('method', 'keyword')
            if method == 'keyword':
                keyword = options.get('keyword', '')
                if keyword:
                    result = search_text_by_keyword(url, keyword)
                else:
                    return jsonify({'error': 'Keyword is required'}), 400
            elif method == 'ai':
                topic_query = options.get('topic_query', '')
                if topic_query:
                    # Use ai_scrape_result_list which can handle both result lists and text extraction
                    # API key will be loaded from config.py automatically (pass None)
                    result = ai_scrape_result_list(url, topic_query, None)
                else:
                    return jsonify({'error': 'Topic query is required'}), 400
        
        elif scrape_type == 'image':
            method = options.get('method', 'keyword')
            if method == 'keyword':
                keyword = options.get('keyword', '')
                if keyword:
                    result = search_image_by_keyword(url, keyword)
                else:
                    return jsonify({'error': 'Keyword is required'}), 400
            elif method == 'list_all':
                result = list_all_images(url)
        
        elif scrape_type == 'link':
            keyword = options.get('keyword', '')
            if keyword:
                result = search_link_by_keyword(url, keyword)
            else:
                return jsonify({'error': 'Keyword is required'}), 400
        
        elif scrape_type == 'card':
            # Auto-detection, no selector needed - always pass None
            result = scrape_card_results(url, None)
        
        else:
            return jsonify({'error': 'Invalid scrape type'}), 400
        
        # Format result for JSON response
        if isinstance(result, str):
            if result.startswith('Error:') or result.startswith('Not found'):
                return jsonify({
                    'success': False,
                    'error': result,
                    'data': None
                })
            # If it's a string but not an error, treat it as a single result
            result = [result]
        
        # Handle different result types
        if result is None:
            return jsonify({
                'success': False,
                'error': 'No data extracted',
                'data': None
            })
        
        # Convert result to list if it's a single item
        if not isinstance(result, list):
            if isinstance(result, dict):
                # Single card or result item
                result = [result]
            else:
                # Should already be handled above for strings, but handle other types
                result = [result]
        
        # Ensure all items are JSON serializable
        def make_serializable(obj):
            if isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_serializable(item) for item in obj]
            elif hasattr(obj, '__dict__'):
                return str(obj)
            else:
                return obj
        
        result = make_serializable(result)
        
        item_count = len(result) if isinstance(result, list) else 1
        return jsonify({
            'success': True,
            'data': result,
            'message': f'Successfully extracted {item_count} item(s)'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data': None
        }), 500


@app.route('/api/export', methods=['POST'])
def export_data():
    """Export scraped data to JSON file."""
    try:
        data = request.get_json()
        export_data_list = data.get('data', [])
        filename = data.get('filename', f'scraped_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        
        if not filename.endswith('.json'):
            filename += '.json'
        
        # Sanitize filename
        filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).strip()
        
        downloads_dir = os.path.join(os.path.dirname(__file__), 'downloads')
        filepath = os.path.join(downloads_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data_list, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            'success': True,
            'message': f'Data exported to {filename}',
            'filename': filename
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/download/<filename>')
def download_file(filename):
    """Download exported file."""
    try:
        downloads_dir = os.path.join(os.path.dirname(__file__), 'downloads')
        filepath = os.path.join(downloads_dir, filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("WEB SCRAPER - Web Interface")
    print("="*60)
    print("\nStarting web server...")
    print("Open your browser and go to: http://127.0.0.1:5000")
    print("\nPress Ctrl+C to stop the server")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)

