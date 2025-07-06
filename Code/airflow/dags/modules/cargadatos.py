import pandas as pd
def cargar_datos_clientes(**kwargs):
    conf = kwargs["dag_run"].conf
    df = pd.read_csv(conf["clientes_path"], sep=";")
    print("Clientes cargados:", df.shape)
    kwargs['ti'].xcom_push(key='clientes_df', value=df)

def cargar_datos_servicios(**kwargs):
    conf = kwargs["dag_run"].conf
    df = pd.read_excel(conf["servicios_path"])
    print("Servicios cargados df:", df.head())
    kwargs['ti'].xcom_push(key='servicios_df', value=df)