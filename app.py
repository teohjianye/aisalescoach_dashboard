from flask import Flask, render_template, jsonify, request
import psycopg2
import psycopg2.extras
from datetime import datetime
import json
from collections import defaultdict

app = Flask(__name__)

# Azure PostgreSQL connection configuration (same as mobile app)
DB_CONFIG = {
    'host': 'aisalescoach.postgres.database.azure.com',
    'port': 5432,
    'database': 'postgres',
    'user': 'aisalescoach',
    'password': 'Q4me?7g7',
    'sslmode': 'require',  # Azure requires SSL
    'connect_timeout': 30,
    'application_name': 'ai_sales_coaching_webapp'
}

def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/customer-outcomes')
def customer_outcomes():
    return render_template('customer_outcomes.html')

@app.route('/api/calls')
def get_calls():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM call_records ORDER BY timestamp DESC')
    calls = cur.fetchall()
    cur.close()
    conn.close()
    
    calls_list = []
    for call in calls:
        calls_list.append({
            'id': call['id'],
            'timestamp': call['timestamp'].isoformat() if call['timestamp'] else None,
            'duration': call['duration'],
            'sales_rep_name': call['sales_rep_name'],
            'customer_name': call['customer_name'],
            'status': call['status'],
            'call_type': call['call_type'],
            'outcome': call['outcome'],
            'notes': call['notes']
        })
    
    return jsonify(calls_list)

@app.route('/api/dashboard/overview')
def get_dashboard_overview():
    call_type = request.args.get('call_type')
    outcome = request.args.get('outcome')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Build dynamic query for call type statistics
    where_clause = "WHERE 1=1"
    params = []
    
    if call_type:
        where_clause += " AND cr.call_type = %s"
        params.append(call_type)
    
    if outcome:
        where_clause += " AND cr.outcome = %s"
        params.append(outcome)
    
    # Get call type statistics with average scores
    query = f'''
        SELECT 
            cr.call_type,
            COUNT(*) as call_count,
            ROUND(AVG(cf.overall_score)::numeric, 2) as avg_score,
            COUNT(CASE WHEN cr.outcome = 'Won' THEN 1 END) as won_count,
            COUNT(CASE WHEN cr.outcome = 'Lost' THEN 1 END) as lost_count,
            COUNT(CASE WHEN cr.outcome = 'Follow up required' THEN 1 END) as follow_up_count,
            COUNT(CASE WHEN cr.outcome = 'Escalated' THEN 1 END) as escalated_count
        FROM call_records cr
        LEFT JOIN call_feedback cf ON cr.id = cf.call_id
        {where_clause}
        GROUP BY cr.call_type
        ORDER BY call_count DESC
    '''
    cur.execute(query, params)
    call_type_stats = cur.fetchall()
    
    # Get sales rep statistics
    cur.execute('''
        SELECT 
            cr.sales_rep_name,
            COUNT(*) as call_count,
            ROUND(AVG(cf.overall_score)::numeric, 2) as avg_score,
            COUNT(CASE WHEN cr.outcome = 'Won' THEN 1 END) as won_count,
            COUNT(CASE WHEN cr.outcome = 'Lost' THEN 1 END) as lost_count
        FROM call_records cr
        LEFT JOIN call_feedback cf ON cr.id = cf.call_id
        GROUP BY cr.sales_rep_name
        ORDER BY avg_score DESC
    ''')
    sales_rep_stats = cur.fetchall()
    
    # Get overall statistics
    cur.execute('''
        SELECT 
            COUNT(*) as total_calls,
            ROUND(AVG(cf.overall_score)::numeric, 2) as overall_avg_score,
            COUNT(CASE WHEN cr.outcome = 'Won' THEN 1 END) as total_won,
            COUNT(CASE WHEN cr.outcome = 'Lost' THEN 1 END) as total_lost,
            COUNT(CASE WHEN cr.outcome = 'Follow up required' THEN 1 END) as total_follow_up,
            COUNT(CASE WHEN cr.outcome = 'Escalated' THEN 1 END) as total_escalated
        FROM call_records cr
        LEFT JOIN call_feedback cf ON cr.id = cf.call_id
    ''')
    overall_stats = cur.fetchone()
    
    cur.close()
    conn.close()
    
    # Convert rows to dictionaries
    call_type_data = []
    for row in call_type_stats:
        call_type_data.append({
            'call_type': row['call_type'],
            'call_count': row['call_count'],
            'avg_score': float(row['avg_score']) if row['avg_score'] else 0,
            'won_count': row['won_count'],
            'lost_count': row['lost_count'],
            'follow_up_count': row['follow_up_count'],
            'escalated_count': row['escalated_count'],
            'win_rate': round((row['won_count'] / row['call_count']) * 100, 1) if row['call_count'] > 0 else 0
        })
    
    sales_rep_data = []
    for row in sales_rep_stats:
        sales_rep_data.append({
            'sales_rep_name': row['sales_rep_name'],
            'call_count': row['call_count'],
            'avg_score': float(row['avg_score']) if row['avg_score'] else 0,
            'won_count': row['won_count'],
            'lost_count': row['lost_count'],
            'win_rate': round((row['won_count'] / row['call_count']) * 100, 1) if row['call_count'] > 0 else 0
        })
    
    return jsonify({
        'call_types': call_type_data,
        'sales_reps': sales_rep_data,
        'overall': {
            'total_calls': overall_stats['total_calls'],
            'overall_avg_score': float(overall_stats['overall_avg_score']) if overall_stats['overall_avg_score'] else 0,
            'total_won': overall_stats['total_won'],
            'total_lost': overall_stats['total_lost'],
            'total_follow_up': overall_stats['total_follow_up'],
            'total_escalated': overall_stats['total_escalated'],
            'overall_win_rate': round((overall_stats['total_won'] / overall_stats['total_calls']) * 100, 1) if overall_stats['total_calls'] > 0 else 0
        }
    })

@app.route('/api/calls/filter')
def get_filtered_calls():
    call_type = request.args.get('call_type')
    sales_rep = request.args.get('sales_rep')
    customer = request.args.get('customer')
    outcome = request.args.get('outcome')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Build dynamic query
    query = '''
        SELECT cr.*, cf.overall_score
        FROM call_records cr
        LEFT JOIN call_feedback cf ON cr.id = cf.call_id
        WHERE 1=1
    '''
    params = []
    
    if call_type:
        query += ' AND cr.call_type = %s'
        params.append(call_type)
    
    if sales_rep:
        query += ' AND cr.sales_rep_name = %s'
        params.append(sales_rep)
    
    if customer:
        query += ' AND cr.customer_name = %s'
        params.append(customer)
    
    if outcome:
        query += ' AND cr.outcome = %s'
        params.append(outcome)
    
    query += ' ORDER BY cr.timestamp DESC'
    
    cur.execute(query, params)
    calls = cur.fetchall()
    cur.close()
    conn.close()
    
    calls_list = []
    for call in calls:
        calls_list.append({
            'id': call['id'],
            'timestamp': call['timestamp'].isoformat() if call['timestamp'] else None,
            'duration': call['duration'],
            'sales_rep_name': call['sales_rep_name'],
            'customer_name': call['customer_name'],
            'status': call['status'],
            'call_type': call['call_type'],
            'outcome': call['outcome'],
            'notes': call['notes'],
            'overall_score': float(call['overall_score']) if call['overall_score'] else None
        })
    
    return jsonify(calls_list)

@app.route('/api/calls/<call_id>')
def get_call_details(call_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get call record
    cur.execute('SELECT * FROM call_records WHERE id = %s', (call_id,))
    call = cur.fetchone()
    
    if not call:
        cur.close()
        conn.close()
        return jsonify({'error': 'Call not found'}), 404
    
    # Get conversation turns
    cur.execute('''
        SELECT * FROM conversation_turns 
        WHERE call_record_id = %s 
        ORDER BY id ASC
    ''', (call_id,))
    turns = cur.fetchall()
    
    # Get feedback
    cur.execute('SELECT * FROM call_feedback WHERE call_id = %s', (call_id,))
    feedback = cur.fetchone()
    
    cur.close()
    conn.close()
    
    # Format response
    result = {
        'call': {
            'id': call['id'],
            'timestamp': call['timestamp'].isoformat() if call['timestamp'] else None,
            'duration': call['duration'],
            'sales_rep_name': call['sales_rep_name'],
            'customer_name': call['customer_name'],
            'audio_file_path': call['audio_file_path'],
            'transcription': call['transcription'],
            'status': call['status'],
            'call_type': call['call_type'],
            'outcome': call['outcome'],
            'notes': call['notes']
        },
        'turns': []
    }
    
    for turn in turns:
        result['turns'].append({
            'id': turn['id'],
            'speaker': turn['speaker'],
            'text': turn['text'],
            'start_time': float(turn['start_time']) if turn['start_time'] else None,
            'end_time': float(turn['end_time']) if turn['end_time'] else None,
            'confidence': float(turn['confidence']) if turn['confidence'] else None,
            'notes': turn['notes']
        })
    
    if feedback:
        # Handle JSON parsing for complex fields (same as mobile app)
        try:
            conversation_metrics = feedback['conversation_metrics']
            if isinstance(conversation_metrics, str):
                conversation_metrics = json.loads(conversation_metrics)
            elif conversation_metrics is None:
                conversation_metrics = {}
        except (json.JSONDecodeError, TypeError):
            conversation_metrics = {}
        
        try:
            recommendations = feedback['recommendations']
            if isinstance(recommendations, str):
                recommendations = json.loads(recommendations)
            elif recommendations is None:
                recommendations = []
        except (json.JSONDecodeError, TypeError):
            recommendations = []
        
        try:
            feedback_timestamps = feedback['feedback_timestamps']
            if isinstance(feedback_timestamps, str):
                feedback_timestamps = json.loads(feedback_timestamps)
            elif feedback_timestamps is None:
                feedback_timestamps = {}
        except (json.JSONDecodeError, TypeError):
            feedback_timestamps = {}
        
        try:
            transcript_references = feedback['transcript_references']
            if isinstance(transcript_references, str):
                transcript_references = json.loads(transcript_references)
            elif transcript_references is None:
                transcript_references = {}
        except (json.JSONDecodeError, TypeError):
            transcript_references = {}
        
        result['feedback'] = {
            'what_went_well': feedback['what_went_well'],
            'what_could_be_improved': feedback['what_could_be_improved'],
            'discovery_questions_assessment': feedback['discovery_questions_assessment'],
            'objection_handling_evaluation': feedback['objection_handling_evaluation'],
            'customer_primary_concern': feedback['customer_primary_concern'],
            'conversation_metrics': conversation_metrics,
            'overall_score': float(feedback['overall_score']) if feedback['overall_score'] else None,
            'recommendations': recommendations,
            'feedback_timestamps': feedback_timestamps,
            'transcript_references': transcript_references
        }
    
    return jsonify(result)

@app.route('/api/calls/<call_id>/update', methods=['POST'])
def update_call(call_id):
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Update call record (including call_type which was missing)
        cur.execute('''
            UPDATE call_records 
            SET call_type = %s, outcome = %s, notes = %s, updated_at = NOW()
            WHERE id = %s
        ''', (data.get('call_type'), data.get('outcome'), data.get('notes'), call_id))
        
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/calls/new', methods=['POST'])
def create_call():
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Insert new call record
        cur.execute('''
            INSERT INTO call_records (
                id, timestamp, duration, sales_rep_name, customer_name,
                audio_file_path, transcription, status, call_type, outcome, notes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            data['id'],
            data['timestamp'],
            data['duration'],
            data['sales_rep_name'],
            data['customer_name'],
            data['audio_file_path'],
            data['transcription'],
            data['status'],
            data['call_type'],
            data.get('outcome'),
            data.get('notes')
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': str(e)}), 500

# Customer Management API Endpoints

@app.route('/api/customers')
def get_customers():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM customers ORDER BY name ASC')
    customers = cur.fetchall()
    cur.close()
    conn.close()
    
    customers_list = []
    for customer in customers:
        customers_list.append({
            'id': customer['id'],
            'name': customer['name'],
            'company': customer['company'],
            'phone': customer['phone'],
            'email': customer['email'],
            'notes': customer['notes'],
            'created_at': customer['created_at'].isoformat() if customer['created_at'] else None,
            'updated_at': customer['updated_at'].isoformat() if customer['updated_at'] else None
        })
    
    return jsonify(customers_list)

@app.route('/api/customers', methods=['POST'])
def create_customer():
    data = request.json
    
    if not data or not data.get('name'):
        return jsonify({'error': 'Name is required'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            INSERT INTO customers (id, name, company, phone, email, notes, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        ''', (
            data['id'],
            data['name'],
            data.get('company'),
            data.get('phone'),
            data.get('email'),
            data.get('notes')
        ))
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'message': 'Customer created successfully'}), 201
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/customers/<customer_id>', methods=['PUT'])
def update_customer(customer_id):
    data = request.json
    
    if not data or not data.get('name'):
        return jsonify({'error': 'Name is required'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            UPDATE customers 
            SET name = %s, company = %s, phone = %s, email = %s, notes = %s, updated_at = NOW()
            WHERE id = %s
        ''', (
            data['name'],
            data.get('company'),
            data.get('phone'),
            data.get('email'),
            data.get('notes'),
            customer_id
        ))
        
        if cur.rowcount == 0:
            cur.close()
            conn.close()
            return jsonify({'error': 'Customer not found'}), 404
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'message': 'Customer updated successfully'})
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/customers/<customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('DELETE FROM customers WHERE id = %s', (customer_id,))
        
        if cur.rowcount == 0:
            cur.close()
            conn.close()
            return jsonify({'error': 'Customer not found'}), 404
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'message': 'Customer deleted successfully'})
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': str(e)}), 500

# Sales Rep Management API Endpoints

@app.route('/api/sales-reps')
def get_sales_reps():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM sales_reps ORDER BY name ASC')
    sales_reps = cur.fetchall()
    cur.close()
    conn.close()
    
    sales_reps_list = []
    for sales_rep in sales_reps:
        sales_reps_list.append({
            'id': sales_rep['id'],
            'name': sales_rep['name'],
            'email': sales_rep['email'],
            'phone': sales_rep['phone'],
            'title': sales_rep['title'],
            'department': sales_rep['department'],
            'created_at': sales_rep['created_at'].isoformat() if sales_rep['created_at'] else None,
            'updated_at': sales_rep['updated_at'].isoformat() if sales_rep['updated_at'] else None
        })
    
    return jsonify(sales_reps_list)

@app.route('/api/sales-reps', methods=['POST'])
def create_sales_rep():
    data = request.json
    
    if not data or not data.get('name'):
        return jsonify({'error': 'Name is required'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            INSERT INTO sales_reps (id, name, email, phone, title, department, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        ''', (
            data['id'],
            data['name'],
            data.get('email'),
            data.get('phone'),
            data.get('title'),
            data.get('department')
        ))
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'message': 'Sales rep created successfully'}), 201
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/sales-reps/<sales_rep_id>', methods=['PUT'])
def update_sales_rep(sales_rep_id):
    data = request.json
    
    if not data or not data.get('name'):
        return jsonify({'error': 'Name is required'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            UPDATE sales_reps 
            SET name = %s, email = %s, phone = %s, title = %s, department = %s, updated_at = NOW()
            WHERE id = %s
        ''', (
            data['name'],
            data.get('email'),
            data.get('phone'),
            data.get('title'),
            data.get('department'),
            sales_rep_id
        ))
        
        if cur.rowcount == 0:
            cur.close()
            conn.close()
            return jsonify({'error': 'Sales rep not found'}), 404
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'message': 'Sales rep updated successfully'})
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/sales-reps/<sales_rep_id>', methods=['DELETE'])
def delete_sales_rep(sales_rep_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('DELETE FROM sales_reps WHERE id = %s', (sales_rep_id,))
        
        if cur.rowcount == 0:
            cur.close()
            conn.close()
            return jsonify({'error': 'Sales rep not found'}), 404
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'message': 'Sales rep deleted successfully'})
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': str(e)}), 500

# Filter options endpoints

@app.route('/api/filter-options')
def get_filter_options():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get unique sales reps
    cur.execute('SELECT DISTINCT sales_rep_name FROM call_records WHERE sales_rep_name IS NOT NULL ORDER BY sales_rep_name')
    sales_reps = [row['sales_rep_name'] for row in cur.fetchall()]
    
    # Get unique customers
    cur.execute('SELECT DISTINCT customer_name FROM call_records WHERE customer_name IS NOT NULL ORDER BY customer_name')
    customers = [row['customer_name'] for row in cur.fetchall()]
    
    # Get unique call types
    cur.execute('SELECT DISTINCT call_type FROM call_records WHERE call_type IS NOT NULL ORDER BY call_type')
    call_types = [row['call_type'] for row in cur.fetchall()]
    
    # Get unique outcomes
    cur.execute('SELECT DISTINCT outcome FROM call_records WHERE outcome IS NOT NULL ORDER BY outcome')
    outcomes = [row['outcome'] for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return jsonify({
        'sales_reps': sales_reps,
        'customers': customers,
        'call_types': call_types,
        'outcomes': outcomes
    })

@app.route('/api/customer-outcomes')
def get_customer_outcomes():
    """Get all calls organized by their outcomes"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get all call records
    cur.execute('''
        SELECT 
            id,
            customer_name,
            sales_rep_name,
            call_type,
            outcome,
            timestamp,
            duration,
            status,
            notes
        FROM call_records 
        ORDER BY timestamp DESC
    ''')
    
    calls = cur.fetchall()
    cur.close()
    conn.close()
    
    # Organize all calls by outcome
    outcome_groups = {
        'Won': [],
        'Follow up required': [],
        'Lost': [],
        'Escalated': [],
        'No outcome': []  # For calls without an outcome
    }
    
    for call in calls:
        outcome = call['outcome'] if call['outcome'] else 'No outcome'
        if outcome not in outcome_groups:
            outcome_groups[outcome] = []
            
        outcome_groups[outcome].append({
            'call_id': call['id'],
            'customer_name': call['customer_name'] or 'No customer name',
            'sales_rep_name': call['sales_rep_name'],
            'timestamp': call['timestamp'].isoformat() if call['timestamp'] else None,
            'call_type': call['call_type'],
            'outcome': call['outcome'],
            'duration': call['duration'],
            'status': call['status'],
            'notes': call['notes']
        })
    
    return jsonify(outcome_groups)

@app.route('/api/customer-outcomes/update', methods=['POST'])
def update_customer_outcome():
    """Update the outcome for a specific call"""
    data = request.json
    call_id = data.get('call_id')
    new_outcome = data.get('outcome')
    
    if not call_id or not new_outcome:
        return jsonify({'error': 'Call ID and outcome are required'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Update the outcome for the specific call
        cur.execute('''
            UPDATE call_records 
            SET outcome = %s, updated_at = NOW()
            WHERE id = %s
        ''', (new_outcome, call_id))
        
        if cur.rowcount == 0:
            cur.close()
            conn.close()
            return jsonify({'error': 'Call not found'}), 404
        
        # Get the call details for the response message
        cur.execute('''
            SELECT customer_name, sales_rep_name FROM call_records 
            WHERE id = %s
        ''', (call_id,))
        
        call_details = cur.fetchone()
        customer_name = call_details['customer_name'] or 'Unknown customer'
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'message': f'Updated call for {customer_name} to {new_outcome}'})
        
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 