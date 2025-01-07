# Importa a classe MongoClient da biblioteca pymongo.
# Isso nos permitirá conectar a um banco de dados MongoDB.
from pymongo import MongoClient

def conectaBanco(username, password):
    # Cria um objeto MongoClient. Este objeto representa uma conexão de cliente com o banco de dados MongoDB.
    # Usamos uma f-string para formatar a string de conexão com o nome de usuário e a senha.
    # O URI de conexão inclui o nome de usuário, senha e informações do cluster.
    client = MongoClient(f'mongodb+srv://{username}:{password}@centurydatamongocluster.k5fsf.mongodb.net/?retryWrites=true&w=majority&appName=CenturyDataMongoCluster')
    db = client["CenturyData"]
    return db["certificados"]