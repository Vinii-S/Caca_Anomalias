import sqlite3
import pandas as pd

df = pd.read_json('transacoes_treino.json')

conn = sqlite3.connect('Conexao.db')

df.to_sql('transacoes', conn, if_exists='append', index=False, chunksize=1000)

conn.close()