# LLM Model Validation Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent model validation platform inspired by financial model validation practices and regulatory guidelines (SR 11-7), leveraging Large Language Models (LLMs) to automate and enhance the testing and validation of machine learning models. This tool helps validation analysts, data scientists and ML engineers ensure their models meet quality standards, are well-documented, and behave as expected, following principles similar to those used in financial model risk management.

## Background

This project is inspired in financial model validation practices, particularly the Federal Reserve's Supervisory Guidance on Model Risk Management (SR 11-7). While SR 11-7 provides guidance for financial institutions on model risk management, its principles of rigorous validation, documentation, and testing are valuable for all types of machine learning models. Key aspects incorporated from SR 11-7 include:

- Comprehensive model documentation review
- Independent testing and validation
- Analysis of model design and assumptions
- Assessment of data quality and relevance
- Ongoing monitoring and periodic review

## Features

- **Automated Test Generation**: Uses LLMs to analyze model documentation and code to generate comprehensive test suites
- **Interactive Testing**: Engage in conversational testing with the LLM to refine and improve tests
- **File Management**: Support for various model artifacts including:
  - Model documentation
  - Training scripts
  - Trained models
  - Training and test datasets
- **Test Result Visualization**: Dynamic visualization of test results including charts, tables, and metrics
- **Report Generation**: Generate detailed validation reports in DOCX format
- **Extensible Architecture**: Modular design supporting multiple LLM providers (Claude, ChatGPT) and execution environments

## Architecture

The application consists of three main components:

1. **Frontend**: React-based web interface with a modern, responsive design
2. **Backend API**: Flask-based REST API handling validation logic and LLM interactions
3. **Execution Service**: Isolated environment for secure model testing and validation

## Installation

1. Clone the repository:
```bash
git clone https://github.com/joseprupi/valyq
cd valyq
```

2. Set up the Python environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Install frontend dependencies:
```bash
cd validation_frontend
npm install
```

4. Create a `.env` file in the root directory with your configuration:
```env
ENVIRONMENT=development
FLASK_SERVICE_URL=http://localhost
FLASK_SERVICE_PORT=5000
LLM_PROVIDER=claude  # or chatgpt
LLM_API_KEY=your_api_key_here
AUTH_SECRET_KEY=your_secret_key_here
```

## Running the Application

1. Start the backend server:
```bash
python main.py
```

2. In a separate terminal, start the frontend development server:
```bash
cd validation_frontend
npm start
```

3. Start the execution service (remote_executor folder), either as a Docker container or a local service.

4. Access the application at `http://localhost:3000`

## Usage

1. **Create a Validation**:
   - Upload your model files (documentation, training script, model file, datasets)
   - Submit to create a new validation instance

2. **Generate and Run Tests**:
   - Add custom tests with specific validation criteria
   - Use the conversational interface to refine tests
   - View test results and visualizations

3. **Generate Reports**:
   - Create comprehensive validation reports
   - Export results for documentation and review

## Contributing

We welcome contributions!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

Create an issue for bug reports or feature requests