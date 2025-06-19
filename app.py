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
        SELECT speaker, text, start_time, end_time, confidence, notes
        FROM conversation_turns 
        WHERE call_record_id = %s 
        ORDER BY start_time ASC
    ''', (call_id,))
    conversation_turns = cur.fetchall()
    
    # Get call feedback
    cur.execute('''
        SELECT what_went_well, what_could_be_improved, 
               discovery_questions_assessment, objection_handling_evaluation,
               customer_primary_concern, conversation_metrics, overall_score,
               recommendations, feedback_timestamps, transcript_references
        FROM call_feedback 
        WHERE call_id = %s
    ''', (call_id,))
    feedback = cur.fetchone()
    
    cur.close()
    conn.close()
    
    # Format conversation
    conversation = []
    for turn in conversation_turns:
        conversation.append({
            'speaker': turn['speaker'],
            'text': turn['text'],
            'start_time': float(turn['start_time']),
            'end_time': float(turn['end_time']),
            'confidence': float(turn['confidence']),
            'notes': turn['notes']
        })
    
    result = {
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
        'notes': call['notes'],
        'conversation': conversation
    }
    
    if feedback:
        result['feedback'] = {
            'what_went_well': feedback['what_went_well'],
            'what_could_be_improved': feedback['what_could_be_improved'],
            'discovery_questions_assessment': feedback['discovery_questions_assessment'],
            'objection_handling_evaluation': feedback['objection_handling_evaluation'],
            'customer_primary_concern': feedback['customer_primary_concern'],
            'conversation_metrics': feedback['conversation_metrics'] if feedback['conversation_metrics'] else {},
            'overall_score': float(feedback['overall_score']) if feedback['overall_score'] else None,
            'recommendations': feedback['recommendations'] if feedback['recommendations'] else [],
            'feedback_timestamps': feedback['feedback_timestamps'] if feedback['feedback_timestamps'] else {},
            'transcript_references': feedback['transcript_references'] if feedback['transcript_references'] else {}
        }
    
    return jsonify(result)

@app.route('/api/calls/<call_id>/update', methods=['POST'])
def update_call(call_id):
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Update call record
        cur.execute('''
            UPDATE call_records 
            SET outcome = %s, notes = %s, updated_at = NOW()
            WHERE id = %s
        ''', (data.get('outcome'), data.get('notes'), call_id))
        
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 