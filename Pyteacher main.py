
from flask import Flask, render_template, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
import os, ast, sys
import subprocess
from bs4 import BeautifulSoup


app = Flask(__name__, static_folder='Static', template_folder='Templates')


# Global database configuration
DATABASE_NAME = 'PyGuider.db'
DATABASE_PATH = os.path.join(os.path.dirname(__file__), DATABASE_NAME)


app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)


class python_references(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    input = db.Column(db.Text, nullable=False)
    name = db.Column(db.Text, nullable=False)
    definition = db.Column(db.Text, nullable=False)
    example = db.Column(db.Text)


# Function definitions
def read_html_file(file_path: str) -> str:
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return "File not found"

    with open(file_path, 'r') as file:
        html_content = file.read()
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text()


def intro():
    return [0]


def pydefinitions():
    """
    Retrieve Python definitions from the database and return as a dictionary.
    
    Returns:
        dict: Dictionary containing Python definitions.
    """
    
    # Query database for all Python definitions
    results = python_references.query.order_by(python_references.id).all()
    
    # Initialize empty dictionary to store definitions
    definitions = {}
    
    # Iterate over query results
    for result in results:
        definitions[result.id] = {
            'input': result.input,
            'name': result.name,
            'definition': result.definition,
            'example': result.example
        }
    
    return definitions


def pyguider():
    if request.method == 'POST':
        code = request.form['code']
        input_prompt = request.form.get('input_prompt')
        if input_prompt:
            user_input = input(input_prompt)
            return render_template('page3.html', messages=['Input:', user_input])
        try:
            output = subprocess.check_output(['python', '-c', code],
                                            stderr=subprocess.STDOUT).decode('utf-8')
            return render_template('page3.html', messages=['Output:'] + output.split('\n'))
        except Exception as e:
            return render_template('page3.html', messages=['Error:'] + str(e).split('\n'))
    return render_template('page3.html', messages=['Enter Python code:'])


def tasks():
    return [
        "Tasks not yet available."
    ]


def about_the_app():
    file_path = os.path.join('Templates', 'page5.html')
    return read_html_file(file_path)


def how_to_use():
    return ["Exiting the application."]


# Menu items
menu_items = [
    {"option": "1", "description": "Introduction to Computer Science", "function": intro, "page": "page1", "route": "/intro", "endpoint": "page1"},
    {"option": "2", "description": "PyDefinitions", "function": pydefinitions, "page": "page2", "route": "/pydefinitions", "endpoint": "page2"},
    {"option": "3", "description": "PyGuider (write your codes here with guidance.)", "function": pyguider, "page": "page3", "route": "/pyguider", "endpoint": "page3"},
    {"option": "4", "description": "Tasks", "function": tasks, "page": "page4", "route": "/tasks", "endpoint": "page4"},
    {"option": "5", "description": "About PyGuider", "function": about_the_app, "page": "page5", "route": "/about", "endpoint": "page5"},
    {"option": "6", "description": "How to Use PyGuider", "function": how_to_use, "page": "page6", "route": "/how_to_use", "endpoint": "page6"}
]


# Route for the main page
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', menu_items=menu_items)


# Route for redirecting options
@app.route('/option/<option>', methods=['GET'])
def redirect_option(option):
    for item in menu_items:
        if item["option"] == option:
            return redirect(item["route"])
    return "Invalid option", 404


# Routes for other pages
@app.route('/intro', endpoint='page1')
def page1():
    messages = intro()
    return render_template('page1.html', messages=messages)

# Routes for other pages
# New route for searching definitions
@app.route('/pydefinitions/search', methods=['POST'])
def search_definitions():
    query = request.form['query']
    
    # Validate query
    if not query or query.strip() == "":
        return "Invalid query", 400
    
    results = python_references.query.filter(python_references.name.like(f"%{query}%")).all()
    return render_template('page2.html', results=results, query=query)

# Updated route for /pydefinitions
@app.route('/pydefinitions', methods=['GET', 'POST'], endpoint='page2')
def page2():
    if request.method == 'POST':
        query = request.form['query']
        if query:  # Check for non-empty query
            results = python_references.query.filter(python_references.name.like(f"%{query}%")).all()
            return render_template('page2.html', results=results, query=query)
        else:
            results = python_references.query.order_by(python_references.id).all()
            return render_template('page2.html', results=results, query='')
    else:
        results = python_references.query.order_by(python_references.id).all()
        return render_template('page2.html', results=results, query='')

@app.route('/pyguider', methods=['GET', 'POST'], endpoint='page3')
def page3():
    if request.method == 'POST':
        return pyguider()
    else:
        messages = pyguider()
        return render_template('page3.html', messages=messages)


@app.route('/tasks', endpoint='page4')
def page4():
    messages = tasks()
    return render_template('page4.html', messages=messages)


@app.route('/about', endpoint='page5')
def page5():
    messages = about_the_app()
    return render_template('page5.html', messages=messages)


@app.route('/how_to_use', endpoint='page6')
def page6():
    messages = how_to_use()
    return render_template('page6.html', messages=messages)


@app.route('/contacts', endpoint='contacts')
def contacts():
    return render_template('contacts.html')


# Routes for handling code execution and installation
@app.route('/install_package', methods=['POST'])
def install_package():
    package_name = request.form['package_name']
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return jsonify({'success': True, 'message': f'{package_name} installed successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# Store input values
input_values = []

# Route to execute code
@app.route('/execute-code', methods=['POST'])
def execute_code():
    code = request.json['code']
    try:
        # Parse code for input() calls
        tree = ast.parse(code)
        input_count = 0
        prompts = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'input':
                input_count += 1
                # Extract prompt from input() call
                if node.args:
                    prompts.append(node.args[0].s)

        if input_count > 0:
            return jsonify({'output': '', 'input': input_count, 'prompts': prompts})
        else:
            # Execute code using Python interpreter
            output = subprocess.check_output(['python', '-c', code], stderr=subprocess.STDOUT).decode('utf-8')
            return jsonify({'output': output, 'input': 0})
    except Exception as e:
        return jsonify({'output': str(e), 'input': 0})
    
 # Route to handle user input
@app.route('/input', methods=['POST'])
def handle_input():
    input_value = request.json['input']
    code = request.json['code']
    prompt = request.json['prompt']

    # Replace input() call with input value
    modified_code = code.replace('input("' + prompt + '")', '"' + input_value + '"')

    try:
        # Execute modified code
        output = subprocess.check_output(['python', '-c', modified_code], stderr=subprocess.STDOUT).decode('utf-8')
    except Exception as e:
        output = str(e)

    return jsonify({'output': output})


# API endpoint to retrieve hints
@app.route('/hints/<string:input>', methods=['GET'])
def get_hints(input):
    try:
        # Validate input
        if not input or len(input) < 1:
            return jsonify({"error": "Invalid input length"}), 400

        # Retrieve hints from database
        results = python_references.query.filter(python_references.input.like(f"{input}%")).limit(10).all()

        # Handle no hints found
        if not results:
            return jsonify({"message": "No hints found"})

        # Convert results to JSON
        hints = [
            {
                "id": result.id,
                "input": result.input,
                "name": result.name,
                "definition": result.definition,
                "example": result.example
            }
            for result in results
        ]

        return jsonify(hints)
    except Exception as e:
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500


@app.route('/full-info/<int:id>', methods=['GET'])
def get_full_info(id):
    try:
        result = python_references.query.get(id)
        if result:
            return jsonify({
                "name": result.name,
                "definition": result.definition,
                "example": result.example
            })
        else:
            return jsonify({"error": "No data found"}), 404
    except Exception as e:
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True)   