from flask import Flask, request, jsonify
import psycopg2

app = Flask(__name__)

DB_URL = "postgresql://requisitoriados_user:x0xLGMH3N71ZfUG9UX7rcBiujKiELzKY@dpg-d114ho2li9vc738covqg-a.oregon-postgres.render.com/requisitoriados"

def connect_db():
    return psycopg2.connect(DB_URL, sslmode='require')

@app.route('/estadisticas/denuncias', methods=['GET'])
def estadisticas_denuncias():
    intervalo = request.args.get('intervalo', 'mes')

    # Definir truncado y rangos según el tipo de intervalo
    hoy = datetime.now()
    if intervalo == 'mes':
        trunc = 'week'
        desde = hoy - timedelta(days=30)
    elif intervalo == '6M':
        trunc = 'month'
        desde = hoy - timedelta(days=180)
    elif intervalo == 'YTD':
        trunc = 'month'
        desde = datetime(hoy.year, 1, 1)
    elif intervalo == '1Y':
        trunc = 'month'  # O 'quarter' si prefieres menos puntos
        desde = hoy - timedelta(days=365)
    elif intervalo in ['dia', 'anio']:  # soporte adicional original
        trunc = 'day' if intervalo == 'dia' else 'year'
        desde = hoy - timedelta(days=30 if intervalo == 'dia' else 365)
    else:
        return jsonify({"exito": False, "error": "Intervalo inválido"}), 400

    conn = connect_db()
    cur = conn.cursor()
    cur.execute(f"""
        SELECT DATE_TRUNC('{trunc}', fecha) AS periodo, COUNT(*) 
        FROM auditoria_denuncias 
        WHERE fecha >= %s AND fecha <= %s
        GROUP BY periodo 
        ORDER BY periodo;
    """, (desde, hoy))
    resultados = cur.fetchall()
    cur.close()
    conn.close()

    data = [{"periodo": r[0].strftime("%Y-%m-%d"), "cantidad": r[1]} for r in resultados]
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
