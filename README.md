# Flask School Report CRM App with MySQL Integration

![Python](https://img.shields.io/badge/Python-3.9-blue)
![Flask](https://img.shields.io/badge/Flask-2.0-green)
![HTML](https://img.shields.io/badge/HTML-5-orange)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.0-blue)
![Font Awesome](https://img.shields.io/badge/Font%20Awesome-6.0-green)
![jQuery](https://img.shields.io/badge/jQuery-3.6.0-blue)


This is a full-stack School Report CRM built using:
- **Python** and **Flask** for the backend.
- **HTML**, **TailwindCSS**, and **Font Awesome** for the frontend.
- **jQuery** for client-side interactivity.
- Connecting to a MySQL database.
- Using Flask routes to handle HTTP requests.
- Exporting data to Excel.
- Utility functions for rendering templates.

## Features

- **Flask Framework**: A lightweight WSGI web application framework.
- **MySQL Integration**: Connect and query a MySQL database.
- **Secure Authentication**: Password hashing using Werkzeug.
- **Dynamic Web Pages**: Render templates with context variables.
- **Excel Export**: Generate Excel files with Pandas and XlsxWriter.
- **Dynamic Reports**: Real-time data filtering and export.
- **Responsive Design**: Fully responsive UI with TailwindCSS.
- **Interactive Elements**: Smooth client-side interactions with jQuery.

---

## Getting Started

### Prerequisites

1. Python 3.10 or later.
2. MySQL installed and running.
3. Required Python packages:
   - Flask
   - mysql-connector-python
   - pandas
   - xlsxwriter

---

### Installation

1. Clone the repository or copy the code files.

```bash
# Clone the repository
git clone https://github.com/bishnu93bca/school-report-crm.git
cd school-report-crm
```

2. Set up a Python virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install flask mysql-connector-python pandas xlsxwriter
```

4. Set up the MySQL database:
   - Create a MySQL database named `school`.
   - Create necessary tables as per your schema.

5. Update the database connection details in the code:

```python
# MySQL connection
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="password",
        database="school"
    )
```

---

### Running the Application

1. Start the Flask app:

```bash
python app.py
```

2. Open your web browser and go to:

```
http://127.0.0.1:5000/
```

---

### Key Files

- **`app.py`**: The main Flask application file.
- **Templates**: HTML files stored in the `templates/` directory.
- **Static**: Static files (CSS, JS, images) in the `static/` directory.

---

### Export to Excel Example

The application includes functionality to export data from MySQL to an Excel file using Pandas and XlsxWriter. An example route:

```python
@app.route('/export_excel')
def export_excel():
    query = "SELECT * FROM some_table"
    cursor.execute(query)
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=['Column1', 'Column2', 'Column3'])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')

    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', download_name='data.xlsx')
```

---

### Utility Functions

#### Active Class Utility

This utility helps dynamically set the active class for navigation links:

```python
@app.context_processor
def utility_processor():
    def active_class(page_name, active_page):
        return 'active' if page_name == active_page else ''
    return dict(active_class=active_class)
```

---

### Troubleshooting

1. **MySQL Connection Issues**:
   - Ensure MySQL server is running.
   - Double-check connection details (host, user, password, database).

2. **Missing Packages**:
   - Run `pip install -r requirements.txt` if a `requirements.txt` file exists.
   - Install individual packages with `pip install <package-name>`.

3. **Excel Export Issues**:
   - Ensure Pandas and XlsxWriter are installed and imported correctly.
   - Verify that the `some_table` query fetches valid data.

---

### Next Steps

- Add more routes for additional features.
- Enhance database schema for more complex functionality.
- Implement authentication and session management for secure access.

---

### License

This project is licensed under the MIT License. Feel free to use and modify it as needed.




