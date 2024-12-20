from flask import Blueprint, request, jsonify, send_file
from core.services.execution_service import ExecutionService
from domain.exceptions.validation_exceptions import ExecutionError
from core.interfaces.file_storage import FileStorage
from api.middleware.auth import require_auth


execution_bp = Blueprint('execution', __name__)

def init_execution_routes(execution_service: ExecutionService, file_storage: FileStorage) -> Blueprint:
     
    @execution_bp.route('/create-execution', methods=['POST'])
    @require_auth()
    async def create_execution():
        """Create new execution environment and upload files"""
        try:
            if 'files' not in request.files:
                return jsonify({'error': 'No files provided'}), 400
                
            uploaded_files = request.files.getlist('files')
            result = await execution_service.create_execution(uploaded_files)
            
            return jsonify({
                'execution_id': result.execution_id,
                'directory': result.directory
            })

        except ExecutionError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': 'Internal server error'}), 500
 
    @execution_bp.route('/execute', methods=['POST'])
    @require_auth()
    async def execute_code():
        """Execute provided code in the execution environment"""
        try:
            data = request.get_json()
            if 'code' not in data:
                return jsonify({'error': 'No code provided'}), 400

            result = await execution_service.execute_code(data['code'])
            return jsonify(result)

        except ExecutionError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': 'Internal server error'}), 500
 
    @execution_bp.route('/list-execution-files/<execution_id>', methods=['GET'])
    @require_auth()
    async def list_execution_files(execution_id: str):
        """List files in execution directory"""
        try:
            files = await execution_service.list_files(execution_id)
            return jsonify({
                'execution_id': execution_id,
                'structure': files
            })

        except ExecutionError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': 'Internal server error'}), 500
 
    @execution_bp.route('/app/uploads/<execution_id>/<path:file_path>', methods=['GET'])
    @require_auth()
    async def serve_execution_file(execution_id: str, file_path: str):
        """Serve files from execution directory"""
        try:
            file_path = await execution_service.get_file_path(execution_id, file_path)
            return await file_storage.serve_file(file_path)

        except ExecutionError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': 'Internal server error'}), 500
 
    @execution_bp.route('/compile-existing-latex', methods=['POST'])
    @require_auth()
    async def compile_latex():
        """Compile LaTeX files in execution directory"""
        try:
            data = request.get_json()
            if not data or 'execution_id' not in data or 'filename' not in data:
                return jsonify({'error': 'Missing required fields'}), 400

            pdf_content = await execution_service.compile_latex(
                data['execution_id'],
                data['filename']
            )
            
            return send_file(
                pdf_content,
                mimetype='application/pdf',
                as_attachment=True,
                download_name='report.pdf'
            )

        except ExecutionError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': 'Internal server error'}), 500

    return execution_bp