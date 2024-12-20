from flask import Flask, request, jsonify, send_file, send_from_directory
import sys
import io
import traceback
import tempfile
import os
import subprocess
import logging
import uuid
from werkzeug.utils import secure_filename
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024 * 1024  # 32MB max file size

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

UPLOAD_BASE_DIR = Path('/app/uploads')
UPLOAD_BASE_DIR.mkdir(parents=True, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def compile_latex(latex_content, output_dir, request_files):
    """Compile LaTeX content to PDF with proper UTF-8 encoding."""
    logger.debug(f"Files in request: {list(request_files.keys())}")
    
    # Handle uploaded files
    saved_files = []
    for key in request_files:
        if key.startswith('files_'):
            file = request_files[key]
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(output_dir, filename)
                logger.debug(f"Saving file: {file_path}")
                file.save(file_path)
                saved_files.append(filename)
    
    logger.debug(f"Saved files: {saved_files}")
    
    # Add UTF-8 support after \documentclass if not present
    if r"\usepackage[utf8]{inputenc}" not in latex_content:
        latex_content = latex_content.replace(
            r"\documentclass{article}",
            r"\documentclass{article}" + "\n" + r"\usepackage[utf8]{inputenc}" + "\n" + r"\usepackage[T1]{fontenc}"
        )
    
    # Write LaTeX content to file with UTF-8 encoding
    tex_file = os.path.join(output_dir, "document.tex")
    with open(tex_file, "w", encoding='utf-8') as f:
        f.write(latex_content)
    
    logger.debug(f"Written LaTeX content to: {tex_file}")
    logger.debug(f"Directory contents before compilation: {os.listdir(output_dir)}")
    
    compilation_warnings = []
    # Run pdflatex with detailed output
    try:
        for i in range(2):  # Run twice for references
            logger.debug(f"LaTeX compilation attempt {i+1}")
            result = subprocess.run(
                [
                    "pdflatex",
                    "-interaction=nonstopmode",
                    "-file-line-error",
                    tex_file
                ],
                cwd=output_dir,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            # Log the output
            logger.debug(f"LaTeX stdout:\n{result.stdout}")
            if result.stderr:
                logger.error(f"LaTeX stderr:\n{result.stderr}")
            
            # Check for warnings and errors in the log file
            log_file = os.path.join(output_dir, "document.log")
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    log_content = f.read()
                    warning_lines = [line.strip() for line in log_content.split('\n') 
                                   if ('warning' in line.lower() or 'error' in line.lower())
                                   and not line.strip().startswith('Package')]
                    if warning_lines:
                        compilation_warnings.extend(warning_lines)
        
        pdf_path = os.path.join(output_dir, "document.pdf")
        
        # Check if PDF was generated
        if os.path.exists(pdf_path):
            return pdf_path, compilation_warnings
        else:
            raise Exception("PDF file was not generated")
            
    except subprocess.CalledProcessError as e:
        # Check if PDF was generated despite the error
        pdf_path = os.path.join(output_dir, "document.pdf")
        if os.path.exists(pdf_path):
            return pdf_path, compilation_warnings
        raise Exception(f"LaTeX compilation failed: {e.stdout}\n{e.stderr}")
    except Exception as e:
        # Final check for PDF
        pdf_path = os.path.join(output_dir, "document.pdf")
        if os.path.exists(pdf_path):
            return pdf_path, compilation_warnings
        raise Exception(f"Error during compilation: {str(e)}")

@app.route('/execute', methods=['POST'])
def execute_code():
    """Execute Python code and return the output"""
    # Get code from the JSON request
    data = request.get_json()
    code = data.get("code", "")
    
    # Prepare to capture stdout and stderr
    stdout = io.StringIO()
    stderr = io.StringIO()
    
    # Redirect stdout and stderr
    sys.stdout = stdout
    sys.stderr = stderr

    output = ""
    error = ""
    try:
        # Execute the code
        exec(code, globals())
        output = stdout.getvalue()
        error = stderr.getvalue()
    except Exception as e:
        # Capture the full traceback for debugging
        error = traceback.format_exc()
    finally:
        # Reset stdout and stderr to default
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
    
    # Return output and errors as JSON
    return jsonify({"output": output, "error": error})

@app.route('/latex-to-pdf', methods=['POST'])
def latex_to_pdf():
    try:
        if 'latex' not in request.form:
            return jsonify({"error": "No LaTeX content provided"}), 400
        
        latex_content = request.form['latex']
        
        logger.info("Starting PDF generation")
        logger.debug(f"Received files: {list(request.files.keys())}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.debug(f"Created temp directory: {temp_dir}")
            pdf_path = compile_latex(latex_content, temp_dir, request.files)
            logger.info(f"PDF generated successfully at: {pdf_path}")
            return send_file(
                pdf_path,
                mimetype='application/pdf',
                as_attachment=True,
                download_name='document.pdf'
            )
            
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/create-execution', methods=['POST'])
def create_execution():
    try:
        # Generate a unique directory name
        execution_id = str(uuid.uuid4())
        execution_dir = UPLOAD_BASE_DIR / execution_id
        execution_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Created execution directory: {execution_dir}")
        
        # Handle file uploads
        files = request.files.getlist('files')
        if not files:
            return jsonify({'error': 'No files provided'}), 400
        
        saved_files = []
        for file in files:
            if file.filename:
                filename = secure_filename(file.filename)
                file_path = execution_dir / filename
                logger.debug(f"Saving file: {file_path}")
                file.save(file_path)
                saved_files.append(filename)
        
        return jsonify({
            'execution_id': execution_id,
            'directory': str(execution_dir),
            'saved_files': saved_files
        })
        
    except Exception as e:
        logger.error(f"Error in create_execution: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/compile-existing-latex', methods=['POST'])
def compile_existing_latex():
    """
    Compile an existing LaTeX file from an execution directory into a PDF.
    Expects JSON input with:
    - execution_id: The UUID of the execution directory
    - filename: The name of the .tex file to compile
    """
    try:
        data = request.get_json()
        if not data or 'execution_id' not in data or 'filename' not in data:
            return jsonify({
                "error": "Missing required parameters. Please provide execution_id and filename"
            }), 400

        execution_id = data['execution_id']
        filename = secure_filename(data['filename'])
        
        # Validate execution directory exists
        execution_dir = UPLOAD_BASE_DIR / execution_id
        if not execution_dir.exists() or not execution_dir.is_dir():
            return jsonify({
                "error": f"Execution directory not found: {execution_id}"
            }), 404

        # Validate tex file exists and has .tex extension
        tex_file_path = execution_dir / filename
        if not tex_file_path.exists() or tex_file_path.suffix.lower() != '.tex':
            return jsonify({
                "error": f"LaTeX file not found or invalid: {filename}"
            }), 404

        logger.info(f"Starting PDF generation for existing file: {tex_file_path}")
        
        # Read the LaTeX content
        with open(tex_file_path, 'r', encoding='utf-8') as f:
            latex_content = f.read()

        # Use the existing compile_latex function, but with the execution directory
        pdf_path, warnings = compile_latex(latex_content, str(execution_dir), {})
        
        logger.info(f"PDF generated successfully at: {pdf_path}")
        if warnings:
            logger.warning(f"Compilation warnings: {warnings}")
        
        # Generate the output filename based on the input filename
        output_filename = f"{tex_file_path.stem}.pdf"
        
        response = send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=output_filename
        )
        
        # Add warnings to response headers if any
        if warnings:
            response.headers['X-LaTeX-Warnings'] = '; '.join(warnings[:5])  # Limit to first 5 warnings
            
        return response

    except Exception as e:
        logger.error(f"Error generating PDF from existing file: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Check if PDF was generated despite the error
        pdf_path = os.path.join(str(execution_dir), "document.pdf")
        if os.path.exists(pdf_path):
            logger.info("PDF was generated despite errors, returning it with warning")
            response = send_file(
                pdf_path,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"{tex_file_path.stem}.pdf"
            )
            response.headers['X-LaTeX-Errors'] = str(e)
            return response
            
        return jsonify({"error": str(e)}), 500

@app.route('/list-execution-files/<execution_id>', methods=['GET'])
def list_execution_files(execution_id):
    """
    List all files and folders within an execution directory.
    Returns a JSON structure representing the directory tree.
    """
    try:

        execution_dir = UPLOAD_BASE_DIR / execution_id
        execution_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate and get the execution directory
        execution_dir = UPLOAD_BASE_DIR / execution_id
        if not execution_dir.exists() or not execution_dir.is_dir():
            return jsonify({
                "error": f"Execution directory not found: {execution_id}"
            }), 404

        def get_directory_structure(path):
            """
            Recursively get the directory structure starting from the given path.
            Returns a dict with 'type', 'name', 'size' (for files), and 'children' (for directories)
            """
            item = {}
            path_obj = Path(path)
            item['name'] = path_obj.name
            item['type'] = 'directory' if path_obj.is_dir() else 'file'
            
            if path_obj.is_file():
                item['size'] = path_obj.stat().st_size
                # Add file extension if present
                if path_obj.suffix:
                    item['extension'] = path_obj.suffix[1:]  # Remove the leading dot
            else:
                item['children'] = []
                for child_path in sorted(path_obj.iterdir()):
                    child_item = get_directory_structure(child_path)
                    item['children'].append(child_item)

            return item

        # Get the directory structure
        structure = get_directory_structure(execution_dir)
        
        # Add some basic statistics
        stats = {
            'total_files': sum(1 for _ in execution_dir.rglob('*') if _.is_file()),
            'total_size': sum(f.stat().st_size for f in execution_dir.rglob('*') if f.is_file()),
            'execution_id': execution_id,
            'created_time': execution_dir.stat().st_ctime
        }

        return jsonify({
            'structure': structure,
            'stats': stats,
            'directory':str(execution_dir)
        })

    except Exception as e:
        logger.error(f"Error listing execution files: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/test-images/<execution_id>/<path:image_path>', methods=['GET'])
def serve_test_image(execution_id, image_path):
    """Serve images from test execution directory"""
    try:
        image_file_path = os.path.join('/app/uploads', execution_id, image_path)
        return send_file(image_file_path, mimetype='image/png')  # Adjust mimetype as needed
    except Exception as e:
        print(f"Error serving image: {str(e)}")
        return jsonify({'error': 'Image not found'}), 404

@app.route('/app/uploads/<execution_id>/<path:filename>')
def serve_upload(execution_id, filename):
    """Serve files from upload directories"""
    try:
        # Ensure the path is within the uploads directory
        upload_path = os.path.join(UPLOAD_BASE_DIR, execution_id)
        return send_from_directory(upload_path, filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

if __name__ == '__main__':
    print("Starting server")
    app.run(host="0.0.0.0", port=5000, debug=True)