import os
import uuid
import subprocess
from flask import Flask, request, jsonify, send_file, render_template, after_this_request
app = Flask(__name__)
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), 'downloads')
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/download', methods=['POST'])
def download_media():
    data = request.get_json()
    url = data.get('url')
    target_format = data.get('format', 'mp4')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    file_id = str(uuid.uuid4())
    temp_file = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.%(ext)s")
    try:
        download_cmd = [
            'yt-dlp',
            '--output', temp_file,
            url
        ]
        subprocess.run(download_cmd, check=True)
        downloaded_file = None
        for file in os.listdir(DOWNLOAD_FOLDER):
            if file.startswith(file_id):
                downloaded_file = os.path.join(DOWNLOAD_FOLDER, file)
                break
        if not downloaded_file:
            return jsonify({'error': 'Download failed'}), 500
        file_root, file_ext = os.path.splitext(downloaded_file)
        if file_ext.lower().replace('.', '') != target_format.lower():
            converted_file = os.path.join(DOWNLOAD_FOLDER, f"{file_id}_converted.{target_format}")
            convert_cmd = [
                'ffmpeg',
                '-i', downloaded_file,
                '-c:v', 'copy',
                '-c:a', 'copy',
                converted_file
            ]
            subprocess.run(convert_cmd, check=True)
            os.remove(downloaded_file)
            output_file = converted_file
        else:
            output_file = downloaded_file
        @after_this_request
        def remove_file(response):
            try:
                os.remove(output_file)
            except Exception as e:
                print(f"Error deleting file: {e}")
            return response

        return send_file(output_file, as_attachment=True)

    except subprocess.CalledProcessError as e:
        return jsonify({'error': 'Error during processing', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

