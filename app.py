from flask import Flask, request, jsonify
import psycopg2
import requests
import base64

app = Flask(__name__)

DB_URL = "postgresql://requisitoriados_user:x0xLGMH3N71ZfUG9UX7rcBiujKiELzKY@dpg-d114ho2li9vc738covqg-a.oregon-postgres.render.com/requisitoriados"


def connect_db():
    return psycopg2.connect(DB_URL, sslmode='require')

def init_reportes_table():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS reportes_exitosos (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER NOT NULL,
            requisitoriado_id INTEGER NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS denuncias_exitosas (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER NOT NULL,
            requisitoriado_id INTEGER NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    cur.close()
    conn.close()

@app.route('/estadisticas/denuncias', methods=['GET'])
def estadisticas_denuncias():
    intervalo = request.args.get('intervalo', 'mes')
    if intervalo not in ['dia', 'mes', 'anio']:
        return jsonify({"exito": False, "error": "Intervalo inválido"}), 400

    trunc = {
        "dia": "day",
        "mes": "month",
        "anio": "year"
    }[intervalo]

    conn = connect_db()
    cur = conn.cursor()
    cur.execute(f"""
        SELECT DATE_TRUNC('{trunc}', fecha) AS periodo, COUNT(*) 
        FROM denuncias_exitosas 
        GROUP BY periodo 
        ORDER BY periodo;
    """)
    resultados = cur.fetchall()
    cur.close()
    conn.close()

    data = [{"periodo": str(r[0]), "cantidad": r[1]} for r in resultados]
    return jsonify({"exito": True, "estadisticas": data})

@app.route('/estadisticas/localizacion', methods=['GET'])
def estadisticas_por_ubicacion():
    tipo = request.args.get('tipo', 'ciudad')
    if tipo not in ['ciudad', 'pais']:
        return jsonify({"exito": False, "error": "Tipo inválido"}), 400

    conn = connect_db()
    cur = conn.cursor()
    cur.execute(f"""
        SELECT u.{tipo}, COUNT(*) 
        FROM denuncias_exitosas d
        JOIN usuario u ON d.usuario_id = u.id
        GROUP BY u.{tipo}
        ORDER BY COUNT(*) DESC
        LIMIT 10;
    """)
    resultados = cur.fetchall()
    cur.close()
    conn.close()

    data = [{"nombre": r[0], "cantidad": r[1]} for r in resultados]
    return jsonify({"exito": True, "estadisticas": data})

@app.route('/estadisticas/top_requisitoriados', methods=['GET'])
def top_requisitoriados():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.requisitoriado_id, rq.nombre, COUNT(*) as total
        FROM denuncias_exitosas r
        JOIN requisitoriados rq ON r.requisitoriado_id = rq.id
        GROUP BY r.requisitoriado_id, rq.nombre
        ORDER BY total DESC
        LIMIT 5;
    """)
    resultados = cur.fetchall()
    cur.close()
    conn.close()

    data = [{"id": r[0], "nombre": r[1], "cantidad": r[2]} for r in resultados]
    return jsonify({"exito": True, "top_requisitoriados": data})

if __name__ != '__main__':
    init_reportes_table()
else:
    init_reportes_table()
    app.run(debug=True)
