from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
import os
import json
import pandas as pd

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'
db = SQLAlchemy(app)

# Ensure directories exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)

class Data(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_year = db.Column(db.String(80), nullable=False)
    make = db.Column(db.String(80), nullable=False)
    model = db.Column(db.String(80), nullable=False)
    rejection_percentage = db.Column(db.String(10), nullable=False)
    reason_1 = db.Column(db.String(200), nullable=False)
    reason_2 = db.Column(db.String(200), nullable=False)
    reason_3 = db.Column(db.String(200), nullable=False)

# Create the database and tables within an application context
with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and file.filename.endswith('.json'):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            with open(filepath) as f:
                data = json.load(f)
                for item in data:
                    record = Data.query.filter_by(model_year=item['model_year'], make=item['make'], model=item['model']).first()
                    if record:
                        record.rejection_percentage = item['rejection_percentage']
                        record.reason_1 = item['reason_1']
                        record.reason_2 = item['reason_2']
                        record.reason_3 = item['reason_3']
                    else:
                        new_record = Data(
                            model_year=item['model_year'],
                            make=item['make'],
                            model=item['model'],
                            rejection_percentage=item['rejection_percentage'],
                            reason_1=item['reason_1'],
                            reason_2=item['reason_2'],
                            reason_3=item['reason_3']
                        )
                        db.session.add(new_record)
                db.session.commit()
            flash('File successfully uploaded and data updated/added.')
            return redirect(url_for('index'))
        else:
            flash('Only JSON files are allowed')
            return redirect(request.url)
    data = Data.query.all()
    df = pd.DataFrame([(d.id, d.model_year, d.make, d.model, d.rejection_percentage, d.reason_1, d.reason_2, d.reason_3) for d in data],
                      columns=['ID', 'Model Year', 'Make', 'Model', 'Rejection Percentage', 'Reason 1', 'Reason 2', 'Reason 3'])
    table = df.to_html(classes='table table-striped', index=False)
    return render_template('index.html', table=table)

@app.route('/search')
def search():
    query = request.args.get('query', '')
    if query:
        results = Data.query.filter(
            (Data.model_year.ilike(f'%{query}%')) |
            (Data.make.ilike(f'%{query}%')) |
            (Data.model.ilike(f'%{query}%')) |
            (Data.rejection_percentage.ilike(f'%{query}%')) |
            (Data.reason_1.ilike(f'%{query}%')) |
            (Data.reason_2.ilike(f'%{query}%')) |
            (Data.reason_3.ilike(f'%{query}%'))
        ).limit(50).all()
        result_list = [
            {
                'model_year': r.model_year,
                'make': r.make,
                'model': r.model,
                'rejection_percentage': r.rejection_percentage,
                'reason_1': r.reason_1,
                'reason_2': r.reason_2,
                'reason_3': r.reason_3
            }
            for r in results
        ]
        return jsonify(result_list)
    return jsonify([])

if __name__ == '__main__':
    app.run(debug=True)
