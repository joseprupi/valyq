from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from typing import Dict, Any
from datetime import datetime
from pathlib import Path
import uuid
from api.middleware.auth import require_auth

from core.services.validation_service import ValidationService
from core.services.document_service import DocumentService
from core.services.test_service import TestService
from domain.exceptions.validation_exceptions import ValidationError

validation_bp = Blueprint('validation', __name__)


def init_validation_routes(validation_service: ValidationService,
                           test_service: TestService,
                           document_service: DocumentService) -> Blueprint:
    @validation_bp.route('/create-validation', methods=['POST'])
    @require_auth()
    async def create_validation():
        try:
            files = {
                'documentation': request.files.get('documentation'),
                'trainingScript': request.files.get('trainingScript'),
                'trainedModel': request.files.get('trainedModel'),
                'trainingDataset': request.files.get('trainingDataset'),
                'testDataset': request.files.get('testDataset')
            }

            result = await validation_service.create_validation(
                files=files
            )

            return jsonify({
                'status': 'success',
                'validation_id': str(result.validation_id),
                'execution_id': result.execution_id
            })

        except ValidationError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': 'Internal server error'}), 500

    @validation_bp.route('/status/<validation_id>', methods=['GET'])
    @require_auth()
    async def get_status(validation_id: str):
        try:
            status = await validation_service.get_validation_status(validation_id)
            return jsonify(status)
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': 'Internal server error'}), 500

    @validation_bp.route('/download/<validation_id>', methods=['GET'])
    @require_auth()
    async def download_results(validation_id: str):
        try:
            file_path = await validation_service.get_results_file(validation_id)
            return send_file(file_path)
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': 'Internal server error'}), 500

    @validation_bp.route('/load-validation-with-tests/<validation_id>', methods=['GET'])
    @require_auth()
    async def load_validation_with_tests(validation_id: str):
        try:
            result = await validation_service.load_validation_with_tests(validation_id)
            return jsonify(result)
        except ValidationError as e:
            return jsonify({'error': str(e)}), 404
        except Exception as e:
            return jsonify({'error': 'Internal server error'}), 500

    @validation_bp.route('/load-validation/<validation_id>', methods=['GET'])
    @require_auth()
    async def load_validation(validation_id: str):
        try:
            validation = await validation_service.load_validation(validation_id)

            files = {
                file_type: Path(file_path).name
                for file_type, file_path in validation.model_files.items()
            }

            return jsonify({
                'validation_id': str(validation.validation_id),
                'status': validation.status.value,
                'execution_id': validation.execution_id,
                'files': files,
                'created_at': validation.created_at.isoformat(),
                'updated_at': validation.updated_at.isoformat()
            })

        except ValidationError as e:
            return jsonify({'error': str(e)}), 404
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': 'Internal server error'}), 500

    @validation_bp.route('/generate-report/<validation_id>', methods=['POST'])
    @require_auth()
    async def generate_validation_report(validation_id: str):
        try:
            # Load validation and its tests
            tests = await test_service.load_tests(validation_id)

            # Generate report
            report_path = await document_service.generate_validation_report(
                validation_id=validation_id,
                tests=tests
            )

            # Send file
            return send_file(
                report_path,
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                as_attachment=True,
                download_name=f'validation_report_{validation_id}.docx'
            )

        except ValidationError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': 'Internal server error'}), 500

    return validation_bp
