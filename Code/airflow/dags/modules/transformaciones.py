### TRANSFORMACIONES.PY
import pandas as pd

def transformar_datos_clientes(**kwargs):


    ti = kwargs['ti']
    df = ti.xcom_pull(task_ids='cargar_datos_clientes', key='clientes_df')
    print(" Antes de limpieza (clientes):", df.shape)


    df = df.fillna(df.median(numeric_only=True))
    df = df.fillna("desconocido") 

    print("\ Despues de limpieza (clientes):", df.shape)
    ti.xcom_push(key='clientes_limpios', value=df)

def transformar_datos_servicios(**kwargs):
    ti = kwargs['ti']
    df = ti.xcom_pull(task_ids='cargar_datos_servicios', key='servicios_df')
    print("Antes de limpieza (servicios):", df.shape)
    df = df.fillna(df.median(numeric_only=True))
    df = df.fillna("desconocido") 
    print("Despues de limpieza (servicios):", df.shape)
    ti.xcom_push(key='servicios_limpios', value=df)

def transformacion_final(**kwargs):
    import os
    import pickle
    from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler

    ti = kwargs['ti']
    conf = kwargs["dag_run"].conf
    usar_kbest = conf.get("usar_kbest", True)
    k = int(conf.get("k", 10))
    metodo_escalado = conf.get("metodo_escalado", "standard")

    df_clientes = ti.xcom_pull(task_ids='transformar_datos_clientes', key='clientes_limpios')
    df_servicios = ti.xcom_pull(task_ids='transformar_datos_servicios', key='servicios_limpios')

    if df_clientes is None or df_servicios is None:
        raise ValueError("No se encontraron datos en XCom (clientes o servicios)")

    df = unificar_datos(df_clientes, df_servicios)
    print("Antes de transformación final:", df.shape)
    df = df.drop(columns=['id_cliente'])

    df = codificar_variables(df, ti=ti)
    df = balancear_clases(df, target_col='abandono')

    X = df.drop(columns=['abandono'])
    y = df['abandono']

    if metodo_escalado == "standard":
        scaler = StandardScaler()
    elif metodo_escalado == "minmax":
        scaler = MinMaxScaler()
    elif metodo_escalado == "robust":
        scaler = RobustScaler()
    else:
        raise ValueError(f"Método de escalado no reconocido: {metodo_escalado}")

    X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=X.columns)

    # Guardar artefactos en /tmp para ser loggeados en MLflow
    os.makedirs("/tmp/artefactos_modelo", exist_ok=True)

    # ✅ Scaler
    scaler_path = "/tmp/artefactos_modelo/scaler.pkl"
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)
    ti.xcom_push(key='scaler_path', value=scaler_path)

    # ✅ Columnas entrenamiento
    columnas_path = "/tmp/artefactos_modelo/columnas_entrenamiento.txt"
    with open(columnas_path, "w") as f:
        for col in X.columns:
            f.write(col + "\n")
    ti.xcom_push(key='columnas_path', value=columnas_path)

    # ✅ SelectKBest (si aplica)
    if usar_kbest:
        df_final = seleccionar_caracteristicas(X_scaled, y, k)

        kbest_path = "/tmp/artefactos_modelo/kbest_columnas.txt"
        with open(kbest_path, "w") as f:
            for col in df_final.columns:
                f.write(col + "\n")
        ti.xcom_push(key='kbest_path', value=kbest_path)
    else:
        df_final = X_scaled

    # ✅ Añadir columna target
    df_final['abandono'] = y.reset_index(drop=True)

    # Exportar CSV final
    output_path = '/opt/airflow/dags/data/datos_unificados.csv'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_final.to_csv(output_path, index=False)
    ti.xcom_push(key='datos_finales', value=df_final)

    print(f"✅ Transformación final completada y artefactos guardados: {df_final.shape}")



def unificar_datos(df_clientes, df_servicios):
    df_clientes.columns = df_clientes.columns.str.strip().str.lower()
    df_servicios.columns = df_servicios.columns.str.strip().str.lower()

    if 'id_cliente' not in df_clientes.columns or 'id_cliente' not in df_servicios.columns:
        raise KeyError("La columna 'id_cliente' no existe en uno de los DataFrames.")

    df_unificado = pd.merge(df_clientes, df_servicios, on="id_cliente", how="inner")
    print(" Datos unificados:", df_unificado.shape)
    return df_unificado

def codificar_variables(df, ti=None):
    from sklearn.preprocessing import LabelEncoder
    import pickle
    import os

    label_encoders = {}
    df_copiado = df.copy()

    for col in df_copiado.select_dtypes(include='object').columns:
        le = LabelEncoder()
        df_copiado[col] = le.fit_transform(df_copiado[col].astype(str))
        label_encoders[col] = le

    if ti:
        # Guardar los codificadores para loguear en MLflow
        os.makedirs("/tmp/artefactos_modelo", exist_ok=True)
        label_encoders_path = "/tmp/artefactos_modelo/label_encoders.pkl"
        with open(label_encoders_path, "wb") as f:
            pickle.dump(label_encoders, f)

        ti.xcom_push(key="label_encoders_path", value=label_encoders_path)

    return df_copiado


def balancear_clases(df, target_col='abandono'):
    from sklearn.utils import resample

    clase_mayor = df[df[target_col] == df[target_col].mode()[0]]
    clase_menor = df[df[target_col] != df[target_col].mode()[0]]

    clase_menor_upsampled = resample(clase_menor,
                                     replace=True,
                                     n_samples=len(clase_mayor),
                                     random_state=42)
    return pd.concat([clase_mayor, clase_menor_upsampled])

def seleccionar_caracteristicas(X, y, k=10, ti=None):
    from sklearn.feature_selection import SelectKBest, f_classif
    import os

    selector = SelectKBest(score_func=f_classif, k=min(k, X.shape[1]))
    X_new = selector.fit_transform(X, y)
    columnas_seleccionadas = X.columns[selector.get_support()]
    X_df = pd.DataFrame(X_new, columns=columnas_seleccionadas)

    if ti:
        os.makedirs("/tmp/artefactos_modelo", exist_ok=True)
        kbest_path = "/tmp/artefactos_modelo/kbest_columnas.txt"
        with open(kbest_path, "w") as f:
            for col in columnas_seleccionadas:
                f.write(col + "\n")
        ti.xcom_push(key='kbest_path', value=kbest_path)

    return X_df
