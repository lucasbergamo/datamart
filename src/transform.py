import os
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", datefmt='%Y-%m-%d %H:%M:%S')

print("\n" + "="*50 + "\n")  # Separador visual para indicar o fim do carregamento de arquivos

raw_path  = "data/raw"
trusted_path = "data/trusted"

os.makedirs(trusted_path, exist_ok=True)

print('Iniciando Transformações')


arquivos = [f for f in os.listdir(raw_path) if f.endswith('.csv')]

# Carregar os arquivos CSV e armazenar como DataFrames
dfs = {arquivo: pd.read_csv(os.path.join(raw_path, arquivo)) for arquivo in arquivos}

# Exibir o nome dos arquivos carregados e o número de linhas de cada um
print("\n".join([f"Arquivo carregado: {arquivo} - {df.shape[0]} linhas" for arquivo, df in dfs.items()]))


def verificar_nulos(dfs):
    for arquivo, df in dfs.items():
        nulos = df.isnull().sum()
        nulos_existentes = nulos[nulos > 0]
        
        if not nulos_existentes.empty:
            logging.warning(f"⚠️ {arquivo} contém valores nulos:\n{nulos_existentes}")
        else:
            logging.info(f"✅ {arquivo}: sem valores nulos.")

verificar_nulos(dfs)

# Preencher valores nulos de forma mais controlada
for arquivo, df in dfs.items():
    dfs[arquivo] = df.fillna({
        col: 'Desconhecido' if df[col].dtype == 'object' else
             0 if df[col].dtype in ['float64', 'int64'] else
             pd.to_datetime('1970-01-01')
        for col in df.columns
    })

print("\n" + "="*50 + "\n")  # Separador visual para indicar o fim do carregamento de arquivos

# Remover duplicatas
for arquivo in dfs:
    dfs[arquivo] = dfs[arquivo].drop_duplicates()

# Verificar duplicatas

for arquivo, df in dfs.items():
    print(f"{arquivo} duplicados: {df.duplicated().sum()}")


dfs['cliente.csv'] = (
    dfs['cliente.csv']
    .assign(nome_cliente=lambda df: (df['nome'] + ' ' + df['sobrenome']).str.title())
    .drop(columns=['nome', 'sobrenome'])
    .rename(columns={'id': 'id_cliente', 'telefone': 'telefone', 'email': 'email'})
)

dfs['produtos.csv'] = (
    dfs['produtos.csv']
    .drop(columns=['EAN'])
    .rename(columns={'id': 'id_produto', 'Nome': 'nome_produto', 'Descrição': 'categoria', 'Preço': 'preco'})
)


transacoes = (
    pd.concat([dfs['transacoes_1.csv'], dfs['transacoes_2.csv'], dfs['transacoes_3.csv']], ignore_index=True)
    .assign(data_transacao=lambda df: pd.to_datetime(df['data_transacao']).dt.date)
    .drop_duplicates()
)


# Salvar apenas os arquivos desejados

arquivos_para_salvar = {
    'cliente.parquet': dfs['cliente.csv'],
    'produtos.parquet': dfs['produtos.csv'],
    'transacoes.parquet': transacoes
}


# Salvar os arquivos transformados em Parquet
for nome_arquivo, df in arquivos_para_salvar.items():
    parquet_file = os.path.join(trusted_path, nome_arquivo)
    df.to_parquet(parquet_file, index=False, compression='snappy', engine='pyarrow')
    print(f"Arquivo salvo: {parquet_file}")


print("\n" + "="*50 + "\n")  # Separador visual
print("📊 Visualização das primeiras 5 linhas de cada tabela:\n")

for nome_arquivo, df in arquivos_para_salvar.items():
    num_linhas = df.shape[0]  # Número de linhas do DataFrame
    print(f"\n🔹 {nome_arquivo} (Top 5 linhas, {num_linhas} linhas no total):")
    print(df.head())
    print("\n" + "-"*50 + "\n")  # Separador visual entre tabelas
  

print("\nArquivos transformados salvos em formato Parquet na pasta 'trusted'")


