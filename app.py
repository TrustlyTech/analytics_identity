from flask import Flask, request, jsonify
import psycopg2

app = Flask(__name__)

DB_URL = "postgresql://requisitoriados_user:x0xLGMH3N71ZfUG9UX7rcBiujKiELzKY@dpg-d114ho2li9vc738covqg-a.oregon-postgres.render.com/requisitoriados"

def connect_db():
    return psycopg2.connect(DB_URL, sslmode='require')

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
        FROM auditoria_denuncias 
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
        SELECT {tipo}, COUNT(*)
        FROM auditoria_denuncias
        GROUP BY {tipo}
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
        SELECT requisitoriado_nombre, COUNT(*) as total
        FROM auditoria_denuncias
        GROUP BY requisitoriado_nombre
        ORDER BY total DESC
        LIMIT 5;
    """)
    resultados = cur.fetchall()
    cur.close()
    conn.close()

    data = [{"nombre": r[0], "cantidad": r[1]} for r in resultados]
    return jsonify({"exito": True, "top_requisitoriados": data})

# No necesitas crear tablas aquí porque ya se usa auditoria_denuncias

if __name__ == '__main__':
    app.run(debug=True)
