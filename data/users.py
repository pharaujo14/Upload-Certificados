def get_bdr_users(db):
    """
    Retorna lista de nomes dos usuários com role 'bdr'
    """
    usuarios_collection = db["users"]  # ajuste se o nome for outro

    cursor = usuarios_collection.find(
        {"role": "bdr"},
        {"_id": 0, "nome": 1}
    )

    return sorted([user["nome"] for user in cursor if "nome" in user])
