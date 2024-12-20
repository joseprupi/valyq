from flask import Blueprint, request, jsonify, send_file
from core.services.test_service import TestService
from domain.exceptions.validation_exceptions import ValidationError
from pathlib import Path
from api.middleware.auth import require_auth

test_bp = Blueprint('test', __name__)

def init_test_routes(test_service: TestService) -> Blueprint:

    @test_bp.route('/test-images/<validation_id>/tests/test_<test_number>/images/<image_name>', methods=['GET'])
    async def serve_test_image(validation_id: str, test_number: str, image_name: str):
        try:
            # Construct path to image
            image_path = Path(test_service.validation_service.base_upload_folder) / \
                        validation_id / 'tests' / f'test_{test_number}' / 'images' / image_name

            print(image_path)
            
            if not image_path.exists():
                return jsonify({'error': 'Image not found'}), 404

            return send_file(
                str(image_path),
                mimetype='image/*',
                as_attachment=False
            )
        except Exception as e:
            return jsonify({'error': 'Internal server error'}), 500

    @test_bp.route('/execute-test', methods=['POST'])
    @require_auth()
    async def execute_test():
        try:
            data = request.get_json()
            
            # Validate required fields
            if 'validation_id' not in data:
                raise ValidationError("validation_id is required")
                
            execution_args = {
                'validation_id': data['validation_id'],
                'test_id': data.get('test_id'),
                'description': data.get('description'),
                'follow_up_message': data.get('follow_up_message')
            }
            
            # For follow-ups, test_id is required but description is not
            if execution_args['test_id'] and not execution_args['description']:
                del execution_args['description']
                
            # For new tests, description is required but test_id is not
            if not execution_args['test_id'] and not execution_args['description']:
                raise ValidationError("description is required for new tests")

            result = await test_service.execute_test(**execution_args)
            return jsonify(result)
            
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            print(f"Error in execute_test route: {str(e)}")  # Log the error
            return jsonify({'error': 'Internal server error'}), 500

    @test_bp.route('/test-results/<execution_id>/<test_number>', methods=['GET'])
    @require_auth()
    async def get_test_results(execution_id: str, test_number: str):
        try:
            results = await test_service.get_test_results(execution_id, test_number)
            return jsonify(results)
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': 'Internal server error'}), 500
        
    @test_bp.route('/tests/<validation_id>', methods=['GET'])
    @require_auth()
    async def get_validation_tests(validation_id: str):
        """Get all tests for a validation"""
        try:
            tests = await test_service.load_tests(validation_id)
            return jsonify(tests)
        except TestExecutionError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': 'Internal server error'}), 500

    @test_bp.route('/test/<validation_id>/<test_id>', methods=['DELETE'])
    @require_auth()
    async def delete_test(validation_id: str, test_id: str):
        """Delete a specific test"""
        try:
            await test_service.delete_test(validation_id, test_id)
            return jsonify({'status': 'success'})
        except TestExecutionError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': 'Internal server error'}), 500

    return test_bp