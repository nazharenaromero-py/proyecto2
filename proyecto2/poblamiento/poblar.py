import random
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy import create_engine, text

random.seed(7)
Faker.seed(7)
fake = Faker("es_CL")

DATABASE_URL = "mysql+pymysql://root:ROOT@localhost:3306/gestion_centros_deportivos"
engine = create_engine(DATABASE_URL)


def fecha_random(dias_atras=150, dias_adelante=20):
    hoy = datetime.now().date()
    return hoy + timedelta(days=random.randint(-dias_atras, dias_adelante))


def fecha_hora_random(dias_atras=120):
    dt = datetime.now() - timedelta(
        days=random.randint(0, dias_atras),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def poblar_todo():
    with engine.begin() as conn:
        # 1. Comunas (7)
        comunas = [
            ("Santiago", "Metropolitana", "Municipalidad de Santiago"),
            ("Providencia", "Metropolitana", "Municipalidad de Providencia"),
            ("Ñuñoa", "Metropolitana", "Corporación de Deportes de Ñuñoa"),
            ("Maipú", "Metropolitana", "Municipalidad de Maipú"),
            ("Valparaíso", "Valparaíso", "Municipalidad de Valparaíso"),
            ("Viña del Mar", "Valparaíso", "Casa del Deporte Viña del Mar"),
            ("Concepción", "Biobío", "Municipalidad de Concepción"),
        ]
        for nom, reg, org in comunas:
            conn.execute(
                text("""
                    INSERT INTO comuna (nombre_comuna, region, organismo_responsable)
                    VALUES (:nom, :reg, :org)
                """),
                {"nom": nom, "reg": reg, "org": org},
            )

        cod_comunas = [r[0] for r in conn.execute(text("SELECT cod_comuna FROM comuna")).fetchall()]

        # 2. Centros deportivos (15)
        for i in range(1, 16):
            conn.execute(
                text("""
                    INSERT INTO centro_deportivo (
                        cod_comuna, nombre_centro, direccion, fecha_apertura,
                        capacidad_maxima, presupuesto_anual, estado_operativo
                    )
                    VALUES (
                        :cod_comuna, :nombre_centro, :direccion, :fecha_apertura,
                        :capacidad_maxima, :presupuesto_anual, :estado_operativo
                    )
                """),
                {
                    "cod_comuna": random.choice(cod_comunas),
                    "nombre_centro": f"Centro Deportivo {i}",
                    "direccion": fake.street_address(),
                    "fecha_apertura": fecha_random(3000, -300),
                    "capacidad_maxima": random.randint(200, 1000),
                    "presupuesto_anual": round(random.uniform(50000000, 250000000), 2),
                    "estado_operativo": random.choice(["Activo", "Activo", "En Mantención"]),
                },
            )

        cod_centros = [r[0] for r in conn.execute(text("SELECT cod_centro FROM centro_deportivo")).fetchall()]

        # 3. Espacios deportivos (45)
        for cod_cen in cod_centros:
            for e in range(1, 4):
                piso = random.choice(["Madera", "Sintético", "Cemento", "Agua"])
                conn.execute(
                    text("""
                        INSERT INTO espacio_deportivo (
                            cod_centro, nombre_espacio, superficie, capacidad,
                            tipo_piso, condicion_actual, nivel_acceso, espacio_activo
                        )
                        VALUES (
                            :cod_centro, :nombre_espacio, :superficie, :capacidad,
                            :tipo_piso, :condicion_actual, :nivel_acceso, :espacio_activo
                        )
                    """),
                    {
                        "cod_centro": cod_cen,
                        "nombre_espacio": f"Espacio {cod_cen}-{e}",
                        "superficie": round(random.uniform(100.0, 1200.0), 2),
                        "capacidad": random.randint(20, 100),
                        "tipo_piso": piso,
                        "condicion_actual": random.choice(["Óptima", "Regular", "En Reparación"]),
                        "nivel_acceso": random.choice(["Público", "Socios", "Competitivo"]),
                        "espacio_activo": 1,
                    },
                )

        espacios = [r[0] for r in conn.execute(text("SELECT numero_interno FROM espacio_deportivo")).fetchall()]

        # 4. Personas y teléfonos (260 personas -> ~200 participantes + 60 staff)
        ruts = []
        for idx in range(1, 261):
            rut = f"{10000000 + idx}-{idx % 10}"
            ruts.append(rut)
            funcion = "Participante" if idx > 60 else random.choice(["Entrenamiento", "Mantención", "Administración"])

            conn.execute(
                text("""
                    INSERT INTO persona (
                        rut_persona, primer_nombre, apellido_paterno, apellido_materno,
                        fecha_nacimiento, email, funciones, persona_activa
                    )
                    VALUES (
                        :rut_persona, :primer_nombre, :apellido_paterno, :apellido_materno,
                        :fecha_nacimiento, :email, :funciones, :persona_activa
                    )
                """),
                {
                    "rut_persona": rut,
                    "primer_nombre": fake.first_name(),
                    "apellido_paterno": fake.last_name(),
                    "apellido_materno": fake.last_name(),
                    "fecha_nacimiento": fecha_random(16000, -5500),
                    "email": f"persona{idx}@correo.cl",
                    "funciones": funcion,
                    "persona_activa": 1,
                },
            )

            conn.execute(
                text("""
                    INSERT INTO persona_telefono (rut_persona, telefono)
                    VALUES (:rut_persona, :telefono)
                """),
                {"rut_persona": rut, "telefono": f"+569{random.randint(10000000, 99999999)}"},
            )

        ruts_instructores = [
            r[0] for r in conn.execute(text("SELECT rut_persona FROM persona WHERE funciones = 'Entrenamiento'")).fetchall()
        ] or ruts[:10]
        ruts_mantencion = [
            r[0] for r in conn.execute(text("SELECT rut_persona FROM persona WHERE funciones = 'Mantención'")).fetchall()
        ] or ruts[:10]
        ruts_participantes = ruts[60:]

        # 5. Roles, usuarios y usuario_rol (50 usuarios)
        for rol_nom, desc in [
            ("Administrador", "Acceso total"),
            ("Coordinador", "Gestión de actividades y reportes"),
            ("Operador", "Registro diario"),
        ]:
            conn.execute(
                text("INSERT INTO rol (nombre_rol, descripcion) VALUES (:nom, :desc)"),
                {"nom": rol_nom, "desc": desc},
            )

        cod_roles = [r[0] for r in conn.execute(text("SELECT cod_rol FROM rol")).fetchall()]
        for u in range(1, 51):
            conn.execute(
                text("""
                    INSERT INTO usuario_sistema (
                        rut_persona, username, password, estado_cuenta, fecha_creacion
                    )
                    VALUES (
                        :rut_persona, :username, :password, :estado_cuenta, :fecha_creacion
                    )
                """),
                {
                    "rut_persona": ruts[u - 1],
                    "username": f"usuario_{u}",
                    "password": f"pass_{u}",
                    "estado_cuenta": "Activo",
                    "fecha_creacion": fecha_random(300, -10),
                },
            )
            uid = conn.execute(text("SELECT LAST_INSERT_ID()")).scalar()
            for r_id in random.sample(cod_roles, k=random.randint(1, 2)):
                conn.execute(
                    text("INSERT INTO usuario_rol (id_usuario, cod_rol) VALUES (:uid, :rid)"),
                    {"uid": uid, "rid": r_id},
                )

        # 6. Programas deportivos (6)
        for p in range(1, 7):
            f_ini = fecha_random(180, -30)
            f_fin = f_ini + timedelta(days=90)
            conn.execute(
                text("""
                    INSERT INTO programa_deportivo (nombre_programa, objetivo, fecha_inicio, fecha_termino)
                    VALUES (:nom, :obj, :fini, :ffin)
                """),
                {
                    "nom": f"Programa Deportivo {p}",
                    "obj": f"Objetivo del programa {p}",
                    "fini": f_ini,
                    "ffin": f_fin,
                },
            )

        cod_programas = [r[0] for r in conn.execute(text("SELECT cod_programa FROM programa_deportivo")).fetchall()]

        # 7. Actividades y subtipos (48)
        tipos = ["Individual", "Grupal", "Acuática"]
        for a in range(1, 49):
            tipo = tipos[a % 3]
            conn.execute(
                text("""
                    INSERT INTO actividad (
                        cod_programa, nombre_actividad, duracion_estimada, nivel_dificultad,
                        cupo_maximo, valor_inscripcion, tipo_actividad, actividad_activa
                    )
                    VALUES (
                        :cod_programa, :nombre_actividad, :duracion_estimada, :nivel_dificultad,
                        :cupo_maximo, :valor_inscripcion, :tipo_actividad, :actividad_activa
                    )
                """),
                {
                    "cod_programa": random.choice(cod_programas),
                    "nombre_actividad": f"Actividad {a}",
                    "duracion_estimada": random.choice([45, 60, 90]),
                    "nivel_dificultad": random.choice(["Básico", "Intermedio", "Avanzado"]),
                    "cupo_maximo": random.randint(15, 35),
                    "valor_inscripcion": random.choice([0.0, 5000.0, 10000.0, 15000.0]),
                    "tipo_actividad": tipo,
                    "actividad_activa": 1,
                },
            )
            cod_act = conn.execute(text("SELECT LAST_INSERT_ID()")).scalar()

            if tipo == "Individual":
                conn.execute(
                    text("INSERT INTO actividad_individual (cod_actividad, equipamiento_requerido) VALUES (:id, :eq)"),
                    {"id": cod_act, "eq": "Implemento personal"},
                )
            elif tipo == "Grupal":
                conn.execute(
                    text("INSERT INTO actividad_grupal (cod_actividad, cantidad_minima_participantes) VALUES (:id, :min_p)"),
                    {"id": cod_act, "min_p": random.randint(6, 12)},
                )
            else:
                conn.execute(
                    text("""
                        INSERT INTO actividad_aquatica (cod_actividad, profundidad_minima, requisitos_seguridad)
                        VALUES (:id, :prof, :req)
                    """),
                    {"id": cod_act, "prof": 1.50, "req": "Gorro y traje de baño"},
                )

        cod_actividades = [r[0] for r in conn.execute(text("SELECT cod_actividad FROM actividad")).fetchall()]

        # 8. Programaciones (200)
        for _ in range(200):
            h_ini = random.randint(8, 19)
            conn.execute(
                text("""
                    INSERT INTO programacion_actividad (
                        cod_actividad, numero_interno, rut_persona_instructor,
                        fecha, hora_inicio, hora_termino, cupos_disponibles, estado_ejecucion
                    )
                    VALUES (
                        :cod_actividad, :numero_interno, :rut_persona_instructor,
                        :fecha, :hora_inicio, :hora_termino, :cupos_disponibles, :estado_ejecucion
                    )
                """),
                {
                    "cod_actividad": random.choice(cod_actividades),
                    "numero_interno": random.choice(espacios),
                    "rut_persona_instructor": random.choice(ruts_instructores),
                    "fecha": fecha_random(120, 15),
                    "hora_inicio": f"{h_ini:02d}:00:00",
                    "hora_termino": f"{h_ini + 1:02d}:00:00",
                    "cupos_disponibles": random.randint(15, 30),
                    "estado_ejecucion": random.choice(["Finalizada", "Programada", "En Curso"]),
                },
            )

        programaciones = [r[0] for r in conn.execute(text("SELECT id_programacion FROM programacion_actividad")).fetchall()]

        # 9. Inscripciones (1100 sin duplicar programación + persona)
        usados = set()
        inscripciones = []
        while len(inscripciones) < 1100:
            id_pro = random.choice(programaciones)
            rut_par = random.choice(ruts_participantes)
            if (id_pro, rut_par) in usados:
                continue
            usados.add((id_pro, rut_par))

            estado = random.choice(["Confirmada", "Confirmada", "Cancelada"])
            asistencia = 1 if estado == "Confirmada" and random.random() < 0.75 else 0

            conn.execute(
                text("""
                    INSERT INTO inscripcion (
                        id_programacion, rut_persona, fecha_inscripcion,
                        estado_inscripcion, asistencia_efectiva, observaciones
                    )
                    VALUES (
                        :id_programacion, :rut_persona, :fecha_inscripcion,
                        :estado_inscripcion, :asistencia_efectiva, :observaciones
                    )
                """),
                {
                    "id_programacion": id_pro,
                    "rut_persona": rut_par,
                    "fecha_inscripcion": fecha_hora_random(120),
                    "estado_inscripcion": estado,
                    "asistencia_efectiva": asistencia,
                    "observaciones": "Sin observaciones",
                },
            )
            ins_id = conn.execute(text("SELECT LAST_INSERT_ID()")).scalar()
            inscripciones.append((ins_id, rut_par))

        # 10. Evaluaciones (600)
        for ins_id, rut_par in random.sample(inscripciones, 600):
            conn.execute(
                text("""
                    INSERT INTO evaluacion (
                        id_inscripcion, rut_persona, calificacion, comentario, fecha_evaluacion
                    )
                    VALUES (
                        :id_inscripcion, :rut_persona, :calificacion, :comentario, :fecha_evaluacion
                    )
                """),
                {
                    "id_inscripcion": ins_id,
                    "rut_persona": rut_par,
                    "calificacion": round(random.uniform(3.0, 7.0), 1),
                    "comentario": "Buena sesión",
                    "fecha_evaluacion": fecha_hora_random(90),
                },
            )

        # 11. Órdenes de mantención (120)
        for _ in range(120):
            f_sol = fecha_random(120, -5)
            estado_o = random.choice(["Resuelta", "Pendiente", "En Proceso"])
            f_res = (f_sol + timedelta(days=random.randint(1, 10))) if estado_o == "Resuelta" else None

            conn.execute(
                text("""
                    INSERT INTO orden_mantencion (
                        numero_interno, rut_persona_responsable, descripcion_problema,
                        prioridad, estado, fecha_solicitud, fecha_resolucion
                    )
                    VALUES (
                        :numero_interno, :rut_persona_responsable, :descripcion_problema,
                        :prioridad, :estado, :fecha_solicitud, :fecha_resolucion
                    )
                """),
                {
                    "numero_interno": random.choice(espacios),
                    "rut_persona_responsable": random.choice(ruts_mantencion),
                    "descripcion_problema": "Revisión general del espacio",
                    "prioridad": random.choice(["Baja", "Media", "Alta", "Crítica"]),
                    "estado": estado_o,
                    "fecha_solicitud": f_sol,
                    "fecha_resolucion": f_res,
                },
            )

    print("Listo, base de datos poblada.")


if __name__ == "__main__":
    poblar_todo()