# cryptoguard-pqc-backend

## Overview
Cryptoguard is a Flask-based application designed to provide code scanning and generate a Component Bill of Materials (CBOM). This project aims to enhance security by analyzing code and managing dependencies effectively.

## Project Structure
```
cryptoguard-pqc-backend/
├── app.py              # Main Flask app
├── routes/             # API endpoint definitions
│   └── api.py
├── analysis/           # Code scanning and CBOM logic
│   └── cbom_generator.py
├── data/               # Temporary storage for uploads/repos
│   └── uploads/
├── db/                 # Database logic
│   └── database.py
└── requirements.txt    # Dependencies
```

## Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   cd cryptoguard-pqc-backend
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
1. Run the Flask application:
   ```
   python app.py
   ```

2. Access the API endpoints at `http://localhost:5000`.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.